"""Exportes (D7, fork VE) — registros limpios por empresa, derivados de la cadena de eventos.

COMPLIANCE-READY, NO COMPLIANCE-DEPENDENT. El upstream registraba cada transacción ante
Hacienda porque la fiscalidad española es clara. Aquí no lo es: IGTF 3% a pagos en divisas
fuera de la banca nacional, ofensiva SENIAT sobre USDT, y el tratamiento del crédito mutuo
—compensación de obligaciones— es AMBIGUO (§5). El sistema no puede depender de una claridad
fiscal que no existe.

Consecuencia: el motor da los registros; cada miembro cumple donde y como decida.
**EL SISTEMA NO DECLARA POR NADIE Y NO PROMETE NEUTRALIDAD FISCAL** (N-d7.1/N-d7.2). Si el
motor clasificara fiscalmente al miembro y la interpretación fuera incorrecta, el sistema LE
CREÓ el problema — bajo un marco ambiguo donde el riesgo es enforcement arbitrario, no
incumplimiento de una norma clara. Es la clase de decisión que I3 reserva al humano.
Por eso aquí no hay IGTF, ni `gravable`, ni base imponible, ni un porcentaje sobre un importe.
El silencio es el diseño, no un hueco: AC-d7.4 lo fija por AST sobre todo `src/`.

POR QUÉ MÓDULO NUEVO Y NO DENTRO DEL LEDGER (patrón de `anclaje.py`, TB.3): el ledger exporta
`op(state, ...) -> (new_state, event)`. `exportar_registros` no tiene esa forma —no mueve
valor, no emite evento— y meterla ahí invita a darle un `ratified_by` (F-d2.6). Dependencia de
un solo sentido (`exportes` → `ledger`), sin ciclos.

POR QUÉ DESDE LOS EVENTOS Y NO DESDE EL ESTADO (C-d7.2): un exporte fiscal es un histórico de
período; el estado es solo el presente. Un exporte de marzo con los saldos de julio CUADRA
CONSIGO MISMO Y ES FALSO (F-d7.7). Además los eventos ya están encadenados y `verify_chain` ya
los valida → el exporte hereda la verificabilidad gratis.

EL MOTOR NO ESCRIBE (C-d7.1). Devuelve la cadena; el archivo es del llamador. Mismo porqué que
`anclar`: un motor sin disco ni red corre en un apagón y no es capturable.

Señalados (N10 — no fake-resueltos):
  - El exporte es la superficie de fuga más probable, y NO por un bug: su propósito es SALIR
    del sistema (ST-d7.1). El scope protege lo que el motor devuelve; lo que el miembro haga
    con su CSV está fuera, y es correcto que pueda compartirlo.
  - `hash_evento`/`raiz_ancla` solo valen ante un tercero si la raíz se PUBLICÓ (ST-d7.2), y
    publicar está fuera del motor (ST-d2.1). Por eso `raiz_ancla` se OMITE si el llamador no
    pasa un ancla: rellenarla al vuelo daría falsa sensación de prueba.
  - Un exporte de una célula de dos identifica a la contraparte (ST-d7.3). Aritmética, no bug.
  - No se promete neutralidad fiscal: una reclasificación agresiva del SENIAT (¿cada
    compensación = pago en divisa gravable?) es escenario real (§6.7) → asesoría local, jamás
    una interpretación incrustada aquí.

Spec: B2B/workflows/micorriza-ve/d7-exportes/{spec,constraints,failure-model}.md
      B2B/workflows/micorriza-ve/d7-exportes/DESIGN-TB7.md
Acceptance: AC-7 (global), AC-d7.1..d7.10

Provenance: Opus en TB.7 (tests mecánicos con fan-out). stdlib only.
"""
import csv as _csv
import io as _io
import json as _json

import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from ledger.mutual_credit_ledger import SCOPES, _seudonimo, replay, _is_strict_int

FORMATOS = ("json", "csv")

# Prefijos que Excel interpreta como fórmula al abrir un CSV (ST-d7.4). Los `member_id` los
# eligen humanos: no es paranoia. OJO — `-` va aquí porque `-cmd` es fórmula, pero el escape
# solo se aplica a celdas de TEXTO: un importe negativo (-2500) es un número y escaparlo
# rompería AC-d7.3 (`^-?\d+$`).
_PREFIJOS_FORMULA = ("=", "+", "-", "@")

