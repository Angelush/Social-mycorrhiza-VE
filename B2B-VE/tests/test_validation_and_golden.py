"""Validation, golden-set regression, and report-renderer tests (E2, AC4, spec §1)."""

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

_SOLVER = Path(__file__).resolve().parent.parent / "src" / "clearing" / "clearing_solver.py"
_spec = importlib.util.spec_from_file_location("clearing_solver_v", _SOLVER)
mod = importlib.util.module_from_spec(_spec)
sys.modules["clearing_solver_v"] = mod
_spec.loader.exec_module(mod)
clear = mod.clear
render_report = mod.render_report

GOLDEN_DIR = Path(__file__).resolve().parent.parent / "workflows" / "micorriza" / "evals" / "golden-set"

def member(id_, cmin=-10**12, cmax=10**12, turnover=10**12):
    return {"id": id_, "turnover_cents": turnover,
            "credit_min_cents": cmin, "credit_max_cents": cmax}

def base():
    return {
        "cell_id": "v",
        "members": [member("A"), member("B")],
        "obligations": [
            {"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 100},
        ],
    }

# ---------- REJECTION TESTS ----------
def test_input_is_list_not_dict():
    with pytest.raises(ValueError):
        clear([])

def test_cell_id_key_missing():
    d = base()
    del d["cell_id"]
    with pytest.raises(ValueError):
        clear(d)

def test_cell_id_empty_string():
    d = base()
    d["cell_id"] = ""
    with pytest.raises(ValueError):
        clear(d)

def test_members_is_dict_not_list():
    d = base()
    d["members"] = {}
    with pytest.raises(ValueError):
        clear(d)

def test_member_entry_is_string():
    d = base()
    d["members"][0] = "A"
    with pytest.raises(ValueError):
        clear(d)

def test_member_missing_id():
    d = base()
    del d["members"][0]["id"]
    with pytest.raises(ValueError):
        clear(d)

def test_member_id_empty_string():
    d = base()
    d["members"][0]["id"] = ""
    with pytest.raises(ValueError):
        clear(d)

def test_member_id_is_int():
    d = base()
    d["members"][0]["id"] = 5
    with pytest.raises(ValueError):
        clear(d)

def test_duplicate_member_ids():
    d = base()
    d["members"].append(member("A"))
    with pytest.raises(ValueError):
        clear(d)

def test_member_missing_credit_min():
    d = base()
    del d["members"][0]["credit_min_cents"]
    with pytest.raises(ValueError):
        clear(d)

def test_member_missing_credit_max():
    d = base()
    del d["members"][0]["credit_max_cents"]
    with pytest.raises(ValueError):
        clear(d)

def test_member_missing_turnover():
    d = base()
    del d["members"][0]["turnover_cents"]
    with pytest.raises(ValueError):
        clear(d)

def test_credit_min_is_string():
    d = base()
    d["members"][0]["credit_min_cents"] = "0"
    with pytest.raises(ValueError):
        clear(d)

def test_credit_min_is_bool():
    d = base()
    d["members"][0]["credit_min_cents"] = False
    with pytest.raises(ValueError):
        clear(d)

def test_credit_min_positive():
    d = base()
    d["members"][0]["credit_min_cents"] = 5
    with pytest.raises(ValueError):
        clear(d)

def test_credit_max_negative():
    d = base()
    d["members"][0]["credit_max_cents"] = -5
    with pytest.raises(ValueError):
        clear(d)

def test_obligations_is_dict():
    d = base()
    d["obligations"] = {}
    with pytest.raises(ValueError):
        clear(d)

def test_obligation_entry_is_string():
    d = base()
    d["obligations"][0] = "o1"
    with pytest.raises(ValueError):
        clear(d)

def test_obligation_missing_creditor():
    d = base()
    del d["obligations"][0]["creditor"]
    with pytest.raises(ValueError):
        clear(d)

def test_duplicate_obligation_ids():
    d = base()
    d["obligations"].append({"id": "o1", "debtor": "B", "creditor": "A", "amount_cents": 50})
    with pytest.raises(ValueError):
        clear(d)

def test_obligation_id_is_int():
    d = base()
    d["obligations"][0]["id"] = 1
    with pytest.raises(ValueError):
        clear(d)

def test_obligation_id_empty_string():
    d = base()
    d["obligations"][0]["id"] = ""
    with pytest.raises(ValueError):
        clear(d)

def test_debtor_is_int():
    d = base()
    d["obligations"][0]["debtor"] = 5
    with pytest.raises(ValueError):
        clear(d)

def test_amount_cents_is_bool():
    d = base()
    d["obligations"][0]["amount_cents"] = True
    with pytest.raises(ValueError):
        clear(d)

def test_amount_cents_is_float():
    d = base()
    d["obligations"][0]["amount_cents"] = 1.5
    with pytest.raises(ValueError):
        clear(d)

def test_amount_cents_zero():
    d = base()
    d["obligations"][0]["amount_cents"] = 0
    with pytest.raises(ValueError):
        clear(d)

def test_amount_cents_negative():
    d = base()
    d["obligations"][0]["amount_cents"] = -100
    with pytest.raises(ValueError):
        clear(d)

def test_self_loop():
    d = base()
    d["obligations"][0]["debtor"] = "A"
    d["obligations"][0]["creditor"] = "A"
    with pytest.raises(ValueError):
        clear(d)

def test_debtor_unknown():
    d = base()
    d["obligations"][0]["debtor"] = "Z"
    with pytest.raises(ValueError):
        clear(d)

# ---------- EDGE CASE ----------
def test_zero_obligations_noop():
    out = clear({"cell_id": "empty", "members": [member("A"), member("B")], "obligations": []})
    assert out["settlements"] == []
    assert out["residual_obligations"] == []
    assert out["metrics"] == {"gross_debt_before_cents": 0, "gross_debt_after_cents": 0,
                              "reduction_pct": 0.0, "cycles_cancelled": 0}
    assert out["net_positions"] == {"A": 0, "B": 0}
    assert out["credit_flags"] == []
    assert out["audit_trace"] == []

# ---------- GOLDEN-SET REGRESSION ----------
@pytest.mark.parametrize("fname", ["test_A.json", "test_B.json", "test_C.json"])
def test_golden_regression(fname):
    case = json.loads((GOLDEN_DIR / fname).read_text())
    assert clear(copy.deepcopy(case["input"])) == case["expected_output"]

# ---------- RENDERER TESTS ----------
CYCLE3 = {
    "cell_id": "cellA",
    "members": [member("A"), member("B"), member("C")],
    "obligations": [
        {"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 10000},
        {"id": "o2", "debtor": "B", "creditor": "C", "amount_cents": 10000},
        {"id": "o3", "debtor": "C", "creditor": "A", "amount_cents": 10000},
    ],
}

def test_renderer_cycle3():
    out = clear(CYCLE3)
    rep = render_report(out)
    assert isinstance(rep, str)
    assert rep.endswith("\n")
    assert rep.startswith("# Settlement proposal — cellA")
    for h in ["## Metrics", "## Settlements", "## Residual obligations",
              "## Net positions", "## Credit flags", "## Audit trace"]:
        assert h in rep
    assert "100.00 €" in rep
    assert "- none" in rep

def test_renderer_deterministic():
    assert render_report(clear(CYCLE3)) == render_report(clear(CYCLE3))

SYNTH = {"cell_id": "x", "settlements": [],
         "residual_obligations": [{"debtor": "A", "creditor": "B", "amount_cents": 2550}],
         "metrics": {"gross_debt_before_cents": 2550, "gross_debt_after_cents": 2550,
                     "reduction_pct": 0.0, "cycles_cancelled": 0},
         "net_positions": {"A": -2550, "B": 2550}, "credit_flags": [], "audit_trace": []}

def test_renderer_synthetic_negative():
    rep = render_report(SYNTH)
    assert "-25.50 €" in rep
    assert "25.50 €" in rep
    assert "- A: -25.50 €" in rep
