# -*- coding: utf-8 -*-
"""Aceptación de D6 — salida con saldo (TB.6).

AC-7 (la puerta), AC-d68.1/2/3/4/6/7/8/10. D8 (`puente.pausar()`) NO entra en este nodo:
sale a TB.6b con dep M9 explícita — ver `DESIGN-TB6.md` §0. Los AC de la pausa (AC-d68.5,
AC-d68.9 y las filas 1–2 de AC-d68.8) se escriben allí, no aquí: un test de la pausa hoy sería
un test de código que no existe.
"""

import ast
import copy
import importlib.util
import inspect
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

led = _load("mutual_credit_ledger_d6", "src/ledger/mutual_credit_ledger.py")


# ── Fixture ───────────────────────────────────────────────────────────────────────────────
# El fixture es el PISO: los saldos se construyen por la puerta (obligación + liquidación),
# jamás escribiendo `balance_cents` a mano. Un fixture que muta el estado directamente prueba
# que el motor acepta un estado que el motor no pudo haber producido.
#
# A = el que se va · B = su contraparte · F = el fondo · V = el avalista.

def _celula(**lineas):
    params = {
        "neg_line_bp": 100,
        "pos_line_bp": 1000,
        "velocity_window_s": 86400,
        "velocity_max_cents": 5_000_000,
        "moneda": "USD",
        "sal_seudonimo": "sal-secreta-xyz",
        "paused": False
    }
    state, ev = led.create_cell("cel-d6", params, "comite", 1000)
    eventos = [ev]
    ts = 1000
    for mid in ("A", "B", "F", "V"):
        ts += 1
        miembro = {"id": mid, "turnover_cents": 100_000_000}
        miembro.update(lineas.get(mid, {}))
        state, ev = led.add_member(state, miembro, "comite", ts)
        eventos.append(ev)
    return state, eventos


def _mover(state, eventos, deudor, acreedor, cents, ts):
    """Deja al acreedor en +cents y al deudor en -cents, POR LA PUERTA."""
    ob_id = f"o-{deudor}{acreedor}-{ts}"
    state, ev = led.record_obligation(
        state, {"id": ob_id, "debtor": deudor, "creditor": acreedor, "amount_cents": cents}, ts)
    eventos.append(ev)
    state, ev = led.settle_obligation(state, ob_id, cents, ts + 1)
    eventos.append(ev)
    return state, eventos


def _saldos(state):
    return {mid: m["balance_cents"] for mid, m in state["members"].items()}


# ── AC-7 — las operaciones nuevas pasan por la puerta existente (EL QUE IMPORTA) ───────────

@pytest.mark.parametrize("malo", [None, "", 123, [], {}])
def test_ac_7_1_ratified_by_obligatorio(malo):
    """AC-7(1) — `member_exited` está en `ratification_kinds`: sin ratificador, no hay salida."""
    state, _ = _celula()
    with pytest.raises(ValueError, match="ratified_by"):
        led.salida_con_saldo(state, "A", {"tipo": "simple"}, malo, 2000)


def test_ac_7_1_ratified_by_ausente():
    """AC-7(1) — y tampoco cuela un payload SIN la clave (la vía del evento fabricado)."""
    state, _ = _celula()
    with pytest.raises(ValueError, match="ratified_by"):
        led._apply(state, "member_exited",
                   {"member_id": "A", "resolucion": {"tipo": "simple"}}, 2000)


def test_ac_7_2_evento_encadenado():
    """AC-7(2) — el evento encadena: `prev_hash` == head previo y `seq` == prev+1."""
    state, _ = _celula()
    head_previo = state["head_hash"]
    seq_previo = state["seq"]
    nuevo, ev = led.salida_con_saldo(state, "A", {"tipo": "simple"}, "comite", 2000)
    assert ev["prev_hash"] == head_previo
    assert ev["seq"] == seq_previo + 1
    assert ev["kind"] == "member_exited"
    assert nuevo["head_hash"] == ev["hash"]


