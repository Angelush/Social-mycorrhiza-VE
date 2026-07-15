"""Acceptance tests for the mutual-credit ledger (AC-L1..L9, spec-ledger.md)."""

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

_BASE = Path(__file__).resolve().parent.parent
def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, _BASE / rel)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m

led = _load("mutual_credit_ledger_t", "src/ledger/mutual_credit_ledger.py")
sol = _load("clearing_solver_lt", "src/clearing/clearing_solver.py")

# moneda: USD es la unidad de cuenta del sistema (D1). Las células USD NO llevan
# expira_en_dias — declararlo sería una célula confundida sobre qué es.
PARAMS = {"neg_line_bp": 100, "pos_line_bp": 1000, "velocity_window_s": 86400,
          "velocity_max_cents": 5_000_000, "moneda": "USD", "paused": False}

def fresh_cell(ts=1000):
    """cell1 with members A,B,C,D (turnover 100_000_000 -> lines -1_000_000/+10_000_000); returns (state, events)."""
    state, ev = led.create_cell("cell1", dict(PARAMS), "ana", ts)
    events = [ev]
    for mid in "ABCD":
        state, ev = led.add_member(state, {"id": mid, "turnover_cents": 100_000_000}, "ana", ts)
        events.append(ev)
    return state, events

def flow_a():
    """Flow A of tests-ledger.md up to and including apply_clearing; returns (state, events, proposal)."""
    state, events = fresh_cell()
    for oid, d, c, amt, ts in [("o1","A","B",10000,1010), ("o2","B","C",6000,1020),
                               ("o3","C","A",4000,1030), ("o4","D","A",2500,1040)]:
        state, ev = led.record_obligation(state, {"id": oid, "debtor": d, "creditor": c, "amount_cents": amt}, ts)
        events.append(ev)
    proposal = sol.clear(led.to_clearing_input(state))
    state, ev = led.apply_clearing(state, proposal, "ana", 1050)
    events.append(ev)
    return state, events, proposal

def assert_rejects(state, fn, *args, **kw):
    """fn must raise ValueError and leave state canonically unchanged."""
    before = led.canonical(state)
    with pytest.raises(ValueError):
        fn(state, *args, **kw)
    assert led.canonical(state) == before

class TestFlowA:
    def test_defaults_and_clearing(self):
        state, events, proposal = flow_a()
        stmt_a = led.member_statement(state, "A")
        assert stmt_a["credit_min_cents"] == -1_000_000
        assert stmt_a["credit_max_cents"] == 10_000_000

    def test_obligations_after_apply(self):
        state, _, proposal = flow_a()
        obs = state["obligations"]
        assert len(obs) == 3
        assert obs["o1"]["amount_cents"] == 6000
        assert obs["o2"]["amount_cents"] == 2000
        assert obs["o4"]["amount_cents"] == 2500
        assert "o3" not in obs

    def test_all_balances_zero(self):
        state, _, _ = flow_a()
        for mid in "ABCD":
            stmt = led.member_statement(state, mid)
            assert stmt["balance_cents"] == 0

    def test_applied_hash_registered(self):
        _, events, _ = flow_a()
        apply_ev = events[-1]
        assert "hash" in apply_ev
        assert apply_ev["hash"] != ""

    def test_net_open_positions_identical(self):
        _, events_pre, _ = flow_a()
        state_before = led.replay(events_pre[:-1])
        state_after = led.replay(events_pre)
        for mid in "ABCD":
            def net_open(s):
                owed_by = sum(o["amount_cents"] for o in s["obligations"].values() if o["debtor"] == mid)
                owed_to = sum(o["amount_cents"] for o in s["obligations"].values() if o["creditor"] == mid)
                return owed_to - owed_by
            assert net_open(state_before) == net_open(state_after)

    def test_reduction_pct(self):
        _, _, proposal = flow_a()
        assert proposal["metrics"]["reduction_pct"] == pytest.approx(53.333333)

    def test_settle_o1_2500(self):
        state, _, _ = flow_a()
        state, _ = led.settle_obligation(state, "o1", 2500, 1060)
        stmt_a = led.member_statement(state, "A")
        stmt_b = led.member_statement(state, "B")
        assert stmt_a["balance_cents"] == -2500
        assert stmt_b["balance_cents"] == 2500
        assert state["obligations"]["o1"]["amount_cents"] == 3500
        metrics = led.cell_metrics(state)
        assert metrics["sum_balances_cents"] == 0
        assert metrics["gross_open_cents"] == 8000
        assert metrics["cell_id"] == "cell1"
        assert metrics["members"] == 4
        assert metrics["open_obligations"] == 3
        assert metrics["paused"] is False
        assert metrics["seq"] == 11

