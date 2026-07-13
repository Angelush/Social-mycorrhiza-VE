"""M6: property-based (P-C1..P-C4) + golden regression (G-C1) tests for Sim-C2C, via hypothesis.

These exercise invariants that must hold across ALL inputs, not just the seeds in the fixtures:
the matcher wrapper is uncrashable by any model output, forgetting is monotone in `now`, the
anti-cascade throttle bounds any burst, and campaigns are byte-reproducible across seeds.
"""
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from sim_c2c.adapter import C2CAdapter
from sim_c2c.campaign import build_campaign, default_config
from sim_c2c.track_a import _window_bucket

C2C_ROOT = Path(__file__).resolve().parent.parent.parent / "C2C"
_ADAPTER = C2CAdapter(C2C_ROOT)


# P-C1: the matcher guardrail is UNCRASHABLE by any model output — a valid request never raises,
# whatever garbage the injected proposer returns (the prompt-injection wall, invariant 8).
@given(model_out=st.lists(st.one_of(
    st.none(), st.integers(), st.text(),
    st.dictionaries(st.text(min_size=1, max_size=8), st.text(max_size=8), max_size=4),
), max_size=6))
@settings(max_examples=60, deadline=None)
def test_pc1_matcher_uncrashable_by_any_model_output(model_out):
    req = {
        "asker": "a", "cell_ids": ["c1"], "now": "T1", "expires_at": "T9",
        "max_proposals": 5, "self": {"needs": ["bread"]},
        "candidates": [{"token": "b", "cell_id": "c1", "offers": ["bread"],
                        "consent": {"surfaceable": True}}],
    }
    out = _ADAPTER.match(req, lambda ctx: model_out)  # must never raise
    for p in out["proposals"]:
        assert set(p.keys()) == {"token", "cell_id", "kind", "reason", "cited_facts", "expires_at"}


# P-C2: forgetting is monotone — a fact unexpired at a later `now` is also unexpired earlier; an
# expired fact never resurfaces as `now` advances past its expiry.
@given(expiry=st.integers(min_value=1, max_value=20), now=st.integers(min_value=0, max_value=25))
@settings(max_examples=60, deadline=None)
def test_pc2_forgetting_is_monotone_in_now(expiry, now):
    req = {
        "asker": "a", "target": "b", "cell_id": "c1", "now": "T%02d" % now, "max_hops": 3,
        "graph": {"vouches": [],
                  "facts": [{"about": "b", "statement": "s", "cell_id": "c1",
                             "expires_at": "T%02d" % expiry}]},
    }
    out = _ADAPTER.query(req)
    surfaced = len(out["from_your_position"]["facts"]) > 0
    # unexpired iff expires_at > now (lexicographic == numeric here, fixed width)
    assert surfaced == (("T%02d" % expiry) > ("T%02d" % now))


# P-C3: the anti-cascade throttle bounds ANY burst — sensed count per artifact never exceeds the
# velocity cap per window bucket, and Track A agrees a burst was throttled.
@given(burst=st.integers(min_value=1, max_value=12), cap=st.integers(min_value=1, max_value=5))
@settings(max_examples=60, deadline=None)
def test_pc3_velocity_cap_bounds_any_burst(burst, cap):
    now = 100
    traces = [{"about": "art", "signal": "contribution", "strength": 1.0,
               "created_at": now, "cell_id": "c1"} for _ in range(burst)]
    req = {"cell_id": "c1", "now": now, "window": 5, "velocity_cap": cap,
           "half_life": 4, "min_strength": 0.0, "traces": traces}
    out = _ADAPTER.sense(req)
    sensed_for_art = sum(1 for s in out["sensed"] if s["about"] == "art")
    assert sensed_for_art <= cap
    if burst > cap:
        assert out["audit_trace"]["damped_velocity"] == burst - cap


# P-C4: campaigns are byte-reproducible for any seed.
@given(seed=st.integers(min_value=0, max_value=999))
@settings(max_examples=8, deadline=None)
def test_pc4_campaign_reproducible_for_any_seed(seed):
    a = build_campaign(default_config(seed=seed, T=12), C2C_ROOT, max_rounds=2)
    b = build_campaign(default_config(seed=seed, T=12), C2C_ROOT, max_rounds=2)
    assert a.history == b.history


# G-C1: golden regression — a pinned campaign stays clean and unhalted with a stable shape.
def test_gc1_golden_campaign_shape():
    result = build_campaign(default_config(seed=7), C2C_ROOT, max_rounds=3)
    assert not result.halted
    assert len(result.history) == 3
    metrics = set(result.history[0].welfare_report.metrics)
    assert metrics == {"reachability_of_cooperation", "vouch_graph_diversity",
                       "cascade_damping_ratio", "bootstrapping_cost"}
    assert set(result.history[0].integrity_report.results) == {
        "no_person_scalar", "no_market_leak", "asker_relative",
        "forgetting", "consent_privacy", "anti_cascade"}


def test_window_bucket_matches_stigmergy_definition():
    # sanity on Track A's replicated bucket math vs the module's own comment (D-04).
    assert _window_bucket(100, 100, 5) == 0
    assert _window_bucket(96, 100, 5) == 0     # elapsed 4 <= window 5 -> current bucket
    assert _window_bucket(94, 100, 5) == 1     # elapsed 6 -> next bucket
