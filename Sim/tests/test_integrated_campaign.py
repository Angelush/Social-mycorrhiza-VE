"""MI-4: end-to-end integrated campaign + the F-VS2 finding + properties/golden (ACI4.1–4.3)."""
from random import Random

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from engine.measurement import Verdict
from engine.types import RangeBound, SearchSpace
from sim_integrated.campaign import build_campaign, default_config
from sim_integrated.identity import Identity
from sim_integrated.policies import BridgeExploiter
from sim_integrated.researcher import IntegratedResearcher
from sim_integrated.track_a import IntegratedTrackA
from sim_integrated.track_b import IntegratedTrackB
from sim_integrated.world import IntegratedWorld

from test_integrated_world_smoke import setup_b2b, B2B_ROOT, C2C_ROOT
from sim_c2c.adapter import C2CAdapter


def test_clean_campaign_zero_violations_and_reproducible():
    a = build_campaign(default_config(seed=5), B2B_ROOT, C2C_ROOT, max_rounds=4)
    assert not a.halted, (
        f"ACI4.1: SUT-enforced walls must hold on the real stack; halted on "
        f"{a.halting_report.failed_invariants if a.halting_report else None}")
    assert len(a.history) == 4
    b = build_campaign(default_config(seed=5), B2B_ROOT, C2C_ROOT, max_rounds=4)
    assert a.history == b.history, "ACI4.1: same seed must yield an identical campaign history"


def test_fvs2_finding_demonstrated_against_real_b2b():
    # ACI4.2: the seam's native failure — a person-scalar fed to a credit decision — leaks against the
    # REAL B2B and is caught only by the provenance oracle. Reported as a first-class finding.
    ex = Identity("X", "business", b2b_cell="cell-A", c2c_cell="room-gift")
    actors = {"X": BridgeExploiter(ex, modes=frozenset({"score_to_credit"}), c2c_target="c0")}
    b2b = {"cell-A": setup_b2b("cell-A", ("X", "c0"))}
    world = IntegratedWorld(b2b, C2CAdapter(C2C_ROOT), actors, {"X": ex},
                            b2b_rosters={"cell-A": ("X", "c0")},
                            c2c_modes={"room-gift": "communal_gift"}, rng=Random(1))
    for _ in range(4):
        world.step()
    report = IntegratedTrackA().measure(world.trace)
    assert report.results["value_social_score_to_credit"].verdict is Verdict.FAIL
    assert report.violation is True


def test_researcher_refuses_track_b_objective_and_only_moves_adversary_intensity():
    for metric in IntegratedTrackB.GOODHART_FLAGS:
        with pytest.raises(ValueError):
            IntegratedResearcher.assert_descriptive_only(
                SearchSpace(bounds={metric: RangeBound(0.0, 1.0)}))
    result = build_campaign(default_config(seed=5), B2B_ROOT, C2C_ROOT, max_rounds=3)
    intensities = [r.config["adversary_intensity"] for r in result.history]
    assert intensities == sorted(intensities)


@given(seed=st.integers(min_value=0, max_value=500))
@settings(max_examples=6, deadline=None)
def test_property_campaign_reproducible_any_seed(seed):
    a = build_campaign(default_config(seed=seed, T=10), B2B_ROOT, C2C_ROOT, max_rounds=2)
    b = build_campaign(default_config(seed=seed, T=10), B2B_ROOT, C2C_ROOT, max_rounds=2)
    assert a.history == b.history


def test_golden_campaign_shape():
    result = build_campaign(default_config(seed=5), B2B_ROOT, C2C_ROOT, max_rounds=3)
    assert not result.halted and len(result.history) == 3
    assert set(result.history[0].integrity_report.results) == {
        "value_social_debt_leak", "value_social_score_to_credit", "cell_contagion"}
    assert set(result.history[0].welfare_report.metrics) == {
        "bridge_attempts_total", "bridge_rejected_fraction"}