class TestDeterminismReplay:
    def test_canonical_states_equal(self):
        state1, events1 = flow_a()[:2]
        state2, events2 = flow_a()[:2]
        assert led.canonical(state1) == led.canonical(state2)

    def test_event_streams_equal(self):
        _, events1 = flow_a()[:2]
        _, events2 = flow_a()[:2]
        assert events1 == events2

    def test_replay_equals_live(self):
        state, events = flow_a()[:2]
        replayed = led.replay(events)
        assert led.canonical(replayed) == led.canonical(state)

    def test_verify_chain_passes(self):
        _, events = flow_a()[:2]
        led.verify_chain(events)

    def test_corrupt_payload_amount(self):
        _, events = flow_a()[:2]
        corrupted = copy.deepcopy(events)
        corrupted[5]["payload"]["obligation"]["amount_cents"] += 1
        with pytest.raises(ValueError):
            led.replay(corrupted)

    def test_corrupt_hash(self):
        _, events = flow_a()[:2]
        corrupted = copy.deepcopy(events)
        corrupted[2]["hash"] = "flipped"
        with pytest.raises(ValueError):
            led.verify_chain(corrupted)

class TestGates:
    def test_create_cell_bad_ratified_by(self):
        with pytest.raises(ValueError):
            led.create_cell("cell2", dict(PARAMS), "", 1000)
        with pytest.raises(ValueError):
            led.create_cell("cell2", dict(PARAMS), 123, 1000)

    def test_add_member_bad_ratified_by(self):
        state, _ = fresh_cell()
        assert_rejects(state, led.add_member, {"id": "E", "turnover_cents": 100_000_000}, "", 1010)
        assert_rejects(state, led.add_member, {"id": "E", "turnover_cents": 100_000_000}, 123, 1010)

    def test_update_member_bad_ratified_by(self):
        state, _ = fresh_cell()
        assert_rejects(state, led.update_member, "A", {"credit_min_cents": -500}, "", 1010)
        assert_rejects(state, led.update_member, "A", {"credit_min_cents": -500}, 123, 1010)

    def test_apply_clearing_bad_ratified_by(self):
        state, _ = fresh_cell()
        assert_rejects(state, led.apply_clearing, {"settlements": []}, "", 1010)
        assert_rejects(state, led.apply_clearing, {"settlements": []}, 123, 1010)

    def test_pause_resume_bad_ratified_by(self):
        state, _ = fresh_cell()
        assert_rejects(state, led.pause_cell, "", 1010)
        assert_rejects(state, led.pause_cell, 123, 1010)
        assert_rejects(state, led.resume_cell, "", 1010)
        assert_rejects(state, led.resume_cell, 123, 1010)

