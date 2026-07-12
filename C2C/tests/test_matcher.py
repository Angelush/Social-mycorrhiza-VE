"""Acceptance tests for the Capa-3 prosocial-affordance matcher.

Maps to workflows/micorriza-politica/capa3/evals/acceptance.md AC1-AC13 + AC-X.

The correctness under test is the DETERMINISTIC WRAPPER's. Every test injects a deterministic
or adversarial STUB `propose` — the suite is fully offline (no live API calls). The defining test
is AC10: given a fully-adversarial/hallucinated stub model (off-cell, non-consenting, person-scalar,
engagement-shaped, unknown token, off-schema), the wrapper drops everything bad and never crashes.

Uses an INDEPENDENT hand-written eligibility filter + key-walker oracle (not the module's own
logic) so the wrapper cannot self-confirm a bug (AGD-045).
"""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

_MOD = Path(__file__).resolve().parent.parent / "src" / "matcher" / "matcher.py"
_spec = importlib.util.spec_from_file_location("matcher", _MOD)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)
match = mod.match
MatcherBreachError = mod.MatcherBreachError

FORBIDDEN = ("score", "rating", "reputation", "rank", "blacklist", "ban",
             "penalty", "global_id", "dni")
ENGAGEMENT = ("click", "dwell", "engagement", "viral", "watch_time", "impression",
              "ctr", "feed", "time_in_app", "notification", "streak")

NOW = "2026-07-06T00:00:00Z"
FUTURE = "2027-01-01T00:00:00Z"
PAST = "2020-01-01T00:00:00Z"
SOON = "2026-07-14T00:00:00Z"


# ---- independent oracles ----------------------------------------------------
def any_key_matches(obj, tokens):
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


def oracle_eligible_tokens(candidates, cell_ids, now):
    """Independent re-derivation of which candidate tokens are eligible to be surfaced."""
    out = set()
    for c in candidates:
        consent = c.get("consent") or {}
        in_cell = c.get("cell_id") in set(cell_ids)
        consenting = consent.get("surfaceable") is True
        exp = c.get("expires_at")
        unexpired = exp is None or exp > now
        if in_cell and consenting and unexpired:
            out.add(c["token"])
    return out


# ---- builders ---------------------------------------------------------------
def _cand(token, cell="barrio-1", offers=None, needs=None, goals=None,
          surfaceable=True, exp=FUTURE, facts=None):
    c = {"token": token, "cell_id": cell,
         "offers": offers or [], "needs": needs or [], "goals": goals or [],
         "expires_at": exp}
    if surfaceable is not None:
        c["consent"] = {"surfaceable": surfaceable}
    if facts is not None:
        c["facts"] = facts
    return c


def _req(candidates=None, cell_ids=None, self_offers=None, self_needs=None,
         self_goals=None, now=NOW, expires_at=SOON, max_proposals=3, asker="a"):
    return {
        "asker": asker,
        "cell_ids": cell_ids or ["barrio-1"],
        "now": now,
        "expires_at": expires_at,
        "max_proposals": max_proposals,
        "self": {"offers": self_offers or [], "needs": self_needs or [],
                 "goals": self_goals or []},
        "candidates": candidates or [],
    }


# ---- stub models (deterministic, injected) ----------------------------------
def stub_echo(context):
    """One clean offer_meets_need proposal per eligible candidate the wrapper handed us."""
    return [{"token": c["token"], "kind": "offer_meets_need",
             "reason": "you offer what " + c["token"] + " needs"}
            for c in context["candidates"]]


def stub_fixed(proposals):
    return lambda context: copy.deepcopy(proposals)


def stub_empty(context):
    return []


# ---- AC1: a valid candidate is surfaced -------------------------------------
def test_ac1_valid_candidate_surfaced():
    r = _req(self_offers=["bike repair"],
             candidates=[_cand("t7", needs=["bike fixed"])])
    out = match(r, stub_echo)
    assert out["verdict"] == "proposals_surfaced"
    assert len(out["proposals"]) == 1
    p = out["proposals"][0]
    assert p["token"] == "t7"
    assert p["cell_id"] == "barrio-1"
    assert p["kind"] == "offer_meets_need"
    assert p["reason"]
    assert p["expires_at"] == SOON
    # oracle agrees on eligibility
    assert oracle_eligible_tokens(r["candidates"], r["cell_ids"], NOW) == {"t7"}


