"""Property-based tests for the assurance engine (no-loss, bonus conservation,
determinism, anti-surveillance shape) over randomly generated campaigns.

Targets the tail-of-distribution (AGD-016). Requires `hypothesis`.
"""
import copy
import importlib.util
import json
from collections import Counter
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

_ENGINE = Path(__file__).resolve().parent.parent / "src" / "assurance" / "assurance_engine.py"
_spec = importlib.util.spec_from_file_location("assurance_engine_p", _ENGINE)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)
resolve = mod.resolve

FORBIDDEN = ("score", "rating", "reputation", "rank", "blacklist", "ban",
             "penalty", "global_id", "dni")
TOKENS = ["t1", "t2", "t3", "t4", "t5"]


@st.composite
def campaigns(draw):
    kind = draw(st.sampled_from(["binary", "monetary"]))
    n = draw(st.integers(min_value=0, max_value=12))
    pledges = []
    for i in range(n):
        p = {"pledge_id": f"p{i}", "participant_token": draw(st.sampled_from(TOKENS))}
        if kind == "monetary":
            p["amount_cents"] = draw(st.integers(min_value=0, max_value=100000))
        pledges.append(p)
    # A dominant-assurance bonus is only valid on a monetary campaign; a binary
    # campaign must carry bonus 0 (membrane + anti-Sybil), so don't generate it.
    bonus = draw(st.integers(min_value=0, max_value=99999)) if kind == "monetary" else 0
    return {
        "campaign_id": "c", "cell_id": "cell", "kind": kind,
        "threshold": draw(st.integers(min_value=1, max_value=8)),
        "sponsor_bonus_cents": bonus,
        "expires_at": "2026-12-31T00:00:00Z", "pledges": pledges,
    }


def _scan_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _scan_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _scan_keys(v)


@settings(max_examples=400)
@given(campaigns())
def test_no_loss(camp):
    out = resolve(copy.deepcopy(camp))
    if out["status"] != "refunds" or camp["kind"] != "monetary":
        return
    sums = Counter()
    for p in camp["pledges"]:
        sums[p["participant_token"]] += p["amount_cents"]
    refunds = {r["participant_token"]: r["refund_cents"]
               for r in out["resolution"]["refunds"]}
    for token, total in sums.items():
        assert refunds[token] == total  # nobody is ever short


@settings(max_examples=400)
@given(campaigns())
def test_bonus_conservation(camp):
    out = resolve(copy.deepcopy(camp))
    bonuses = [r["bonus_cents"] for r in out["resolution"]["refunds"]]
    if out["status"] == "refunds" and out["distinct_committers"] > 0:
        # bonus is split across committers exactly; with no committers it is not
        # distributed (returns to sponsor), so conservation only binds when >0.
        assert sum(bonuses) == camp["sponsor_bonus_cents"]
        assert max(bonuses) - min(bonuses) <= 1
    elif out["status"] == "fires":
        assert bonuses == []


@settings(max_examples=300)
@given(campaigns())
def test_determinism(camp):
    a = resolve(copy.deepcopy(camp))
    b = resolve(copy.deepcopy(camp))
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


@settings(max_examples=300)
@given(campaigns())
def test_no_surveillance_shape(camp):
    out = resolve(copy.deepcopy(camp))
    keys = {k.lower() for k in _scan_keys(out)}
    assert keys.isdisjoint(FORBIDDEN)


@settings(max_examples=300)
@given(campaigns())
def test_threshold_rule(camp):
    out = resolve(copy.deepcopy(camp))
    distinct = len(set(p["participant_token"] for p in camp["pledges"]))
    assert out["distinct_committers"] == distinct
    assert out["status"] == ("fires" if distinct >= camp["threshold"] else "refunds")