# Los tipos de evento que tocan el bolsillo de un miembro. `cell_created`/`cell_paused`/… son
# gobernanza de la célula, no registros del miembro: no van a su exporte fiscal.
_TIPOS_EXPORTABLES = ("obligation_recorded", "obligation_settled", "clearing_applied")


def _escapar_csv(valor: str) -> str:
    """Antepone `'` a una celda de TEXTO que empiece por un prefijo de fórmula (ST-d7.4)."""
    if valor and valor[0] in _PREFIJOS_FORMULA:
        return "'" + valor
    return valor


def _lineas_del_miembro(events: list, member_id: str, desde_ts: int, hasta_ts: int) -> list:
    """Las líneas del período en que `member_id` es parte. Derivado de EVENTOS (C-d7.2)."""
    lineas = []
    for ev in events:
        if not (desde_ts <= ev["ts"] <= hasta_ts):
            continue
        kind, payload = ev["kind"], ev["payload"]
        if kind not in _TIPOS_EXPORTABLES:
            continue

        if kind == "obligation_recorded":
            ob = payload["obligation"]
            if member_id not in (ob["debtor"], ob["creditor"]):
                continue
            es_deudor = ob["debtor"] == member_id
            lineas.append({
                "fecha": ev["ts"],
                "tipo": kind,
                "contraparte": ob["creditor"] if es_deudor else ob["debtor"],
                # Signo desde la posición del miembro: deber es negativo. El exporte lo lee un
                # humano que decide, y un importe sin signo obliga a deducir la dirección.
                "importe_centavos": -ob["amount_cents"] if es_deudor else ob["amount_cents"],
                "referencia": ob["id"],
                "hash_evento": ev["hash"],
            })

        elif kind == "obligation_settled":
            # La liquidación no nombra a las partes: hay que resolver la obligación por su id
            # sobre el propio stream — el exporte no puede mirar el estado (C-d7.2).
            ob = _obligacion_por_id(events, payload["obligation_id"], hasta_ts)
            if ob is None or member_id not in (ob["debtor"], ob["creditor"]):
                continue
            es_deudor = ob["debtor"] == member_id
            lineas.append({
                "fecha": ev["ts"],
                "tipo": kind,
                "contraparte": ob["creditor"] if es_deudor else ob["debtor"],
                "importe_centavos": payload["amount_cents"] if es_deudor else -payload["amount_cents"],
                "referencia": payload["obligation_id"],
                "hash_evento": ev["hash"],
            })

        elif kind == "clearing_applied":
            for tramo in payload.get("proposal", {}).get("legs", []):
                if member_id not in (tramo["debtor"], tramo["creditor"]):
                    continue
                es_deudor = tramo["debtor"] == member_id
                lineas.append({
                    "fecha": ev["ts"],
                    "tipo": kind,
                    "contraparte": tramo["creditor"] if es_deudor else tramo["debtor"],
                    "importe_centavos": tramo["amount_cents"] if es_deudor else -tramo["amount_cents"],
                    "referencia": payload.get("proposal", {}).get("id", ""),
                    "hash_evento": ev["hash"],
                })
    return lineas


def _obligacion_por_id(events: list, ob_id: str, hasta_ts: int):
    for ev in events:
        if ev["kind"] == "obligation_recorded" and ev["payload"]["obligation"]["id"] == ob_id:
            return ev["payload"]["obligation"]
    return None


def _saldo_en(events: list, member_id: str, hasta_ts: int) -> int:
    """Saldo del miembro al final de `hasta_ts`, por REPLAY del prefijo del stream.

    Reusa `replay` en vez de sumar a mano: es la maquinaria que ya reconstruye byte a byte, y
    dos formas de calcular un saldo es una que se equivoca en silencio.
    """
    prefijo = [ev for ev in events if ev["ts"] <= hasta_ts]
    if not prefijo:
        return 0
    estado = replay(prefijo)
    m = estado["members"].get(member_id)
    return 0 if m is None else m["balance_cents"]


