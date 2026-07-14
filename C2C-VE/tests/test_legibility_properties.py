"""Property-based tests for the Capa-2 trust-legibility consultar (P1-P5).

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

_MOD = Path(__file__).resolve().parent.parent / "src" / "legibility" / "legibilidad.py"
_spec = importlib.util.spec_from_file_location("legibilidad", _MOD)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)
consultar = mod.consultar
LegibilityBreachError = mod.ErrorDeBrechaLegibilidad

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
    return {"de": frm, "a": to, "celula_id": cell, "expira_en": exp}


def _req(avales, consultante="a", objetivo="x", cell="barrio-1", now=NOW, max_hops=4, hechos=None):
    return {"consultante": consultante, "objetivo": objetivo, "celula_id": cell, "ahora": now,
            "saltos_max": max_hops, "grafo": {"avales": avales, "hechos": hechos or []}}


_edges = st.lists(st.tuples(_tokens, _tokens), max_size=8)


def _mk_vouches(edges, cell="barrio-1", exp=FUTURE):
    return [_vouch(f, t, cell, exp) for f, t in edges]


# P1: no forbidden key ever appears in a verdict
@settings(max_examples=100)
@given(edges=_edges)
def test_p1_no_forbidden_key_in_verdict(edges):
    out = consultar(_req(_mk_vouches(edges)))
    keys = {str(k).lower() for k in _scan_keys(out)}
    assert all(not any(t in k for t in FORBIDDEN) for k in keys)


# P2: adding only-expired items never changes the verdict (forgetting)
@settings(max_examples=100)
@given(edges=_edges, extra=_edges)
def test_p2_expired_items_never_matter(edges, extra):
    base = consultar(_req(_mk_vouches(edges)))["veredicto"]
    with_expired = consultar(_req(_mk_vouches(edges) + _mk_vouches(extra, exp=PAST)))["veredicto"]
    assert base == with_expired


# P3: adding out-of-cell items never changes the verdict (contextual)
@settings(max_examples=100)
@given(edges=_edges, extra=_edges)
def test_p3_out_of_cell_never_matters(edges, extra):
    base = consultar(_req(_mk_vouches(edges)))["veredicto"]
    with_other = consultar(_req(_mk_vouches(edges) + _mk_vouches(extra, cell="otro")))["veredicto"]
    assert base == with_other


# P4: a forbidden key nested at random depth is always refused
@settings(max_examples=100)
@given(bad=st.sampled_from(FORBIDDEN), depth=st.integers(min_value=0, max_value=4))
def test_p4_surveillance_key_always_refused(bad, depth):
    node = {bad: 1}
    for i in range(depth):
        node = {f"wrap{i}": node}
    fact = {"sobre": "x", "celula_id": "barrio-1", "afirmacion": "s", "meta": node}
    try:
        consultar(_req([], hechos=[fact]))
        assert False, "surveillance key survived into the graph"
    except LegibilityBreachError:
        pass


# P5: adding a vouch can only create or keep reachability, never remove it (positive-sum)
@settings(max_examples=100)
@given(edges=_edges, new=st.tuples(_tokens, _tokens))
def test_p5_adding_vouch_is_monotone(edges, new):
    before = consultar(_req(_mk_vouches(edges)))["desde_tu_posicion"]["alcanzable"]
    after = consultar(_req(_mk_vouches(edges) + [_vouch(new[0], new[1])]))["desde_tu_posicion"]["alcanzable"]
    # whitelist graph: adding an edge cannot destroy reachability
    if before:
        assert after
