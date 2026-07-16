from pathlib import Path
from random import Random

from engine.measurement import Verdict
from engine.types import TraceEvent
from sim_b2b.adapter import B2BAdapter
from sim_b2b.config import RoundConfig
from sim_b2b.policies_adversarial import VelocityAttacker
from sim_b2b.policies_core import Circulator, ClearingScheduler, ComplianceOfficer
from sim_b2b.topology import generate_trade_graph
from sim_b2b.track_a import B2BTrackA
from sim_b2b.world import B2BWorld

B2B_ROOT = Path(__file__).resolve().parent.parent.parent / "B2B-VE"

CFG = RoundConfig(
    actor_mix={}, n_firms=8, T=15, clearing_cadence=5, base_turnover_cents=10_000_000,
    neg_line_bp=1000, pos_line_bp=1000, topology_params={}, adversary_intensity=0.5,
    velocity_window_s=1, ticks_per_second=10, velocity_max_cents=500_000, credit_crunch=False, seed=7,
)


def _build_cell_with_setup_events():
    adapter = B2BAdapter(B2B_ROOT)
    adapter.create_cell(
        "cell-1",
        {
            "moneda": "USD", "sal_seudonimo": "sim-ve-sal",
            "neg_line_bp": CFG.neg_line_bp, "pos_line_bp": CFG.pos_line_bp,
            "velocity_window_s": CFG.velocity_window_s, "velocity_max_cents": CFG.velocity_max_cents,
        },
        ratified_by="ops", ts=0,
    )
    neighbors = generate_trade_graph(CFG.n_firms, seed=CFG.seed)
    setup_events = []
    for fid in neighbors:
        adapter.add_member({"id": fid, "turnover_cents": CFG.base_turnover_cents}, ratified_by="ops", ts=0)
        stmt = adapter.member_statement(fid, "comite_credito")
        setup_events.append(
            TraceEvent(
                tick=-1, actor_id="__setup__", proposal=None,
                result={
                    "kind": "member_added",
                    "payload": {
                        "member": {
                            "id": fid,
                            "turnover_cents": CFG.base_turnover_cents,
                            "credit_min_cents": stmt["credit_min_cents"],
                            "credit_max_cents": stmt["credit_max_cents"],
                        },
                        "ratified_by": "ops",
                    },
                },
            )
        )
    return adapter, neighbors, setup_events


def test_conservation_and_credit_bound_pass_on_real_cooperative_trace():
    adapter, neighbors, setup_events = _build_cell_with_setup_events()
    actors = {fid: Circulator(fid) for fid in neighbors}
    actors["__clearing_scheduler__"] = ClearingScheduler(cadence_ticks=CFG.clearing_cadence)
    world = B2BWorld(adapter, actors, CFG, neighbors, rng=Random(1))
    for _ in range(CFG.T):
        world.step()

    full_trace = setup_events + list(world.trace)
    track_a = B2BTrackA(velocity_window_s=CFG.velocity_window_s, velocity_max_cents=CFG.velocity_max_cents)
    report = track_a.measure(full_trace)

    assert report.results["conservation"].verdict is Verdict.PASS, report.results["conservation"].exploit_trace
    assert report.results["credit_bound"].verdict is Verdict.PASS, report.results["credit_bound"].exploit_trace
    assert report.results["firewall"].verdict is Verdict.PASS, report.results["firewall"].exploit_trace
    assert report.violation is False


def test_velocity_oracle_confirms_the_cap_holds_under_a_live_attack():
    adapter, neighbors, setup_events = _build_cell_with_setup_events()
    fids = list(neighbors)
    actors = {fids[0]: VelocityAttacker(fids[0], burst_cents=300_000, target_neighbor=fids[1])}
    actors.update({fid: Circulator(fid) for fid in fids[1:]})
    world = B2BWorld(adapter, actors, CFG, neighbors, rng=Random(5))
    for _ in range(5):
        world.step()

    full_trace = setup_events + list(world.trace)
    track_a = B2BTrackA(velocity_window_s=CFG.velocity_window_s, velocity_max_cents=CFG.velocity_max_cents)
    report = track_a.measure(full_trace)

    # the attack is rejected by the real ledger, so the invariant HOLDS -- PASS is the
    # correct, expected outcome (the finding is in Track B / the attempt count, not here)
    assert report.results["velocity"].verdict is Verdict.PASS, report.results["velocity"].exploit_trace


def test_sanctions_reports_descriptive_findings_without_failing():
    adapter, neighbors, setup_events = _build_cell_with_setup_events()
    actors = {fid: Circulator(fid) for fid in neighbors}
    actors["__compliance_officer__"] = ComplianceOfficer(warn_threshold_cents=-1)
    world = B2BWorld(adapter, actors, CFG, neighbors, rng=Random(9))
    for _ in range(CFG.T):
        world.step()

    full_trace = setup_events + list(world.trace)
    track_a = B2BTrackA(velocity_window_s=CFG.velocity_window_s, velocity_max_cents=CFG.velocity_max_cents)
    report = track_a.measure(full_trace)

    assert report.results["sanctions"].verdict is Verdict.PASS
    findings = report.results["sanctions"].exploit_trace
    assert "line_reduction_rejections_on_drawn_down_members" in findings
    assert "unrestricted_downward_rehabilitations" in findings
    assert findings["line_reduction_rejections_on_drawn_down_members"] >= 0
    assert findings["unrestricted_downward_rehabilitations"] >= 0


