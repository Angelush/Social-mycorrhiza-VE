# -*- coding: utf-8 -*-
"""Aceptación de D8 — pausa del puente (TB.6b).

AC-d68.5 (EL QUE IMPORTA), AC-d68.8 filas 1–2, AC-d68.9, AC-7 sobre los kinds nuevos.
El resto de D6 vive en `test_d6_salida.py`: aquí solo entra lo que la pausa añade.

Por qué D8 salió de TB.6 (DESIGN-TB6 §0, decisión humana 2026-07-15): `puente_pausar` ES el
mecanismo de respuesta a sanciones, y eso lo vigila M9. Saldado en
`docs/verificaciones/2026-07-15-sanciones.md`: el alivio va por licencia general REVOCABLE
(I-VE7 verificada, no intuida) y julio-2026 trajo designación DIRIGIDA, no snapback general —
que es exactamente el caso donde hay que parar el puente SIN matar el crédito interno. La
distinción `puente_pausado` ≠ `paused` no es una sutileza de diseño: es el delta.
"""

import importlib.util
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


led = _load("mutual_credit_ledger_d8", "src/ledger/mutual_credit_ledger.py")


# ── Fixture (el mismo patrón que D6: los saldos se construyen POR LA PUERTA) ───────────────

def _celula(**lineas):
    params = {
        "neg_line_bp": 100,
        "pos_line_bp": 1000,
        "velocity_window_s": 86400,
        "velocity_max_cents": 5_000_000,
        "moneda": "USD",
        "sal_seudonimo": "sal-secreta-xyz",
        "paused": False,
    }
    state, ev = led.create_cell("cel-d8", params, "comite", 1000)
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
    ob_id = f"o-{deudor}{acreedor}-{ts}"
    state, ev = led.record_obligation(
        state, {"id": ob_id, "debtor": deudor, "creditor": acreedor, "amount_cents": cents}, ts)
    eventos.append(ev)
    state, ev = led.settle_obligation(state, ob_id, cents, ts + 1)
    eventos.append(ev)
    return state, eventos


def _saldos(state):
    return {mid: m["balance_cents"] for mid, m in state["members"].items()}


# ── Estado inicial ────────────────────────────────────────────────────────────────────────

def test_el_puente_arranca_activo():
    """`puente_pausado` inicial `False`: una célula que arranca con el puente pausado no es una
    cosa. Es estado derivado, no configuración — como `paused`."""
    state, _ = _celula()
    assert state["params"]["puente_pausado"] is False
    assert led.cell_metrics(state)["puente_pausado"] is False


def test_create_cell_ignora_el_puente_pausado_del_llamador():
    """CORRIGE DESIGN-TB6 §7, que predijo que `puente_pausado` sería un param del llamador.

    `create_cell` reconstruye `params` clave a clave (lista blanca, la técnica de D3) y lo fija
    por su cuenta. Comprobarlo es lo que hace que el `head_hash` del golden sea invariante: si
    la clave llegara desde fuera, viajaría en el payload de `cell_created`.
    """
    params = {
        "neg_line_bp": 100, "pos_line_bp": 1000,
        "velocity_window_s": 86400, "velocity_max_cents": 5_000_000,
        "moneda": "USD", "sal_seudonimo": "sal-x",
        "puente_pausado": True,          # el llamador insiste…
        "paused": True,                  # …en las dos, y las dos se ignoran igual
    }
    state, ev = led.create_cell("cel-ignora", params, "comite", 1000)
    assert state["params"]["puente_pausado"] is False
    assert state["params"]["paused"] is False


def test_el_motor_no_inyecta_puente_pausado_en_el_evento():
    """LA NAVAJA DEL GOLDEN, y hay que decir bien POR QUÉ corta (DESIGN §1).

    Lo que mantiene invariante el `head_hash` NO es que la clave «no pueda» viajar en el evento:
    el payload de `cell_created` es el `params` del llamador **verbatim**, así que si alguien
    pasa `puente_pausado`, ahí sale. Lo que lo mantiene invariante es que **el motor no inyecta
    la clave en el payload** — la fija solo en el estado — y el flujo del golden no la pasa.

    La distinción no es pedantería: si el motor la inyectara, el head_hash cambiaría por
    construcción y la regeneración del golden dejaría de auto-verificarse, que es justo la
    ventaja que TB.2 y TB.4 no tuvieron.
    """
    params = {
        "neg_line_bp": 100, "pos_line_bp": 1000,
        "velocity_window_s": 86400, "velocity_max_cents": 5_000_000,
        "moneda": "USD", "sal_seudonimo": "sal-x",
    }
    state, ev = led.create_cell("cel-limpia", params, "comite", 1000)
    assert "puente_pausado" not in ev["payload"]["params"]   # el motor no la mete
    assert state["params"]["puente_pausado"] is False        # pero el estado la tiene


