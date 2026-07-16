from pathlib import Path

from sim_b2b.campaign import build_campaign
from sim_b2b.config import RoundConfig

B2B_ROOT = Path(__file__).resolve().parent.parent.parent / "B2B-VE"


def _cfg(**overrides):
    base = dict(
        actor_mix={
            "circulator": 0.5, "hoarder": 0.1, "wallflower": 0.1,
            "defrauder": 0.1, "velocity_attacker": 0.1, "cell_leaker": 0.1,
        },
        n_firms=10, T=15, clearing_cadence=5, base_turnover_cents=10_000_000,
        neg_line_bp=1000, pos_line_bp=1000, topology_params={}, adversary_intensity=0.3,
        velocity_window_s=1, ticks_per_second=10, velocity_max_cents=500_000,
        credit_crunch=False, seed=42,
    )
    base.update(overrides)
    return RoundConfig(**base)


def test_full_campaign_runs_to_completion_and_never_violates():
    result = build_campaign(_cfg(), B2B_ROOT, max_rounds=3)

    assert result.halted is False
    assert len(result.history) == 3
    assert len(result.journal.entries) == 3
    assert result.journal.verify_chain() is True
    for record in result.history:
        assert record.integrity_report.violation is False, record.integrity_report.failed_invariants


def test_campaign_is_reproducible_across_two_independent_builds():
    result1 = build_campaign(_cfg(), B2B_ROOT, max_rounds=2)
    result2 = build_campaign(_cfg(), B2B_ROOT, max_rounds=2)

    hashes1 = [e.entry_hash for e in result1.journal.entries]
    hashes2 = [e.entry_hash for e in result2.journal.entries]
    assert hashes1 == hashes2
    assert len(hashes1) == 2


def test_researcher_nudges_adversary_intensity_across_rounds():
    result = build_campaign(_cfg(T=5), B2B_ROOT, max_rounds=3)
    intensities = [r.config["adversary_intensity"] for r in result.history]

    assert intensities[0] == 0.3
    assert intensities[1] > intensities[0]
    assert intensities[2] > intensities[1]


def test_campaign_produces_a_usable_welfare_report_each_round():
    result = build_campaign(_cfg(), B2B_ROOT, max_rounds=2)
    for record in result.history:
        metrics = record.welfare_report.metrics
        assert "net_debt_reduction_clearing_only_pct" in metrics
        assert "clearing_benefit_gini" in metrics
        assert "default_mutualisation_cents" in metrics