def _setup_two_members(min_a=-1_000_000, max_a=1_000_000, min_b=-1_000_000, max_b=1_000_000):
    def ev(mid, cmin, cmax):
        return TraceEvent(
            tick=-1, actor_id="__setup__", proposal=None,
            result={
                "kind": "member_added",
                "payload": {
                    "member": {"id": mid, "turnover_cents": 10_000_000, "credit_min_cents": cmin, "credit_max_cents": cmax},
                    "ratified_by": "ops",
                },
            },
        )
    return [ev("A", min_a, max_a), ev("B", min_b, max_b)]


def _obligation_event(oid, debtor, creditor, amount, tick, ts):
    return TraceEvent(
        tick=tick, actor_id=debtor, proposal=None,
        result={
            "kind": "obligation_recorded", "ts": ts,
            "payload": {"obligation": {"id": oid, "debtor": debtor, "creditor": creditor, "amount_cents": amount}},
        },
    )


def test_conservation_catches_a_hand_crafted_uneven_cycle_reduction():
    # A->B 100, B->C 100, C->A 100 is a perfect cycle: a true clearing must reduce all three
    # edges by the SAME amount or someone's net position changes. This plants an uneven
    # reduction (100, 100, 99) directly in a hand-built ClearingOutcome -- exactly the shape
    # of corruption a silent-conservation-breach SUT plant would produce -- and confirms the
    # independent recompute (not a re-display of the solver's own numbers) actually catches it.
    from sim_b2b.world import ClearingOutcome

    setup = _setup_two_members() + [
        TraceEvent(
            tick=-1, actor_id="__setup__", proposal=None,
            result={
                "kind": "member_added",
                "payload": {
                    "member": {"id": "C", "turnover_cents": 10_000_000, "credit_min_cents": -1_000_000, "credit_max_cents": 1_000_000},
                    "ratified_by": "ops",
                },
            },
        )
    ]
    records = [
        _obligation_event("o1", "A", "B", 100, tick=0, ts=0),
        _obligation_event("o2", "B", "C", 100, tick=0, ts=0),
        _obligation_event("o3", "C", "A", 100, tick=0, ts=0),
    ]
    bad_proposal = {
        "cell_id": "cell-1",
        "settlements": [
            {"obligation_id": "o1", "reduce_by_cents": 100},
            {"obligation_id": "o2", "reduce_by_cents": 100},
            {"obligation_id": "o3", "reduce_by_cents": 99},  # <- the planted 1-cent drop
        ],
        "residual_obligations": [{"debtor": "C", "creditor": "A", "amount_cents": 1}],
        "net_positions": {"A": 0, "B": 0, "C": 0},  # solver's own (also-corrupted) self-report
        "credit_flags": [],
    }
    clearing_event = TraceEvent(
        tick=1, actor_id="__clearing_scheduler__", proposal=None,
        result=ClearingOutcome(
            proposal=bad_proposal,
            applied_event={"kind": "clearing_applied", "payload": {"proposal": bad_proposal}},
        ),
    )

    track_a = B2BTrackA(velocity_window_s=1, velocity_max_cents=10_000_000)
    report = track_a.measure(setup + records + [clearing_event])

    assert report.results["conservation"].verdict is Verdict.FAIL
    assert report.violation is True


def test_silent_clamp_on_trade_is_detected():
    from sim_b2b.proposals import Trade

    setup = _setup_two_members()
    clamped_event = TraceEvent(
        tick=0, actor_id="A",
        proposal=Trade(obligation_id="o1", debtor="A", creditor="B", cents=500),  # requested 500
        result={
            "kind": "obligation_recorded", "ts": 0,
            "payload": {"obligation": {"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 400}},  # committed 400
        },
    )
    track_a = B2BTrackA(velocity_window_s=1, velocity_max_cents=10_000_000)
    report = track_a.measure(setup + [clamped_event])

    assert report.results["credit_bound"].verdict is Verdict.FAIL
    assert report.results["credit_bound"].exploit_trace["kind"] == "silent_clamp_trade"


def test_firewall_flags_an_accepted_obligation_naming_an_unknown_member():
    setup = _setup_two_members()  # only A and B are known
    foreign_event = _obligation_event("o1", "A", "ghost-firm", 100, tick=0, ts=0)

    track_a = B2BTrackA(velocity_window_s=1, velocity_max_cents=10_000_000)
    report = track_a.measure(setup + [foreign_event])

    assert report.results["firewall"].verdict is Verdict.FAIL
    assert report.results["firewall"].exploit_trace["kind"] == "accepted_unknown_member"


def test_velocity_replay_catches_an_independently_over_cap_accepted_sequence():
    setup = _setup_two_members()
    # two accepted 60-cent obligations from A within the same 1-second window, cap is 100:
    # 60 alone is fine, but the cumulative 120 within the window independently exceeds it --
    # this simulates what an accepted-but-actually-over-cap sequence would look like if the
    # ledger's own velocity enforcement were bypassed.
    events = [
        _obligation_event("o1", "A", "B", 60, tick=0, ts=0),
        _obligation_event("o2", "A", "B", 60, tick=1, ts=0),
    ]
    track_a = B2BTrackA(velocity_window_s=1, velocity_max_cents=100)
    report = track_a.measure(setup + events)

    assert report.results["velocity"].verdict is Verdict.FAIL
    assert report.results["velocity"].exploit_trace["debtor"] == "A"
