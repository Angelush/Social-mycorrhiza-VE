"""Track A — C2C integrity oracles. Red/green, halt-on-violation, position-relative.

Independence discipline (N-03 style, AST-checked in the tests): this module imports NO C2C module.
It re-derives every property from the recorded ModuleCall(request, output) pairs using its OWN copy
of the taxonomies and its OWN recompute — never the SUT's numbers or its scan. The taxonomies
below are duplicated verbatim from the VE Capa layers on purpose (the BILINGUAL sets of TA.2):
an oracle that imported the layer it checks would be self-confirmation, not an independent check.
"""
from __future__ import annotations

from collections.abc import Sequence

from engine.measurement import IntegrityReport, InvariantResult, TrackA, Verdict
from engine.types import TraceEvent
from .world import ModuleCall, Rejected

# --- independent copies of the VE taxonomies (NOT imported from C2C-VE) ----------------------
FORBIDDEN_KEYS = [
    'score', 'puntuacion', 'puntaje', 'rating', 'calificacion',
    'reputation', 'reputacion', 'rank', 'ranking', 'clasificacion',
    'blacklist', 'lista_negra', 'ban', 'veto', 'penalty', 'penalizacion',
    'sancion', 'karma', 'global_id', 'dni', 'cedula', 'rif', 'pasaporte',
]
MARKET_KEYS = [
    'price', 'precio', 'cost', 'costo', 'coste', 'fee', 'tarifa',
    'cents', 'centavos', 'centimos', 'currency', 'moneda', 'divisa',
    'valuation', 'valoracion', 'denominat', 'denominacion',
    'pago', 'cobro', 'usd', 'ves', 'dolar', 'dolares', 'bolivar', 'bolivares',
]
RECIPROCITY_LEDGER_KEYS = [
    'debt', 'deuda', 'owed', 'debe', 'balance', 'saldo',
    'credit', 'credito', 'reciprocity', 'reciprocidad', 'iou',
    'favor_balance', 'saldo_de_favores',
]
ENGAGEMENT_KEYS = [
    'click', 'clic', 'dwell', 'engagement', 'viral', 'viralidad', 'watch_time',
    'impression', 'impresiones', 'ctr', 'feed', 'time_in_app', 'notification',
    'notificacion', 'streak', 'racha', 'like_count', 'me_gusta', 'follower', 'seguidores',
    'retencion',
]

# Known descriptive output schemas — the oracle's own knowledge of each module's LEGAL output shape
# (the VE wire, probed live against the real modules and frozen here). A silent per-person scalar
# (e.g. a 'reachability' table that carries no forbidden substring) shows up as a key OUTSIDE this
# closed schema — that is how T-A1 catches it structurally, not by name.
_TOP_SCHEMA = {
    "admitir": {"sala", "celula_id", "interaccion_id", "expira_en", "admitido", "traza_auditoria"},
    "consultar": {"consultante", "objetivo", "celula_id", "desde_tu_posicion", "veredicto",
                  "nota", "traza_auditoria"},
    "emparejar": {"consultante", "celulas_ids", "propuestas", "veredicto", "nota",
                  "traza_auditoria"},
    "resolver": {"campana_id", "celula_id", "estado", "comprometidos_distintos", "umbral",
                 "expira_en", "moneda", "resolucion", "traza_auditoria"},
    "sentir": {"celula_id", "ahora", "sentidas", "veredicto", "nota", "traza_auditoria"},
    "decidir": {"circulo_id", "propuesta_id", "veredicto", "objeciones_primordiales",
                "inquietudes", "nota", "expira_en", "traza_auditoria"},
}
_FROM_POSITION_SCHEMA = {"alcanzable", "saltos_minimos", "rutas_de_aval",
                         "avalado_por_gente_de_tu_confianza", "hechos"}


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


def _contains_str(obj, needle: str) -> bool:
    if isinstance(obj, str):
        return obj == needle
    if isinstance(obj, dict):
        return any(_contains_str(k, needle) or _contains_str(v, needle) for k, v in obj.items())
    if isinstance(obj, (list, tuple)):
        return any(_contains_str(it, needle) for it in obj)
    return False


def _unexpired(expires_at, now) -> bool:
    return expires_at is None or expires_at > now


def _window_bucket(created_at: int, now: int, window: int) -> int:
    elapsed = now - created_at
    if elapsed <= window:
        return 0
    return 1 + (elapsed - window - 1) // window