def test_el_evento_es_el_acto_y_el_estado_es_el_hecho():
    """Señalado (→ README de TB.9): un `params` con `puente_pausado: True` queda en la cadena
    aunque el motor lo haya ignorado. El evento registra lo que se PIDIÓ; el estado, lo que el
    motor DECIDIÓ. Es la misma convención que `referencias_comerciales: []` en D5, y `replay` la
    conserva — pero un auditor que lea el payload y no el estado leerá una pausa que nunca
    existió. Se fija en test para que sea decisión y no accidente.
    """
    params = {
        "neg_line_bp": 100, "pos_line_bp": 1000,
        "velocity_window_s": 86400, "velocity_max_cents": 5_000_000,
        "moneda": "USD", "sal_seudonimo": "sal-x",
        "puente_pausado": True,
    }
    state, ev = led.create_cell("cel-eco", params, "comite", 1000)
    assert ev["payload"]["params"]["puente_pausado"] is True   # el acto: se pidió
    assert state["params"]["puente_pausado"] is False          # el hecho: se ignoró
    assert led.canonical(led.replay([ev])) == led.canonical(state)


# ── AC-d68.5 — EL QUE IMPORTA ─────────────────────────────────────────────────────────────

def test_ac_d68_5_con_el_puente_pausado_el_flujo_del_piloto_CORRE_ENTERO():
    """AC-d68.5 — I-VE7: la red local sobrevive a la muerte del puente.

    Este es el test del nodo, y ejerce el flujo del piloto ENTERO a propósito, no una operación
    de muestra: la forma de F-d68.4 es que la pausa se coma el ledger, y una muestra de una
    operación no lo vería. El crédito interno es la parte robusta del sistema; el puente es la
    frágil. Si la pausa detuviera el crédito interno, el sistema habría acoplado su
    supervivencia a su pieza más frágil y fallaría exactamente en el escenario para el que se
    diseñó.
    """
    state, eventos = _celula()
    state, ev = led.puente_pausar(state, "comite", 1100)
    eventos.append(ev)
    assert state["params"]["puente_pausado"] is True

    # ── Todo el ciclo del piloto, con el puente parado ──
    # alta de miembro
    state, ev = led.add_member(state, {"id": "Z", "turnover_cents": 50_000_000}, "comite", 1110)
    eventos.append(ev)
    # obligación
    state, ev = led.record_obligation(
        state, {"id": "ob-1", "debtor": "B", "creditor": "A", "amount_cents": 4000}, 1120)
    eventos.append(ev)
    # liquidación bilateral
    state, ev = led.settle_obligation(state, "ob-1", 4000, 1130)
    eventos.append(ev)
    # actualización de miembro
    state, ev = led.update_member(state, "Z", {"status": "warned"}, "comite", 1140)
    eventos.append(ev)
    # compensación de ciclo
    state, eventos = _mover(state, eventos, "A", "B", 1000, 1150)
    # anclaje (D2) — sigue funcionando: es read/emit sobre la cadena
    state, ev = led.record_obligation(
        state, {"id": "ob-2", "debtor": "V", "creditor": "F", "amount_cents": 700}, 1160)
    eventos.append(ev)

    # ── Las OTRAS TRES resoluciones de salida siguen pasando ──
    state, ev = led.salida_con_saldo(state, "Z", {"tipo": "simple"}, "comite", 1200)
    eventos.append(ev)
    state, ev = led.salida_con_saldo(
        state, "V", {"tipo": "plan_de_pago", "plazo_meses": 6}, "comite", 1210)
    eventos.append(ev)
    state, ev = led.salida_con_saldo(
        state, "B", {"tipo": "absorcion_avalista", "avalista": "A"}, "comite", 1220)
    eventos.append(ev)

    # ── Y SOLO la liquidación del puente se rechaza ──
    with pytest.raises(ValueError, match="puente_pausado"):
        led.salida_con_saldo(
            state, "F", {"tipo": "liquidacion_puente", "fondo": "A"}, "comite", 1230)

    # La cadena sigue sana y L1 se conserva: el rechazo no dejó el estado a medias.
    led.verify_chain(eventos)
    assert led.canonical(led.replay(eventos)) == led.canonical(state)
    assert sum(_saldos(state).values()) == 0
    assert state["params"]["puente_pausado"] is True


