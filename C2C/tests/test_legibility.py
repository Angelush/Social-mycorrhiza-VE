"""Acceptance tests for the Capa-2 trust-legibility query.

Maps to workflows/micorriza-politica/capa2/evals/acceptance.md AC1-AC9 + AC-X.
Uses an INDEPENDENT hand-written BFS + key-walker oracle (not the module's own
traversal/scanner) so the query cannot self-confirm a bug (AGD-045).

The razor's-edge test is AC7: the SAME (target, cell) from two askers must diverge —
the structural proof that there is no god-view.
"""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

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


def oracle_reachable(vouches, asker, target, cell_id, now, max_hops):
    """Independent BFS: is target reachable from asker within max_hops over
    in-cell, unexpired vouch edges? (Hand-written; separate from the module.)"""
    def alive(item):
        exp = item.get("expires_at")
        return exp is None or exp > now
    edges = {}
    for v in vouches:
        if v.get("cell_id") == cell_id and alive(v):
            edges.setdefault(v["from"], set()).add(v["to"])
    if asker == target:
        return False, None
    frontier = {asker}
    seen = {asker}
    for hop in range(1, max_hops + 1):
        nxt = set()
        for node in frontier:
            nxt |= edges.get(node, set())
        if target in nxt:
            return True, hop
        nxt -= seen
        seen |= nxt
        frontier = nxt
        if not frontier:
            break
    return False, None


# ---- builders ---------------------------------------------------------------
def _vouch(frm, to, cell="barrio-1", exp=FUTURE):
    return {"from": frm, "to": to, "cell_id": cell, "expires_at": exp}


def _fact(about, statement="completed 12 exchanges", cell="barrio-1", exp=FUTURE):
    return {"about": about, "statement": statement, "cell_id": cell, "expires_at": exp}


def _req(asker="a", target="x", cell="barrio-1", now=NOW, max_hops=3,
         vouches=None, facts=None):
    return {
        "asker": asker, "target": target, "cell_id": cell, "now": now,
        "max_hops": max_hops,
        "graph": {"vouches": vouches or [], "facts": facts or []},
    }


# ---- AC1: a reachable, in-cell, unexpired target is known via trust ----------
def test_ac1_two_hop_known():
    r = _req(vouches=[_vouch("a", "t7"), _vouch("t7", "x")])
    out = query(r)
    assert out["verdict"] == "known_via_trust"
    assert out["from_your_position"]["reachable"] is True
    assert out["from_your_position"]["nearest_hops"] == 2
    assert ["a", "t7", "x"] in out["from_your_position"]["vouch_paths"]
    assert "t7" in out["from_your_position"]["vouched_by_people_you_trust"]
    # oracle agrees
    reach, hops = oracle_reachable(r["graph"]["vouches"], "a", "x", "barrio-1", NOW, 3)
    assert reach and hops == 2


def test_ac1_direct_one_hop():
    out = query(_req(vouches=[_vouch("a", "x")]))
    assert out["from_your_position"]["nearest_hops"] == 1
    assert ["a", "x"] in out["from_your_position"]["vouch_paths"]


def test_ac2_fact_surfaces_verbatim():
    f = _fact("x")
    out = query(_req(vouches=[_vouch("a", "x")], facts=[f]))
    facts = out["from_your_position"]["facts"]
    assert any(fx["statement"] == "completed 12 exchanges" for fx in facts)


def test_ac1_self_query_no_path_but_fact():
    # asker == target: no vouch-path, but a fact about self surfaces
    out = query(_req(asker="a", target="a", facts=[_fact("a", "hosted 3 events")]))
    assert out["from_your_position"]["reachable"] is False
    assert out["verdict"] == "known_via_trust"  # via the fact
    out2 = query(_req(asker="a", target="a"))
    assert out2["verdict"] == "no_info_from_your_position"


# ---- AC2: out-of-cell items ignored -----------------------------------------
def test_ac2_out_of_cell_ignored():
    out = query(_req(vouches=[_vouch("a", "t7", cell="otro"),
                              _vouch("t7", "x", cell="otro")]))
    assert out["verdict"] == "no_info_from_your_position"
    assert out["from_your_position"]["reachable"] is False
    assert out["from_your_position"]["vouch_paths"] == []


