"""Track A — VE integrity oracles for the B2B side (TS.2).

Three oracles over the Fase-2 invariants: `fx_irrepresentable` (D1/I5/N3),
`visibilidad_saldos` (D3), `puerta_humana_ops_nuevas` (M8/D6/D8).

Independence discipline (AST-checked in the tests): this module imports NO B2B-VE module and
never touches the adapter. It re-derives every property from the recorded trace using its OWN
copies of the taxonomies and gate lists — duplicated verbatim from the VE sources on purpose:
an oracle that imported the layer it checks would be self-confirmation, not an independent check.
"""
from __future__ import annotations

from collections.abc import Sequence

from engine.measurement import IntegrityReport, InvariantResult, TrackA, Verdict
from engine.types import TraceEvent
from .world import ClearingOutcome, Rejected, ScopedStatements


# --- the oracle's OWN copy of the FX/rate taxonomy: `_TASA_KEYS` of the VE ledger (D1),
# duplicated VERBATIM (never imported), glued variants included (TA.6's reviewer hardening).
# Substring match, like the layers themselves. 'fx' is deliberately kept even though it is a
# short token: no legal wire key contains it — a future collision would show up as a false
# FAIL, which is the honest failure direction for a value invariant.
TASA_KEYS = [
    'tasa_de_cambio', 'tipo_de_cambio', 'exchange_rate', 'fx', 'paralelo', 'bcv',
    'tasadecambio', 'tipodecambio', 'exchangerate',
]

# --- the oracle's OWN copy of the ratification-gated kinds (M8's `ratification_kinds` plus the
# VE additions). Kind strings are English: the E2 seam is IN the wire and the oracle follows the
# wire, not the docs. `obligation_recorded`/`obligation_settled` are NOT here BY DESIGN: trading
# and paying what you owe carry no human gate (N-d68.4 in spirit) — an oracle that demanded a
# gate there would be inventing policy, not checking it.
GATED_KINDS = {
    "cell_created", "member_added", "member_updated", "clearing_applied",
    "cell_paused", "cell_resumed",
    # the VE "ops nuevas": D6 exit and D8 bridge pause/resume
    "member_exited", "bridge_paused", "bridge_resumed",
}