class TestRejections:
    def test_unknown_debtor(self):
        state, _ = fresh_cell()
        assert_rejects(state, led.record_obligation, {"id": "ox", "debtor": "X", "creditor": "A", "amount_cents": 100}, 1010)

    def test_self_loop(self):
        state, _ = fresh_cell()
        assert_rejects(state, led.record_obligation, {"id": "ox", "debtor": "A", "creditor": "A", "amount_cents": 100}, 1010)

    def test_duplicate_obligation_id(self):
        state, _ = fresh_cell()
        state, _ = led.record_obligation(state, {"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 100}, 1010)
        assert_rejects(state, led.record_obligation, {"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 100}, 1010)

    def test_id_reuse_after_full_settlement(self):
        state, _ = fresh_cell()
        state, _ = led.record_obligation(state, {"id": "x", "debtor": "A", "creditor": "B", "amount_cents": 100}, 1010)
        state, _ = led.settle_obligation(state, "x", 100, 1020)
        assert_rejects(state, led.record_obligation, {"id": "x", "debtor": "A", "creditor": "B", "amount_cents": 100}, 1030)

    @pytest.mark.parametrize("amount", [True, 1.5, 0, -5])
    def test_invalid_amount(self, amount):
        state, _ = fresh_cell()
        assert_rejects(state, led.record_obligation, {"id": "oa", "debtor": "A", "creditor": "B", "amount_cents": amount}, 1010)

    def test_member_id_duplicate(self):
        state, _ = fresh_cell()
        assert_rejects(state, led.add_member, {"id": "A", "turnover_cents": 100_000_000}, "ana", 1010)

    def test_turnover_bool(self):
        state, _ = fresh_cell()
        assert_rejects(state, led.add_member, {"id": "E", "turnover_cents": True}, "ana", 1010)

    def test_credit_min_positive(self):
        state, _ = fresh_cell()
        assert_rejects(state, led.add_member, {"id": "E", "turnover_cents": 100_000_000, "credit_min_cents": 5}, "ana", 1010)

    def test_credit_max_negative(self):
        state, _ = fresh_cell()
        assert_rejects(state, led.add_member, {"id": "E", "turnover_cents": 100_000_000, "credit_max_cents": -5}, "ana", 1010)

    def test_velocity_window_zero(self):
        with pytest.raises(ValueError):
            led.create_cell("bad", {"neg_line_bp": 100, "pos_line_bp": 1000, "velocity_window_s": 0, "velocity_max_cents": 5_000_000, "paused": False}, "ana", 1000)

    def test_ts_regression(self):
        state, _ = fresh_cell(1000)
        for oid, d, c, amt, ts in [("o1","A","B",10000,1010), ("o2","B","C",6000,1020), ("o3","C","A",4000,1030), ("o4","D","A",2500,1040)]:
            state, _ = led.record_obligation(state, {"id": oid, "debtor": d, "creditor": c, "amount_cents": amt}, ts)
        assert_rejects(state, led.record_obligation, {"id": "o5", "debtor": "A", "creditor": "B", "amount_cents": 100}, 900)

    def test_paused_blocks_record(self):
        state, _ = fresh_cell()
        state, _ = led.pause_cell(state, "ana", 1010)
        assert_rejects(state, led.record_obligation, {"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 100}, 1020)

    def test_paused_blocks_settle(self):
        state, _ = fresh_cell()
        state, _ = led.record_obligation(state, {"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 100}, 1010)
        state, _ = led.pause_cell(state, "ana", 1020)
        assert_rejects(state, led.settle_obligation, "o1", 50, 1030)

    def test_paused_blocks_apply(self):
        state, _ = fresh_cell()
        state, _ = led.record_obligation(state, {"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 100}, 1010)
        state, _ = led.pause_cell(state, "ana", 1020)
        assert_rejects(state, led.apply_clearing, {"settlements": []}, "ana", 1030)

    def test_paused_blocks_add(self):
        state, _ = fresh_cell()
        state, _ = led.pause_cell(state, "ana", 1010)
        assert_rejects(state, led.add_member, {"id": "E", "turnover_cents": 100_000_000}, "ana", 1020)

    def test_paused_blocks_update(self):
        state, _ = fresh_cell()
        state, _ = led.pause_cell(state, "ana", 1010)
        assert_rejects(state, led.update_member, "A", {"credit_min_cents": -500}, "ana", 1020)

    def test_paused_blocks_double_pause(self):
        state, _ = fresh_cell()
        state, _ = led.pause_cell(state, "ana", 1010)
        assert_rejects(state, led.pause_cell, "ana", 1020)

    def test_resume_works_second_rejects(self):
        state, _ = fresh_cell()
        state, _ = led.pause_cell(state, "ana", 1010)
        state, _ = led.resume_cell(state, "ana", 1020)
        assert_rejects(state, led.resume_cell, "ana", 1030)

    def test_velocity_window(self):
        params = dict(PARAMS)
        params["velocity_max_cents"] = 5_000_000
        state, _ = led.create_cell("cell_v", params, "ana", 1000)
        for mid in "ABCD":
            state, _ = led.add_member(state, {"id": mid, "turnover_cents": 1_000_000_000, "credit_min_cents": -10_000_000, "credit_max_cents": 10_000_000}, "ana", 1000)
        state, _ = led.record_obligation(state, {"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 3_000_000}, 2000)
        assert_rejects(state, led.record_obligation, {"id": "o2", "debtor": "A", "creditor": "B", "amount_cents": 2_500_000}, 3000)
        state, _ = led.record_obligation(state, {"id": "o2", "debtor": "A", "creditor": "B", "amount_cents": 2_500_000}, 2000 + 86401)

    def test_projection_creditor_max(self):
        state, _ = fresh_cell()
        state, _ = led.add_member(state, {"id": "E", "turnover_cents": 100_000_000, "credit_max_cents": 1000}, "ana", 1000)
        assert_rejects(state, led.record_obligation, {"id": "o1", "debtor": "A", "creditor": "E", "amount_cents": 2000}, 1010)

    def test_projection_debtor_min(self):
        state, _ = fresh_cell()
        state, _ = led.add_member(state, {"id": "F", "turnover_cents": 100_000_000, "credit_min_cents": -1000}, "ana", 1000)
        assert_rejects(state, led.record_obligation, {"id": "o1", "debtor": "F", "creditor": "A", "amount_cents": 2000}, 1010)

class TestSettleBounds:
    def test_settle_within_new_line(self):
        state, _ = fresh_cell()
        state, _ = led.record_obligation(state, {"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 800}, 1010)
        state, _ = led.settle_obligation(state, "o1", 100, 1020)
        state, _ = led.update_member(state, "A", {"credit_min_cents": -500}, "ana", 1030)
        assert_rejects(state, led.settle_obligation, "o1", 500, 1040)
        state, _ = led.settle_obligation(state, "o1", 400, 1040)
        stmt = led.member_statement(state, "A")
        assert stmt["balance_cents"] == -500

    def test_update_below_current_balance(self):
        state, _ = fresh_cell()
        state, _ = led.record_obligation(state, {"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 100}, 1010)
        state, _ = led.settle_obligation(state, "o1", 100, 1020)
        assert_rejects(state, led.update_member, "A", {"credit_min_cents": -50}, "ana", 1030)

class TestSanctionsLadder:
    def test_active_to_line_reduced_jump_rejects(self):
        state, _ = fresh_cell()
        assert_rejects(state, led.update_member, "A", {"status": "line_reduced"}, "ana", 1010)

    def test_active_to_warned_to_line_reduced_accepts(self):
        state, _ = fresh_cell()
        state, _ = led.update_member(state, "A", {"status": "warned"}, "ana", 1010)
        state, _ = led.update_member(state, "A", {"status": "line_reduced"}, "ana", 1020)

    def test_suspended_cannot_record_as_debtor(self):
        state, _ = fresh_cell()
        state, _ = led.update_member(state, "B", {"status": "warned"}, "ana", 1010)
        state, _ = led.update_member(state, "B", {"status": "line_reduced"}, "ana", 1020)
        state, _ = led.update_member(state, "B", {"status": "suspended"}, "ana", 1030)
        assert_rejects(state, led.record_obligation, {"id": "o1", "debtor": "B", "creditor": "A", "amount_cents": 100}, 1040)

    def test_suspended_cannot_record_as_creditor(self):
        state, _ = fresh_cell()
        state, _ = led.update_member(state, "B", {"status": "warned"}, "ana", 1021)
        state, _ = led.update_member(state, "B", {"status": "line_reduced"}, "ana", 1022)
        state, _ = led.update_member(state, "B", {"status": "suspended"}, "ana", 1030)
        assert_rejects(state, led.record_obligation, {"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 100}, 1040)

    def test_suspended_open_obligation_still_settles(self):
        state, _ = fresh_cell()
        state, _ = led.record_obligation(state, {"id": "o1", "debtor": "B", "creditor": "A", "amount_cents": 100}, 1010)
        state, _ = led.update_member(state, "B", {"status": "warned"}, "ana", 1021)
        state, _ = led.update_member(state, "B", {"status": "line_reduced"}, "ana", 1022)
        state, _ = led.update_member(state, "B", {"status": "suspended"}, "ana", 1023)
        state, _ = led.settle_obligation(state, "o1", 50, 1030)

    def test_suspended_to_active_accepted(self):
        state, _ = fresh_cell()
        state, _ = led.update_member(state, "B", {"status": "warned"}, "ana", 1021)
        state, _ = led.update_member(state, "B", {"status": "line_reduced"}, "ana", 1022)
        state, _ = led.update_member(state, "B", {"status": "suspended"}, "ana", 1023)
        state, _ = led.update_member(state, "B", {"status": "active"}, "ana", 1030)

class TestProposalForgery:
    def test_tampered_reduce_by_cents(self):
        state, events = fresh_cell()
        for oid, d, c, amt, ts in [("o1","A","B",10000,1010), ("o2","B","C",6000,1020),
                                       ("o3","C","A",4000,1030), ("o4","D","A",2500,1040)]:
            state, ev = led.record_obligation(state, {"id": oid, "debtor": d, "creditor": c, "amount_cents": amt}, ts)
            events.append(ev)
        proposal = sol.clear(led.to_clearing_input(state))
        tampered = copy.deepcopy(proposal)
        tampered["settlements"][0]["reduce_by_cents"] += 1
        assert_rejects(state, led.apply_clearing, tampered, "ana", 1050)

    def test_reapply_identical_proposal(self):
        state, events = fresh_cell()
        for oid, d, c, amt, ts in [("o1","A","B",10000,1010), ("o2","B","C",6000,1020),
                                       ("o3","C","A",4000,1030), ("o4","D","A",2500,1040)]:
            state, ev = led.record_obligation(state, {"id": oid, "debtor": d, "creditor": c, "amount_cents": amt}, ts)
            events.append(ev)
        proposal = sol.clear(led.to_clearing_input(state))
        state, _ = led.apply_clearing(state, proposal, "ana", 1050)
        assert_rejects(state, led.apply_clearing, proposal, "ana", 1051)

    def test_forged_globally_balanced_per_member_unbalanced(self):
        state, events = fresh_cell()
        for oid, d, c, amt, ts in [("o1","A","B",10000,1010), ("o2","B","C",6000,1020),
                                       ("o3","C","A",4000,1030), ("o4","D","A",2500,1040)]:
            state, ev = led.record_obligation(state, {"id": oid, "debtor": d, "creditor": c, "amount_cents": amt}, ts)
            events.append(ev)
        forged = {"cell_id": "cell1", "settlements": [
            {"obligation_id": "o1", "reduce_by_cents": 1000},
            {"obligation_id": "o4", "reduce_by_cents": 1000}
        ]}
        assert_rejects(state, led.apply_clearing, forged, "ana", 1050)

    def test_split_entries_same_obligation(self):
        state, events = fresh_cell()
        for oid, d, c, amt, ts in [("o1","A","B",10000,1010), ("o2","B","C",6000,1020),
                                       ("o3","C","A",4000,1030), ("o4","D","A",2500,1040)]:
            state, ev = led.record_obligation(state, {"id": oid, "debtor": d, "creditor": c, "amount_cents": amt}, ts)
            events.append(ev)
        split_forged = {"cell_id": "cell1", "settlements": [
            {"obligation_id": "o1", "reduce_by_cents": 5000},
            {"obligation_id": "o1", "reduce_by_cents": 5000}
        ]}
        assert_rejects(state, led.apply_clearing, split_forged, "ana", 1050)

    def test_unknown_obligation_id(self):
        state, events = fresh_cell()
        for oid, d, c, amt, ts in [("o1","A","B",10000,1010)]:
            state, ev = led.record_obligation(state, {"id": oid, "debtor": d, "creditor": c, "amount_cents": amt}, ts)
            events.append(ev)
        forged = {"cell_id": "cell1", "settlements": [
            {"obligation_id": "o99", "reduce_by_cents": 1000}
        ]}
        assert_rejects(state, led.apply_clearing, forged, "ana", 1050)

    def test_wrong_cell_id(self):
        state, events = fresh_cell()
        for oid, d, c, amt, ts in [("o1","A","B",10000,1010)]:
            state, ev = led.record_obligation(state, {"id": oid, "debtor": d, "creditor": c, "amount_cents": amt}, ts)
            events.append(ev)
        forged = {"cell_id": "cell2", "settlements": [
            {"obligation_id": "o1", "reduce_by_cents": 4000}
        ]}
        assert_rejects(state, led.apply_clearing, forged, "ana", 1050)

class TestViews:
    def test_to_clearing_input_schema(self):
        state, _, _ = flow_a()
        data = led.to_clearing_input(state)
        sol.clear(data)

    def test_member_statement_consistency(self):
        state, _, _ = flow_a()
        for mid in "ABCD":
            stmt = led.member_statement(state, mid)
            assert stmt["member_id"] == mid
            assert stmt["status"] == "active"
            assert stmt["balance_cents"] == 0
            assert "owed_by_cents" in stmt
            assert "owed_to_cents" in stmt
            assert "projected_cents" in stmt

    def test_render_statement_format(self):
        # D1/C-d1.6: el simbolo se deriva de params["moneda"]. cell1 es USD -> "$".
        # El "€" hardcodeado de upstream era una mentira en cuanto la unidad de cuenta dejo
        # de ser el euro, y el extracto lo lee el humano que decide.
        state, _, _ = flow_a()
        rendered = led.render_statement(state, "A")
        assert rendered.startswith("# Statement — A @ cell1")
        assert "$" in rendered
        assert "€" not in rendered
        assert rendered.endswith("\n")
        rendered2 = led.render_statement(state, "A")
        assert rendered == rendered2

class TestIndependentOracle:
    def test_oracle_balances_and_open_obligations(self):
        state, events, _ = flow_a()
        balances = {"A": 0, "B": 0, "C": 0, "D": 0}
        open_obs = {}
        for ev in events:
            kind = ev["kind"]
            payload = ev["payload"]
            if kind == "obligation_recorded":
                ob = payload["obligation"]
                oid = ob["id"]
                open_obs[oid] = {"debtor": ob["debtor"], "creditor": ob["creditor"], "amount_cents": ob["amount_cents"]}
            elif kind == "clearing_applied":
                for s in payload["proposal"]["settlements"]:
                    oid = s["obligation_id"]
                    reduce_by = s["reduce_by_cents"]
                    if oid in open_obs:
                        open_obs[oid]["amount_cents"] -= reduce_by
                        if open_obs[oid]["amount_cents"] <= 0:
                            del open_obs[oid]
            elif kind == "obligation_settled":
                oid = payload["obligation_id"]
                amount = payload["amount_cents"]
                if oid in open_obs:
                    debtor = open_obs[oid]["debtor"]
                    creditor = open_obs[oid]["creditor"]
                    balances[debtor] -= amount
                    balances[creditor] += amount
                    open_obs[oid]["amount_cents"] -= amount
                    if open_obs[oid]["amount_cents"] <= 0:
                        del open_obs[oid]
        for mid in "ABCD":
            stmt = led.member_statement(state, mid)
            assert stmt["balance_cents"] == balances[mid]
        for oid, obs in state["obligations"].items():
            assert oid in open_obs
            assert obs["amount_cents"] == open_obs[oid]["amount_cents"]
        assert sum(balances.values()) == 0

class TestGoldenFlow:
    def test_golden_flow_pin(self):
        """Byte-exact regression pin of Flow A (evals/golden-set/ledger_flow.json)."""
        import hashlib
        golden = json.loads((_BASE / "workflows" / "micorriza" / "evals" / "golden-set" / "ledger_flow.json").read_text())
        state, _, _ = flow_a()
        state, _ = led.settle_obligation(state, "o1", 2500, 1060)
        assert hashlib.sha256(led.canonical(state)).hexdigest() == golden["final_state_sha256"]
        assert state["head_hash"] == golden["head_hash"]
        assert state["seq"] == golden["seq"]
        assert led.cell_metrics(state)["gross_open_cents"] == golden["gross_open_cents"]