# ---- AC3: expired items forgotten -------------------------------------------
def test_ac3_expired_dropped():
    expired = _req(vouches=[_vouch("a", "t7", exp=PAST), _vouch("t7", "x", exp=PAST)])
    assert query(expired)["verdict"] == "no_info_from_your_position"


def test_ac3_fresh_kept():
    fresh = _req(vouches=[_vouch("a", "t7", exp=FUTURE), _vouch("t7", "x", exp=FUTURE)])
    assert query(fresh)["verdict"] == "known_via_trust"


def test_ac3_null_expiry_kept():
    out = query(_req(vouches=[_vouch("a", "x", exp=None)]))
    assert out["verdict"] == "known_via_trust"


# ---- AC4: absence is not a mark ---------------------------------------------
def test_ac4_empty_graph_neutral():
    out = query(_req())  # empty graph
    assert out["verdict"] == "no_info_from_your_position"
    assert out["from_your_position"]["reachable"] is False
    # no negative/blacklist field anywhere
    assert not any_key_matches(out, ("blacklist", "distrust", "ban", "penalty"))


def test_ac4_unreachable_returns_normally():
    # edges exist but none path a->x
    out = query(_req(vouches=[_vouch("b", "c"), _vouch("c", "d")]))
    assert out["verdict"] == "no_info_from_your_position"


# ---- AC5: no scalar out; surveillance shape refused in input ----------------
def test_ac5a_verdict_has_no_forbidden_keys():
    out = query(_req(vouches=[_vouch("a", "x")], facts=[_fact("x")]))
    keys = {str(k).lower() for k in scan_keys(out)}
    assert keys.isdisjoint(FORBIDDEN)


def test_ac5a_verdict_has_no_person_ranking_number():
    # the only numbers allowed: nearest_hops, considered_*, max_hops. No score/rank field.
    out = query(_req(vouches=[_vouch("a", "t7"), _vouch("t7", "x")]))
    fp = out["from_your_position"]
    assert set(fp.keys()) == {"reachable", "nearest_hops", "vouch_paths",
                              "vouched_by_people_you_trust", "facts"}


@pytest.mark.parametrize("graph", [
    {"vouches": [], "facts": [{"about": "x", "reputation": 0.9, "cell_id": "barrio-1"}]},
    {"vouches": [{"from": "a", "to": "x", "cell_id": "barrio-1",
                  "expires_at": None, "meta": {"trust_rank": 1}}], "facts": []},
    {"vouches": [], "facts": [{"about": "x", "cell_id": "barrio-1",
                               "seller": {"trust_score": 88}}]},
])
def test_ac5b_surveillance_shape_in_graph_refused(graph):
    r = _req()
    r["graph"] = graph
    with pytest.raises(LegibilityBreachError):
        query(r)


def test_ac5b_surveillance_in_envelope_refused():
    r = _req()
    r["blacklist"] = ["t9"]
    with pytest.raises(LegibilityBreachError):
        query(r)


# ---- AC6: no enumeration / no god-view entrypoint ---------------------------
def test_ac6_no_godview_functions():
    # the only public query entrypoint takes an asker + single target
    public = {n for n in dir(mod) if not n.startswith("_")}
    for forbidden_name in ("standing_of", "rank_all", "rank", "list_all",
                           "reputation_of", "score", "all_standings"):
        assert forbidden_name not in public


@pytest.mark.parametrize("bad_target", ["*", ["x", "y"], {"t": 1}, None, ""])
def test_ac6_wildcard_or_list_target_refused(bad_target):
    with pytest.raises(LegibilityBreachError):
        query(_req(target=bad_target))


# ---- AC7: position-relativity — the two-askers divergence proof --------------
def test_ac7_two_askers_diverge():
    graph = {"vouches": [_vouch("A", "t7"), _vouch("t7", "x")], "facts": []}
    rA = {"asker": "A", "target": "x", "cell_id": "barrio-1", "now": NOW,
          "max_hops": 3, "graph": graph}
    rB = dict(rA, asker="B")
    outA = query(copy.deepcopy(rA))
    outB = query(copy.deepcopy(rB))
    assert outA["verdict"] == "known_via_trust"
    assert outB["verdict"] == "no_info_from_your_position"
    assert outA != outB  # the same (target, cell) yields different answers => no god-view


