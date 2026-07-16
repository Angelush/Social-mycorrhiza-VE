"""M6: end-to-end Sim-C2C campaign over the real C2C stack + the descriptive-only seam (AC6.1–6.3)."""
from pathlib import Path

import pytest

from engine.types import RangeBound, SearchSpace
from sim_c2c.campaign import build_campaign, default_config
from sim_c2c.researcher import C2CResearcher
from sim_c2c.track_b import C2CTrackB

C2C_ROOT = Path(__file__).resolve().parent.parent.parent / "C2C-VE"


def test_campaign_runs_clean_and_unhalted_on_the_real_sut():
    result = build_campaign(default_config(), C2C_ROOT, max_rounds=4)
    assert not result.halted, (
        f"AC6.2: a clean SUT must produce zero integrity violations; halted on "
        f"{result.halting_report.failed_invariants if result.halting_report else None}"
    )
    assert len(result.history) == 4
    for record in result.history:
        assert not record.integrity_report.violation


def test_campaign_is_byte_reproducible():
    a = build_campaign(default_config(seed=11), C2C_ROOT, max_rounds=3)
    b = build_campaign(default_config(seed=11), C2C_ROOT, max_rounds=3)
    assert a.history == b.history, "AC6.2: same seed must yield an identical campaign history"


def test_researcher_search_space_carries_no_track_b_objective():
    # AC6.1: the descriptive-only seam — a search space that names a welfare metric is refused.
    for metric in C2CTrackB.GOODHART_FLAGS:
        bad = SearchSpace(bounds={metric: RangeBound(0.0, 1.0)})
        with pytest.raises(ValueError):
            C2CResearcher.assert_descriptive_only(bad)
    # the default campaign space is accepted (only adversary_intensity)
    ok = SearchSpace(bounds={"adversary_intensity": RangeBound(0.0, 1.0)})
    C2CResearcher.assert_descriptive_only(ok)


def test_researcher_nudges_adversary_intensity_monotonically():
    result = build_campaign(default_config(), C2C_ROOT, max_rounds=4)
    intensities = [r.config["adversary_intensity"] for r in result.history]
    assert intensities == sorted(intensities), "intensity should be non-decreasing"