class C2CTrackA(TrackA):
    def measure(self, trace: Sequence[TraceEvent]) -> IntegrityReport:
        calls = [(e, e.result) for e in trace if isinstance(e.result, ModuleCall)]

        v1, t1 = Verdict.PASS, None   # no_person_scalar
        v2, t2 = Verdict.PASS, None   # no_market_leak
        v3, t3 = Verdict.PASS, None   # asker_relative
        v4, t4 = Verdict.PASS, None   # forgetting
        v5, t5 = Verdict.PASS, None   # consent_privacy
        v6, t6 = Verdict.PASS, None   # anti_cascade

        for event, mc in calls:
            out = mc.output
            if isinstance(out, Rejected):
                # the module's own wall fired — nothing was emitted; oracles judge only what a
                # SUCCESSFUL call returned (a bypassed wall is exactly what they must catch).
                continue

            # T-A1: no surveillance-shaped key AND no out-of-schema (person-scalar) key emitted.
            if v1 is Verdict.PASS:
                hit = _find_key(out, FORBIDDEN_KEYS + ENGAGEMENT_KEYS)
                if hit is not None:
                    v1, t1 = Verdict.FAIL, {"kind": "forbidden_key_in_output",
                                            "method": mc.method, "key": hit}
                else:
                    extra = set(out) - _TOP_SCHEMA.get(mc.method, set(out))
                    if extra:
                        v1, t1 = Verdict.FAIL, {"kind": "out_of_schema_output",
                                                "method": mc.method, "extra": sorted(extra)}
                    elif mc.method == "consultar":
                        fp = out.get("desde_tu_posicion", {})
                        fextra = set(fp) - _FROM_POSITION_SCHEMA
                        if fextra:
                            v1, t1 = Verdict.FAIL, {"kind": "person_scalar_leak",
                                                    "method": "consultar", "extra": sorted(fextra)}

            # T-A2: an admitted interaction in a non-market room must carry no market/reciprocity key.
            if v2 is Verdict.PASS and mc.method == "admitir" and out.get("admitido") is True:
                sala = mc.request.get("sala")
                carga = mc.request.get("carga", {})
                if sala in ("don_comunal", "igualdad"):
                    hit = _find_key(carga, MARKET_KEYS)
                    if hit is None and sala == "don_comunal":
                        hit = _find_key(carga, RECIPROCITY_LEDGER_KEYS)
                    if hit is not None:
                        v2, t2 = Verdict.FAIL, {"kind": "market_leak_admitted",
                                                "sala": sala, "key": hit,
                                                "interaccion_id": mc.request.get("interaccion_id")}

            # T-A3: every returned vouch-path is asker-relative: starts at the asker, ends at target.
            if v3 is Verdict.PASS and mc.method == "consultar":
                asker = out.get("consultante")
                target = out.get("objetivo")
                for path in out.get("desde_tu_posicion", {}).get("rutas_de_aval", []):
                    if not path or path[0] != asker or path[-1] != target:
                        v3, t3 = Verdict.FAIL, {"kind": "position_independent_path",
                                                "consultante": asker, "objetivo": target,
                                                "path": path}
                        break

            # T-A4: forgetting — no expired vouch/fact may surface at request['ahora'].
            if v4 is Verdict.PASS and mc.method == "consultar":
                now = mc.request.get("ahora")
                graph = mc.request.get("grafo", {})
                cell = mc.request.get("celula_id")
                live_edges = {(v["de"], v["a"]) for v in graph.get("avales", [])
                              if v.get("celula_id") == cell and _unexpired(v.get("expira_en"), now)}
                for path in out.get("desde_tu_posicion", {}).get("rutas_de_aval", []):
                    for a, b in zip(path, path[1:]):
                        if (a, b) not in live_edges:
                            v4, t4 = Verdict.FAIL, {"kind": "expired_or_off_cell_edge_surfaced",
                                                    "edge": [a, b], "ahora": now}
                            break
                    if v4 is Verdict.FAIL:
                        break
                if v4 is Verdict.PASS:
                    for f in out.get("desde_tu_posicion", {}).get("hechos", []):
                        if not _unexpired(f.get("expira_en"), now):
                            v4, t4 = Verdict.FAIL, {"kind": "expired_fact_surfaced",
                                                    "fact": f, "ahora": now}
                            break

            # T-A5: governance surfaces reasons, never objector tokens.
            if v5 is Verdict.PASS and mc.method == "decidir":
                objectors = [d.get("ficha") for d in mc.request.get("posturas", [])
                             if d.get("postura") == "objetar"]
                for tok in objectors:
                    if tok is not None and _contains_str(out, tok):
                        v5, t5 = Verdict.FAIL, {"kind": "objector_token_leaked", "ficha": tok}
                        break

            # T-A6: a stigmergy burst over the velocity cap must be throttled
            # (amortiguadas_velocidad > 0).
            if v6 is Verdict.PASS and mc.method == "sentir":
                now = mc.request.get("ahora")
                window = mc.request.get("ventana")
                cap = mc.request.get("tope_velocidad")
                cell = mc.request.get("celula_id")
                groups: dict[tuple, int] = {}
                for tr in mc.request.get("trazas", []):
                    if tr.get("celula_id") != cell:
                        continue
                    if tr.get("creado_en", 0) > now:
                        continue
                    if tr.get("senal") == "bandera" and not (tr.get("contexto") or ""):
                        continue
                    key = (tr.get("about"), _window_bucket(tr["creado_en"], now, window))
                    groups[key] = groups.get(key, 0) + 1
                burst = any(n > cap for n in groups.values())
                if burst and out["traza_auditoria"].get("amortiguadas_velocidad", 0) <= 0:
                    v6, t6 = Verdict.FAIL, {"kind": "unthrottled_burst",
                                            "groups": {str(k): n for k, n in groups.items()},
                                            "cap": cap}

        results = {
            "no_person_scalar": InvariantResult(verdict=v1, exploit_trace=t1),
            "no_market_leak": InvariantResult(verdict=v2, exploit_trace=t2),
            "asker_relative": InvariantResult(verdict=v3, exploit_trace=t3),
            "forgetting": InvariantResult(verdict=v4, exploit_trace=t4),
            "consent_privacy": InvariantResult(verdict=v5, exploit_trace=t5),
            "anti_cascade": InvariantResult(verdict=v6, exploit_trace=t6),
        }
        return IntegrityReport(results=results)