def test_ac_7_3_replay_reconstruye_byte_a_byte():
    """AC-7(3) — EL TEST QUE CIERRA F-d68.1: `replay` reconstruye el estado byte a byte.

    Una helper que mutara `state` directamente no podría producir un stream que `replay`
    reconstruya, porque no habría pasado por `_apply`. No hace falta prohibir la helper: basta
    con hacer imposible que su resultado pase.
    """
    state, eventos = _celula()
    state, eventos = _mover(state, eventos, "B", "A", 5000, 1010)
    state, ev = led.salida_con_saldo(
        state, "A", {"tipo": "liquidacion_puente", "fondo": "F"}, "comite", 2000)
    eventos.append(ev)

    led.verify_chain(eventos)
    reconstruido = led.replay(eventos)
    assert led.canonical(reconstruido) == led.canonical(state)


def test_ac_7_4_ts_monotono():
    """AC-7(4) — la monotonía heredada de `ts` cubre al kind nuevo sin código nuevo."""
    state, _ = _celula()
    with pytest.raises(ValueError, match="ts"):
        led.salida_con_saldo(state, "A", {"tipo": "simple"}, "comite", state["last_ts"] - 1)


def test_ac_7_5_cortafuegos_paused():
    """AC-7(5) — con la célula pausada (inv. 8) no hay salida: el cortafuegos heredado manda."""
    state, _ = _celula()
    state, _ev = led.pause_cell(state, "comite", 1500)
    with pytest.raises(ValueError, match="paused"):
        led.salida_con_saldo(state, "A", {"tipo": "simple"}, "comite", 2000)


# ── AC-d68.1 — cero helpers directas ──────────────────────────────────────────────────────

def test_ac_d68_1_cero_helpers_directas():
    """AC-d68.1 — por AST: ninguna función pública muta `state`; toda mutación va por `_apply`.

    Un test de la palabra `salida_con_saldo` solo cazaría a quien se llame así. El muro es la
    FORMA: (a) nadie asigna dentro del `state` que recibe, y (b) todo lo que devuelve el par
    canónico `(state, event)` lo produce llamando a `_apply`.
    """
    arbol = ast.parse((_BASE / "src/ledger/mutual_credit_ledger.py").read_text(encoding="utf-8"))
    publicas = [n for n in arbol.body
                if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")]
    assert publicas, "no se enumeró nada — el AST no está leyendo el módulo"

    for fn in publicas:
        args = {a.arg for a in fn.args.args}
        if "state" not in args:
            continue

        # (a) Nadie escribe dentro del `state` del llamador. `to_clearing_input` copia primero
        #     (`state_cp`), y esa raíz distinta es justamente la diferencia que importa.
        for nodo in ast.walk(fn):
            objetivos = []
            if isinstance(nodo, ast.Assign):
                objetivos = nodo.targets
            elif isinstance(nodo, (ast.AugAssign, ast.AnnAssign)):
                objetivos = [nodo.target]
            for t in objetivos:
                raiz = t
                while isinstance(raiz, (ast.Subscript, ast.Attribute)):
                    raiz = raiz.value
                if isinstance(raiz, ast.Name) and raiz.id == "state" \
                        and isinstance(t, (ast.Subscript, ast.Attribute)):
                    pytest.fail(f"{fn.name}: muta `state` directamente (F-d68.1)")

        # (b) Si devuelve el par canónico, lo devuelve porque llamó a `_apply`.
        devuelve_par = (isinstance(fn.returns, ast.Subscript)
                        and ast.unparse(fn.returns).startswith("tuple["))
        if devuelve_par:
            llama_apply = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                              and n.func.id == "_apply" for n in ast.walk(fn))
            assert llama_apply, f"{fn.name}: devuelve (state, event) sin pasar por `_apply`"


# ── AC-d68.2 — L1 se conserva en toda salida (C-d68.2) ─────────────────────────────────────

def test_ac_d68_2_simple():
    """AC-d68.2 fila 1 — `simple`: saldo 0, nadie cambia."""
    state, eventos = _celula()
    antes = _saldos(state)
    state, _ev = led.salida_con_saldo(state, "A", {"tipo": "simple"}, "comite", 2000)
    assert _saldos(state) == antes == {"A": 0, "B": 0, "F": 0, "V": 0}
    assert led.cell_metrics(state)["sum_balances_cents"] == 0