def _find_key(obj, substrings):
    """Recursive case-insensitive key-substring scan (the oracle's own, mirrors the layers)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            kl = str(k).lower()
            for s in substrings:
                if s in kl:
                    return str(k)
            hit = _find_key(v, substrings)
            if hit is not None:
                return hit
    elif isinstance(obj, (list, tuple)):
        for it in obj:
            hit = _find_key(it, substrings)
            if hit is not None:
                return hit
    return None


def _numeric_leaf(obj):
    """First numeric leaf (int/float, bools excluded) anywhere in obj, or None.

    This is the TYPE wall of D3 (TB.4's AC-7 lesson): under `publico` the guarantee is not
    'no key named balance' but 'no numbers AT ALL' — a future `salud_crediticia: 7` must fail
    without anyone having foreseen its name.
    """
    if isinstance(obj, bool):
        return None
    if isinstance(obj, (int, float)):
        return obj
    if isinstance(obj, dict):
        for k, v in obj.items():
            hit = _numeric_leaf(v)
            if hit is not None:
                return (str(k), hit)
    elif isinstance(obj, (list, tuple)):
        for it in obj:
            hit = _numeric_leaf(it)
            if hit is not None:
                return hit
    return None


class B2BTrackAVE(TrackA):
    def measure(self, trace: Sequence[TraceEvent]) -> IntegrityReport:
        v_fx, t_fx = Verdict.PASS, None
        v_vis, t_vis = Verdict.PASS, None
        v_gate, t_gate = Verdict.PASS, None

        cell_moneda: str | None = None
        seudonimo_by_member: dict[str, str] = {}

        for event in trace:
            result = event.result

            # ---- fx_irrepresentable + puerta: every ledger EVENT dict in the trace ----
            if isinstance(result, dict) and "kind" in result:
                kind = result.get("kind")

                if kind == "cell_created":
                    cell_moneda = result.get("payload", {}).get("params", {}).get("moneda")

                if v_fx is Verdict.PASS:
                    hit = _find_key(result, TASA_KEYS)
                    if hit is not None:
                        v_fx, t_fx = Verdict.FAIL, {"kind": "tasa_key_in_event",
                                                    "event_kind": kind, "key": hit}
                    elif kind == "obligation_recorded":
                        ob = result.get("payload", {}).get("obligation", {})
                        if "moneda" in ob:
                            # a per-obligation moneda is the door to partitioned L1 + a rate:
                            # mixing must stay UNREPRESENTABLE (D1), not merely unused.
                            v_fx, t_fx = Verdict.FAIL, {"kind": "obligation_carries_moneda",
                                                        "obligation_id": ob.get("id")}

                if v_gate is Verdict.PASS and kind in GATED_KINDS:
                    rb = result.get("payload", {}).get("ratified_by")
                    if not (isinstance(rb, str) and rb):
                        v_gate, t_gate = Verdict.FAIL, {"kind": "gated_op_without_ratification",
                                                        "event_kind": kind, "tick": event.tick}
                continue

            # ---- fx: the clearing proposal must carry THE cell's one moneda ----
            if isinstance(result, ClearingOutcome):
                if v_fx is Verdict.PASS:
                    hit = _find_key(result.proposal, TASA_KEYS)
                    if hit is not None:
                        v_fx, t_fx = Verdict.FAIL, {"kind": "tasa_key_in_proposal", "key": hit}
                    elif cell_moneda is not None and result.proposal.get("moneda") != cell_moneda:
                        v_fx, t_fx = Verdict.FAIL, {"kind": "proposal_moneda_mismatch",
                                                    "cell": cell_moneda,
                                                    "proposal": result.proposal.get("moneda")}
                if (v_gate is Verdict.PASS and result.applied_event is not None):
                    rb = result.applied_event.get("payload", {}).get("ratified_by")
                    if not (isinstance(rb, str) and rb):
                        v_gate, t_gate = Verdict.FAIL, {"kind": "gated_op_without_ratification",
                                                        "event_kind": "clearing_applied",
                                                        "tick": event.tick}
                continue

            # ---- visibilidad_saldos: the scoped statement probes ----
            if isinstance(result, ScopedStatements):
                if v_vis is not Verdict.PASS:
                    continue
                pub = result.publico
                if isinstance(pub, Rejected):
                    v_vis, t_vis = Verdict.FAIL, {"kind": "publico_rejected",
                                                  "member": result.member_id}
                    continue
                if set(pub) != {"seudonimo"}:
                    v_vis, t_vis = Verdict.FAIL, {"kind": "publico_beyond_seudonimo",
                                                  "member": result.member_id,
                                                  "keys": sorted(pub)}
                    continue
                leaf = _numeric_leaf(pub)
                if leaf is not None:
                    v_vis, t_vis = Verdict.FAIL, {"kind": "numeric_leaf_under_publico",
                                                  "member": result.member_id, "leaf": leaf}
                    continue
                seud = pub.get("seudonimo")
                if seud == result.member_id:
                    v_vis, t_vis = Verdict.FAIL, {"kind": "seudonimo_is_identity",
                                                  "member": result.member_id}
                    continue
                prev = seudonimo_by_member.setdefault(result.member_id, seud)
                if prev != seud:
                    # stability IS the arbiter's utility (D2/D3): two seudónimos for one member
                    # break the link between anchors.
                    v_vis, t_vis = Verdict.FAIL, {"kind": "seudonimo_unstable",
                                                  "member": result.member_id}
                    continue
                if not isinstance(result.cruce_ajeno, Rejected):
                    v_vis, t_vis = Verdict.FAIL, {"kind": "foreign_miembro_scope_not_rejected",
                                                  "member": result.member_id}
                continue

        return IntegrityReport(results={
            "fx_irrepresentable": InvariantResult(verdict=v_fx, exploit_trace=t_fx),
            "visibilidad_saldos": InvariantResult(verdict=v_vis, exploit_trace=t_vis),
            "puerta_humana_ops_nuevas": InvariantResult(verdict=v_gate, exploit_trace=t_gate),
        })


class B2BTrackAComposite(TrackA):
    """Runs the inherited Track A plus the VE oracles and merges the (disjoint) results, so a
    VE violation also HALTS a campaign — Track A is a hard stop, never one data point more."""

    def __init__(self, base: TrackA) -> None:
        self._base = base
        self._ve = B2BTrackAVE()

    def measure(self, trace: Sequence[TraceEvent]) -> IntegrityReport:
        base = self._base.measure(trace)
        ve = self._ve.measure(trace)
        overlap = set(base.results) & set(ve.results)
        assert not overlap, f"oracle name collision: {overlap}"
        return IntegrityReport(results={**base.results, **ve.results})
