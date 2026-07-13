"""Acceptance tests for the Layer-1 clearing solver.

Maps directly to workflows/micorriza/evals/acceptance.md (AC1-AC6) and
evals/tests.md (Tests A/B/C). The solver is a deterministic, value-moving
proposal generator: these tests are the quality moat (Axiom 7).

Run: pytest -q tests/test_clearing_solver.py
Optional property tests require `hypothesis`; optional oracle requires `networkx`.
"""
import copy
import importlib.util
import sys
from pathlib import Path

import pytest

# Load src/clearing/clearing_solver.py without needing a package install.
_SOLVER = Path(__file__).resolve().parent.parent / "src" / "clearing" / "clearing_solver.py"
_spec = importlib.util.spec_from_file_location("clearing_solver", _SOLVER)
clearing_solver = importlib.util.module_from_spec(_spec)
sys.modules["clearing_solver"] = clearing_solver
_spec.loader.exec_module(clearing_solver)
clear = clearing_solver.clear


# --------------------------------------------------------------------------
# Helpers — independent oracle (never reuse the solver's own math: AGD-045)
# --------------------------------------------------------------------------
def raw_net_positions(data):
    """net = sum(incoming) - sum(outgoing), recomputed from raw obligations."""
    net = {m["id"]: 0 for m in data["members"]}
    for o in data["obligations"]:
        net[o["creditor"]] += o["amount_cents"]
        net[o["debtor"]] -= o["amount_cents"]
    return net


def residual_net_positions(members, residual):
    net = {mid: 0 for mid in members}
    for o in residual:
        net[o["creditor"]] += o["amount_cents"]
        net[o["debtor"]] -= o["amount_cents"]
    return net


def gross(obligations):
    return sum(o["amount_cents"] for o in obligations)


def has_cycle(residual):
    """Kahn's algorithm: a DAG fully reduces; leftover nodes => a cycle exists."""
    indeg, adj, nodes = {}, {}, set()
    for o in residual:
        d, c = o["debtor"], o["creditor"]
        nodes.add(d); nodes.add(c)
        adj.setdefault(d, []).append(c)
        indeg[c] = indeg.get(c, 0) + 1
        indeg.setdefault(d, indeg.get(d, 0))
    queue = [n for n in nodes if indeg.get(n, 0) == 0]
    seen = 0
    while queue:
        n = queue.pop()
        seen += 1
        for m in adj.get(n, []):
            indeg[m] -= 1
            if indeg[m] == 0:
                queue.append(m)
    return seen != len(nodes)


def member(id_, cmin=-10**12, cmax=10**12, turnover=10**12):
    return {"id": id_, "turnover_eur_cents": turnover,
            "credit_min_cents": cmin, "credit_max_cents": cmax}


