"""Acceptance tests for the Capa-6 sociocratic governance (consent, not consensus).

Maps to workflows/micorriza-politica/capa6/evals/acceptance.md AC1-AC12 + AC-X.

The component is DETERMINISTIC (no LLM, no stub, no network). The defining test is AC1: the same
proposal in the same circle yields the same verdict regardless of any reputation the members carry —
a weighted/reputation-bearing input is refused, and one-token-one-voice holds.

Uses an INDEPENDENT hand-written resolution oracle (not the module's own logic) so the module cannot
self-confirm a bug (AGD-045).
"""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

_MOD = Path(__file__).resolve().parent.parent / "src" / "governance" / "governance.py"
_spec = importlib.util.spec_from_file_location("governance", _MOD)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)
decide = mod.decide
GovernanceBreachError = mod.GovernanceBreachError

FORBIDDEN = ("score", "rating", "reputation", "rank", "blacklist", "ban",
             "penalty", "global_id", "dni")
WEIGHT = ("weight", "shares", "voting_power", "vote_count", "tally", "majority",
          "percent", "proxy", "seats", "quorum")

NOW = "2026-07-07T00:00:00Z"
SOON = "2026-08-01T00:00:00Z"
PAST = "2020-01-01T00:00:00Z"


# ---- independent oracles ----------------------------------------------------
def scan_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from scan_keys(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from scan_keys(v)


def oracle_verdict(req):
    """Independent re-derivation of the verdict + surfaced reasons (separate from the module)."""
    circle, now = req["circle_id"], req["now"]
    paramount, concerns = [], []
    for d in req["dispositions"]:
        if d["circle_id"] != circle:
            continue
        exp = d.get("expires_at")
        if exp is not None and exp <= now:
            continue
        if d["disposition"] == "object":
            obj = d["objection"]
            if obj["paramount"]:
                paramount.append(obj["reason"])
            else:
                concerns.append(obj["reason"])
    verdict = "revisit" if paramount else "adopted"
    return verdict, sorted(paramount), sorted(concerns)


# ---- builders ---------------------------------------------------------------
def _disp(token, disposition="consent", reason=None, paramount=None, circle="c1", expires_at=None):
    d = {"token": token, "disposition": disposition, "circle_id": circle}
    if disposition == "object":
        d["objection"] = {"paramount": paramount, "reason": reason}
    if expires_at is not None:
        d["expires_at"] = expires_at
    return d


def _req(dispositions=None, circle="c1", proposal="p1", now=NOW, expires_at=SOON):
    return {"circle_id": circle, "proposal_id": proposal, "now": now,
            "expires_at": expires_at, "dispositions": dispositions or []}


# ---- AC2 / A: consent adopts ------------------------------------------------
def test_ac2_consent_adopts():
    r = _req([_disp("t1"), _disp("t2"), _disp("t3")])
    out = decide(r)
    assert out["verdict"] == "adopted"
    assert out["paramount_objections"] == []
    assert out["concerns"] == []
    assert out["expires_at"] == SOON
    assert oracle_verdict(r)[0] == "adopted"


def test_ac2_empty_circle_adopts_vacuously():
    out = decide(_req([]))
    assert out["verdict"] == "adopted"  # vacuous consent (ST2)


# ---- AC4 / B: a single paramount objection blocks ---------------------------
def test_ac4_single_paramount_blocks():
    disps = [_disp("t%d" % i) for i in range(5)]
    disps.append(_disp("tx", "object", reason="no budget until Q3", paramount=True))
    r = _req(disps)
    out = decide(r)
    assert out["verdict"] == "revisit"
    assert out["paramount_objections"] == [{"reason": "no budget until Q3"}]
    v, p, c = oracle_verdict(r)
    assert v == "revisit" and p == ["no budget until Q3"]


def test_ac4_remove_objection_flips_to_adopted():
    disps = [_disp("t%d" % i) for i in range(5)]
    assert decide(_req(disps))["verdict"] == "adopted"


def test_ac4_nonparamount_concern_does_not_block():
    r = _req([_disp("t1"), _disp("t2"),
              _disp("tc", "object", reason="prefer a trial", paramount=False)])
    out = decide(r)
    assert out["verdict"] == "adopted"
    assert out["concerns"] == [{"reason": "prefer a trial"}]


# ---- AC1 / C: voice independent of reputation -------------------------------
def test_ac1_weighted_voice_refused():
    for wk in ("weight", "shares", "voting_power", "vote_count", "proxy", "majority", "quorum"):
        d = _disp("t1")
        d[wk] = 10
        with pytest.raises(GovernanceBreachError):
            decide(_req([d]))


def test_ac1_weight_nested_refused():
    d = _disp("tx", "object", reason="r", paramount=True)
    d["objection"]["weight"] = 5
    with pytest.raises(GovernanceBreachError):
        decide(_req([d]))


def test_ac1_verdict_invariant_to_token_labels():
    # a "senior" label is just a token; there is no weighting path, so the verdict is unchanged
    r1 = _req([_disp("senior-elder"), _disp("newcomer"),
               _disp("tx", "object", reason="r", paramount=True)])
    r2 = _req([_disp("nobody-a"), _disp("nobody-b"),
               _disp("tx", "object", reason="r", paramount=True)])
    assert decide(r1)["verdict"] == decide(r2)["verdict"] == "revisit"


def test_ac8_one_token_one_voice_duplicate_refused():
    with pytest.raises(GovernanceBreachError):
        decide(_req([_disp("t1"), _disp("t1")]))


# ---- AC2b / D: no majority / no tally ---------------------------------------
def test_ac2b_no_tally_number_in_output():
    disps = [_disp("t%d" % i) for i in range(5)]
    disps.append(_disp("tx", "object", reason="r", paramount=True))
    out = decide(_req(disps))
    # the verdict is a categorical string; no top-level numeric verdict field
    assert isinstance(out["verdict"], str)
    for k in ("percent", "majority", "tally", "for", "against", "approve_pct"):
        assert k not in out


# ---- AC3 / E: no person-scalar in -------------------------------------------
def test_ac3_reputation_refused():
    d = _disp("tx", "object", reason="r", paramount=True)
    d["objection"]["reputation"] = 5
    with pytest.raises(GovernanceBreachError):
        decide(_req([d]))


def test_ac3_request_level_surveillance_refused():
    r = _req([_disp("t1")])
    r["member"] = {"trust_score": 88}
    with pytest.raises(GovernanceBreachError):
        decide(r)


# ---- AC5 / F: an objection is a pause, never a mark -------------------------
def test_ac5_no_objector_token_in_output():
    r = _req([_disp("consenter"),
              _disp("objector-token", "object", reason="no budget", paramount=True)])
    out = decide(r)
    all_values = list(scan_keys(out))
    # no objector token appears anywhere in the output (keys or values)
    def walk_values(o):
        if isinstance(o, dict):
            for v in o.values():
                yield from walk_values(v)
        elif isinstance(o, list):
            for v in o:
                yield from walk_values(v)
        else:
            yield o
    assert "objector-token" not in list(walk_values(out))
    assert "consenter" not in list(walk_values(out))


# ---- AC6 / G: circle-local, no auto-propagation -----------------------------
def test_ac6_off_circle_dropped():
    r = _req([_disp("t1"),
              _disp("tx", "object", reason="r", paramount=True, circle="c2")])
    out = decide(r)
    assert out["verdict"] == "adopted"  # the c2 objection does not block c1
    assert out["audit_trace"]["dropped_off_circle"] >= 1


def test_ac6_no_escalation_field():
    out = decide(_req([_disp("t1")]))
    for k in ("parent", "escalate", "global", "propagate", "parent_circle"):
        assert k not in out


# ---- AC7 / H: forgetting -----------------------------------------------------
def test_ac7_expired_objection_dropped():
    r = _req([_disp("t1"),
              _disp("tx", "object", reason="r", paramount=True, expires_at=PAST)])
    out = decide(r)
    assert out["verdict"] == "adopted"  # expired objection no longer blocks
    assert out["audit_trace"]["dropped_expired"] >= 1


def test_ac7_fresh_objection_blocks_and_stamped():
    r = _req([_disp("t1"),
              _disp("tx", "object", reason="r", paramount=True, expires_at=SOON)])
    out = decide(r)
    assert out["verdict"] == "revisit"
    assert out["expires_at"] == SOON


# ---- D-03: one-token-one-voice is a PER-CIRCLE invariant --------------------
def test_d03_off_circle_duplicate_token_does_not_block():
    # the same token consents in c1 and appears again on an off-circle (c2) disposition;
    # the c2 entry is dropped, so it must NOT veto c1's round (was a blocker/DoS before D-03).
    r = _req([_disp("alice"), _disp("bob"), _disp("alice", circle="c2")])
    out = decide(r)
    assert out["verdict"] == "adopted"
    assert out["audit_trace"]["dropped_off_circle"] >= 1


def test_d03_expired_duplicate_token_does_not_block():
    r = _req([_disp("alice"), _disp("alice", expires_at=PAST)])  # expired dup dropped, not fatal
    out = decide(r)
    assert out["verdict"] == "adopted"
    assert out["audit_trace"]["dropped_expired"] >= 1


def test_d03_in_circle_duplicate_still_refused():
    # the invariant still bites where it matters: two live in-circle voices, same token
    with pytest.raises(GovernanceBreachError):
        decide(_req([_disp("alice"), _disp("alice")]))


# ---- AC9: determinism + canonical order -------------------------------------
def test_ac9_determinism_and_canonical_order():
    disps = [_disp("t1", "object", reason="z-reason", paramount=True),
             _disp("t2", "object", reason="a-reason", paramount=True)]
    a = decide(_req(disps))
    b = decide(_req(list(reversed(disps))))
    assert a["paramount_objections"] == [{"reason": "a-reason"}, {"reason": "z-reason"}]
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# ---- AC10: envelope validation ----------------------------------------------
@pytest.mark.parametrize("mutate", [
    lambda r: r.update(circle_id=""),
    lambda r: r.pop("circle_id"),
    lambda r: r.update(proposal_id=""),
    lambda r: r.update(now=""),
    lambda r: r.update(expires_at=""),
    lambda r: r.update(dispositions="x"),
    lambda r: r["dispositions"].append("not a dict"),
    lambda r: r["dispositions"].append({"token": "t", "disposition": "consent",
                                        "circle_id": "c1", "priority": 1}),  # bad key
    lambda r: r["dispositions"].append({"token": "t", "disposition": "veto",
                                        "circle_id": "c1"}),  # bad disposition
    lambda r: r["dispositions"].append({"token": "t", "disposition": "object",
                                        "circle_id": "c1"}),  # object w/o objection
    lambda r: r["dispositions"].append({"token": "t", "disposition": "object", "circle_id": "c1",
                                        "objection": {"reason": "r"}}),  # no paramount
    lambda r: r["dispositions"].append({"token": "t", "disposition": "object", "circle_id": "c1",
                                        "objection": {"paramount": True, "reason": ""}}),  # empty reason
    lambda r: r["dispositions"].append({"token": "t", "disposition": "object", "circle_id": "c1",
                                        "objection": {"paramount": "yes", "reason": "r"}}),  # not bool
    lambda r: r["dispositions"].append({"token": "t", "disposition": "consent", "circle_id": "c1",
                                        "objection": {"paramount": True, "reason": "r"}}),  # consent+obj
    lambda r: r["dispositions"].append({"token": "", "disposition": "consent", "circle_id": "c1"}),
])
def test_ac10_envelope_validation(mutate):
    r = _req([_disp("seed")])
    mutate(r)
    with pytest.raises(GovernanceBreachError):
        decide(r)


# ---- AC11: no LLM / no network / stdlib-only --------------------------------
def test_ac11_no_network_imports():
    src = _MOD.read_text()
    for banned in ("import anthropic", "from anthropic", "import requests", "import httpx",
                   "import openai", "import urllib", "import socket"):
        assert banned not in src


def test_ac11_decide_takes_only_request():
    import inspect
    assert list(inspect.signature(decide).parameters) == ["request"]


# ---- AC12: bad-faith blocker enforced as procedure, not judged --------------
def test_ac12_spurious_paramount_still_blocks():
    r = _req([_disp("t1"), _disp("t2"),
              _disp("bad", "object", reason="I just don't like it", paramount=True)])
    out = decide(r)
    assert out["verdict"] == "revisit"
    assert out["paramount_objections"] == [{"reason": "I just don't like it"}]


# ---- AC-X: cross-layer consistency ------------------------------------------
def test_acx_capa1_surveillance_shape_refused():
    r = _req([_disp("t1")])
    r["member"] = {"trust_score": 88}
    with pytest.raises(GovernanceBreachError):
        decide(r)


def test_acx_forbidden_keys_match_all_layers():
    def load(rel):
        p = Path(__file__).resolve().parent.parent / rel
        s = importlib.util.spec_from_file_location(p.stem, p)
        m = importlib.util.module_from_spec(s)
        s.loader.exec_module(m)
        return m
    memb = load("src/partition/membrane.py")
    leg = load("src/legibility/legibility_query.py")
    matcher = load("src/matcher/matcher.py")
    stig = load("src/stigmergy/stigmergy.py")
    assert (set(mod.FORBIDDEN_KEYS) == set(memb.FORBIDDEN_KEYS) == set(leg.FORBIDDEN_KEYS)
            == set(matcher.FORBIDDEN_KEYS) == set(stig.FORBIDDEN_KEYS))
