"""Track A — VE integrity oracle for the C2C side (TS.2): `moneda_unica_por_campana` (TA.6).

Independence discipline (AST-checked in the tests): imports NO C2C module and never touches
the adapter — it re-derives everything from the recorded ModuleCall(request, output) pairs.
"""
from __future__ import annotations

from collections.abc import Sequence

from engine.measurement import IntegrityReport, InvariantResult, TrackA, Verdict
from engine.types import TraceEvent
from .world import ModuleCall, Rejected

_MONEDAS = ("USD", "VES")  # the oracle's own copy of Capa 4's MONEDAS (never imported)


def _moneda_values(obj):
    """Every value under a key named exactly 'moneda' or 'bono_moneda', anywhere in obj."""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k) in ("moneda", "bono_moneda"):
                out.append(v)
            out.extend(_moneda_values(v))
    elif isinstance(obj, (list, tuple)):
        for it in obj:
            out.extend(_moneda_values(it))
    return out


class C2CTrackAVE(TrackA):
    def measure(self, trace: Sequence[TraceEvent]) -> IntegrityReport:
        v, t = Verdict.PASS, None

        for event in trace:
            mc = event.result
            if not isinstance(mc, ModuleCall) or mc.method != "resolver":
                continue
            if isinstance(mc.output, Rejected):
                # the module's own wall fired; the oracle judges only what a SUCCESSFUL
                # resolve emitted — a bypassed wall is exactly what it must catch.
                continue
            if v is not Verdict.PASS:
                break

            envelope_moneda = mc.request.get("moneda")
            if envelope_moneda not in _MONEDAS:
                v, t = Verdict.FAIL, {"kind": "campana_sin_moneda_valida",
                                      "campana": mc.request.get("campana_id"),
                                      "moneda": envelope_moneda}
                continue

            # ONE moneda value across request AND output: a per-pledge moneda that differs
            # from the envelope's — or an output that answers in another unit — is the mixing
            # TA.6 makes a hard breach. If the SUT stopped rejecting it, only this sees it.
            distinct = set(_moneda_values(mc.request)) | set(_moneda_values(mc.output))
            if distinct != {envelope_moneda}:
                v, t = Verdict.FAIL, {"kind": "moneda_mezclada_en_campana",
                                      "campana": mc.request.get("campana_id"),
                                      "sobre": envelope_moneda,
                                      "vistas": sorted(map(str, distinct))}

        return IntegrityReport(results={
            "moneda_unica_por_campana": InvariantResult(verdict=v, exploit_trace=t),
        })


class C2CTrackAComposite(TrackA):
    """Inherited C2C Track A + the VE oracle, merged (disjoint names) so a VE violation
    also halts the campaign."""

    def __init__(self, base: TrackA) -> None:
        self._base = base
        self._ve = C2CTrackAVE()

    def measure(self, trace: Sequence[TraceEvent]) -> IntegrityReport:
        base = self._base.measure(trace)
        ve = self._ve.measure(trace)
        overlap = set(base.results) & set(ve.results)
        assert not overlap, f"oracle name collision: {overlap}"
        return IntegrityReport(results={**base.results, **ve.results})
