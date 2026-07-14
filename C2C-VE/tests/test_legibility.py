"""Acceptance tests for the Capa-2 trust-legibility consultar.

Maps to workflows/micorriza-politica/capa2/evals/acceptance.md AC1-AC9 + AC-X.
Uses an INDEPENDENT hand-written BFS + key-walker oracle (not the module's own
traversal/scanner) so the consultar cannot self-confirm a bug (AGD-045).

The razor's-edge test is AC7: the SAME (objetivo, cell) from two askers must diverge —
the structural proof that there is no god-view.
"""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

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


# ---- independent oracles ----------------------------------------------------
def any_key_matches(obj, tokens):
    """Independently detect whether any dict key (recursively) contains a token."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if any(t in str(k).lower() for t in tokens):
                return True
            if any_key_matches(v, tokens):
                return True
    elif isinstance(obj, list):
        return any(any_key_matches(v, tokens) for v in obj)
    return False


def scan_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from scan_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from scan_keys(v)


def oracle_reachable(avales, consultante, objetivo, cell_id, now, max_hops):
    """Independent BFS: is objetivo reachable from consultante within max_hops over
    in-cell, unexpired vouch edges? (Hand-written; separate from the module.)"""
    def alive(item):
        exp = item.get("expira_en")
        return exp is None or exp > now
    edges = {}
    for v in avales:
        if v.get("celula_id") == cell_id and alive(v):
            edges.setdefault(v["de"], set()).add(v["a"])
    if consultante == objetivo:
        return False, None
    frontier = {consultante}
    seen = {consultante}
    for hop in range(1, max_hops + 1):
        nxt = set()
        for node in frontier:
            nxt |= edges.get(node, set())
        if objetivo in nxt:
            return True, hop
        nxt -= seen
        seen |= nxt
        frontier = nxt
        if not frontier:
            break
    return False, None


# ---- builders ---------------------------------------------------------------
def _vouch(frm, to, cell="barrio-1", exp=FUTURE):
    return {"de": frm, "a": to, "celula_id": cell, "expira_en": exp}


def _fact(about, statement="completed 12 exchanges", cell="barrio-1", exp=FUTURE):
    return {"sobre": about, "afirmacion": statement, "celula_id": cell, "expira_en": exp}


def _req(consultante="a", objetivo="x", cell="barrio-1", now=NOW, max_hops=3,
         avales=None, hechos=None):
    return {
        "consultante": consultante, "objetivo": objetivo, "celula_id": cell, "ahora": now,
        "saltos_max": max_hops,
        "grafo": {"avales": avales or [], "hechos": hechos or []},
    }


# ---- AC1: a reachable, in-cell, unexpired objetivo is known via trust ----------
def test_ac1_two_hop_known():
    r = _req(avales=[_vouch("a", "t7"), _vouch("t7", "x")])
    out = consultar(r)
    assert out["veredicto"] == "conocido_via_confianza"
    assert out["desde_tu_posicion"]["alcanzable"] is True
    assert out["desde_tu_posicion"]["saltos_minimos"] == 2
    assert ["a", "t7", "x"] in out["desde_tu_posicion"]["rutas_de_aval"]
    assert "t7" in out["desde_tu_posicion"]["avalado_por_gente_de_tu_confianza"]
    # oracle agrees
    reach, hops = oracle_reachable(r["grafo"]["avales"], "a", "x", "barrio-1", NOW, 3)
    assert reach and hops == 2


def test_ac1_direct_one_hop():
    out = consultar(_req(avales=[_vouch("a", "x")]))
    assert out["desde_tu_posicion"]["saltos_minimos"] == 1
    assert ["a", "x"] in out["desde_tu_posicion"]["rutas_de_aval"]


def test_ac2_fact_surfaces_verbatim():
    f = _fact("x")
    out = consultar(_req(avales=[_vouch("a", "x")], hechos=[f]))
    hechos = out["desde_tu_posicion"]["hechos"]
    assert any(fx["afirmacion"] == "completed 12 exchanges" for fx in hechos)


def test_ac1_self_query_no_path_but_fact():
    # consultante == objetivo: no vouch-path, but a fact about self surfaces
    out = consultar(_req(consultante="a", objetivo="a", hechos=[_fact("a", "hosted 3 events")]))
    assert out["desde_tu_posicion"]["alcanzable"] is False
    assert out["veredicto"] == "conocido_via_confianza"  # via the fact
    out2 = consultar(_req(consultante="a", objetivo="a"))
    assert out2["veredicto"] == "sin_informacion_desde_tu_posicion"


# ---- AC2: out-of-cell items ignored -----------------------------------------
def test_ac2_out_of_cell_ignored():
    out = consultar(_req(avales=[_vouch("a", "t7", cell="otro"),
                              _vouch("t7", "x", cell="otro")]))
    assert out["veredicto"] == "sin_informacion_desde_tu_posicion"
    assert out["desde_tu_posicion"]["alcanzable"] is False
    assert out["desde_tu_posicion"]["rutas_de_aval"] == []


# ---- AC3: expired items forgotten -------------------------------------------
def test_ac3_expired_dropped():
    expired = _req(avales=[_vouch("a", "t7", exp=PAST), _vouch("t7", "x", exp=PAST)])
    assert consultar(expired)["veredicto"] == "sin_informacion_desde_tu_posicion"


def test_ac3_fresh_kept():
    fresh = _req(avales=[_vouch("a", "t7", exp=FUTURE), _vouch("t7", "x", exp=FUTURE)])
    assert consultar(fresh)["veredicto"] == "conocido_via_confianza"


def test_ac3_null_expiry_kept():
    out = consultar(_req(avales=[_vouch("a", "x", exp=None)]))
    assert out["veredicto"] == "conocido_via_confianza"


# ---- AC4: absence is not a mark ---------------------------------------------
def test_ac4_empty_graph_neutral():
    out = consultar(_req())  # empty graph
    assert out["veredicto"] == "sin_informacion_desde_tu_posicion"
    assert out["desde_tu_posicion"]["alcanzable"] is False
    # no negative/blacklist field anywhere
    assert not any_key_matches(out, ("blacklist", "distrust", "ban", "penalty"))


def test_ac4_unreachable_returns_normally():
    # edges exist but none path a->x
    out = consultar(_req(avales=[_vouch("b", "c"), _vouch("c", "d")]))
    assert out["veredicto"] == "sin_informacion_desde_tu_posicion"


# ---- AC5: no scalar out; surveillance shape refused in input ----------------
def test_ac5a_verdict_has_no_forbidden_keys():
    out = consultar(_req(avales=[_vouch("a", "x")], hechos=[_fact("x")]))
    keys = {str(k).lower() for k in scan_keys(out)}
    assert keys.isdisjoint(FORBIDDEN)


def test_ac5a_verdict_has_no_person_ranking_number():
    # the only numbers allowed: saltos_minimos, *_considerados, saltos_max. No score/rank field.
    out = consultar(_req(avales=[_vouch("a", "t7"), _vouch("t7", "x")]))
    fp = out["desde_tu_posicion"]
    assert set(fp.keys()) == {"alcanzable", "saltos_minimos", "rutas_de_aval",
                              "avalado_por_gente_de_tu_confianza", "hechos"}


@pytest.mark.parametrize("graph", [
    {"avales": [], "hechos": [{"sobre": "x", "reputation": 0.9, "celula_id": "barrio-1"}]},
    {"avales": [{"de": "a", "a": "x", "celula_id": "barrio-1",
                  "expira_en": None, "meta": {"trust_rank": 1}}], "hechos": []},
    {"avales": [], "hechos": [{"sobre": "x", "celula_id": "barrio-1",
                               "seller": {"trust_score": 88}}]},
])
def test_ac5b_surveillance_shape_in_graph_refused(graph):
    r = _req()
    r["grafo"] = graph
    with pytest.raises(LegibilityBreachError):
        consultar(r)


def test_ac5b_surveillance_in_envelope_refused():
    r = _req()
    r["blacklist"] = ["t9"]
    with pytest.raises(LegibilityBreachError):
        consultar(r)


# ---- AC6: no enumeration / no god-view entrypoint ---------------------------
def test_ac6_no_godview_functions():
    # the only public consultar entrypoint takes an consultante + single objetivo
    public = {n for n in dir(mod) if not n.startswith("_")}
    for forbidden_name in ("standing_of", "rank_all", "rank", "list_all",
                           "reputation_of", "score", "all_standings"):
        assert forbidden_name not in public


@pytest.mark.parametrize("bad_target", ["*", ["x", "y"], {"t": 1}, None, ""])
def test_ac6_wildcard_or_list_target_refused(bad_target):
    with pytest.raises(LegibilityBreachError):
        consultar(_req(objetivo=bad_target))


# ---- AC7: position-relativity — the two-askers divergence proof --------------
def test_ac7_two_askers_diverge():
    graph = {"avales": [_vouch("A", "t7"), _vouch("t7", "x")], "hechos": []}
    rA = {"consultante": "A", "objetivo": "x", "celula_id": "barrio-1", "ahora": NOW,
          "saltos_max": 3, "grafo": graph}
    rB = dict(rA, consultante="B")
    outA = consultar(copy.deepcopy(rA))
    outB = consultar(copy.deepcopy(rB))
    assert outA["veredicto"] == "conocido_via_confianza"
    assert outB["veredicto"] == "sin_informacion_desde_tu_posicion"
    assert outA != outB  # the same (objetivo, cell) yields different answers => no god-view


# ---- AC8: determinism -------------------------------------------------------
def test_ac8_determinism():
    r = _req(avales=[_vouch("a", "t7"), _vouch("a", "t8"),
                      _vouch("t7", "x"), _vouch("t8", "x")])
    a = consultar(copy.deepcopy(r))
    b = consultar(copy.deepcopy(r))
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    # both equal-length paths present, deterministically ordered
    assert a["desde_tu_posicion"]["rutas_de_aval"] == sorted(a["desde_tu_posicion"]["rutas_de_aval"])


# ---- AC9: envelope validation -----------------------------------------------
@pytest.mark.parametrize("mutate", [
    lambda r: r.update(consultante=""),
    lambda r: r.pop("consultante"),
    lambda r: r.update(celula_id=""),
    lambda r: r.update(ahora=""),
    lambda r: r.update(saltos_max=0),
    lambda r: r.update(saltos_max=-1),
    lambda r: r.update(saltos_max="3"),
    lambda r: r.update(saltos_max=True),
    lambda r: r.update(grafo=[]),
    lambda r: r.update(grafo={"avales": "x", "hechos": []}),
    lambda r: r.update(grafo={"avales": [{"de": "a"}], "hechos": []}),  # malformed edge
    lambda r: r.update(grafo={"avales": [], "hechos": [{"afirmacion": "hi"}]}),  # no sobre
])
def test_ac9_envelope_validation(mutate):
    r = _req(avales=[_vouch("a", "x")])
    mutate(r)
    with pytest.raises(LegibilityBreachError):
        consultar(r)


# ---- D-02 / D-05: dense graph stays bounded; reachability stays exact --------
def test_d02_dense_graph_bounded_but_reachability_exact():
    # a diamond chain has 2^k shortest paths; the concrete sample must be capped while
    # reachable / nearest_hops / vouched_by stay EXACT (computed by the linear reverse BFS).
    k = 20
    avales = []
    for i in range(k):
        avales += [_vouch("n%d" % i, "A%d" % i), _vouch("n%d" % i, "B%d" % i),
                    _vouch("A%d" % i, "n%d" % (i + 1)), _vouch("B%d" % i, "n%d" % (i + 1))]
    out = consultar(_req(consultante="n0", objetivo="n%d" % k, max_hops=2 * k, avales=avales))
    fp = out["desde_tu_posicion"]
    assert fp["alcanzable"] is True
    assert fp["saltos_minimos"] == 2 * k                               # exact, not enumerated
    assert set(fp["avalado_por_gente_de_tu_confianza"]) == {"A0", "B0"}    # exact direct trustees
    assert len(fp["rutas_de_aval"]) <= mod._MAX_RUTAS_DE_AVAL            # sample is bounded
    assert out["traza_auditoria"]["rutas_truncadas"] is True            # 2^20 >> cap


def test_d05_duplicate_edges_yield_no_duplicate_paths():
    out = consultar(_req(avales=[_vouch("a", "x"), _vouch("a", "x")]))
    assert out["desde_tu_posicion"]["rutas_de_aval"] == [["a", "x"]]  # not [["a","x"],["a","x"]]


# ---- AC-X: cross-layer consistency (shared forbidden taxonomy) --------------
def test_acx_capa1_surveillance_shape_refused_as_graph_node():
    r = _req()
    r["grafo"] = {"avales": [],
                  "hechos": [{"sobre": "x", "celula_id": "barrio-1",
                             "seller": {"trust_score": 88}}]}
    with pytest.raises(LegibilityBreachError):
        consultar(r)


def test_acx_forbidden_keys_match_membrane_and_engine():
    # the three layers must share the exact taxonomy
    memb = Path(__file__).resolve().parent.parent / "src" / "partition" / "membrana.py"
    _s = importlib.util.spec_from_file_location("membrana", memb)
    _m = importlib.util.module_from_spec(_s)
    _s.loader.exec_module(_m)
    assert set(mod.FORBIDDEN_KEYS) == set(_m.FORBIDDEN_KEYS)
