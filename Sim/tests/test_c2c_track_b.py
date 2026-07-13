"""M4: Track B welfare — descriptive-only, position-relative, no per-person scalar (AC4.1–AC4.2)."""
import pytest

from engine.measurement import Distribution, WelfareReport, assert_no_person_scalar
from sim_c2c.track_b import C2CTrackB

# the C2C surveillance taxonomy (the defense-in-depth lint alphabet)
FORBIDDEN = frozenset({"score", "rating", "reputation", "rank",
                       "blacklist", "ban", "penalty", "global_id", "dni"})

from test_c2c_world_actors import _run


def test_metrics_are_all_aggregate_no_agent_slot():
    world = _run(7)
    report = C2CTrackB().measure(world.trace)
    assert isinstance(report, WelfareReport)
    for key, val in report.metrics.items():
        assert isinstance(val, (Distribution, int, float)) and not isinstance(val, bool)
        if isinstance(val, Distribution):
            # samples are bare numbers — no identity is representable
            for s in val.samples:
                assert isinstance(s, (int, float)) and not isinstance(s, bool)


def test_no_person_scalar_lint_passes_on_real_output():
    world = _run(7)
    report = C2CTrackB().measure(world.trace)
    assert_no_person_scalar(report, FORBIDDEN)  # must not raise


def test_every_metric_ships_a_goodhart_flag():
    tb = C2CTrackB()
    world = _run(7)
    report = tb.measure(world.trace)
    for key in report.metrics:
        flag = tb.goodhart_flag(key)
        assert "DESCRIPTIVE ONLY" in flag


def test_welfare_report_structurally_rejects_a_per_person_scalar():
    # The type wall itself: a metric keyed value that is an identity->score mapping is unrepresentable
    # because a plain dict is not a Distribution/int/float. (The exact trap the C2C brief warns about.)
    with pytest.raises(TypeError):
        WelfareReport(metrics={"fertility": {"alice": 0.9, "bob": 0.2}})


def test_reachability_fraction_in_unit_interval():
    world = _run(7)
    report = C2CTrackB().measure(world.trace)
    frac = report.metrics["reachability_of_cooperation"].summary["fraction_positions_reached"]
    assert 0.0 <= frac <= 1.0
    assert 0.0 <= report.metrics["cascade_damping_ratio"] <= 1.0
