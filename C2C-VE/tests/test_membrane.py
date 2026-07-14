"""Acceptance tests for the Capa-1 relational-mode partition firewall.

Maps to workflows/micorriza-politica/capa1/evals/acceptance.md AC1-AC8 + AC-X.
Uses an INDEPENDENT recursive key-walker oracle (hand-written, not the firewall's
own scanner) so the firewall cannot self-confirm a bug (AGD-045).
"""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

_MOD = Path(__file__).resolve().parent.parent / "src" / "partition" / "membrane.py"
_spec = importlib.util.spec_from_file_location("membrane", _MOD)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)
admit = mod.admit
MembraneBreachError = mod.MembraneBreachError

FORBIDDEN = ("score", "rating", "reputation", "rank", "blacklist", "ban",
             "penalty", "global_id", "dni")
MARKET = ("price", "cost", "fee", "_cents", "currency", "valuation", "denominat")


# ---- independent oracle -----------------------------------------------------
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


def _mk(mode, payload, **kw):
    base = {"mode": mode, "cell_id": "barrio-1", "interaction_id": "ix1",
            "expires_at": "2026-12-31T00:00:00Z", "participants": ["t1", "t2"],
            "payload": payload}
    base.update(kw)
    return base


# ---- AC1: well-typed interactions are admitted ------------------------------
def test_ac1_gift_admits():
    out = admit(_mk("communal_gift", {"offer": "help moving", "note": "no strings"}))
    assert out["admitted"] is True
    assert out["mode"] == "communal_gift"
    assert out["cell_id"] == "barrio-1"
    assert out["interaction_id"] == "ix1"
    assert out["expires_at"] == "2026-12-31T00:00:00Z"


def test_ac1_equality_in_kind_admits():
    out = admit(_mk("equality_matching", {"turns_taken": 1, "turns_owed_in_kind": 1}))
    assert out["admitted"] is True


def test_ac1_market_with_price_admits():
    out = admit(_mk("market_price", {"item": "bike", "amount_cents": 8000, "currency": "EUR"}))
    assert out["admitted"] is True


def test_ac1_expires_at_absent_carries_null():
    ix = _mk("communal_gift", {"offer": "x"})
    del ix["expires_at"]
    assert admit(ix)["expires_at"] is None


# ---- D-01: the envelope is whitelisted (no market key can ride the envelope) --
def test_d01_market_key_on_envelope_refused_in_gift_room():
    ix = _mk("communal_gift", {"offer": "help moving"})
    ix["fee_cents"] = 100  # a market instrument as a top-level sibling of payload
    with pytest.raises(MembraneBreachError):
        admit(ix)


def test_d01_arbitrary_unknown_envelope_key_refused():
    ix = _mk("market_price", {"item": "bike"})
    ix["extra_metadata"] = {"anything": 1}
    with pytest.raises(MembraneBreachError):
        admit(ix)


def test_d01_all_whitelisted_envelope_keys_still_admit():
    ix = {"mode": "equality_matching", "cell_id": "c1", "interaction_id": "i1",
          "expires_at": "2026-12-31T00:00:00Z", "participants": ["t1"],
          "payload": {"turn": 1}}
    assert admit(ix)["admitted"] is True


# ---- AC2: market leak into a non-market room is refused ----------------------
@pytest.mark.parametrize("mode", ["communal_gift", "equality_matching"])
@pytest.mark.parametrize("payload", [
    {"offer": "childcare", "price": 500},
    {"swap": {"terms": {"fee_cents": 200}}},          # nested one level down
    {"help": "ride", "currency": "USD"},
    {"deal": {"cost": 10}},
])
def test_ac2_market_leak_refused(mode, payload):
    with pytest.raises(MembraneBreachError):
        admit(_mk(mode, payload))
    # oracle agrees the payload carries a market key
    assert any_key_matches(payload, MARKET)


# ---- AC3: reciprocity ledger refused in gift, allowed in-kind in equality ----
def test_ac3_ledger_refused_in_gift():
    with pytest.raises(MembraneBreachError):
        admit(_mk("communal_gift", {"care": "meals", "balance_owed": 3}))


