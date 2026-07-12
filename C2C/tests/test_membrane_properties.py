"""Property-based tests for the Capa-1 partition firewall (P1-P4).

hypothesis-driven: no market key ever survives admission into a non-market room;
no surveillance key ever survives into any room or into a verdict.
"""
import importlib.util
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

_MOD = Path(__file__).resolve().parent.parent / "src" / "partition" / "membrane.py"
_spec = importlib.util.spec_from_file_location("membrane", _MOD)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)
admit = mod.admit
MembraneBreachError = mod.MembraneBreachError

FORBIDDEN = ("score", "rating", "reputation", "rank", "blacklist", "ban",
             "penalty", "global_id", "dni")
MARKET = ("price", "cost", "fee", "_cents", "currency", "valuation", "denominat")
LEDGER = ("debt", "owed", "balance", "credit", "reciprocity", "iou", "favor_balance")
_ALL_BAD = FORBIDDEN + MARKET + LEDGER

# keys guaranteed to contain no forbidden/market/ledger substring
_clean_keys = st.sampled_from(["offer", "need", "note", "help", "care", "item",
                               "slot", "turn", "topic", "when", "where", "kind_of"])
_clean_scalars = st.one_of(st.integers(), st.booleans())


def _clean_payload():
    return st.dictionaries(_clean_keys, _clean_scalars, max_size=5)


def _nest(inner_key, inner_val, depth):
    node = {inner_key: inner_val}
    for i in range(depth):
        node = {f"wrap{i}": node}
    return node


def _scan_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _scan_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _scan_keys(v)


def _mk(mode, payload, **kw):
    ix = {"mode": mode, "cell_id": "c1", "interaction_id": "ix1",
          "participants": ["t1"], "payload": payload}
    ix.update(kw)
    return ix


# P1: clean payloads admit in every room
@settings(max_examples=100)
@given(mode=st.sampled_from(["communal_gift", "equality_matching", "market_price"]),
       payload=_clean_payload())
def test_p1_clean_payload_admits(mode, payload):
    assert admit(_mk(mode, payload))["admitted"] is True


# P2: a market key at any depth always refuses in the two non-market rooms
@settings(max_examples=100)
@given(mode=st.sampled_from(["communal_gift", "equality_matching"]),
       market_key=st.sampled_from(["price", "cost", "fee", "unit_cents", "currency"]),
       depth=st.integers(min_value=0, max_value=4))
def test_p2_market_key_always_refused(mode, market_key, depth):
    try:
        admit(_mk(mode, _nest(market_key, 1, depth)))
        assert False, "market key survived into a non-market room"
    except MembraneBreachError:
        pass


# P3: a forbidden (surveillance) key at any depth refuses in ALL rooms
@settings(max_examples=100)
@given(mode=st.sampled_from(["communal_gift", "equality_matching", "market_price"]),
       bad=st.sampled_from(FORBIDDEN),
       depth=st.integers(min_value=0, max_value=4))
def test_p3_surveillance_key_always_refused(mode, bad, depth):
    try:
        admit(_mk(mode, _nest(bad, 1, depth)))
        assert False, "surveillance key survived"
    except MembraneBreachError:
        pass


# P4: every admitted verdict is free of forbidden keys
@settings(max_examples=100)
@given(mode=st.sampled_from(["communal_gift", "equality_matching", "market_price"]),
       payload=_clean_payload())
def test_p4_verdict_has_no_forbidden_keys(mode, payload):
    out = admit(_mk(mode, payload))
    keys = {str(k).lower() for k in _scan_keys(out)}
    assert all(not any(t in k for t in _ALL_BAD) for k in keys)