def test_ac_d68_2_liquidacion_puente():
    """AC-d68.2 fila 2 — `liquidacion_puente`: el saliente a 0, el FONDO hereda su saldo.

    RECONCILIACIÓN (DESIGN §2.1): la fila de AC-d68.2 dice «fondo −5000» y eso ROMPE L1 —
    que es el invariante que ese mismo AC existe para probar. A tenía +5000 y B −5000; si A
    pasa a 0 y F a −5000, la suma es −10000. El AC se contradice a sí mismo, y entre su
    cabecera (`sum == 0`) y su ilustración manda la cabecera: la ilustración es un signo
    volteado, igual que el vector de AC-d5.2 en TB.5.

    Lo que pasa de verdad: el fondo le paga al saliente FUERA del motor (en USDT) y adentro
    HEREDA su acreencia → F = +5000. Es la misma regla que el avalista, con el signo que toque.
    """
    state, eventos = _celula()
    state, eventos = _mover(state, eventos, "B", "A", 5000, 1010)
    assert _saldos(state) == {"A": 5000, "B": -5000, "F": 0, "V": 0}

    state, _ev = led.salida_con_saldo(
        state, "A", {"tipo": "liquidacion_puente", "fondo": "F"}, "comite", 2000)

    assert _saldos(state) == {"A": 0, "B": -5000, "F": 5000, "V": 0}
    assert sum(_saldos(state).values()) == 0
    assert led.cell_metrics(state)["sum_balances_cents"] == 0


def test_ac_d68_2_absorcion_avalista():
    """AC-d68.2 fila 3 — `absorcion_avalista`: el saliente a 0, el avalista hereda su −3000."""
    state, eventos = _celula()
    state, eventos = _mover(state, eventos, "A", "B", 3000, 1010)
    assert _saldos(state) == {"A": -3000, "B": 3000, "F": 0, "V": 0}

    state, _ev = led.salida_con_saldo(
        state, "A", {"tipo": "absorcion_avalista", "avalista": "V"}, "comite", 2000)

    assert _saldos(state) == {"A": 0, "B": 3000, "F": 0, "V": -3000}
    assert sum(_saldos(state).values()) == 0
    assert led.cell_metrics(state)["sum_balances_cents"] == 0


def test_ac_d68_2_plan_de_pago_no_mueve_el_saldo():
    """AC-d68.2 fila 4 — `plan_de_pago` NO mueve nada (F-d68.8).

    El plan de pago es un acuerdo FUERA del motor. «Provisionar» o «reservar» el saldo negativo
    sería inventar un asiento: el negativo sigue ahí, en un miembro `exited`, porque esa es la
    verdad.
    """
    state, eventos = _celula()
    state, eventos = _mover(state, eventos, "A", "B", 3000, 1010)

    state, _ev = led.salida_con_saldo(
        state, "A", {"tipo": "plan_de_pago", "plazo_meses": 6}, "comite", 2000)

    assert _saldos(state) == {"A": -3000, "B": 3000, "F": 0, "V": 0}
    assert state["members"]["A"]["status"] == "exited"
    assert led.cell_metrics(state)["sum_balances_cents"] == 0


# ── AC-d68.3 / AC-d68.6 — la contraparte no se atropella (M6: flag/reject, jamás clamp) ────

def test_ac_d68_3_avalista_no_se_atropella():
    """AC-d68.3 — absorber empujaría al avalista fuera de sus líneas → ValueError NOMBRÁNDOLO,
    y el estado del llamador queda INTACTO. Nunca se recorta (M6/F-d68.5): un avalista empujado
    fuera de sus líneas «porque alguien se fue» es contagio, y el impago es contagioso (U2).
    """
    state, eventos = _celula(V={"credit_min_cents": -1000})
    state, eventos = _mover(state, eventos, "A", "B", 3000, 1010)
    antes = copy.deepcopy(state)

    with pytest.raises(ValueError, match="^V$"):
        led.salida_con_saldo(
            state, "A", {"tipo": "absorcion_avalista", "avalista": "V"}, "comite", 2000)

    assert led.canonical(state) == led.canonical(antes)


