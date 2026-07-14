"""Property-based tests for the Capa-3 prosocial-affordance matcher (P1-P6).

hypothesis-driven invariants of the deterministic wrapper, exercised with deterministic and
ADVERSARIAL stub `propose` callables (fully offline):
- no surveillance/engagement key ever survives into the output;
- the model's return order never changes the emitted proposals (canonical sort);
- an ineligible token (off-cell, non-consenting, expired, unknown) is never surfaced, whatever
  the adversarial stub returns;
- a surveillance/engagement key at any depth in the request is always refused;
- the emitted count never exceeds max_proposals;
- an arbitrary/garbage stub return never crashes the wrapper.
"""
import importlib.util
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

_MOD = Path(__file__).resolve().parent.parent / "src" / "matcher" / "matcher.py"
_spec = importlib.util.spec_from_file_location("matcher", _MOD)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)
match = mod.match
MatcherBreachError = mod.MatcherBreachError

FORBIDDEN_ENGAGEMENT = tuple(mod.FORBIDDEN_KEYS) + tuple(mod.ENGAGEMENT_KEYS)

NOW = "2026-07-06T00:00:00Z"
FUTURE = "2027-01-01T00:00:00Z"
PAST = "2020-01-01T00:00:00Z"
SOON = "2026-07-14T00:00:00Z"

_tokens = st.sampled_from(["t1", "t2", "t3", "t4", "g1", "g2", "x", "y"])
_cells = st.sampled_from(["barrio-1", "huerta-norte", "otro"])
_kinds = st.sampled_from(["offer_meets_need", "shared_goal", "translation", "bogus"])


def _scan_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _scan_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _scan_keys(v)


@st.composite
def _candidate(draw):
    return {
        "token": draw(_tokens),
        "cell_id": draw(_cells),
        "offers": [], "needs": [], "goals": [],
        "consent": {"surfaceable": draw(st.booleans())},
        "expires_at": draw(st.sampled_from([FUTURE, PAST, None])),
    }


def _req(candidates, cell_ids=None, max_proposals=3):
    return {
        "asker": "a", "cell_ids": cell_ids or ["barrio-1"], "now": NOW,
        "expires_at": SOON, "max_proposals": max_proposals,
        "self": {"offers": [], "needs": [], "goals": []},
        "candidates": candidates,
    }


def _eligible(candidates, cell_ids):
    out = set()
    for c in candidates:
        if (c["cell_id"] in set(cell_ids)
                and (c.get("consent") or {}).get("surfaceable") is True
                and (c.get("expires_at") is None or c["expires_at"] > NOW)):
            out.add(c["token"])
    return out


def stub_echo(context):
    return [{"token": c["token"], "kind": "offer_meets_need", "reason": "r"}
            for c in context["candidates"]]


# P1: no forbidden/engagement key ever appears in the output
@settings(max_examples=100)
@given(cands=st.lists(_candidate(), max_size=6))
def test_p1_no_forbidden_or_engagement_key_in_output(cands):
    out = match(_req(cands), stub_echo)
    keys = {str(k).lower() for k in _scan_keys(out)}
    assert all(not any(t in k for t in FORBIDDEN_ENGAGEMENT) for k in keys)


# P2: permuting the model's return order never changes the emitted proposals
@settings(max_examples=100)
@given(cands=st.lists(_candidate(), min_size=1, max_size=6), seed=st.randoms())
def test_p2_model_order_irrelevant(cands, seed):
    props = [{"token": c["token"], "kind": "shared_goal", "reason": "r"} for c in cands]
    shuffled = list(props)
    seed.shuffle(shuffled)
    base = match(_req(cands, max_proposals=99), lambda ctx: list(props))["proposals"]
    perm = match(_req(cands, max_proposals=99), lambda ctx: list(shuffled))["proposals"]
    assert base == perm


# P3: no ineligible token is ever surfaced, whatever the adversarial stub returns
@settings(max_examples=200)
@given(cands=st.lists(_candidate(), max_size=6),
       claimed=st.lists(st.tuples(_tokens, _kinds), max_size=8),
       cell_ids=st.lists(_cells, min_size=1, max_size=2, unique=True))
def test_p3_ineligible_never_surfaces(cands, claimed, cell_ids):
    stub = lambda ctx: [{"token": t, "kind": k, "reason": "r"} for t, k in claimed]
    out = match(_req(cands, cell_ids=cell_ids, max_proposals=99), stub)
    eligible = _eligible(cands, cell_ids)
    for p in out["proposals"]:
        assert p["token"] in eligible
        assert p["kind"] in ("offer_meets_need", "shared_goal", "translation")
        assert p["cell_id"] in set(cell_ids)


# P4: a forbidden/engagement key nested at random depth is always refused
@settings(max_examples=100)
@given(bad=st.sampled_from(FORBIDDEN_ENGAGEMENT), depth=st.integers(min_value=0, max_value=4))
def test_p4_surveillance_or_engagement_key_always_refused(bad, depth):
    node = {bad: 1}
    for i in range(depth):
        node = {"wrap%d" % i: node}
    cand = {"token": "t1", "cell_id": "barrio-1", "offers": [], "needs": [], "goals": [],
            "consent": {"surfaceable": True}, "expires_at": FUTURE,
            "facts": [{"statement": "s", "cell_id": "barrio-1", "meta": node}]}
    try:
        match(_req([cand]), stub_echo)
        assert False, "surveillance/engagement key survived into the request"
    except MatcherBreachError:
        pass


# P5: the emitted count never exceeds max_proposals
@settings(max_examples=100)
@given(cands=st.lists(_candidate(), max_size=8), cap=st.integers(min_value=1, max_value=5))
def test_p5_bounded(cands, cap):
    out = match(_req(cands, max_proposals=cap), stub_echo)
    assert len(out["proposals"]) <= cap
    assert out["audit_trace"]["emitted"] <= cap


# P6: an arbitrary/garbage stub return never crashes the wrapper
@settings(max_examples=100)
@given(cands=st.lists(_candidate(), max_size=4),
       ret=st.recursive(
           st.one_of(st.none(), st.booleans(), st.integers(), st.text(max_size=5)),
           lambda c: st.one_of(st.lists(c, max_size=4),
                               st.dictionaries(st.text(max_size=5), c, max_size=4)),
           max_leaves=8))
def test_p6_garbage_model_never_crashes(cands, ret):
    out = match(_req(cands), lambda ctx: ret)
    assert out["verdict"] in ("proposals_surfaced", "no_matches_from_your_position")
