"""Property-based tests for the mutual-credit ledger using hypothesis."""

import copy
import importlib.util
import sys
from pathlib import Path

import pytest
from hypothesis import given, settings, strategies as st

_BASE = Path(__file__).resolve().parent.parent
def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, _BASE / rel)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m

led = _load("mutual_credit_ledger_tp", "src/ledger/mutual_credit_ledger.py")
sol = _load("clearing_solver_ltp", "src/clearing/clearing_solver.py")

PARAMS = {"neg_line_bp": 100, "pos_line_bp": 1000, "velocity_window_s": 86400,
          "velocity_max_cents": 5_000_000, "moneda": "USD", "paused": False}

def fresh_cell(ts=1000):
    state, ev = led.create_cell("cell1", dict(PARAMS), "ana", ts)
    events = [ev]
    for mid in "ABCD":
        state, ev = led.add_member(state, {"id": mid, "turnover_cents": 100_000_000}, "ana", ts)
        events.append(ev)
    return state, events

@st.composite
def op_stream(draw):
    ops = []
    last_ts = 1000
    obligation_counter = 0
    open_obs = {}
    num_ops = draw(st.integers(min_value=0, max_value=25))
    for _ in range(num_ops):
        op_type = draw(st.sampled_from(["record", "settle", "pause", "resume", "invalid_self", "invalid_zero"]))
        ts = last_ts + draw(st.integers(min_value=0, max_value=100)) + 1
        last_ts = ts
        if op_type == "record":
            debtor = draw(st.sampled_from(list("ABCD")))
            creditor = draw(st.sampled_from([m for m in "ABCD" if m != debtor]))
            amount = draw(st.integers(min_value=1, max_value=50_000))
            oid = f"p{obligation_counter}"
            obligation_counter += 1
            open_obs[oid] = amount
            ops.append(("record_obligation", {"id": oid, "debtor": debtor, "creditor": creditor, "amount_cents": amount}, ts))
        elif op_type == "settle":
            if open_obs:
                oid = draw(st.sampled_from(list(open_obs.keys())))
                amount = draw(st.integers(min_value=1, max_value=open_obs[oid]))
                ops.append(("settle_obligation", oid, amount, ts))
                open_obs[oid] -= amount
                if open_obs[oid] <= 0:
                    del open_obs[oid]
        elif op_type == "pause":
            ops.append(("pause_cell", "ana", ts))
        elif op_type == "resume":
            ops.append(("resume_cell", "ana", ts))
        elif op_type == "invalid_self":
            member = draw(st.sampled_from(list("ABCD")))
            oid = f"p{obligation_counter}"
            obligation_counter += 1
            ops.append(("record_obligation", {"id": oid, "debtor": member, "creditor": member, "amount_cents": 100}, ts))
        elif op_type == "invalid_zero":
            debtor = draw(st.sampled_from(list("ABCD")))
            creditor = draw(st.sampled_from([m for m in "ABCD" if m != debtor]))
            oid = f"p{obligation_counter}"
            obligation_counter += 1
            ops.append(("record_obligation", {"id": oid, "debtor": debtor, "creditor": creditor, "amount_cents": 0}, ts))
    return ops

@given(ops=op_stream())
@settings(max_examples=100, deadline=None)
def test_property_balances_and_bounds(ops):
    """After every accepted op, sum(balances)==0 and every balance within its member bounds."""
    state, events = fresh_cell(1000)
    for op in ops:
        op_type = op[0]
        args = op[1:]
        before = led.canonical(state)
        try:
            if op_type == "record_obligation":
                state, ev = led.record_obligation(state, args[0], args[1])
                events.append(ev)
            elif op_type == "settle_obligation":
                state, ev = led.settle_obligation(state, args[0], args[1], args[2])
                events.append(ev)
            elif op_type == "pause_cell":
                state, ev = led.pause_cell(state, args[0], args[1])
                events.append(ev)
            elif op_type == "resume_cell":
                state, ev = led.resume_cell(state, args[0], args[1])
                events.append(ev)
        except ValueError:
            assert led.canonical(state) == before
            continue
        metrics = led.cell_metrics(state)
        assert metrics["sum_balances_cents"] == 0
        for mid in "ABCD":
            stmt = led.member_statement(state, mid)
            assert stmt["credit_min_cents"] <= stmt["balance_cents"] <= stmt["credit_max_cents"]

@given(ops=op_stream())
@settings(max_examples=100, deadline=None)
def test_property_replay_and_verify(ops):
    """Final replay(events)==state canonically and verify_chain(events) passes."""
    state, events = fresh_cell(1000)
    for op in ops:
        op_type = op[0]
        args = op[1:]
        try:
            if op_type == "record_obligation":
                state, ev = led.record_obligation(state, args[0], args[1])
                events.append(ev)
            elif op_type == "settle_obligation":
                state, ev = led.settle_obligation(state, args[0], args[1], args[2])
                events.append(ev)
            elif op_type == "pause_cell":
                state, ev = led.pause_cell(state, args[0], args[1])
                events.append(ev)
            elif op_type == "resume_cell":
                state, ev = led.resume_cell(state, args[0], args[1])
                events.append(ev)
        except ValueError:
            continue
    replayed = led.replay(events)
    assert led.canonical(replayed) == led.canonical(state)
    led.verify_chain(events)

@given(ops=op_stream())
@settings(max_examples=100, deadline=None)
def test_property_determinism(ops):
    """Run the SAME accepted-op sequence again from scratch -> byte-identical final canonical state."""
    state1, events1 = fresh_cell(1000)
    accepted = []
    for op in ops:
        op_type = op[0]
        args = op[1:]
        try:
            if op_type == "record_obligation":
                state1, ev = led.record_obligation(state1, args[0], args[1])
                events1.append(ev)
                accepted.append(op)
            elif op_type == "settle_obligation":
                state1, ev = led.settle_obligation(state1, args[0], args[1], args[2])
                events1.append(ev)
                accepted.append(op)
            elif op_type == "pause_cell":
                state1, ev = led.pause_cell(state1, args[0], args[1])
                events1.append(ev)
                accepted.append(op)
            elif op_type == "resume_cell":
                state1, ev = led.resume_cell(state1, args[0], args[1])
                events1.append(ev)
                accepted.append(op)
        except ValueError:
            continue
    canonical1 = led.canonical(state1)
    state2, events2 = fresh_cell(1000)
    for op in accepted:
        op_type = op[0]
        args = op[1:]
        if op_type == "record_obligation":
            state2, ev = led.record_obligation(state2, args[0], args[1])
            events2.append(ev)
        elif op_type == "settle_obligation":
            state2, ev = led.settle_obligation(state2, args[0], args[1], args[2])
            events2.append(ev)
        elif op_type == "pause_cell":
            state2, ev = led.pause_cell(state2, args[0], args[1])
            events2.append(ev)
        elif op_type == "resume_cell":
            state2, ev = led.resume_cell(state2, args[0], args[1])
            events2.append(ev)
    canonical2 = led.canonical(state2)
    assert canonical2 == canonical1