def test_ac_d68_6_el_fondo_es_un_miembro_con_lineas():
    """AC-d68.6 (fija ST-d68.1) — el fondo sin línea ES la verdad: no da abasto.

    La respuesta es capitalizarlo, no recortar el check.
    """
    state, eventos = _celula(F={"credit_max_cents": 1000})
    state, eventos = _mover(state, eventos, "B", "A", 5000, 1010)
    antes = copy.deepcopy(state)

    with pytest.raises(ValueError, match="^F$"):
        led.salida_con_saldo(
            state, "A", {"tipo": "liquidacion_puente", "fondo": "F"}, "comite", 2000)

    assert led.canonical(state) == led.canonical(antes)


def test_ac_d68_3_control_negativo_el_avalista_que_si_cabe():
    """CONTROL NEGATIVO — prueba la ADMISIÓN, no solo el rechazo.

    Un check que rechazara SIEMPRE pasaría los dos tests de arriba y mataría al paciente
    (F-d9.1). Con la línea justa (−3000 cabe en credit_min=−3000, el borde inclusive), absorbe.
    """
    state, eventos = _celula(V={"credit_min_cents": -3000})
    state, eventos = _mover(state, eventos, "A", "B", 3000, 1010)

    state, _ev = led.salida_con_saldo(
        state, "A", {"tipo": "absorcion_avalista", "avalista": "V"}, "comite", 2000)

    assert _saldos(state)["V"] == -3000


@pytest.mark.parametrize("estado_malo", ["suspended", "expelled"])
def test_ac_d68_3_avalista_en_la_escalera_no_absorbe(estado_malo):
    """AC-d68.3 — un avalista sancionado no absorbe: sería contagio hacia quien ya está en la
    escalera. Se sube peldaño a peldaño porque la escalera valida saltos de uno (inv. 5).
    """
    state, eventos = _celula()
    state, eventos = _mover(state, eventos, "A", "B", 3000, 1010)
    ts = 1500
    for peldano in ["warned", "line_reduced", "suspended", "expelled"]:
        state, _ = led.update_member(state, "V", {"status": peldano}, "comite", ts)
        ts += 1
        if peldano == estado_malo:
            break

    with pytest.raises(ValueError, match="avalista"):
        led.salida_con_saldo(
            state, "A", {"tipo": "absorcion_avalista", "avalista": "V"}, "comite", 2000)


def test_ac_d68_3_avalista_ya_exited_no_absorbe():
    """AC-d68.3 — ni un avalista que ya se fue. `exited` no está en la escalera, así que este
    caso no lo cubre el test de arriba: hay que ejercerlo aparte.
    """
    state, eventos = _celula()
    state, eventos = _mover(state, eventos, "A", "B", 3000, 1010)
    state, _ = led.salida_con_saldo(state, "V", {"tipo": "simple"}, "comite", 1500)

    with pytest.raises(ValueError, match="avalista"):
        led.salida_con_saldo(
            state, "A", {"tipo": "absorcion_avalista", "avalista": "V"}, "comite", 2000)


@pytest.mark.parametrize("resolucion,clave", [
    ({"tipo": "absorcion_avalista", "avalista": "NO-EXISTE"}, "avalista"),
    ({"tipo": "absorcion_avalista", "avalista": "A"}, "avalista"),
    ({"tipo": "liquidacion_puente", "fondo": "NO-EXISTE"}, "fondo"),
    ({"tipo": "liquidacion_puente", "fondo": "A"}, "fondo"),
])
def test_ac_d68_3_contraparte_inexistente_o_uno_mismo(resolucion, clave):
    """AC-d68.3 — contraparte inexistente, o el propio saliente (auto-absorción: el saldo se
    evaporaría conservando L1 por accidente, que es F-d68.2 con disfraz).
    """
    state, eventos = _celula()
    state, eventos = _mover(state, eventos, "A", "B", 3000, 1010)
    with pytest.raises(ValueError, match=clave):
        led.salida_con_saldo(state, "A", resolucion, "comite", 2000)