# --------------------------------------------------------------------------
# Fixtures — Tests A / B / C from evals/tests.md
# --------------------------------------------------------------------------
TEST_A = {
    "cell_id": "cellA",
    "members": [member("A"), member("B"), member("C")],
    "obligations": [
        {"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 10000},
        {"id": "o2", "debtor": "B", "creditor": "C", "amount_cents": 10000},
        {"id": "o3", "debtor": "C", "creditor": "A", "amount_cents": 10000},
    ],
}

TEST_B = {
    "cell_id": "cellB",
    "members": [member("A"), member("B"), member("C"), member("D")],
    "obligations": [
        {"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 10000},
        {"id": "o2", "debtor": "B", "creditor": "C", "amount_cents": 6000},
        {"id": "o3", "debtor": "C", "creditor": "A", "amount_cents": 4000},
        {"id": "o4", "debtor": "D", "creditor": "A", "amount_cents": 2500},
    ],
}

# Test C: overlapping cycles + parallel edges + a credit-bound breach.
# E receives 5000 net (creditor of D->E) and never pays out, so its net = +5000,
# above credit_max 1000 -> must be flagged, never clamped.
TEST_C = {
    "cell_id": "cellC",
    "members": [member("A"), member("B"), member("C"),
                member("D"), member("E", cmax=1000)],
    "obligations": [
        {"id": "p1", "debtor": "A", "creditor": "B", "amount_cents": 3000},
        {"id": "p2", "debtor": "A", "creditor": "B", "amount_cents": 7000},  # parallel
        {"id": "o3", "debtor": "B", "creditor": "C", "amount_cents": 8000},
        {"id": "o4", "debtor": "C", "creditor": "A", "amount_cents": 5000},
        {"id": "o5", "debtor": "C", "creditor": "D", "amount_cents": 4000},
        {"id": "o6", "debtor": "D", "creditor": "A", "amount_cents": 6000},
        {"id": "o7", "debtor": "D", "creditor": "E", "amount_cents": 5000},
    ],
}

ALL = {"A": TEST_A, "B": TEST_B, "C": TEST_C}


# --------------------------------------------------------------------------
# AC1 — Conservation (independent recompute) — the highest-risk criterion
# --------------------------------------------------------------------------
@pytest.mark.parametrize("name", ["A", "B", "C"])
def test_ac1_conservation(name):
    data = copy.deepcopy(ALL[name])
    out = clear(data)
    pre = raw_net_positions(data)
    post = residual_net_positions([m["id"] for m in data["members"]],
                                  out["residual_obligations"])
    assert pre == post, f"net position changed: pre={pre} post={post}"
    # solver's own reported net_positions must also match the oracle
    assert {k: int(v) for k, v in out["net_positions"].items()} == pre


# --------------------------------------------------------------------------
# AC2 — debt strictly reduced when a cycle exists; unchanged when acyclic
# --------------------------------------------------------------------------
@pytest.mark.parametrize("name", ["A", "B", "C"])
def test_ac2_debt_reduced_when_cycle(name):
    data = copy.deepcopy(ALL[name])
    out = clear(data)
    before = gross(data["obligations"])
    after = gross(out["residual_obligations"])
    assert out["metrics"]["gross_debt_before_cents"] == before
    assert out["metrics"]["gross_debt_after_cents"] == after
    assert after < before  # all three fixtures contain at least one cycle


def test_ac2_acyclic_unchanged():
    data = {
        "cell_id": "chain",
        "members": [member("A"), member("B"), member("C")],
        "obligations": [
            {"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 500},
            {"id": "o2", "debtor": "B", "creditor": "C", "amount_cents": 300},
        ],
    }
    out = clear(data)
    assert gross(out["residual_obligations"]) == gross(data["obligations"])
    assert out["metrics"]["cycles_cancelled"] == 0


# --------------------------------------------------------------------------
# AC3 — residual graph is acyclic
# --------------------------------------------------------------------------
@pytest.mark.parametrize("name", ["A", "B", "C"])
def test_ac3_residual_acyclic(name):
    out = clear(copy.deepcopy(ALL[name]))
    assert not has_cycle(out["residual_obligations"])


# --------------------------------------------------------------------------
# AC4 — determinism: same input twice -> byte-identical output
# --------------------------------------------------------------------------
@pytest.mark.parametrize("name", ["A", "B", "C"])
def test_ac4_determinism(name):
    import json
    a = clear(copy.deepcopy(ALL[name]))
    b = clear(copy.deepcopy(ALL[name]))
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# --------------------------------------------------------------------------
# AC5 — exactness: integer cents only; per-obligation reduction bounded
# --------------------------------------------------------------------------
@pytest.mark.parametrize("name", ["A", "B", "C"])
def test_ac5_exact_cents(name):
    data = copy.deepcopy(ALL[name])
    out = clear(data)
    amounts = {o["id"]: o["amount_cents"] for o in data["obligations"]}
    reduced = {}
    for s in out["settlements"]:
        assert isinstance(s["reduce_by_cents"], int)
        assert not isinstance(s["reduce_by_cents"], bool)
        reduced[s["obligation_id"]] = reduced.get(s["obligation_id"], 0) + s["reduce_by_cents"]
    for oid, total in reduced.items():
        assert 0 <= total <= amounts[oid], f"{oid} over-reduced: {total}>{amounts[oid]}"
    for o in out["residual_obligations"]:
        assert isinstance(o["amount_cents"], int) and o["amount_cents"] > 0


# --------------------------------------------------------------------------
# AC6 — credit-bound breach flagged, not clamped (tail case)
# --------------------------------------------------------------------------
def test_ac6_credit_flag():
    out = clear(copy.deepcopy(TEST_C))
    assert "E" in out["credit_flags"], "member E over +cap must be flagged"
    # not clamped: E's true net position is preserved (== oracle)
    assert out["net_positions"]["E"] == raw_net_positions(TEST_C)["E"]


def test_ac6_no_false_flag():
    out = clear(copy.deepcopy(TEST_A))
    assert out["credit_flags"] == []


# --------------------------------------------------------------------------
# Input validation (E2): reject malformed input, no silent repair
# --------------------------------------------------------------------------
def test_reject_self_loop():
    data = {"cell_id": "x", "members": [member("A")],
            "obligations": [{"id": "o1", "debtor": "A", "creditor": "A", "amount_cents": 5}]}
    with pytest.raises(ValueError):
        clear(data)


def test_reject_unknown_member():
    data = {"cell_id": "x", "members": [member("A")],
            "obligations": [{"id": "o1", "debtor": "A", "creditor": "Z", "amount_cents": 5}]}
    with pytest.raises(ValueError):
        clear(data)


def test_reject_nonpositive_amount():
    data = {"cell_id": "x", "members": [member("A"), member("B")],
            "obligations": [{"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 0}]}
    with pytest.raises(ValueError):
        clear(data)


# --------------------------------------------------------------------------
# Cross-check — independent networkx oracle (tests.md §Cross-check, ST5/AGD-045)
# --------------------------------------------------------------------------
@pytest.mark.parametrize("name", ["A", "B", "C"])
def test_networkx_oracle_net_positions(name):
    nx = pytest.importorskip("networkx")
    data = copy.deepcopy(ALL[name])
    g = nx.MultiDiGraph()
    g.add_nodes_from(m["id"] for m in data["members"])
    for o in data["obligations"]:
        g.add_edge(o["debtor"], o["creditor"], weight=o["amount_cents"])
    oracle = {n: g.in_degree(n, weight="weight") - g.out_degree(n, weight="weight")
              for n in g.nodes}
    out = clear(data)
    assert out["net_positions"] == oracle