def test_ac1_cited_facts_echoed_verbatim():
    fact = {"statement": "completed 12 exchanges", "cell_id": "barrio-1", "expires_at": None}
    r = _req(candidates=[_cand("t7", facts=[fact])])
    out = match(r, stub_fixed([{"token": "t7", "kind": "shared_goal", "reason": "r",
                                "cite_facts": [fact]}]))
    assert out["proposals"][0]["cited_facts"] == [fact]
    # and no scalar snuck in
    keys = {str(k).lower() for k in scan_keys(out)}
    assert keys.isdisjoint(FORBIDDEN)


def test_ac1_no_matches_verdict_when_empty():
    out = match(_req(candidates=[_cand("t7")]), stub_empty)
    assert out["verdict"] == "no_matches_from_your_position"
    assert out["proposals"] == []


# ---- AC2: proposes, never imposes -------------------------------------------
def test_ac2_no_acting_surface():
    public = {n for n in dir(mod) if not n.startswith("_")}
    for forbidden_name in ("connect", "notify", "introduce", "send", "persist",
                           "rank", "message", "auto_connect"):
        assert forbidden_name not in public
    out = match(_req(candidates=[_cand("t7")]), stub_echo)
    # scan the surfaced content, not the audit-trace counters (whose names legitimately contain
    # substrings like "dropped_non_connecting"). No action field may reach the human.
    surfaced = {k: v for k, v in out.items() if k != "audit_trace"}
    assert not any_key_matches(surfaced, ("notify", "connect", "sent", "message", "action"))


# ---- AC3: engagement signal is unrepresentable ------------------------------
def test_ac3_engagement_key_in_candidate_refused():
    c = _cand("t7")
    c["click_count"] = 40  # non-whitelisted AND engagement-shaped
    with pytest.raises(MatcherBreachError):
        match(_req(candidates=[c]), stub_echo)


def test_ac3_engagement_nested_in_self_refused():
    r = _req(candidates=[_cand("t7")])
    r["self"]["meta"] = {"dwell_ms": 9}  # whitelist violation on self
    with pytest.raises(MatcherBreachError):
        match(r, stub_echo)


def test_ac3_non_whitelisted_key_refused():
    c = _cand("t7")
    c["priority"] = 9
    with pytest.raises(MatcherBreachError):
        match(_req(candidates=[c]), stub_echo)


def test_ac3_feed_rank_at_depth_refused():
    c = _cand("t7", facts=[{"statement": "s", "cell_id": "barrio-1",
                            "meta": {"feed_rank": 1}}])
    with pytest.raises(MatcherBreachError):
        match(_req(candidates=[c]), stub_echo)


# ---- AC4: off-cell proposals dropped ----------------------------------------
def test_ac4_off_cell_candidate_never_surfaced():
    # t9 declared in another cell -> ineligible; model proposes it anyway -> dropped
    r = _req(cell_ids=["barrio-1"],
             candidates=[_cand("t9", cell="otro-barrio")])
    out = match(r, stub_fixed([{"token": "t9", "kind": "shared_goal", "reason": "r"}]))
    assert out["proposals"] == []
    assert out["audit_trace"]["dropped_unknown_token"] >= 1


def test_ac4_hallucinated_token_dropped():
    out = match(_req(candidates=[_cand("t7")]),
                stub_fixed([{"token": "ghost", "kind": "offer_meets_need", "reason": "r"}]))
    assert out["proposals"] == []
    assert out["audit_trace"]["dropped_unknown_token"] >= 1


# ---- AC5: no scalar out; surveillance shape dropped/refused -----------------
def test_ac5a_no_forbidden_key_in_output():
    out = match(_req(candidates=[_cand("t7")]), stub_echo)
    keys = {str(k).lower() for k in scan_keys(out)}
    assert all(not any(t in k for t in FORBIDDEN) for k in keys)


def test_ac5b_model_scalar_proposal_dropped_not_stripped():
    out = match(_req(candidates=[_cand("t7")]),
                stub_fixed([{"token": "t7", "kind": "shared_goal", "reason": "r",
                             "match_score": 0.9}]))
    assert out["proposals"] == []  # dropped whole, not stripped-and-kept
    assert out["audit_trace"]["dropped_surveillance_shape"] >= 1