# ── AC-d68.4 — `exited` no es una sanción (C-d68.3) ────────────────────────────────────────

@pytest.mark.parametrize("origen", ["active", "warned", "line_reduced", "suspended", "expelled"])
def test_ac_d68_4_update_member_no_llega_a_exited(origen):
    """AC-d68.4 — a `exited` NO se llega por la escalera DESDE NINGÚN PELDAÑO.

    DESCUBIERTO POR MUTACIÓN, y es el hallazgo del nodo: la versión de este test que solo
    probaba desde `active` PASABA con `exited` metido dentro de la escalera — pero por la razón
    EQUIVOCADA. Desde `active`, `exited` es un salto de cinco peldaños, así que lo rechazaba la
    regla de «un solo peldaño» (inv. 5), no la regla que este AC existe para fijar. El
    ValueError decía `status` en los dos mundos y el `match=` no los distinguía.
    Desde `expelled`, en cambio, `exited` sería un salto de UN peldaño: legal, silencioso, y
    justo F-d68.3 — el emigrante convertido en el último grado de la escalera sancionadora.
    Por eso se recorre la escalera ENTERA: el peldaño que importa es el último, no el primero.
    """
    state, _ = _celula()
    ts = 1500
    for peldano in ["warned", "line_reduced", "suspended", "expelled"]:
        if origen == "active":
            break
        state, _ = led.update_member(state, "A", {"status": peldano}, "comite", ts)
        ts += 1
        if peldano == origen:
            break
    assert state["members"]["A"]["status"] == origen

    with pytest.raises(ValueError, match="status"):
        led.update_member(state, "A", {"status": "exited"}, "comite", ts)
    assert state["members"]["A"]["status"] == origen


@pytest.mark.parametrize("destino", ["active", "warned", "line_reduced", "suspended", "expelled"])
def test_ac_d68_4_exited_es_terminal(destino):
    """AC-d68.4 — de `exited` no se sale a ningún estado: es terminal.

    `match="exited"` a propósito: hoy `ladder.index()` también lanzaría ValueError, pero por
    accidente y con otro mensaje. Un rechazo accidental no es un rechazo diseñado.
    """
    state, _ = _celula()
    state, _ = led.salida_con_saldo(state, "A", {"tipo": "simple"}, "comite", 2000)
    with pytest.raises(ValueError, match="exited"):
        led.update_member(state, "A", {"status": destino}, "comite", 2001)


def test_ac_d68_4_el_emigrante_no_queda_marcado_como_moroso():
    """AC-d68.4 — tras la salida el estado es `exited`, NUNCA `expelled` (F-d68.3).

    La cadena es append-only: si aquí pusiera `expelled`, quedaría para siempre escrito que a
    quien se mudó a Bogotá lo EXPULSARON, y esa marca viaja a cualquier federación futura (U1).
    """
    state, _ = _celula()
    state, _ = led.salida_con_saldo(state, "A", {"tipo": "simple"}, "comite", 2000)
    assert state["members"]["A"]["status"] == "exited"
    assert state["members"]["A"]["status"] != "expelled"


def test_ac_d68_4_la_escalera_heredada_sigue_intacta():
    """AC-d68.4 — la escalera sancionadora no se tocó: un peldaño sí, dos no (AC-L9)."""
    state, _ = _celula()
    state, _ = led.update_member(state, "B", {"status": "warned"}, "comite", 2000)
    assert state["members"]["B"]["status"] == "warned"
    with pytest.raises(ValueError, match="status"):
        led.update_member(state, "B", {"status": "expelled"}, "comite", 2001)


def test_ac_d68_4_las_lineas_de_un_exited_siguen_ajustandose():
    """CONTROL NEGATIVO de la terminalidad — «terminal» habla de ESTADOS.

    Un check que rechazara TODO `update_member` sobre un `exited` pasaría los tests de arriba.
    La spec dice «no puede llegar a él ni salir de él»: eso es el status, no las líneas.
    """
    state, _ = _celula()
    state, _ = led.salida_con_saldo(state, "A", {"tipo": "simple"}, "comite", 2000)
    state, _ = led.update_member(state, "A", {"credit_max_cents": 1}, "comite", 2001)
    assert state["members"]["A"]["credit_max_cents"] == 1
    assert state["members"]["A"]["status"] == "exited"