def exportar_registros(state: dict, events: list, member_id: str, desde_ts: int, hasta_ts: int,
                       scope: str, solicitante: str | None = None, formato: str = "json",
                       ancla: dict | None = None) -> str:
    """Registros del miembro en `[desde_ts, hasta_ts]` como cadena JSON o CSV.

    `scope` es POSICIONAL OBLIGATORIO: reutiliza el de D3 (C-d7.3) — y reutilizarlo incluye
    reutilizar su porqué. La firma de la spec §2 traía `scope="miembro"` por defecto, lo que
    contradice C-d3.1 y su propio AC-d7.1 («scope ausente → ValueError»): con un default, un
    scope ausente no lanza nada. Manda el AC. Ver DESIGN-TB7 §0.1.

    `formato` sí lleva default: no es una propiedad de seguridad, es presentación.

    `ancla`: el ancla PUBLICADA del período, si la hay. El motor NO puede saber si un período
    está anclado —anclar ≠ publicar, y publicar ocurre fuera (ST-d2.1)—, así que lo dice el
    llamador. Sin ancla, la clave `raiz_ancla` NO EXISTE en la salida: no se rellena con una
    raíz calculada al vuelo, que daría falsa sensación de prueba ante un tercero (ST-d7.2).
    """
    if scope not in SCOPES:
        raise ValueError("scope")
    if formato not in FORMATOS:
        raise ValueError("formato")
    if scope == "miembro" and solicitante != member_id:
        # Misma regla que D3, sin reimplementarla: sin esto `miembro` es `publico` con otro
        # nombre (C-d3.2). Dos controles de acceso divergen — se arregla uno y el otro se queda
        # con el agujero (F-d7.5).
        raise ValueError("solicitante")
    if member_id not in state["members"]:
        raise ValueError(member_id)
    if not _is_strict_int(desde_ts) or not _is_strict_int(hasta_ts) or desde_ts > hasta_ts:
        raise ValueError("periodo")

    if scope == "publico":
        # Seudónimo de D3, REUSADO (P4). Sin identidad, sin importes individuales, sin
        # contrapartes: N7/C-d7.4 — jamás identidad + monto en claro.
        datos = {
            "celula_id": state["cell_id"],
            "seudonimo": _seudonimo(state, member_id),
            "moneda": state["params"]["moneda"],
            "periodo": [desde_ts, hasta_ts],
            "lineas": [],
        }
        return _serializar(datos, formato)

    lineas = _lineas_del_miembro(events, member_id, desde_ts, hasta_ts)
    datos = {
        "celula_id": state["cell_id"],
        "miembro_id": member_id,
        # La moneda va UNA VEZ, en la cabecera, jamás por línea (C-d7.5): una columna por línea
        # sugiere que puede variar, y la pregunta siguiente es «¿a qué tasa convierto?». El
        # formato del exporte también puede hacer representable el FX. No se le da la forma.
        "moneda": state["params"]["moneda"],
        "periodo": [desde_ts, hasta_ts],
        "saldo_inicial": _saldo_en(events, member_id, desde_ts - 1),
        "saldo_final": _saldo_en(events, member_id, hasta_ts),
        "lineas": lineas,
    }
    if ancla is not None:
        datos["raiz_ancla"] = ancla["raiz"]
    return _serializar(datos, formato)


def _serializar(datos: dict, formato: str) -> str:
    if formato == "json":
        return _json.dumps(datos, ensure_ascii=False, sort_keys=True, indent=2) + "\n"

    # CSV: cabecera como pares clave/valor y luego las líneas. Los mismos hechos que el JSON
    # (AC-d7.10): dos formatos que discrepan convierten «cuál es la verdad» en una pregunta,
    # justo en el artefacto que un miembro le presenta a un tercero.
    buf = _io.StringIO()
    w = _csv.writer(buf, lineterminator="\n")
    for clave in ("celula_id", "miembro_id", "seudonimo", "moneda", "saldo_inicial",
                  "saldo_final", "raiz_ancla"):
        if clave in datos:
            valor = datos[clave]
            w.writerow(["#", clave, _escapar_csv(valor) if isinstance(valor, str) else valor])
    w.writerow(["#", "periodo", datos["periodo"][0], datos["periodo"][1]])
    w.writerow(["fecha", "tipo", "contraparte", "importe_centavos", "referencia", "hash_evento"])
    for ln in datos["lineas"]:
        w.writerow([
            ln["fecha"], ln["tipo"], _escapar_csv(ln["contraparte"]),
            # Entero, JAMÁS cents/100 (C-d7.6/M4): el float «para que quede bonito» vuelve
            # exactamente donde el número sale del sistema y entra en una hoja de cálculo —
            # que es donde el redondeo se vuelve dinero.
            ln["importe_centavos"],
            _escapar_csv(ln["referencia"]), ln["hash_evento"],
        ])
    return buf.getvalue()