def test_ac5b_model_scalar_nested_dropped():
    out = match(_req(candidates=[_cand("t7")]),
                stub_fixed([{"token": "t7", "kind": "shared_goal", "reason": "r",
                             "meta": {"reputation": 5}}]))
    assert out["proposals"] == []
    assert out["audit_trace"]["dropped_surveillance_shape"] >= 1


def test_ac5c_request_surveillance_refused():
    c = _cand("t7", facts=[{"statement": "s", "cell_id": "barrio-1",
                            "seller": {"trust_score": 88}}])
    with pytest.raises(MatcherBreachError):
        match(_req(candidates=[c]), stub_echo)


# ---- AC6: non-consenting never surfaced -------------------------------------
def test_ac6_non_consenting_dropped():
    r = _req(candidates=[_cand("t8", surfaceable=False)])
    out = match(r, stub_fixed([{"token": "t8", "kind": "shared_goal", "reason": "r"}]))
    assert out["proposals"] == []
    assert oracle_eligible_tokens(r["candidates"], r["cell_ids"], NOW) == set()


def test_ac6_consent_absent_dropped():
    r = _req(candidates=[_cand("t8", surfaceable=None)])
    out = match(r, stub_fixed([{"token": "t8", "kind": "shared_goal", "reason": "r"}]))
    assert out["proposals"] == []


# ---- AC7: forgetting --------------------------------------------------------
def test_ac7_expired_candidate_not_surfaced():
    out = match(_req(candidates=[_cand("t7", exp=PAST)]), stub_echo)
    assert out["verdict"] == "no_matches_from_your_position"


def test_ac7_fresh_candidate_surfaced_and_stamped():
    out = match(_req(candidates=[_cand("t7", exp=FUTURE)]), stub_echo)
    assert out["verdict"] == "proposals_surfaced"
    assert out["proposals"][0]["expires_at"] == SOON


# ---- AC8: model order discarded ---------------------------------------------
def test_ac8_model_order_discarded():
    cands = [_cand("t1"), _cand("t2"), _cand("t3")]
    props = [{"token": t, "kind": "offer_meets_need", "reason": "r"} for t in ("t1", "t2", "t3")]
    out1 = match(_req(candidates=cands, max_proposals=5), stub_fixed([props[2], props[0], props[1]]))
    out2 = match(_req(candidates=cands, max_proposals=5), stub_fixed([props[1], props[2], props[0]]))
    assert json.dumps(out1["proposals"]) == json.dumps(out2["proposals"])


# ---- AC9: bounding ----------------------------------------------------------
def test_ac9_bounding():
    cands = [_cand("t%d" % i) for i in range(5)]
    out = match(_req(candidates=cands, max_proposals=2), stub_echo)
    assert len(out["proposals"]) == 2
    assert out["audit_trace"]["emitted"] == 2


# ---- AC10: adversarial model output — THE wrapper-correctness test ----------
def test_ac10_adversarial_model_all_bad_dropped_never_crashes():
    good = _cand("good", offers=["x"])
    offcell = _cand("t9", cell="otro-barrio")
    nonconsent = _cand("t8", surfaceable=False)
    r = _req(candidates=[good, offcell, nonconsent], max_proposals=5)
    adversarial = [
        {"token": "good", "kind": "offer_meets_need", "reason": "valid"},        # the one good
        {"token": "t9", "kind": "shared_goal", "reason": "off-cell"},            # ineligible
        {"token": "t8", "kind": "shared_goal", "reason": "non-consenting"},      # ineligible
        {"token": "good", "kind": "shared_goal", "reason": "r", "match_score": 1.0},   # scalar
        {"token": "good", "kind": "shared_goal", "reason": "r", "click_rate": 9},      # engagement
        {"token": "ghost", "kind": "offer_meets_need", "reason": "hallucinated"},  # unknown token
        {"kind": "offer_meets_need", "reason": "no token"},                        # off-schema
        {"token": "good", "kind": "not_a_kind", "reason": "bad kind"},             # off-schema
    ]
    out = match(r, stub_fixed(adversarial))  # must NOT raise
    assert len(out["proposals"]) == 1
    assert out["proposals"][0]["token"] == "good"
    assert out["proposals"][0]["kind"] == "offer_meets_need"
    at = out["audit_trace"]
    assert at["dropped_unknown_token"] >= 3      # t9, t8, ghost
    assert at["dropped_surveillance_shape"] >= 1  # scalar + engagement
    assert at["dropped_off_schema"] >= 2          # no-token + bad-kind


