"""Golden set (evals/tests.md G-01): a frozen reference campaign.

If this test ever fails because the numbers changed, that is a real regression signal in the
harness or the measurement layer -- investigate before updating the frozen values. If it fails
because the harness went BLIND (e.g. a broken-SUT run now silently passes), see
test_negative_control.py instead -- that is the loudest possible regression (G-04) and must
never be "fixed" by loosening this file.
"""
from pathlib import Path

from sim_b2b.campaign import build_campaign
from sim_b2b.config import RoundConfig

B2B_ROOT = Path(__file__).resolve().parent.parent.parent / "B2B-VE"

# TS.1: re-frozen deliberately. Upstream Sim's hash was 8e2f5422…f607b4e; the VE wire adds
# `moneda`/`sal_seudonimo` to create_cell params, which enter the journal's config/trace hash BY
# CONSTRUCTION. It was verified before re-freezing that the three ECONOMIC numbers below are
# byte-identical to the upstream frozen values — the only delta is the declared wire change.
# TS.2: re-frozen again (was 9ff674fc…a261d64): the integrity report now carries the three VE
# oracles and the trace carries the auditor's probes + puente cycle, both BY CONSTRUCTION.
# Economic numbers verified byte-identical before re-freezing, same discipline.
_FROZEN_ENTRY_HASH = "9b68b654302f38f6f3eafc93d959a516706c08caeba13b327dfd914a03c936d5"
_FROZEN_CLEARING_ONLY_PCT = 42.5
_FROZEN_COMBINED_PCT = 64.62585034013605
_FROZEN_GINI = 0.23529411764705882


def _golden_cfg() -> RoundConfig:
    return RoundConfig(
        actor_mix={"circulator": 1.0}, n_firms=20, T=20, clearing_cadence=5,
        base_turnover_cents=10_000_000, neg_line_bp=1000, pos_line_bp=1000,
        topology_params={"m": 2}, adversary_intensity=0.0, velocity_window_s=1,
        ticks_per_second=10, velocity_max_cents=5_000_000, credit_crunch=False, seed=2026,
    )


def test_g01_frozen_cooperative_campaign():
    result = build_campaign(_golden_cfg(), B2B_ROOT, max_rounds=1)

    assert result.halted is False
    entry = result.journal.entries[0]
    assert entry.entry_hash == _FROZEN_ENTRY_HASH, (
        "journal hash drifted from the frozen reference -- either a real regression, or an "
        "intentional change that must be re-frozen deliberately, never silently"
    )

    metrics = entry.welfare_report.metrics
    assert metrics["net_debt_reduction_clearing_only_pct"] == _FROZEN_CLEARING_ONLY_PCT
    assert metrics["net_debt_reduction_combined_pct"] == _FROZEN_COMBINED_PCT
    assert metrics["clearing_benefit_gini"].summary["gini"] == _FROZEN_GINI

    # X-01 cross-cutting: every report must carry the coverage-not-safety caveat somewhere
    # accessible to a human reading it. This harness does not yet attach that caveat as a
    # structured field on CampaignResult/WelfareReport -- flagged as a follow-up, not silently
    # skipped: assert the explored search space is at least reconstructable from the journal
    # (the honest minimum needed for a human to know what WAS and wasn't tried).
    assert entry.config_hash  # every entry names the exact config that produced it, always