def test_ac_d68_5_control_negativo_reanudado_la_liquidacion_pasa():
    """AC-d68.5 control negativo — sin esto, AC-d68.5 pasaría con `liquidacion_puente` rota por
    cualquier otra razón (un `fondo` mal validado, por ejemplo) y nadie lo notaría."""
    state, eventos = _celula()
    state, eventos = _mover(state, eventos, "B", "A", 5000, 1010)
    state, _ = led.puente_pausar(state, "comite", 1100)

    with pytest.raises(ValueError, match="puente_pausado"):
        led.salida_con_saldo(
            state, "A", {"tipo": "liquidacion_puente", "fondo": "F"}, "comite", 1200)

    state, _ = led.puente_reanudar(state, "comite", 1300)
    state, _ = led.salida_con_saldo(
        state, "A", {"tipo": "liquidacion_puente", "fondo": "F"}, "comite", 1400)

    assert _saldos(state) == {"A": 0, "B": -5000, "F": 5000, "V": 0}
    assert sum(_saldos(state).values()) == 0


def test_ac_d68_5_la_pausa_no_toca_a_los_otros_tipos_de_salida():
    """AC-d68.5 — el mensaje distingue: si `plan_de_pago` fallara, NO sería por el puente.

    Mutación 3 del DESIGN §7 (la pausa rechaza también `plan_de_pago`): la pausa es una regla de
    UNA resolución. El comité puede seguir acordando planes de pago con el puente parado —
    de hecho es cuando MÁS falta hacen.
    """
    state, eventos = _celula()
    state, eventos = _mover(state, eventos, "A", "B", 3000, 1010)
    state, _ = led.puente_pausar(state, "comite", 1100)

    state, _ = led.salida_con_saldo(
        state, "A", {"tipo": "plan_de_pago", "plazo_meses": 6}, "comite", 1200)
    assert _saldos(state) == {"A": -3000, "B": 3000, "F": 0, "V": 0}
    assert state["members"]["A"]["status"] == "exited"


# ── AC-d68.9 — `puente_pausado` ≠ `paused` (C-d68.4) ──────────────────────────────────────

def test_ac_d68_9_pause_cell_no_toca_el_puente():
    """AC-d68.9 — dos conceptos, dos campos. `pause_cell` es el cortafuegos de la célula."""
    state, _ = _celula()
    state, _ = led.pause_cell(state, "comite", 1100)
    assert state["params"]["paused"] is True
    assert state["params"]["puente_pausado"] is False


def test_ac_d68_9_puente_pausar_no_toca_el_cortafuegos():
    """AC-d68.9 — y al revés: pausar el puente NO pausa la célula.

    Es la mitad que importa. Si `puente_pausar` reutilizara `paused` (mutación 1 del DESIGN §7),
    esta aserción caería — y con ella I-VE7.
    """
    state, _ = _celula()
    state, _ = led.puente_pausar(state, "comite", 1100)
    assert state["params"]["puente_pausado"] is True
    assert state["params"]["paused"] is False


def test_ac_d68_9_los_mensajes_son_distinguibles():
    """AC-d68.9 — el `match=` tiene que poder probar QUIÉN rechazó.

    No es cosmética: con el mismo mensaje, un test que cree estar probando el puente podría
    estar probando el cortafuegos y pasaría igual. Misma lección que AC-d9.5 en TB.5
    (`firewall` vs `clave desconocida`), y que la mutación M2 de TB.6, donde un mensaje
    compartido dejó pasar un AC por la razón equivocada.
    """
    state, _ = _celula()
    # El cortafuegos rechaza con `paused`; el puente, con `puente_pausado`. Que uno sea
    # subcadena del otro es la trampa: se ancla el mensaje entero.
    state_p, _ = led.pause_cell(state, "comite", 1100)
    with pytest.raises(ValueError) as e_cell:
        led.salida_con_saldo(state_p, "A", {"tipo": "simple"}, "comite", 1200)
    assert str(e_cell.value) == "paused"

    state_b, _ = led.puente_pausar(state, "comite", 1100)
    with pytest.raises(ValueError) as e_bridge:
        led.salida_con_saldo(
            state_b, "A", {"tipo": "liquidacion_puente", "fondo": "F"}, "comite", 1200)
    assert str(e_bridge.value) == "puente_pausado"


# ── AC-d68.8 filas 1–2 — reversibilidad (§4 de la spec) ───────────────────────────────────

def test_ac_d68_8_1_doble_pausa():
    """AC-d68.8(1) — pausar un puente pausado lanza: un doble clic no oculta un estado real.

    Convención heredada de `pause_cell`/`resume_cell`. Si fuera idempotente, el segundo
    ratificador creería haber parado algo que ya estaba parado, y la cadena registraría dos
    decisiones donde hubo una.
    """
    state, _ = _celula()
    state, _ = led.puente_pausar(state, "comite", 1100)
    with pytest.raises(ValueError, match="puente_pausado"):
        led.puente_pausar(state, "comite", 1200)


def test_ac_d68_8_2_doble_reanudacion():
    """AC-d68.8(2) — reanudar un puente activo lanza, y con mensaje propio."""
    state, _ = _celula()
    with pytest.raises(ValueError) as e:
        led.puente_reanudar(state, "comite", 1100)
    assert str(e.value) == "puente_no_pausado"


