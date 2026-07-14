"""Property-based tests for the Capa-2 trust-legibility query (P1-P5).

hypothesis-driven invariants of the razor's-edge layer:
- no surveillance key ever survives into a verdict;
- expired items never change the verdict (forgetting);
- out-of-cell items never change the verdict (contextual);
- a surveillance key at any depth is always refused;
- adding a vouch can only create/keep reachability, never remove it (positive-sum).
"""
import importlib.util
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

_MOD = Path(__file__).resolve().parent.parent / "src" / "legibility" / "legibility_query.py"
_spec = importlib.util.spec_from_file_location("legibility_query", _MOD)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)
query = mod.query
LegibilityBreachError = mod.LegibilityBreachError

FORBIDDEN = ("score", "rating", "reputation", "rank", "blacklist", "ban",
             "penalty", "global_id", "dni")

NOW = "2026-07-06T00:00:00Z"
FUTURE = "2027-01-01T00:00:00Z"
PAST = "2020-01-01T00:00:00Z"

_tokens = st.sampled_from(["a", "b", "c", "d", "t7", "t8", "x", "y", "z"])


def _scan_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _scan_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _scan_keys(v)


def _vouch(frm, to, cell="barrio-1", exp=FUTURE):
    return {"from": frm, "to": to, "cell_id": cell, "expires_at": exp}


def _req(vouches, asker="a", target="x", cell="barrio-1", now=NOW, max_hops=4, facts=None):
    return {"asker": asker, "target": target, "cell_id": cell, "now": now,
            "max_hops": max_hops, "graph": {"vouches": vouches, "facts": facts or []}}


_edges = st.lists(st.tuples(_tokens, _tokens), max_size=8)


def _mk_vouches(edges, cell="barrio-1", exp=FUTURE):
    return [_vouch(f, t, cell, exp) for f, t in edges]


# P1: no forbidden key ever appears in a verdict
@settings(max_examples=100)
@given(edges=_edges)
def test_p1_no_forbidden_key_in_verdict(edges):
    out = query(_req(_mk_vouches(edges)))
    keys = {str(k).lower() for k in _scan_keys(out)}
    assert all(not any(t in k for t in FORBIDDEN) for k in keys)


# P2: adding only-expired items never changes the verdict (forgetting)
@settings(max_examples=100)
@given(edges=_edges, extra=_edges)
def test_p2_expired_items_never_matter(edges, extra):
    base = query(_req(_mk_vouches(edges)))["verdict"]
    with_expired = query(_req(_mk_vouches(edges) + _mk_vouches(extra, exp=PAST)))["verdict"]
    assert base == with_expired


# P3: adding out-of-cell items never changes the verdict (contextual)
@settings(max_examples=100)
@given(edges=_edges, extra=_edges)
def test_p3_out_of_cell_never_matters(edges, extra):
    base = query(_req(_mk_vouches(edges)))["verdict"]
    with_other = query(_req(_mk_vouches(edges) + _mk_vouches(extra, cell="otro")))["verdict"]
    assert base == with_other


# P4: a forbidden key nested at random depth is always refused
@settings(max_examples=100)
@given(bad=st.sampled_from(FORBIDDEN), depth=st.integers(min_value=0, max_value=4))
def test_p4_surveillance_key_always_refused(bad, depth):
    node = {bad: 1}
    for i in range(depth):
        node = {f"wrap{i}": node}
    fact = {"about": "x", "cell_id": "barrio-1", "statement": "s", "meta": node}
    try:
        query(_req([], facts=[fact]))
        assert False, "surveillance key survived into the graph"
    except LegibilityBreachError:
        pass


# P5: adding a vouch can only create or keep reachability, never remove it (positive-sum)
@settings(max_examples=100)
@given(edges=_edges, new=st.tuples(_tokens, _tokens))
def test_p5_adding_vouch_is_monotone(edges, new):
    before = query(_req(_mk_vouches(edges)))["from_your_position"]["reachable"]
    after = query(_req(_mk_vouches(edges) + [_vouch(new[0], new[1])]))["from_your_position"]["reachable"]
    # whitelist graph: adding an edge cannot destroy reachability
    if before:
        assert after