# ── AC-d68.8 (parcial) — reversibilidad. Las filas del puente van en TB.6b ─────────────────

def test_ac_d68_8_una_salida_no_se_repite():
    """AC-d68.8 fila 4 — `salida_con_saldo` sobre un `exited` → ValueError.

    No es reversible y no se le añade un `undo` (N-d68.5): mueve valor y cierra una cuenta. Se
    corrige con asientos nuevos, como los asientos — no borrando la historia de una cadena
    append-only.
    """
    state, _ = _celula()
    state, _ = led.salida_con_saldo(state, "A", {"tipo": "simple"}, "comite", 2000)
    with pytest.raises(ValueError, match="exited"):
        led.salida_con_saldo(state, "A", {"tipo": "simple"}, "comite", 2001)


# ── AC-d68.10 — un `exited` no recibe obligaciones nuevas, pero paga las suyas ─────────────

@pytest.mark.parametrize("papel", ["debtor", "creditor"])
def test_ac_d68_10_un_exited_no_recibe_obligaciones_nuevas(papel):
    """AC-d68.10 — sale gratis del filtro de estado heredado (ST-d68.4). El test lo FIJA para
    que nadie lo «arregle» metiendo `exited` en el conjunto de estados operativos.
    """
    state, _ = _celula()
    state, _ = led.salida_con_saldo(state, "A", {"tipo": "simple"}, "comite", 2000)
    ob = {"id": "o-nueva", "debtor": "A", "creditor": "B", "amount_cents": 1000}
    if papel == "creditor":
        ob = {"id": "o-nueva", "debtor": "B", "creditor": "A", "amount_cents": 1000}
    with pytest.raises(ValueError, match="^A$"):
        led.record_obligation(state, ob, 2001)


def test_ac_d68_10_un_exited_paga_lo_que_debe():
    """AC-d68.10 — herencia LITERAL: «sanctions never trap debt; paying what you owe is always
    legal». La obligación abierta de quien se fue se liquida con normalidad.
    """
    state, eventos = _celula()
    state, ev = led.record_obligation(
        state, {"id": "o-vieja", "debtor": "A", "creditor": "B", "amount_cents": 3000}, 1010)
    state, _ = led.salida_con_saldo(
        state, "A", {"tipo": "plan_de_pago", "plazo_meses": 6}, "comite", 2000)

    state, _ = led.settle_obligation(state, "o-vieja", 3000, 2001)

    assert _saldos(state) == {"A": -3000, "B": 3000, "F": 0, "V": 0}
    assert "o-vieja" not in state["obligations"]


# ── AC-d68.7 — el motor no liquida ────────────────────────────────────────────────────────

def test_ac_d68_7_el_motor_no_liquida(monkeypatch):
    """AC-d68.7 — `liquidacion_puente` no toca red ni disco: REGISTRA que se liquidó, no liquida.

    N-d68.2/N9 (F-d68.6): «el motor debería mandar el USDT» le daría al motor claves, red y una
    dirección que congelar. El núcleo solo registra la obligación saldada (§3.2).
    """
    import builtins
    import socket

    def _prohibido(*a, **k):
        raise AssertionError("el motor tocó red o disco durante una liquidación")

    monkeypatch.setattr(socket, "socket", _prohibido)
    monkeypatch.setattr(socket, "create_connection", _prohibido)
    monkeypatch.setattr(builtins, "open", _prohibido)

    state, eventos = _celula()
    state, eventos = _mover(state, eventos, "B", "A", 5000, 1010)
    state, ev = led.salida_con_saldo(
        state, "A", {"tipo": "liquidacion_puente", "fondo": "F"}, "comite", 2000)

    assert _saldos(state)["F"] == 5000
    assert ev["kind"] == "member_exited"