def test_ac_d68_8_el_ciclo_es_un_DIAL_no_un_interruptor():
    """AC-d68.8 — `pausar → reanudar → pausar` pasa entero.

    No es un caso de borde: la lista de designaciones se mueve en los DOS sentidos (hubo
    retiradas en abr-2026; verificación de sanciones, hallazgo 4). Un interruptor de un solo uso
    modelaría mal un programa que se afloja y se aprieta.
    """
    state, eventos = _celula()
    for ts, esperado in [(1100, True), (1200, False), (1300, True)]:
        op = led.puente_pausar if esperado else led.puente_reanudar
        state, ev = op(state, "comite", ts)
        eventos.append(ev)
        assert state["params"]["puente_pausado"] is esperado

    led.verify_chain(eventos)
    assert led.canonical(led.replay(eventos)) == led.canonical(state)


# ── AC-7 — los kinds nuevos pasan por la puerta que YA existe ─────────────────────────────

@pytest.mark.parametrize("op", ["puente_pausar", "puente_reanudar"])
@pytest.mark.parametrize("malo", [None, "", 123, [], {}])
def test_ac_7_1_ratified_by_obligatorio(op, malo):
    """AC-7(1) — los dos kinds están en `ratification_kinds`: sin ratificador, no hay decisión.

    Parar el puente es una decisión del comité, no del motor. El motor NO criba contra la lista
    SDN y no debe (N8/N9/I3): quién está designado lo sabe el comité, con datos que el motor no
    tiene. Esta función registra la decisión; no la toma.
    """
    state, _ = _celula()
    if op == "puente_reanudar":
        state, _ = led.puente_pausar(state, "comite", 1100)
    with pytest.raises(ValueError, match="ratified_by"):
        getattr(led, op)(state, malo, 1200)


@pytest.mark.parametrize("kind", ["bridge_paused", "bridge_resumed"])
def test_ac_7_1_ratified_by_ausente(kind):
    """AC-7(1) — tampoco cuela un payload SIN la clave (la vía del evento fabricado)."""
    state, _ = _celula()
    if kind == "bridge_resumed":
        state, _ = led.puente_pausar(state, "comite", 1100)
    with pytest.raises(ValueError, match="ratified_by"):
        led._apply(state, kind, {}, 1200)


def test_ac_7_2_evento_encadenado():
    """AC-7(2) — el evento encadena: `prev_hash` == head previo y `seq` == prev+1."""
    state, _ = _celula()
    head_previo, seq_previo = state["head_hash"], state["seq"]
    nuevo, ev = led.puente_pausar(state, "comite", 1100)
    assert ev["prev_hash"] == head_previo
    assert ev["seq"] == seq_previo + 1
    assert ev["kind"] == "bridge_paused"
    assert nuevo["head_hash"] == ev["hash"]


def test_ac_7_3_replay_reconstruye_byte_a_byte():
    """AC-7(3) — `replay` reconstruye el estado byte a byte con los kinds nuevos dentro.

    Una helper que pusiera `params["puente_pausado"] = True` a mano no podría producir un stream
    que `replay` reconstruya. No hace falta prohibir la helper: basta con hacer imposible que su
    resultado pase.
    """
    state, eventos = _celula()
    state, ev = led.puente_pausar(state, "comite", 1100)
    eventos.append(ev)
    state, eventos = _mover(state, eventos, "B", "A", 2000, 1110)
    state, ev = led.puente_reanudar(state, "comite", 1200)
    eventos.append(ev)

    led.verify_chain(eventos)
    assert led.canonical(led.replay(eventos)) == led.canonical(state)


@pytest.mark.parametrize("op", ["puente_pausar", "puente_reanudar"])
def test_ac_7_4_ts_monotono(op):
    """AC-7(4) — la monotonía heredada de `ts` cubre a los kinds nuevos sin código nuevo."""
    state, _ = _celula()
    if op == "puente_reanudar":
        state, _ = led.puente_pausar(state, "comite", 1100)
    with pytest.raises(ValueError, match="ts"):
        getattr(led, op)(state, "comite", state["last_ts"] - 1)


def test_ac_7_5_el_cortafuegos_manda_sobre_el_puente():
    """AC-7(5) — con la célula pausada (inv. 8) no se toca el puente: `paused` para TODO.

    La jerarquía no es simétrica y esto la fija: el cortafuegos incluye al puente, el puente no
    incluye al cortafuegos.
    """
    state, _ = _celula()
    state, _ = led.pause_cell(state, "comite", 1100)
    with pytest.raises(ValueError, match="paused"):
        led.puente_pausar(state, "comite", 1200)
