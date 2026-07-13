"""Track A — the integration firewall oracles. Independent (imports neither SUT's modules, AST-
checked): it reconstructs B2B rosters/obligations from the recorded WorldEvents and judges each
BridgeAttempt against its own re-derivation.

Three firewalls, two distinct enforcement loci:
- F-VS1 (debt->gift) and F-CC (cell->cell) are enforced by the real SUTs (membrane raise / unknown-
  member reject); the oracle catches the case where that wall was BYPASSED (the negative control).
- F-VS2 (person-scalar->credit) is NOT enforceable by either SUT — a strict-int credit bound carries
  no provenance — so this oracle IS the wall: any successful B2B credit op tagged c2c_person_scalar
  fails, while a turnover/human_ratified one passes. This is the seam's native failure mode.
"""
from __future__ import annotations

from collections.abc import Sequence

from engine.measurement import IntegrityReport, InvariantResult, TrackA, Verdict
from engine.types import TraceEvent
from .world import BridgeAttempt, Rejected, WorldEvent

# the value-key taxonomy the C2C membrane forbids in non-market rooms (the oracle's own copy)
_VALUE_KEYS = ['price', 'cost', 'fee', '_cents', 'currency', 'valuation', 'denominat',
               'debt', 'owed', 'balance', 'credit', 'reciprocity', 'iou', 'favor_balance']


def _find_value_key(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            kl = str(k).lower()
            for s in _VALUE_KEYS:
                if s in kl:
                    return str(k)
            hit = _find_value_key(v)
            if hit is not None:
                return hit
    elif isinstance(obj, (list, tuple)):
        for it in obj:
            hit = _find_value_key(it)
            if hit is not None:
                return hit
    return None


class IntegratedTrackA(TrackA):
    def measure(self, trace: Sequence[TraceEvent]) -> IntegrityReport:
        # independent reconstruction from the baseline WorldEvents
        rosters: dict[str, set[str]] = {}
        obligations: dict[str, dict[str, int]] = {}   # cell -> {amount: obligation_id}
        for e in trace:
            r = e.result
            if isinstance(r, WorldEvent) and r.kind == "member_added":
                rosters.setdefault(r.cell, set()).add(r.event["member_id"])
            elif isinstance(r, WorldEvent) and r.kind == "obligation_recorded":
                ob = r.event["payload"]["obligation"]
                obligations.setdefault(r.cell, {})[ob["amount_cents"]] = ob["id"]

        v1, t1 = Verdict.PASS, None   # value_social_debt_leak
        v2, t2 = Verdict.PASS, None   # value_social_score_to_credit
        v3, t3 = Verdict.PASS, None   # cell_contagion

        for e in trace:
            r = e.result
            if not isinstance(r, BridgeAttempt):
                continue

            # F-VS1: a denominated debt admitted into a gift/equality room is a leak.
            if v1 is Verdict.PASS and r.kind == "debt_to_gift":
                if not isinstance(r.output, Rejected) and r.output.get("admitted") is True:
                    payload = r.request.get("payload", {})
                    key = _find_value_key(payload)
                    amount = payload.get("settlement_amount_cents")
                    # the leaked value must trace to a REAL B2B obligation (genuine cross-system value)
                    real = any(amount in amts for amts in obligations.values())
                    if key is not None and real:
                        v1, t1 = Verdict.FAIL, {"kind": "debt_admitted_into_gift_room",
                                                "key": key, "amount_cents": amount}

            # F-VS2: a successful credit op derived from a C2C person-scalar (the provenance wall).
            if v2 is Verdict.PASS and r.kind == "score_to_credit":
                if r.provenance == "c2c_person_scalar" and not isinstance(r.output, Rejected):
                    v2, t2 = Verdict.FAIL, {"kind": "social_scalar_fed_a_credit_decision",
                                            "member": r.request.get("member_id"),
                                            "provenance": r.provenance}

            # F-CC: a cell-B obligation committed with a party not in cell B's roster is contagion.
            if v3 is Verdict.PASS and r.kind == "cross_cell":
                if not isinstance(r.output, Rejected):
                    to_cell = r.request.get("to_cell")
                    debtor = r.request.get("debtor")
                    creditor = r.request.get("creditor")
                    roster = rosters.get(to_cell, set())
                    stranger = next((p for p in (debtor, creditor) if p not in roster), None)
                    if stranger is not None:
                        v3, t3 = Verdict.FAIL, {"kind": "foreign_party_obligation_committed",
                                                "to_cell": to_cell, "stranger": stranger}

        return IntegrityReport(results={
            "value_social_debt_leak": InvariantResult(verdict=v1, exploit_trace=t1),
            "value_social_score_to_credit": InvariantResult(verdict=v2, exploit_trace=t2),
            "cell_contagion": InvariantResult(verdict=v3, exploit_trace=t3),
        })