def test_ac_d68_7_sin_spreads_ni_direcciones_ni_claves():
    """AC-d68.7 — por AST sobre la función, no por grep de palabras.

    N-d68.3: ningún spread ni tasa hardcodeados — ni USDT es un dólar perfecto (primas P2P de
    hasta ~40% en pánico); los spreads son decisión humana (§2.4/N-d1.5). El muro es el DATO:
    el saldo del saliente llega a la contraparte SIN pasar por una multiplicación. Un test de
    la palabra «spread» solo caza a quien la escriba (lección de TB.7/TB.5).
    """
    fuente = inspect.getsource(led._apply)
    arbol = ast.parse(fuente.strip())

    rama = None
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Compare) and ast.unparse(nodo) == "kind == 'member_exited'":
            rama = nodo
    assert rama is not None, "no se localizó la rama `member_exited` — el AST no está leyendo nada"

    # La rama entera: desde el `elif` hasta el siguiente. Se busca sobre el `If` que la contiene.
    contenedor = None
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.If) and ast.unparse(nodo.test) == "kind == 'member_exited'":
            contenedor = nodo
    assert contenedor is not None

    for nodo in ast.walk(contenedor):
        if isinstance(nodo, ast.BinOp) and isinstance(nodo.op, (ast.Mult, ast.Div, ast.FloorDiv)):
            pytest.fail(f"aritmética de escala en la salida: `{ast.unparse(nodo)}` — ¿un spread? "
                        f"El saldo se hereda íntegro; escalarlo es decisión humana (N-d68.3)")
        if isinstance(nodo, ast.Constant) and isinstance(nodo.value, float):
            pytest.fail(f"literal flotante `{nodo.value}` en la salida — ¿una tasa? (N-d68.3)")


# ── Esquema cerrado de la `resolucion` (C-d68.6 / F-d68.7) ─────────────────────────────────

@pytest.mark.parametrize("resolucion", [
    None, "simple", 42, [],
    {},
    {"tipo": "desconocido"},
    {"tipo": "liquidacion_puente"},                       # falta el fondo (DESIGN §2.1)
    {"tipo": "absorcion_avalista"},                       # falta el avalista
    {"tipo": "plan_de_pago"},                             # falta el plazo
    {"tipo": "simple", "fondo": "F"},                     # clave de más
    {"tipo": "plan_de_pago", "plazo_meses": 6, "nota": "x"},
    {"tipo": "liquidacion_puente", "avalista": "V"},      # la clave del otro tipo
])
def test_esquema_cerrado_de_resolucion(resolucion):
    """La `resolucion` es un esquema CERRADO, como los del ledger: lista blanca por tipo.

    `allowed_keys` es la defensa más fuerte que hay (AC-d9.6) y aquí se aplica igual. Una clave
    de más no se ignora en silencio: el comité que teclea `avalista` en una liquidación de
    puente está diciendo algo que el motor no va a hacer, y tiene que enterarse.
    """
    state, _ = _celula()
    with pytest.raises(ValueError, match="resolucion"):
        led.salida_con_saldo(state, "A", resolucion, "comite", 2000)


@pytest.mark.parametrize("plazo", [0, -6, 1.5, True, None, "6"])
def test_plazo_de_pago_valido(plazo):
    """`plazo_meses` es un entero estricto y positivo. `True` es un `int` en Python y NO es un
    plazo: `_is_strict_int` es la maquinaria heredada que ya lo sabe.
    """
    state, _ = _celula()
    with pytest.raises(ValueError, match="plazo_meses"):
        led.salida_con_saldo(
            state, "A", {"tipo": "plan_de_pago", "plazo_meses": plazo}, "comite", 2000)


def test_simple_exige_saldo_cero():
    """`simple` es la salida LIMPIA, y limpia significa cero (DESIGN §2.2).

    Si aceptara un saldo distinto de 0, la única forma de conservar L1 sería no tocarlo — y eso
    ya es `plan_de_pago`, con otro nombre y sin plazo. Dos nombres para un hecho es la
    discrepancia esperando a pasar.
    """
    state, eventos = _celula()
    state, eventos = _mover(state, eventos, "B", "A", 5000, 1010)
    with pytest.raises(ValueError, match="resolucion"):
        led.salida_con_saldo(state, "A", {"tipo": "simple"}, "comite", 2000)