def test_ac10_garbage_model_return_never_crashes():
    for junk in (None, "not a list", 42, {"proposals": []}, [None, 1, "x"]):
        out = match(_req(candidates=[_cand("t7")]), lambda ctx, j=junk: j)
        assert out["verdict"] == "no_matches_from_your_position"


def test_ac10_non_list_cite_facts_dropped_never_crashes():
    """An otherwise-valid proposal whose cite_facts is model garbage (non-list) must
    survive with every cite dropped — never crash the wrapper (F7; spec 'never a crash').
    Regression: 42/True/3.5 used to raise TypeError inside the cite-matching step."""
    fact = {"statement": "completed 12 exchanges", "cell_id": "barrio-1", "expires_at": None}
    for junk in (42, True, 3.5, "completed 12 exchanges", {"statement": "s"}):
        out = match(_req(candidates=[_cand("t7", facts=[fact])]),
                    stub_fixed([{"token": "t7", "kind": "shared_goal", "reason": "r",
                                 "cite_facts": junk}]))
        assert len(out["proposals"]) == 1, f"proposal dropped for cite_facts={junk!r}"
        assert out["proposals"][0]["cited_facts"] == []


# ---- AC11: determinism ------------------------------------------------------
def test_ac11_determinism():
    r = _req(self_offers=["bike repair"], candidates=[_cand("t7", needs=["bike fixed"])])
    a = match(copy.deepcopy(r), stub_echo)
    b = match(copy.deepcopy(r), stub_echo)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# ---- AC12: envelope validation ----------------------------------------------
@pytest.mark.parametrize("mutate", [
    lambda r: r.update(asker=""),
    lambda r: r.pop("asker"),
    lambda r: r.update(cell_ids=[]),
    lambda r: r.update(cell_ids="barrio-1"),
    lambda r: r.update(now=""),
    lambda r: r.update(expires_at=""),
    lambda r: r.update(max_proposals=0),
    lambda r: r.update(max_proposals=-1),
    lambda r: r.update(max_proposals="3"),
    lambda r: r.update(max_proposals=True),
    lambda r: r.update(self=[]),
    lambda r: r.update(candidates="x"),
    lambda r: r["candidates"].append({"cell_id": "barrio-1"}),  # missing token
    lambda r: r["candidates"].append({"token": "t", "cell_id": "barrio-1", "priority": 1}),  # bad key
])
def test_ac12_envelope_validation(mutate):
    r = _req(candidates=[_cand("t7")])
    mutate(r)
    with pytest.raises(MatcherBreachError):
        match(r, stub_echo)


def test_ac12_propose_not_callable_refused():
    with pytest.raises(MatcherBreachError):
        match(_req(candidates=[_cand("t7")]), "not callable")


# ---- AC13: injected client, importable offline ------------------------------
def test_ac13_matcher_has_no_top_level_anthropic_import():
    src = _MOD.read_text()
    for line in src.splitlines():
        stripped = line.strip()
        assert not stripped.startswith("import anthropic")
        assert not stripped.startswith("from anthropic")


def test_ac13_claude_client_defers_anthropic_import():
    # claude_matcher.py must also not import anthropic at module top (lazy inside the factory).
    src = (_MOD.parent / "claude_matcher.py").read_text()
    top_level = [l for l in src.splitlines() if l and not l[0].isspace()]
    for line in top_level:
        assert not line.startswith("import anthropic")
        assert not line.startswith("from anthropic")


# ---- AC-X: cross-layer consistency ------------------------------------------
def test_acx_capa1_surveillance_shape_refused_as_candidate_node():
    c = _cand("t7", facts=[{"statement": "s", "cell_id": "barrio-1",
                            "seller": {"trust_score": 88}}])
    with pytest.raises(MatcherBreachError):
        match(_req(candidates=[c]), stub_echo)


def test_acx_forbidden_keys_match_all_layers():
    def load(rel):
        p = Path(__file__).resolve().parent.parent / rel
        s = importlib.util.spec_from_file_location(p.stem, p)
        m = importlib.util.module_from_spec(s)
        s.loader.exec_module(m)
        return m
    memb = load("src/partition/membrane.py")
    leg = load("src/legibility/legibility_query.py")
    assert set(mod.FORBIDDEN_KEYS) == set(memb.FORBIDDEN_KEYS) == set(leg.FORBIDDEN_KEYS)
