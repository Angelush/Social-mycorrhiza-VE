"""Track A — B2B integrity oracles (conservation, credit-bound, firewall, velocity, sanctions).

Trace convention these oracles depend on: every round's trace begins with synthetic
`member_added`-shaped setup events (sim_b2b.campaign.build_world extends the trace with them),
because the initial roster's membership and credit bounds reach the oracles ONLY through the trace.
There is no side channel to the adapter — that is what keeps this an independent re-derivation of
integrity rather than a read of the SUT's own state.
"""
from __future__ import annotations

from collections.abc import Sequence

import networkx as nx

from engine.measurement import IntegrityReport, InvariantResult, TrackA, Verdict
from engine.types import TraceEvent
from .proposals import SanctionStep, Settle, Trade
from .world import ClearingOutcome, Rejected

LADDER = ["active", "warned", "line_reduced", "suspended", "expelled"]


def _net_positions(edges: list[tuple[str, str, int]], firms: set[str]) -> dict[str, int]:
    # networkx-based recompute, deliberately a different code path from the solver's own
    # defaultdict arithmetic (_net_positions in clearing_solver.py) -- using a different
    # library/data structure is what makes this a genuinely independent oracle (F2/C3),
    # not a restatement of the SUT's own numbers.
    g = nx.MultiDiGraph()
    for firm in firms:
        g.add_node(firm)
    for debtor, creditor, amount in edges:
        g.add_edge(debtor, creditor, weight=amount)
    net: dict[str, int] = {}
    for firm in firms:
        incoming = sum(w for _, _, w in g.in_edges(firm, data="weight"))
        outgoing = sum(w for _, _, w in g.out_edges(firm, data="weight"))
        net[firm] = incoming - outgoing
    return net