def test_el_motor_no_deduce_la_resolucion_del_signo():
    """C-d68.6/F-d68.7 — el motor NO adivina.

    Un saldo positivo resuelto con `plan_de_pago` es LEGAL: el motor no vigila que la resolución
    sea la «obvia» — vigila L1, L2 y que la haya ratificado alguien. Deducirla del signo sería
    que el motor decide cómo se resuelve una salida, con consecuencias sobre un avalista que no
    está en la sala.
    """
    state, eventos = _celula()
    state, eventos = _mover(state, eventos, "B", "A", 5000, 1010)
    state, _ = led.salida_con_saldo(
        state, "A", {"tipo": "plan_de_pago", "plazo_meses": 3}, "comite", 2000)
    assert _saldos(state) == {"A": 5000, "B": -5000, "F": 0, "V": 0}


def test_st_d68_7_la_resolucion_es_una_foto_del_saldo_no_del_compromiso():
    """ST-d68.7 — HALLAZGO NO PLANIFICADO (sonda de TB.6). Fija el comportamiento REAL.

    `salida_con_saldo` resuelve el SALDO, y una obligación en vuelo todavía no es saldo: no lo
    toca hasta que se liquida. Así que el comité puede ratificar una salida `simple` —«no debe
    nada»— de un miembro con 3000 en vuelo, y al liquidarse esa obligación el `exited` queda
    en −3000 SIN plan de pago, SIN avalista y sin que nadie haya ratificado ese hecho. L1 y L2
    se conservan; la suite queda verde. La resolución ratificada es una foto que la liquidación
    posterior falsifica.

    No es un defecto de `simple`: es de las cuatro. `absorcion_avalista` mueve el saldo del día
    T al avalista, y lo que estaba en vuelo aterriza en el saliente en T+1 — el avalista NO lo
    cubre. Igual `liquidacion_puente`.

    **No se arregla aquí, y no es dejadez.** «Prohibir salir con obligaciones en vuelo» lo
    descarta la spec: AC-d68.10 exige que un `exited` conserve sus obligaciones abiertas y las
    liquide («paying what you owe is always legal»). Y hacer que el aval cubra las liquidaciones
    futuras sería convertir un acto puntual en una GARANTÍA PERMANENTE que el avalista no
    ratificó — operación de valor sin puerta humana, la forma exacta de ST-d5.8. Las dos salidas
    son decisión de la spec, no del ejecutor (I3).

    El motor no tiene el arreglo: quien ve la cascada es el comité (ST-d68.2, misma familia).
    Este test existe para que el comportamiento sea una DECISIÓN registrada y no un accidente,
    y para que cambiarlo cueste discutirlo. → README de TB.9.
    """
    state, eventos = _celula()
    state, ev = led.record_obligation(
        state, {"id": "en-vuelo", "debtor": "A", "creditor": "B", "amount_cents": 3000}, 1010)
    assert state["members"]["A"]["balance_cents"] == 0, "en vuelo aún no es saldo"

    # El comité ratifica una salida LIMPIA — y el motor la acepta, porque el saldo es 0.
    state, _ = led.salida_con_saldo(state, "A", {"tipo": "simple"}, "comite", 2000)
    assert state["members"]["A"]["status"] == "exited"

    # …y la obligación en vuelo aterriza después, sobre un miembro que ya se fue.
    state, _ = led.settle_obligation(state, "en-vuelo", 3000, 2001)
    assert _saldos(state) == {"A": -3000, "B": 3000, "F": 0, "V": 0}
    assert led.cell_metrics(state)["sum_balances_cents"] == 0  # L1 intacta: por eso NO se ve


def test_miembro_inexistente():
    state, _ = _celula()
    with pytest.raises(ValueError, match="NO-EXISTE"):
        led.salida_con_saldo(state, "NO-EXISTE", {"tipo": "simple"}, "comite", 2000)
