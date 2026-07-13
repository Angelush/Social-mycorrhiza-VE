"""Thin, faithful one-to-one wrapper over the real B2B money-moving system.

The only Sim code that touches B2B's clearing solver and mutual-credit ledger.
It pins their content hash via SUTAdapter, then loads both real modules from
source at construction time, and forwards every call to them verbatim.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from engine.sut_adapter import SUTAdapter


class B2BAdapter(SUTAdapter):
    # Every method below is a deliberate bare pass-through to the real B2B
    # module: unpack (state, event), update self._state, return the event -
    # with zero validation, bounds-checking, exception-catching, or adjudication
    # of its own. That is the single invariant this file exists to uphold. A
    # future editor tempted to add a "helpful" check here would be quietly
    # reintroducing a second copy of the mechanism this wrapper must never become.

    def __init__(self, b2b_root: str | Path) -> None:
        solver_path = Path(b2b_root) / "src" / "clearing" / "clearing_solver.py"
        ledger_path = Path(b2b_root) / "src" / "ledger" / "mutual_credit_ledger.py"

        super().__init__([solver_path, ledger_path], repo_dir=b2b_root)

        solver_spec = importlib.util.spec_from_file_location(
            "b2b_clearing_solver", solver_path
        )
        self._solver = importlib.util.module_from_spec(solver_spec)
        solver_spec.loader.exec_module(self._solver)

        ledger_spec = importlib.util.spec_from_file_location(
            "b2b_mutual_credit_ledger", ledger_path
        )
        self._ledger = importlib.util.module_from_spec(ledger_spec)
        ledger_spec.loader.exec_module(self._ledger)

        self._state: dict | None = None

    def create_cell(self, cell_id: str, params: dict, ratified_by: str, ts: int) -> dict:
        new_state, event = self._ledger.create_cell(cell_id, params, ratified_by, ts)
        self._state = new_state
        return event

    def add_member(self, member: dict, ratified_by: str, ts: int) -> dict:
        new_state, event = self._ledger.add_member(self._state, member, ratified_by, ts)
        self._state = new_state
        return event

    def update_member(self, member_id: str, changes: dict, ratified_by: str, ts: int) -> dict:
        new_state, event = self._ledger.update_member(self._state, member_id, changes, ratified_by, ts)
        self._state = new_state
        return event

    def record_obligation(self, obligation: dict, ts: int) -> dict:
        new_state, event = self._ledger.record_obligation(self._state, obligation, ts)
        self._state = new_state
        return event

    def settle_obligation(self, obligation_id: str, amount_cents: int, ts: int) -> dict:
        new_state, event = self._ledger.settle_obligation(self._state, obligation_id, amount_cents, ts)
        self._state = new_state
        return event

    def run_clearing(self) -> dict:
        clearing_input = self._ledger.to_clearing_input(self._state)
        return self._solver.clear(clearing_input)

    def apply_clearing(self, proposal: dict, ratified_by: str, ts: int) -> dict:
        new_state, event = self._ledger.apply_clearing(self._state, proposal, ratified_by, ts)
        self._state = new_state
        return event

    def pause_cell(self, ratified_by: str, ts: int) -> dict:
        new_state, event = self._ledger.pause_cell(self._state, ratified_by, ts)
        self._state = new_state
        return event

    def resume_cell(self, ratified_by: str, ts: int) -> dict:
        new_state, event = self._ledger.resume_cell(self._state, ratified_by, ts)
        self._state = new_state
        return event

    def member_statement(self, member_id: str) -> dict:
        return self._ledger.member_statement(self._state, member_id)

    def cell_metrics(self) -> dict:
        return self._ledger.cell_metrics(self._state)
