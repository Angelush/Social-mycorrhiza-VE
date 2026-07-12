"""Acceptance tests for the Capa-4 assurance-contract engine.

Maps to evals/acceptance.md AC1-AC6. Uses an INDEPENDENT oracle (collections.Counter
+ integer division, hand-written) so the engine cannot self-confirm a bug (AGD-045).
"""
import copy
import importlib.util
import json
from collections import Counter
from pathlib import Path

import pytest

_ENGINE = Path(__file__).resolve().parent.parent / "src" / "assurance" / "assurance_engine.py"
_spec = importlib.util.spec_from_file_location("assurance_engine", _ENGINE)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)
resolve = mod.resolve

FORBIDDEN = ("score", "rating", "reputation", "rank", "blacklist", "ban",
             "penalty", "global_id", "dni")


# ---- independent oracle -----------------------------------------------------
def oracle(campaign):
    pledges = campaign["pledges"]
    tokens = [p["participant_token"] for p in pledges]
    distinct = len(set(tokens))
    status = "fires" if distinct >= campaign["threshold"] else "refunds"
    sums = Counter()
    if campaign["kind"] == "monetary":
        for p in pledges:
            sums[p["participant_token"]] += p["amount_cents"]
    return distinct, status, sums


def _scan_keys(obj):
    """Recursively yield every dict key in a nested structure."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _scan_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _scan_keys(v)


# ---- fixtures ---------------------------------------------------------------
TEST_A = {
    "campaign_id": "campA", "cell_id": "barrio-1", "kind": "binary",
    "threshold": 3, "sponsor_bonus_cents": 0, "expires_at": "2026-12-31T00:00:00Z",
    "pledges": [{"pledge_id": f"p{i}", "participant_token": t}
                for i, t in enumerate(["t1", "t2", "t3", "t4"])],
}
TEST_B = {
    "campaign_id": "campB", "cell_id": "barrio-1", "kind": "monetary",
    "threshold": 5, "sponsor_bonus_cents": 1000, "expires_at": "2026-12-31T00:00:00Z",
    "pledges": [
        {"pledge_id": "p1", "participant_token": "t1", "amount_cents": 2000},
        {"pledge_id": "p2", "participant_token": "t2", "amount_cents": 3000},
        {"pledge_id": "p3", "participant_token": "t1", "amount_cents": 500},
        {"pledge_id": "p4", "participant_token": "t3", "amount_cents": 1500},
    ],
}


# ---- AC1: threshold correctness (independent recompute) ---------------------
@pytest.mark.parametrize("camp", [TEST_A, TEST_B])
def test_ac1_threshold(camp):
    out = resolve(copy.deepcopy(camp))
    distinct, status, _ = oracle(camp)
    assert out["distinct_committers"] == distinct
    assert out["status"] == status


def test_ac1_boundary_exact():
    camp = copy.deepcopy(TEST_A)
    camp["threshold"] = 4  # distinct == threshold must FIRE (>=)
    assert resolve(camp)["status"] == "fires"
    camp["threshold"] = 5
    assert resolve(camp)["status"] == "refunds"


# ---- AC2: no-loss guarantee -------------------------------------------------
def test_ac2_no_loss():
    out = resolve(copy.deepcopy(TEST_B))
    _, _, sums = oracle(TEST_B)
    refunds = {r["participant_token"]: r["refund_cents"]
               for r in out["resolution"]["refunds"]}
    for token, total in sums.items():
        assert refunds[token] == total  # full make-whole, incl. re-pledge summed


def test_ac2_fires_has_empty_refunds():
    out = resolve(copy.deepcopy(TEST_A))
    assert out["resolution"]["refunds"] == []


# ---- AC3: bonus conservation + exactness ------------------------------------
def test_ac3_bonus_conservation():
    out = resolve(copy.deepcopy(TEST_B))
    bonuses = [r["bonus_cents"] for r in out["resolution"]["refunds"]]
    assert sum(bonuses) == TEST_B["sponsor_bonus_cents"]
    assert max(bonuses) - min(bonuses) <= 1  # split differs by at most 1 cent
    # first rem (by ascending token) get the extra cent
    refunds = out["resolution"]["refunds"]
    by_token = sorted(refunds, key=lambda r: r["participant_token"])
    rem = TEST_B["sponsor_bonus_cents"] % out["distinct_committers"]
    base = TEST_B["sponsor_bonus_cents"] // out["distinct_committers"]
    for i, r in enumerate(by_token):
        assert r["bonus_cents"] == base + (1 if i < rem else 0)


def test_ac3_no_bonus_when_fires():
    out = resolve(copy.deepcopy(TEST_A))
    assert out["resolution"]["fires"]["total_pledged_cents"] == 0


def test_ac3_all_int_no_float():
    for camp in (TEST_A, TEST_B):
        out = resolve(copy.deepcopy(camp))
        s = json.dumps(out)
        assert "." not in s.replace("2026-12-31", "")  # no float literals in money
        for r in out["resolution"]["refunds"]:
            assert isinstance(r["refund_cents"], int)
            assert isinstance(r["bonus_cents"], int)


# ---- AC4: determinism -------------------------------------------------------
@pytest.mark.parametrize("camp", [TEST_A, TEST_B])
def test_ac4_determinism(camp):
    a = resolve(copy.deepcopy(camp))
    b = resolve(copy.deepcopy(camp))
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# ---- AC5: anti-surveillance shape ------------------------------------------
@pytest.mark.parametrize("camp", [TEST_A, TEST_B])
def test_ac5a_no_forbidden_keys_in_output(camp):
    out = resolve(copy.deepcopy(camp))
    keys = {k.lower() for k in _scan_keys(out)}
    assert keys.isdisjoint(FORBIDDEN)


def test_ac5b_reject_forbidden_field_campaign():
    bad = copy.deepcopy(TEST_B)
    bad["global_score"] = {"t1": 0.9}
    with pytest.raises(ValueError):
        resolve(bad)


def test_ac5b_reject_forbidden_field_pledge():
    bad = copy.deepcopy(TEST_B)
    bad["pledges"][0]["reputation"] = 0.9
    with pytest.raises(ValueError):
        resolve(bad)


def test_ac5c_cross_campaign_independence():
    c1 = {"campaign_id": "c1", "cell_id": "b2", "kind": "binary", "threshold": 2,
          "sponsor_bonus_cents": 0, "expires_at": "2026-12-31T00:00:00Z",
          "pledges": [{"pledge_id": "p1", "participant_token": "t1"},
                      {"pledge_id": "p2", "participant_token": "t9"}]}
    c2 = {"campaign_id": "c2", "cell_id": "b3", "kind": "binary", "threshold": 4,
          "sponsor_bonus_cents": 0, "expires_at": "2026-12-31T00:00:00Z",
          "pledges": [{"pledge_id": "p1", "participant_token": "t1"},
                      {"pledge_id": "p2", "participant_token": "t5"}]}
    o1, o2 = resolve(c1), resolve(c2)
    assert o1["status"] == "fires" and o2["status"] == "refunds"
    # no field aggregates t1 across the two campaigns
    assert "t1" not in json.dumps(o1["audit_trace"])


# ---- AC6: membrane (kula/gimwali wall) -------------------------------------
def test_ac6_reject_priced_binary():
    bad = copy.deepcopy(TEST_A)
    bad["pledges"][0]["amount_cents"] = 500  # market price in an equality room
    with pytest.raises(ValueError):
        resolve(bad)


# ---- D-06: binary amount_cents is strictly typed (no == coercion) -----------
@pytest.mark.parametrize("bad_amount", [False, True, 0.0, 1.0, 500, -1])
def test_d06_binary_rejects_nonstrict_amount(bad_amount):
    # False/0.0 used to slip past `amount not in (0, None)` via Python's == coercion;
    # bool/float and any nonzero price are now all a membrane breach.
    bad = copy.deepcopy(TEST_A)
    bad["pledges"][0]["amount_cents"] = bad_amount
    with pytest.raises(ValueError):
        resolve(bad)


@pytest.mark.parametrize("ok_amount", [None, 0])
def test_d06_binary_accepts_explicit_no_price(ok_amount):
    camp = copy.deepcopy(TEST_A)
    camp["pledges"][0]["amount_cents"] = ok_amount
    resolve(camp)  # None or a strict int 0 is an explicit no-price -> must not raise


# ---- input validation -------------------------------------------------------
@pytest.mark.parametrize("mutate", [
    lambda c: c.update(threshold=0),
    lambda c: c.update(campaign_id=""),
    lambda c: c.update(cell_id=""),
    lambda c: c.update(sponsor_bonus_cents=-1),
    lambda c: c["pledges"].append({"pledge_id": "p1", "participant_token": "tx", "amount_cents": 1}),  # dup pledge_id
    lambda c: c.update(kind="weird"),
])
def test_input_validation_rejects(mutate):
    bad = copy.deepcopy(TEST_B)
    mutate(bad)
    with pytest.raises(ValueError):
        resolve(bad)


def test_monetary_missing_amount_rejected():
    bad = copy.deepcopy(TEST_B)
    del bad["pledges"][0]["amount_cents"]
    with pytest.raises(ValueError):
        resolve(bad)


# ---- membrane / anti-Sybil: no market instrument (bonus) in an equality room -
def test_reject_bonus_on_binary_campaign():
    bad = copy.deepcopy(TEST_A)          # binary, head-count, no stake
    bad["sponsor_bonus_cents"] = 500     # a monetary prime attached to it
    with pytest.raises(ValueError):
        resolve(bad)


# ---- AC5b extended: a forbidden key nested at ANY depth is refused ----------
def test_ac5b_reject_nested_forbidden_field():
    bad = copy.deepcopy(TEST_B)
    bad["meta"] = {"nested": {"reputation": 0.9}}  # dossier hidden a level down
    with pytest.raises(ValueError):
        resolve(bad)


# ---- conservation aborts are a distinct signal, NOT a user-input ValueError -
def test_invariant_error_is_not_valueerror():
    assert issubclass(mod.AssuranceInvariantError, Exception)
    assert not issubclass(mod.AssuranceInvariantError, ValueError)