# ---- AC8: determinism -------------------------------------------------------
def test_ac8_determinism():
    r = _req(vouches=[_vouch("a", "t7"), _vouch("a", "t8"),
                      _vouch("t7", "x"), _vouch("t8", "x")])
    a = query(copy.deepcopy(r))
    b = query(copy.deepcopy(r))
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    # both equal-length paths present, deterministically ordered
    assert a["from_your_position"]["vouch_paths"] == sorted(a["from_your_position"]["vouch_paths"])


# ---- AC9: envelope validation -----------------------------------------------
@pytest.mark.parametrize("mutate", [
    lambda r: r.update(asker=""),
    lambda r: r.pop("asker"),
    lambda r: r.update(cell_id=""),
    lambda r: r.update(now=""),
    lambda r: r.update(max_hops=0),
    lambda r: r.update(max_hops=-1),
    lambda r: r.update(max_hops="3"),
    lambda r: r.update(max_hops=True),
    lambda r: r.update(graph=[]),
    lambda r: r.update(graph={"vouches": "x", "facts": []}),
    lambda r: r.update(graph={"vouches": [{"from": "a"}], "facts": []}),  # malformed edge
    lambda r: r.update(graph={"vouches": [], "facts": [{"statement": "hi"}]}),  # no about
])
def test_ac9_envelope_validation(mutate):
    r = _req(vouches=[_vouch("a", "x")])
    mutate(r)
    with pytest.raises(LegibilityBreachError):
        query(r)


# ---- D-02 / D-05: dense graph stays bounded; reachability stays exact --------
def test_d02_dense_graph_bounded_but_reachability_exact():
    # a diamond chain has 2^k shortest paths; the concrete sample must be capped while
    # reachable / nearest_hops / vouched_by stay EXACT (computed by the linear reverse BFS).
    k = 20
    vouches = []
    for i in range(k):
        vouches += [_vouch("n%d" % i, "A%d" % i), _vouch("n%d" % i, "B%d" % i),
                    _vouch("A%d" % i, "n%d" % (i + 1)), _vouch("B%d" % i, "n%d" % (i + 1))]
    out = query(_req(asker="n0", target="n%d" % k, max_hops=2 * k, vouches=vouches))
    fp = out["from_your_position"]
    assert fp["reachable"] is True
    assert fp["nearest_hops"] == 2 * k                               # exact, not enumerated
    assert set(fp["vouched_by_people_you_trust"]) == {"A0", "B0"}    # exact direct trustees
    assert len(fp["vouch_paths"]) <= mod._MAX_VOUCH_PATHS            # sample is bounded
    assert out["audit_trace"]["paths_truncated"] is True            # 2^20 >> cap


def test_d05_duplicate_edges_yield_no_duplicate_paths():
    out = query(_req(vouches=[_vouch("a", "x"), _vouch("a", "x")]))
    assert out["from_your_position"]["vouch_paths"] == [["a", "x"]]  # not [["a","x"],["a","x"]]


# ---- AC-X: cross-layer consistency (shared forbidden taxonomy) --------------
def test_acx_capa1_surveillance_shape_refused_as_graph_node():
    r = _req()
    r["graph"] = {"vouches": [],
                  "facts": [{"about": "x", "cell_id": "barrio-1",
                             "seller": {"trust_score": 88}}]}
    with pytest.raises(LegibilityBreachError):
        query(r)


def test_acx_forbidden_keys_match_membrane_and_engine():
    # the three layers must share the exact taxonomy
    memb = Path(__file__).resolve().parent.parent / "src" / "partition" / "membrane.py"
    _s = importlib.util.spec_from_file_location("membrane", memb)
    _m = importlib.util.module_from_spec(_s)
    _s.loader.exec_module(_m)
    assert set(mod.FORBIDDEN_KEYS) == set(_m.FORBIDDEN_KEYS)
