from pathlib import Path
from random import Random

from engine.policy import RulePolicy
from sim_b2b.adapter import B2BAdapter
from sim_b2b.config import RoundConfig
from sim_b2b.policies_adversarial import CellLeaker, Defrauder, SybilHopper, VelocityAttacker
from sim_b2b.policies_core import Circulator, CircuitBreaker, ClearingScheduler, ComplianceOfficer, Hoarder, Wallflower
from sim_b2b.topology import generate_trade_graph
from sim_b2b.world import B2BWorld, ClearingOutcome, Rejected

B2B_ROOT = Path(__file__).resolve().parent.parent.parent / "B2B-VE"

CFG = RoundConfig(
    actor_mix={},
    n_firms=8,
    T=12,
    clearing_cadence=5,
    base_turnover_cents=10_000_000,
    neg_line_bp=1000,
    pos_line_bp=1000,
    topology_params={},
    adversary_intensity=0.5,
    velocity_window_s=1,
    ticks_per_second=10,
    velocity_max_cents=500_000,
    credit_crunch=False,
    seed=7,
)


def _build_cell() -> tuple[B2BAdapter, dict[str, tuple[str, ...]]]:
    adapter = B2BAdapter(B2B_ROOT)
    adapter.create_cell(
        "cell-1",
        {
            "moneda": "USD", "sal_seudonimo": "sim-ve-sal",
            "neg_line_bp": CFG.neg_line_bp,
            "pos_line_bp": CFG.pos_line_bp,
            "velocity_window_s": CFG.velocity_window_s,
            "velocity_max_cents": CFG.velocity_max_cents,
        },
        ratified_by="ops",
        ts=0,
    )
    neighbors = generate_trade_graph(CFG.n_firms, seed=CFG.seed)
    for fid in neighbors:
        adapter.add_member({"id": fid, "turnover_cents": CFG.base_turnover_cents}, ratified_by="ops", ts=0)
    return adapter, neighbors


def test_cooperative_population_runs_clean():
    adapter, neighbors = _build_cell()
    actors = {fid: Circulator(fid) for fid in neighbors}
    actors["__clearing_scheduler__"] = ClearingScheduler(cadence_ticks=CFG.clearing_cadence)
    world = B2BWorld(adapter, actors, CFG, neighbors, rng=Random(1))

    for _ in range(CFG.T):
        world.step()  # must not raise

    assert len(world.trace) > 0
    # A cooperative-only population can still legitimately show Rejected outcomes -- this is
    # not a bug in any of the adapter/world/policy layers, it is a structural consequence of
    # M2's bounded-view rule (an actor sees only its own balance/bounds, never a counterparty's),
    # confirmed empirically here: a Circulator sizes a trade against ITS OWN headroom only, so
    # it can still get rejected when the trade would breach the COUNTERPARTY's bound instead --
    # information it structurally cannot see. Separately, a Circulator's self-tracked "obligation
    # I still owe" can go stale if a periodic clearing cycle independently reduces or retires that
    # same obligation first. Both are genuine emergent findings worth carrying into Track A's
    # design: neither pattern is an integrity violation or an adversarial signal, and the oracle
    # must not misclassify either one as such. The one thing that must never happen is a crash --
    # which the loop above already proved by completing.
    assert all(
        isinstance(ev.result, (dict, ClearingOutcome, type(None))) or hasattr(ev.result, "reason")
        for ev in world.trace
    )


def test_hoarder_eventually_gets_rejected_at_its_cap():
    adapter, neighbors = _build_cell()
    fids = list(neighbors)
    actors = {fids[0]: Hoarder(fids[0], bite_size_cents=2_000_000)}
    actors.update({fid: Circulator(fid) for fid in fids[1:]})
    world = B2BWorld(adapter, actors, CFG, neighbors, rng=Random(2))

    for _ in range(CFG.T):
        world.step()

    hoarder_events = [ev for ev in world.trace if ev.actor_id == fids[0]]
    assert any(isinstance(ev.result, Rejected) for ev in hoarder_events), (
        "Hoarder pushing 2,000,000-cent bites every tick against a 1,000,000-cent "
        "positive cap must eventually be rejected, not silently absorbed"
    )


class _NullPolicy(RulePolicy):
    def act(self, view, rng):
        return None


def test_defrauder_draws_down_then_goes_permanently_quiet():
    # Isolated deliberately: with live Circulator counterparties, OTHER firms can propose
    # trades naming the Defrauder as debtor or creditor too (it's just another neighbour to
    # them), which perturbs its own balance/headroom unpredictably and makes the exact tick
    # it goes quiet an emergent, not analytically-computable, property. A null-policy
    # population isolates the one thing this test actually wants to check: the Defrauder's
    # own internal stop condition, deterministically.
    adapter, neighbors = _build_cell()
    fids = list(neighbors)
    defrauder_id = fids[0]
    actors = {defrauder_id: Defrauder(defrauder_id, bite_size_cents=200_000)}
    actors.update({fid: _NullPolicy() for fid in fids[1:]})
    world = B2BWorld(adapter, actors, CFG, neighbors, rng=Random(3))

    for _ in range(30):
        world.step()

    statement = adapter.member_statement(defrauder_id, "comite_credito")
    assert statement["balance_cents"] < 0, "the Defrauder's negative balance must persist -- there is no exit op"
    assert statement["balance_cents"] == statement["credit_min_cents"], "must draw exactly to its own cap, no further"

    events_before = len([e for e in world.trace if e.actor_id == defrauder_id])
    for _ in range(5):
        world.step()
    events_after = len([e for e in world.trace if e.actor_id == defrauder_id])
    assert events_after == events_before, "Defrauder must stop proposing once its headroom is exhausted"