class B2BTrackA(TrackA):
    def __init__(self, velocity_window_s: int, velocity_max_cents: int) -> None:
        self._velocity_window_s = velocity_window_s
        self._velocity_max_cents = velocity_max_cents

    def measure(self, trace: Sequence[TraceEvent]) -> IntegrityReport:
        known_members: dict[str, dict[str, int]] = {}
        obligation_parties: dict[str, tuple[str, str]] = {}
        open_obligations: dict[str, int] = {}
        recent_recorded_by_debtor: dict[str, list[tuple[int, int]]] = {}
        member_status: dict[str, str] = {}
        seen_cell_ids: set[str] = set()

        t1a_verdict = Verdict.PASS
        t1a_trace: object | None = None
        t1b_verdict = Verdict.PASS
        t1b_trace: object | None = None
        t1c_verdict = Verdict.PASS
        t1c_trace: object | None = None
        t1d_verdict = Verdict.PASS
        t1d_trace: object | None = None
        t1e_verdict = Verdict.PASS
        line_reduction_rejections = 0
        unrestricted_downward = 0

        for event in trace:
            result = event.result

            if isinstance(result, dict) and result.get("kind") == "member_added":
                member = result["payload"]["member"]
                mid = member["id"]
                known_members[mid] = {
                    "credit_min_cents": member["credit_min_cents"],
                    "credit_max_cents": member["credit_max_cents"],
                }
                member_status.setdefault(mid, "active")
                continue

            if isinstance(result, dict) and result.get("kind") == "obligation_recorded":
                ob = result["payload"]["obligation"]
                oid, debtor, creditor, amount = (
                    ob["id"], ob["debtor"], ob["creditor"], ob["amount_cents"],
                )

                if t1c_verdict is Verdict.PASS and (
                    debtor not in known_members or creditor not in known_members
                ):
                    t1c_verdict = Verdict.FAIL
                    t1c_trace = {
                        "kind": "accepted_unknown_member", "tick": event.tick,
                        "obligation_id": oid, "debtor": debtor, "creditor": creditor,
                    }

                obligation_parties[oid] = (debtor, creditor)
                open_obligations[oid] = amount

                if (
                    t1b_verdict is Verdict.PASS
                    and isinstance(event.proposal, Trade)
                    and event.proposal.cents != amount
                ):
                    t1b_verdict = Verdict.FAIL
                    t1b_trace = {
                        "kind": "silent_clamp_trade", "obligation_id": oid,
                        "requested": event.proposal.cents, "committed": amount,
                    }

                ts = result["ts"]
                history = recent_recorded_by_debtor.setdefault(debtor, [])
                pruned = [(t, a) for (t, a) in history if t > ts - self._velocity_window_s]
                window_sum = sum(a for _, a in pruned)
                if t1d_verdict is Verdict.PASS and window_sum + amount > self._velocity_max_cents:
                    t1d_verdict = Verdict.FAIL
                    t1d_trace = {
                        "debtor": debtor, "tick": event.tick,
                        "window_sum_before": window_sum, "amount": amount,
                        "cap": self._velocity_max_cents,
                    }
                pruned.append((ts, amount))
                recent_recorded_by_debtor[debtor] = pruned
                continue

            if isinstance(result, dict) and result.get("kind") == "obligation_settled":
                oid = result["payload"]["obligation_id"]
                amount = result["payload"]["amount_cents"]

                if (
                    t1b_verdict is Verdict.PASS
                    and isinstance(event.proposal, Settle)
                    and event.proposal.cents != amount
                ):
                    t1b_verdict = Verdict.FAIL
                    t1b_trace = {
                        "kind": "silent_clamp_settle", "obligation_id": oid,
                        "requested": event.proposal.cents, "committed": amount,
                    }

                if oid in open_obligations:
                    open_obligations[oid] -= amount
                    if open_obligations[oid] <= 0:
                        del open_obligations[oid]
                        obligation_parties.pop(oid, None)
                continue

            if isinstance(result, dict) and result.get("kind") == "member_updated":
                mid = result["payload"]["member_id"]
                changes = result["payload"]["changes"]
                new_status = changes.get("status")
                if new_status is not None:
                    old_status = member_status.get(mid, "active")
                    if old_status in LADDER and new_status in LADDER:
                        old_idx, new_idx = LADDER.index(old_status), LADDER.index(new_status)
                        if new_idx > old_idx and new_idx != old_idx + 1:
                            # Should never happen -- the real ledger itself rejects upward
                            # rung-skips, so an ACCEPTED skip here means its own enforcement
                            # has a bug (independent confirmation, not self-confirmation).
                            t1e_verdict = Verdict.FAIL
                        if old_idx - new_idx > 1:
                            unrestricted_downward += 1
                    member_status[mid] = new_status
                continue

            if isinstance(result, Rejected) and isinstance(event.proposal, SanctionStep):
                changes = event.proposal.changes
                if "credit_min_cents" in changes or "credit_max_cents" in changes:
                    line_reduction_rejections += 1
                continue

            if isinstance(result, ClearingOutcome):
                proposal = result.proposal
                seen_cell_ids.add(proposal["cell_id"])

                residual = proposal["residual_obligations"]
                touched_residual = {o["debtor"] for o in residual} | {o["creditor"] for o in residual}
                recomputed_net = _net_positions(
                    [(o["debtor"], o["creditor"], o["amount_cents"]) for o in residual],
                    touched_residual,
                )
                independent_out_of_bounds = {
                    m for m in touched_residual
                    if m in known_members
                    and not (
                        known_members[m]["credit_min_cents"]
                        <= recomputed_net.get(m, 0)
                        <= known_members[m]["credit_max_cents"]
                    )
                }
                solver_flags = set(proposal["credit_flags"])
                if t1b_verdict is Verdict.PASS and independent_out_of_bounds != solver_flags:
                    t1b_verdict = Verdict.FAIL
                    t1b_trace = {
                        "kind": "credit_flags_mismatch",
                        "independent": sorted(independent_out_of_bounds),
                        "solver": sorted(solver_flags),
                    }

                if result.applied_event is not None:
                    settlements = proposal["settlements"]
                    touched_firms: set[str] = set()
                    for s in settlements:
                        parties = obligation_parties.get(s["obligation_id"])
                        if parties is not None:
                            touched_firms.update(parties)

                    pre_edges = [
                        (obligation_parties[oid][0], obligation_parties[oid][1], amt)
                        for oid, amt in open_obligations.items()
                        if oid in obligation_parties
                    ]
                    pre_net = _net_positions(pre_edges, touched_firms)

                    working = dict(open_obligations)
                    for s in settlements:
                        oid, reduce_by = s["obligation_id"], s["reduce_by_cents"]
                        if oid in working:
                            working[oid] -= reduce_by
                            if working[oid] <= 0:
                                del working[oid]

                    post_edges = [
                        (obligation_parties[oid][0], obligation_parties[oid][1], amt)
                        for oid, amt in working.items()
                        if oid in obligation_parties
                    ]
                    post_net = _net_positions(post_edges, touched_firms)

                    if t1a_verdict is Verdict.PASS:
                        for firm in touched_firms:
                            if pre_net.get(firm, 0) != post_net.get(firm, 0):
                                t1a_verdict = Verdict.FAIL
                                t1a_trace = {
                                    "tick": event.tick, "firm": firm,
                                    "pre_net": pre_net.get(firm, 0),
                                    "post_net": post_net.get(firm, 0),
                                }
                                break

                    open_obligations = working
                continue

        if len(seen_cell_ids) > 1:
            t1c_verdict = Verdict.FAIL
            t1c_trace = {"kind": "multiple_cell_ids", "seen": sorted(seen_cell_ids)}

        results = {
            "conservation": InvariantResult(verdict=t1a_verdict, exploit_trace=t1a_trace),
            "credit_bound": InvariantResult(verdict=t1b_verdict, exploit_trace=t1b_trace),
            "firewall": InvariantResult(verdict=t1c_verdict, exploit_trace=t1c_trace),
            "velocity": InvariantResult(verdict=t1d_verdict, exploit_trace=t1d_trace),
            "sanctions": InvariantResult(
                verdict=t1e_verdict,
                exploit_trace={
                    "line_reduction_rejections_on_drawn_down_members": line_reduction_rejections,
                    "unrestricted_downward_rehabilitations": unrestricted_downward,
                },
            ),
        }
        return IntegrityReport(results=results)