def test_ac3_in_kind_counter_admitted_in_equality():
    out = admit(_mk("equality_matching", {"slot": 2, "counter_in_kind": 2}))
    assert out["admitted"] is True


# ---- AC4: directionality (gift-shaped content admits in the market room) -----
def test_ac4_gift_shaped_in_market_admits():
    out = admit(_mk("market_price", {"gift_note": "free with purchase",
                                     "description": "no charge sample"}))
    assert out["admitted"] is True


# ---- AC5: anti-surveillance shape (all rooms) -------------------------------
def test_ac5a_no_forbidden_keys_in_verdict():
    for ix in (_mk("communal_gift", {"offer": "x"}),
               _mk("market_price", {"amount_cents": 100})):
        out = admit(ix)
        keys = {str(k).lower() for k in scan_keys(out)}
        assert keys.isdisjoint(FORBIDDEN)


def test_ac5a_verdict_echoes_no_payload():
    out = admit(_mk("communal_gift", {"secret_offer_detail": "sensitive"}))
    assert "secret_offer_detail" not in json.dumps(out)


@pytest.mark.parametrize("mode", ["communal_gift", "equality_matching", "market_price"])
@pytest.mark.parametrize("payload", [
    {"reputation": 0.9},
    {"seller": {"trust_score": 88}},                  # nested, market room included
    {"note": "ok", "user_rank": 3},
])
def test_ac5b_surveillance_refused_in_every_room(mode, payload):
    with pytest.raises(MembraneBreachError):
        admit(_mk(mode, payload))


def test_ac5b_surveillance_in_envelope_refused():
    ix = _mk("market_price", {"item": "x"}, blacklist=["t9"])
    with pytest.raises(MembraneBreachError):
        admit(ix)


# ---- AC6: no stored refusal / whitelist-not-blacklist -----------------------
def test_ac6_only_admitted_true_is_returned():
    out = admit(_mk("communal_gift", {"offer": "x"}))
    assert out["admitted"] is True
    # a breach is an exception, never a returned admitted:false verdict
    with pytest.raises(MembraneBreachError):
        admit(_mk("communal_gift", {"price": 1}))


# ---- AC7: determinism -------------------------------------------------------
@pytest.mark.parametrize("ix", [
    _mk("communal_gift", {"offer": "help"}),
    _mk("market_price", {"amount_cents": 500, "item": "bread"}),
])
def test_ac7_determinism(ix):
    a = admit(copy.deepcopy(ix))
    b = admit(copy.deepcopy(ix))
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# ---- AC8: envelope validation -----------------------------------------------
@pytest.mark.parametrize("mutate", [
    lambda i: i.update(mode="gift"),          # not one of the 3 literals
    lambda i: i.update(mode="market"),
    lambda i: i.update(interaction_id=""),
    lambda i: i.update(cell_id=""),
    lambda i: i.update(participants="t1"),    # str not list
    lambda i: i.update(participants=["", "t2"]),
    lambda i: i.update(payload=[]),           # list not dict
    lambda i: i.update(expires_at=""),        # present but empty
])
def test_ac8_envelope_validation(mutate):
    ix = _mk("communal_gift", {"offer": "x"})
    mutate(ix)
    with pytest.raises(MembraneBreachError):
        admit(ix)


# ---- AC-X: consistency with Capa 4 (binary campaign == equality interaction) -
def test_acx_capa4_binary_bonus_shape_refused():
    # a Capa-4 binary campaign carrying a sponsor bonus is an equality interaction
    # with a market instrument -> refused here, matching Capa-4 AC6's own refusal.
    with pytest.raises(MembraneBreachError):
        admit(_mk("equality_matching", {"threshold": 3, "sponsor_bonus_cents": 500}))


def test_acx_capa4_priced_binary_shape_refused():
    with pytest.raises(MembraneBreachError):
        admit(_mk("equality_matching", {"threshold": 3, "pledge_amount_cents": 500}))