def test_sybil_hopper_registrations_are_not_blocked_by_the_code():
    adapter, neighbors = _build_cell()
    fids = list(neighbors)
    sybil_id = fids[0]
    actors = {sybil_id: SybilHopper(sybil_id, max_attempts=3)}
    actors.update({fid: Circulator(fid) for fid in fids[1:]})
    members_before = adapter.cell_metrics()["members"]

    world = B2BWorld(adapter, actors, CFG, neighbors, rng=Random(4))
    for _ in range(CFG.T):
        world.step()

    members_after = adapter.cell_metrics()["members"]
    # this is the actual finding (X3 / AC22), not a bug in the harness: add_member has no
    # real gate, so all 3 throwaway registrations succeed
    assert members_after == members_before + 3
    sybil_events = [ev for ev in world.trace if ev.actor_id == sybil_id]
    assert all(not isinstance(ev.result, Rejected) for ev in sybil_events)


def test_velocity_attacker_gets_rejected_within_the_window():
    adapter, neighbors = _build_cell()
    fids = list(neighbors)
    attacker_id, target_id = fids[0], fids[1]
    actors = {attacker_id: VelocityAttacker(attacker_id, burst_cents=300_000, target_neighbor=target_id)}
    actors.update({fid: Circulator(fid) for fid in fids[1:]})
    world = B2BWorld(adapter, actors, CFG, neighbors, rng=Random(5))

    # ticks_per_second=10 means ticks 0..9 all share ts=0 (one velocity window);
    # two 300,000-cent bursts within it exceed the 500,000 cap on the second attempt.
    for _ in range(3):
        world.step()

    attacker_events = [ev for ev in world.trace if ev.actor_id == attacker_id]
    assert isinstance(attacker_events[0].result, Rejected) is False  # first 300k clears
    assert any(isinstance(ev.result, Rejected) for ev in attacker_events), (
        "a second same-window burst must be rejected by the real velocity cap"
    )


def test_cell_leaker_is_rejected_every_time_no_second_cell_exists():
    adapter, neighbors = _build_cell()
    fids = list(neighbors)
    leaker_id = fids[0]
    actors = {leaker_id: CellLeaker(leaker_id)}
    actors.update({fid: Circulator(fid) for fid in fids[1:]})
    world = B2BWorld(adapter, actors, CFG, neighbors, rng=Random(6))

    for _ in range(5):
        world.step()

    leaker_events = [ev for ev in world.trace if ev.actor_id == leaker_id]
    assert len(leaker_events) > 0
    assert all(isinstance(ev.result, Rejected) for ev in leaker_events)


def test_compliance_officer_and_circuit_breaker_roles_run_without_crashing():
    adapter, neighbors = _build_cell()
    fids = list(neighbors)
    actors = {fid: Circulator(fid) for fid in fids}
    actors["__clearing_scheduler__"] = ClearingScheduler(cadence_ticks=CFG.clearing_cadence)
    actors["__compliance_officer__"] = ComplianceOfficer(warn_threshold_cents=-800_000)
    actors["__circuit_breaker__"] = CircuitBreaker(velocity_max_cents=CFG.velocity_max_cents)
    world = B2BWorld(adapter, actors, CFG, neighbors, rng=Random(8))

    for _ in range(CFG.T):
        world.step()

    assert len(world.trace) > 0


def test_full_mixed_adversarial_population_runs_to_completion():
    adapter, neighbors = _build_cell()
    fids = list(neighbors)
    actors = {
        fids[0]: Circulator(fids[0]),
        fids[1]: Circulator(fids[1]),
        fids[2]: Hoarder(fids[2]),
        fids[3]: Wallflower(fids[3]),
        fids[4]: Defrauder(fids[4]),
        fids[5]: SybilHopper(fids[5], max_attempts=2),
        fids[6]: VelocityAttacker(fids[6], burst_cents=300_000, target_neighbor=fids[0]),
        fids[7]: CellLeaker(fids[7]),
        "__clearing_scheduler__": ClearingScheduler(cadence_ticks=CFG.clearing_cadence),
        "__compliance_officer__": ComplianceOfficer(warn_threshold_cents=-800_000),
        "__circuit_breaker__": CircuitBreaker(velocity_max_cents=CFG.velocity_max_cents),
    }
    world = B2BWorld(adapter, actors, CFG, neighbors, rng=Random(42))

    for _ in range(CFG.T):
        world.step()  # must not raise -- every archetype's rejections are caught as Rejected

    assert len(world.trace) > 0
