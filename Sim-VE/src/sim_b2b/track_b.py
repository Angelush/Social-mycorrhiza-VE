from __future__ import annotations

from collections.abc import Sequence

from engine.measurement import Distribution, TrackB, WelfareReport
from engine.types import TraceEvent
from .proposals import Trade
from .world import ClearingOutcome, Rejected


def _gini(values: list[float]) -> float:
    n = len(values)
    total = sum(values)
    if n == 0 or total == 0:
        return 0.0
    sorted_vals = sorted(values)
    cum = sum((i + 1) * v for i, v in enumerate(sorted_vals))
    return (2 * cum - (n + 1) * total) / (n * total)


class B2BTrackB(TrackB):
    def __init__(self, known_bounds: dict[str, dict[str, int]] | None = None) -> None:
        # known_bounds (member_id -> {credit_min_cents, credit_max_cents}) is optional extra
        # context for T2d's near-cap proxy; without it T2d simply reports zero rather than
        # crashing, since credit bounds for the initial roster otherwise only reach this
        # oracle via member_added-shaped trace entries (same convention as Track A).
        self._known_bounds = known_bounds or {}

    def measure(self, trace: Sequence[TraceEvent]) -> WelfareReport:
        known_members: dict[str, dict[str, int]] = dict(self._known_bounds)
        obligation_parties: dict[str, tuple[str, str]] = {}
        owed_by: dict[str, int] = {}
        owed_to: dict[str, int] = {}
        balance: dict[str, int] = {}

        gross_recorded_cents = 0
        clearing_gross_before = 0
        clearing_gross_after = 0
        total_reduced_cents = 0
        per_firm_clearing_benefit: dict[str, int] = {}
        blocked_at_cap_cents = 0
        redistributed_near_cap_cents = 0
        settled_amount_by_pair: dict[tuple[str, str], int] = {}  # (creditor, debtor) -> total

        for event in trace:
            result = event.result

            if isinstance(result, dict) and result.get("kind") == "member_added":
                member = result["payload"]["member"]
                mid = member["id"]
                known_members.setdefault(
                    mid,
                    {
                        "credit_min_cents": member["credit_min_cents"],
                        "credit_max_cents": member["credit_max_cents"],
                    },
                )
                owed_by.setdefault(mid, 0)
                owed_to.setdefault(mid, 0)
                balance.setdefault(mid, 0)
                continue

            if isinstance(event.proposal, Trade):
                creditor = event.proposal.creditor
                amount = event.proposal.cents
                # A trade is "near cap" if the creditor's own projected position, AFTER this
                # trade would apply, lands in the top 20% of its declared credit range -- this
                # must look at the post-trade position, not the pre-trade one: an archetype
                # that always requests a huge fixed bite (e.g. Hoarder) can push straight past
                # its cap from a completely neutral starting position in one attempt, so
                # checking only the pre-trade position would never flag it even though the
                # trade itself is squarely testing the cap.
                near_cap = False
                bounds = known_members.get(creditor)
                if bounds is not None:
                    projected_after = (
                        balance.get(creditor, 0) + owed_to.get(creditor, 0) - owed_by.get(creditor, 0) + amount
                    )
                    span = bounds["credit_max_cents"] - bounds["credit_min_cents"]
                    if span > 0 and (projected_after - bounds["credit_min_cents"]) / span >= 0.8:
                        near_cap = True

                if isinstance(result, dict) and result.get("kind") == "obligation_recorded":
                    ob = result["payload"]["obligation"]
                    oid, debtor, creditor_id, committed = (
                        ob["id"], ob["debtor"], ob["creditor"], ob["amount_cents"],
                    )
                    obligation_parties[oid] = (debtor, creditor_id)
                    owed_by[debtor] = owed_by.get(debtor, 0) + committed
                    owed_to[creditor_id] = owed_to.get(creditor_id, 0) + committed
                    gross_recorded_cents += committed
                    if near_cap:
                        redistributed_near_cap_cents += committed
                elif isinstance(result, Rejected) and near_cap:
                    blocked_at_cap_cents += amount
                continue

            if isinstance(result, dict) and result.get("kind") == "obligation_settled":
                oid = result["payload"]["obligation_id"]
                amount = result["payload"]["amount_cents"]
                parties = obligation_parties.get(oid)
                if parties is not None:
                    debtor, creditor_id = parties
                    owed_by[debtor] = owed_by.get(debtor, 0) - amount
                    owed_to[creditor_id] = owed_to.get(creditor_id, 0) - amount
                    balance[debtor] = balance.get(debtor, 0) - amount
                    balance[creditor_id] = balance.get(creditor_id, 0) + amount
                    settled_amount_by_pair[(creditor_id, debtor)] = (
                        settled_amount_by_pair.get((creditor_id, debtor), 0) + amount
                    )
                    total_reduced_cents += amount
                continue

            if isinstance(result, ClearingOutcome):
                proposal = result.proposal
                metrics = proposal["metrics"]
                clearing_gross_before += metrics["gross_debt_before_cents"]
                clearing_gross_after += metrics["gross_debt_after_cents"]
                if result.applied_event is not None:
                    for s in proposal["settlements"]:
                        oid, reduce_by = s["obligation_id"], s["reduce_by_cents"]
                        parties = obligation_parties.get(oid)
                        if parties is not None:
                            debtor, creditor_id = parties
                            owed_by[debtor] = owed_by.get(debtor, 0) - reduce_by
                            owed_to[creditor_id] = owed_to.get(creditor_id, 0) - reduce_by
                            total_reduced_cents += reduce_by
                            per_firm_clearing_benefit[debtor] = (
                                per_firm_clearing_benefit.get(debtor, 0) + reduce_by
                            )
                            per_firm_clearing_benefit[creditor_id] = (
                                per_firm_clearing_benefit.get(creditor_id, 0) + reduce_by
                            )
                continue

        reduction_pct_clearing_only = (
            (clearing_gross_before - clearing_gross_after) / clearing_gross_before * 100.0
            if clearing_gross_before
            else 0.0
        )
        reduction_pct_combined = (
            total_reduced_cents / gross_recorded_cents * 100.0 if gross_recorded_cents else 0.0
        )

        benefit_values = [float(v) for v in per_firm_clearing_benefit.values()]
        gini_benefit = _gini(benefit_values)

        # T2f: a firm whose reconstructed running balance ended negative is a persisted,
        # never-corrected defaulter in this trace (no exit op erases it -- the negative
        # balance simply stays). Report, per such defaulter, how much each creditor realised
        # settling with them specifically -- the distribution of who absorbs the loss,
        # identity-free (no agent-indexed slot exists on WelfareReport by type -- only the
        # aggregate sample values are reported here, never a {creditor_id: amount} mapping).
        defaulters = {f for f, b in balance.items() if b < 0}
        mutualisation_samples = [
            float(amt)
            for (creditor_id, debtor), amt in settled_amount_by_pair.items()
            if debtor in defaulters
        ]

        metrics_out = {
            "net_debt_reduction_clearing_only_pct": reduction_pct_clearing_only,
            "net_debt_reduction_combined_pct": reduction_pct_combined,
            "clearing_benefit_gini": Distribution(
                summary={"gini": gini_benefit, "n_firms": float(len(benefit_values))},
                samples=tuple(sorted(benefit_values)),
            ),
            # Simplified proxy, honestly labelled: total recorded obligation volume, not a
            # precise isolation of only the marginal credit-margin-using portion of trade.
            "credit_enabled_liquidity_cents": float(gross_recorded_cents),
            "positive_cap_blocked_cents": float(blocked_at_cap_cents),
            "positive_cap_redistributed_cents": float(redistributed_near_cap_cents),
            "default_mutualisation_cents": Distribution(
                summary={
                    "total_cents": float(sum(mutualisation_samples)),
                    "n_creditor_events": float(len(mutualisation_samples)),
                },
                samples=tuple(sorted(mutualisation_samples)),
            ),
        }
        return WelfareReport(metrics=metrics_out)


def contracyclical_delta(with_crunch: WelfareReport, without_crunch: WelfareReport) -> dict[str, float]:
    # T2e is a cross-round comparison (credit_crunch=True vs False) -- it cannot be computed
    # from a single trace/round the way T2a-T2d/T2f are, so it is deliberately a standalone
    # function over two already-computed WelfareReports rather than a TrackB.measure() duty.
    def _scalar(report: WelfareReport, key: str) -> float:
        value = report.metrics[key]
        return float(value) if isinstance(value, (int, float)) else 0.0

    return {
        "reduction_pct_combined_delta": (
            _scalar(with_crunch, "net_debt_reduction_combined_pct")
            - _scalar(without_crunch, "net_debt_reduction_combined_pct")
        ),
        "liquidity_delta_cents": (
            _scalar(with_crunch, "credit_enabled_liquidity_cents")
            - _scalar(without_crunch, "credit_enabled_liquidity_cents")
        ),
    }
