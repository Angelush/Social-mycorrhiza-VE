from pathlib import Path
from random import Random

from engine.measurement import Distribution, WelfareReport, assert_no_person_scalar
from engine.policy import RulePolicy
from sim_b2b.adapter import B2BAdapter
from sim_b2b.config import RoundConfig
from sim_b2b.policies_adversarial import Defrauder
from sim_b2b.policies_core import Circulator, ClearingScheduler, Hoarder
from sim_b2b.topology import generate_trade_graph
from sim_b2b.track_b import B2BTrackB, contracyclical_delta
from sim_b2b.world import B2BWorld

B2B_ROOT = Path(__file__).resolve().parent.parent.parent / "B2B-VE"

CFG = RoundConfig(
    actor_mix={}, n_firms=8, T=20, clearing_cadence=5, base_turnover_cents=10_000_000,
    neg_line_bp=1000, pos_line_bp=1000, topology_params={}, adversary_intensity=0.5,
    velocity_window_s=1, ticks_per_second=10, velocity_max_cents=500_000, credit_crunch=False, seed=7,
)


class _NullPolicy(RulePolicy):
    def act(self, view, rng):
        return None


def _build_cell():
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
    bounds = {}
    for fid in neighbors:
        adapter.add_member({"id": fid, "turnover_cents": CFG.base_turnover_cents}, ratified_by="ops", ts=0)
        stmt = adapter.member_statement(fid, "comite_credito")
        bounds[fid] = {"credit_min_cents": stmt["credit_min_cents"], "credit_max_cents": stmt["credit_max_cents"]}
    return adapter, neighbors, bounds


def test_cooperative_trace_produces_a_sane_welfare_report():
    adapter, neighbors, bounds = _build_cell()
    actors = {fid: Circulator(fid) for fid in neighbors}
    actors["__clearing_scheduler__"] = ClearingScheduler(cadence_ticks=CFG.clearing_cadence)
    world = B2BWorld(adapter, actors, CFG, neighbors, rng=Random(1))
    for _ in range(CFG.T):
        world.step()

    track_b = B2BTrackB(known_bounds=bounds)
    report = track_b.measure(world.trace)

    assert isinstance(report, WelfareReport)
    assert 0.0 <= report.metrics["net_debt_reduction_clearing_only_pct"] <= 100.0
    gini_dist = report.metrics["clearing_benefit_gini"]
    assert isinstance(gini_dist, Distribution)
    assert 0.0 <= gini_dist.summary["gini"] <= 1.0 + 1e-9
    assert report.metrics["credit_enabled_liquidity_cents"] >= 0.0


def test_hoarder_activity_shows_up_as_blocked_or_redistributed():
    adapter, neighbors, bounds = _build_cell()
    fids = list(neighbors)
    actors = {fids[0]: Hoarder(fids[0], bite_size_cents=2_000_000)}
    actors.update({fid: Circulator(fid) for fid in fids[1:]})
    world = B2BWorld(adapter, actors, CFG, neighbors, rng=Random(2))
    for _ in range(CFG.T):
        world.step()

    track_b = B2BTrackB(known_bounds=bounds)
    report = track_b.measure(world.trace)

    blocked = report.metrics["positive_cap_blocked_cents"]
    redistributed = report.metrics["positive_cap_redistributed_cents"]
    assert blocked > 0.0 or redistributed > 0.0, (
        "a Hoarder pushing 2,000,000-cent bites against a 1,000,000-cent cap must register "
        "as either blocked or redistributed near-cap activity"
    )


def test_defrauder_produces_a_nonzero_mutualisation_distribution():
    adapter, neighbors, bounds = _build_cell()
    fids = list(neighbors)
    defrauder_id = fids[0]
    actors = {defrauder_id: Defrauder(defrauder_id, bite_size_cents=200_000)}
    actors.update({fid: _NullPolicy() for fid in fids[1:]})
    world = B2BWorld(adapter, actors, CFG, neighbors, rng=Random(3))
    for _ in range(30):
        world.step()

    track_b = B2BTrackB(known_bounds=bounds)
    report = track_b.measure(world.trace)

    mutualisation = report.metrics["default_mutualisation_cents"]
    assert isinstance(mutualisation, Distribution)
    assert mutualisation.summary["n_creditor_events"] > 0
    assert mutualisation.summary["total_cents"] > 0
    # identity-free by construction: only aggregate scalars/samples, never a per-creditor map
    assert isinstance(mutualisation.samples, tuple)


def test_no_person_scalar_ever_slips_through():
    adapter, neighbors, bounds = _build_cell()
    actors = {fid: Circulator(fid) for fid in neighbors}
    world = B2BWorld(adapter, actors, CFG, neighbors, rng=Random(4))
    for _ in range(CFG.T):
        world.step()

    track_b = B2BTrackB(known_bounds=bounds)
    report = track_b.measure(world.trace)
    assert_no_person_scalar(report, frozenset({"trust_score", "reputation", "reliability_score"}))


def test_contracyclical_delta_computes_the_difference():
    with_crunch = WelfareReport(metrics={
        "net_debt_reduction_combined_pct": 40.0, "credit_enabled_liquidity_cents": 500_000.0,
    })
    without_crunch = WelfareReport(metrics={
        "net_debt_reduction_combined_pct": 25.0, "credit_enabled_liquidity_cents": 300_000.0,
    })
    delta = contracyclical_delta(with_crunch, without_crunch)
    assert delta["reduction_pct_combined_delta"] == 15.0
    assert delta["liquidity_delta_cents"] == 200_000.0
