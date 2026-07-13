"""Property-based tests for the clearing solver (AC1 conservation, AC2 no debt
creation, AC4 determinism) over randomly generated obligation graphs.

These target the tail-of-distribution (AGD-016): the rare graph shapes that a
handful of fixed fixtures never hit. Requires `hypothesis`.
"""
import copy
import importlib.util
import json
import sys
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

_SOLVER = Path(__file__).resolve().parent.parent / "src" / "clearing" / "clearing_solver.py"
_spec = importlib.util.spec_from_file_location("clearing_solver_p", _SOLVER)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)
clear = mod.clear

MEMBERS = ["A", "B", "C", "D", "E"]


def _member(mid):
    return {"id": mid, "turnover_eur_cents": 10**9,
            "credit_min_cents": -10**9, "credit_max_cents": 10**9}


@st.composite
def graphs(draw):
    n_obl = draw(st.integers(min_value=0, max_value=20))
    obligations = []
    for i in range(n_obl):
        d = draw(st.sampled_from(MEMBERS))
        c = draw(st.sampled_from([m for m in MEMBERS if m != d]))
        amt = draw(st.integers(min_value=1, max_value=100000))
        obligations.append({"id": f"o{i}", "debtor": d, "creditor": c,
                            "amount_cents": amt})
    return {"cell_id": "prop", "members": [_member(m) for m in MEMBERS],
            "obligations": obligations}


def _raw_net(data):
    net = {m["id"]: 0 for m in data["members"]}
    for o in data["obligations"]:
        net[o["creditor"]] += o["amount_cents"]
        net[o["debtor"]] -= o["amount_cents"]
    return net


@settings(max_examples=400)
@given(graphs())
def test_conservation(data):
    pre = _raw_net(data)
    out = clear(copy.deepcopy(data))
    assert out["net_positions"] == pre  # AC1


@settings(max_examples=400)
@given(graphs())
def test_no_debt_creation(data):
    out = clear(copy.deepcopy(data))
    assert out["metrics"]["gross_debt_after_cents"] <= out["metrics"]["gross_debt_before_cents"]  # AC2


@settings(max_examples=200)
@given(graphs())
def test_determinism(data):
    a = clear(copy.deepcopy(data))
    b = clear(copy.deepcopy(data))
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)  # AC4


@settings(max_examples=200)
@given(graphs())
def test_settlements_bounded(data):
    out = clear(copy.deepcopy(data))
    amounts = {o["id"]: o["amount_cents"] for o in data["obligations"]}
    tot = {}
    for s in out["settlements"]:
        tot[s["obligation_id"]] = tot.get(s["obligation_id"], 0) + s["reduce_by_cents"]
    for oid, t in tot.items():
        assert 0 <= t <= amounts[oid]  # AC5: never over-reduce an obligation
