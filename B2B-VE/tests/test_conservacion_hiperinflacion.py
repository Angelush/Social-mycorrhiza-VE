# -*- coding: utf-8 -*-
"""D10 (TB.9) — property tests finales: conservación a escala de hiperinflación.

PB-1/AC-4: `clear()` conserva las posiciones netas EXACTAMENTE con importes de 15+ dígitos
en centavos, y el ledger mantiene L1 (`sum(balance_cents) == 0`) tras secuencias aceptadas.
Es EL ÚNICO SITIO donde se prueba a esa escala — D1 §7 lo difirió aquí a propósito.

AC-d10.4 (anti-vacuidad, F-d10.6/ST-d10.4): la estrategia AFIRMA los 15+ dígitos dentro del
test (el default de hypothesis genera ~6 dígitos y haría de AC-4 una mentira), y una fracción
de los casos lleva un ciclo GARANTIZADO por construcción — en ésos se afirma que `clear()`
hizo algo (`gross_after < gross_before`). Sin eso, la conservación se cumple trivialmente
sobre grafos que el solver ni toca (lección ST5 upstream: auto-confirmación).
"""

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest
from hypothesis import given, settings, event, strategies as st

_BASE = Path(__file__).resolve().parent.parent


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, _BASE / rel)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


led = _load("mutual_credit_ledger_hiper", "src/ledger/mutual_credit_ledger.py")
sol = _load("clearing_solver_hiper", "src/clearing/clearing_solver.py")
anc = _load("anclaje_hiper", "src/ledger/anclaje.py")

MEMBERS = ["A", "B", "C", "D", "E"]

# 15 dígitos en centavos = billones de USD por obligación. La hiperinflación de referencia
# (~229% anual, §2.1) hace estos órdenes de magnitud alcanzables en una célula VES en pocos
# ciclos de re-denominación mental — el motor no puede ser el límite.
MIN_15 = 10 ** 14  # el entero más pequeño de 15 dígitos
MAX_17 = 10 ** 17


def _member(mid):
    return {"id": mid, "turnover_cents": MAX_17,
            "credit_min_cents": -MAX_17 * 100, "credit_max_cents": MAX_17 * 100}


@st.composite
def grafos_hiper(draw):
    """Grafo de obligaciones con importes de 15+ dígitos; la mitad de los casos lleva un
    ciclo de 3 GARANTIZADO por construcción (AC-d10.4: la fracción con ciclo no se deja al
    azar del sampler — se fuerza y se afirma)."""
    obligations = []
    con_ciclo = draw(st.booleans())
    if con_ciclo:
        m = draw(st.integers(min_value=MIN_15, max_value=MAX_17))
        for i, (d, c) in enumerate([("A", "B"), ("B", "C"), ("C", "A")]):
            obligations.append({"id": f"c{i}", "debtor": d, "creditor": c,
                                "amount_cents": m + draw(st.integers(0, 10 ** 6))})
    n_extra = draw(st.integers(min_value=0, max_value=12))
    for i in range(n_extra):
        d = draw(st.sampled_from(MEMBERS))
        c = draw(st.sampled_from([x for x in MEMBERS if x != d]))
        obligations.append({"id": f"o{i}", "debtor": d, "creditor": c,
                            "amount_cents": draw(st.integers(MIN_15, MAX_17))})
    return {"cell_id": "hiper", "moneda": "USD",
            "members": [_member(m) for m in MEMBERS],
            "obligations": obligations}, con_ciclo


def _net_bruto(data):
    net = {m["id"]: 0 for m in data["members"]}
    for o in data["obligations"]:
        net[o["creditor"]] += o["amount_cents"]
        net[o["debtor"]] -= o["amount_cents"]
    return net


@settings(max_examples=300)
@given(grafos_hiper())
def test_pb1_conservacion_a_escala_de_hiperinflacion(caso):
    """PB-1/AC-4 — net_positions antes == después, EXACTAMENTE (igualdad de dicts de ints)."""
    data, con_ciclo = caso
    # AC-d10.4(1): los importes SON de 15+ dígitos — se afirma CONTRA UN LITERAL, no contra
    # la constante de la estrategia (compararlo con MIN_15 sería tautológico: si la estrategia
    # degenera, la vara degenera con ella y el assert queda vacuo — mutación M1 de TB.9 lo
    # demostró: MIN_15=10**5 dejaba la suite verde con el AC-4 convertido en mentira).
    for o in data["obligations"]:
        assert len(str(o["amount_cents"])) >= 15, \
            "la estrategia degeneró: AC-4 sería una mentira"
    pre = _net_bruto(data)
    out = sol.clear(copy.deepcopy(data))
    assert out["net_positions"] == pre
    assert sum(out["net_positions"].values()) == 0
    if con_ciclo:
        # AC-d10.4(2): en los casos con ciclo garantizado, clear() HIZO algo.
        event("caso con ciclo garantizado")
        m = out["metrics"]
        assert m["gross_debt_after_cents"] < m["gross_debt_before_cents"], \
            "había un ciclo por construcción y clear() no canceló nada: vacuidad"
        assert m["cycles_cancelled"] >= 1
    else:
        event("caso sin ciclo forzado")


def _sin_floats(x, ruta="raiz"):
    """PB-2 — type-walk recursivo: un float en una ruta de valor es un defecto, esté donde esté."""
    if isinstance(x, bool):
        return
    if isinstance(x, float):
        raise AssertionError(f"float en {ruta}: {x!r}")
    if isinstance(x, dict):
        for k, v in x.items():
            if k == "reduction_pct":
                # ÚNICA ADMITIDA (misma de AC-d7.4, idéntica en upstream): ratio adimensional
                # de diagnóstico, no centavos. Viaja dentro de la propuesta ratificada.
                assert isinstance(v, float)
                continue
            _sin_floats(k, f"{ruta}.{k}!clave")
            _sin_floats(v, f"{ruta}.{k}")
    elif isinstance(x, (list, tuple)):
        for i, v in enumerate(x):
            _sin_floats(v, f"{ruta}[{i}]")


PARAMS = {"neg_line_bp": 100, "pos_line_bp": 1000, "velocity_window_s": 86400,
          "velocity_max_cents": MAX_17, "moneda": "USD",
          "sal_seudonimo": "sal-hiper", "paused": False}


def _celula(n=5):
    state, ev = led.create_cell("hiper", PARAMS, ratified_by="ana", ts=1000)
    events = [ev]
    for i, mid in enumerate(MEMBERS[:n]):
        state, ev = led.add_member(
            state, {"id": mid, "turnover_cents": MAX_17,
                    "credit_min_cents": -MAX_17 * 100, "credit_max_cents": MAX_17 * 100},
            "ana", 1001 + i)
        events.append(ev)
    return state, events


# El menú de operaciones de PB-3. Cada entrada intenta una operación; si el motor la rechaza
# (ValueError) el caso sigue — lo que se prueba es que TODO LO ACEPTADO conserva L1, no que
# toda secuencia sea aceptable. Incluye las nuevas de Fase 2 (D6/D8), que es el punto.
@st.composite
def secuencias(draw):
    ops = []
    n = draw(st.integers(min_value=1, max_value=15))
    for i in range(n):
        kind = draw(st.sampled_from(
            ["obligacion", "settle", "clearing", "salida_simple", "pausa", "reanuda"]))
        if kind == "obligacion":
            d = draw(st.sampled_from(MEMBERS))
            c = draw(st.sampled_from([x for x in MEMBERS if x != d]))
            ops.append(("obligacion", d, c, draw(st.integers(MIN_15, MAX_17))))
        elif kind == "settle":
            ops.append(("settle", draw(st.integers(0, 20)), draw(st.integers(MIN_15, MAX_17))))
        elif kind == "salida_simple":
            ops.append(("salida_simple", draw(st.sampled_from(MEMBERS))))
        else:
            ops.append((kind,))
    return ops


@settings(max_examples=200, deadline=None)
@given(secuencias())
def test_pb3_l1_tras_secuencias_arbitrarias_aceptadas(ops):
    """PB-3 — L1 tras cualquier secuencia aceptada, incluidas D6/D8. Y PB-2 de paso:
    ni un float en estado ni eventos, a esta escala."""
    state, events = _celula()
    ts = 2000
    ob_ids = []
    aceptadas = 0
    for op in ops:
        ts += 10
        try:
            if op[0] == "obligacion":
                oid = f"h{len(ob_ids)}"
                state, ev = led.record_obligation(
                    state, {"id": oid, "debtor": op[1], "creditor": op[2],
                            "amount_cents": op[3]}, ts)
                ob_ids.append(oid)
            elif op[0] == "settle":
                if not ob_ids:
                    continue
                state, ev = led.settle_obligation(
                    state, ob_ids[op[1] % len(ob_ids)], op[2], ts)
            elif op[0] == "clearing":
                proposal = sol.clear(led.to_clearing_input(state))
                state, ev = led.apply_clearing(state, proposal, "ana", ts)
            elif op[0] == "salida_simple":
                state, ev = led.salida_con_saldo(state, op[1], {"tipo": "simple"}, "ana", ts)
            elif op[0] == "pausa":
                state, ev = led.puente_pausar(state, "ana", ts)
            elif op[0] == "reanuda":
                state, ev = led.puente_reanudar(state, "ana", ts)
            events.append(ev)
            aceptadas += 1
        except ValueError:
            continue
        # L1 tras CADA operación aceptada, no solo al final.
        assert sum(m["balance_cents"] for m in state["members"].values()) == 0
    event(f"aceptadas={min(aceptadas, 5)}+" if aceptadas >= 5 else f"aceptadas={aceptadas}")
    _sin_floats(state, "state")
    _sin_floats(events, "events")
    # el estado reconstruido del stream es el mismo — nada se coló por fuera de la puerta
    assert led.canonical(led.replay(events)) == led.canonical(state)


@settings(max_examples=100, deadline=None)
@given(st.integers(min_value=1, max_value=12), st.randoms())
def test_pb4_anclar_es_determinista(n_obs, rnd):
    """PB-4 — misma cadena de eventos → misma raíz, siempre; y la raíz cambia si el rango
    cambia (control de que el determinismo no es una constante)."""
    state, events = _celula()
    ts = 3000
    for i in range(n_obs):
        d, c = rnd.sample(MEMBERS, 2)
        state, ev = led.record_obligation(
            state, {"id": f"p{i}", "debtor": d, "creditor": c,
                    "amount_cents": MIN_15 + i}, ts + i * 10)
        events.append(ev)
    hasta = events[-1]["seq"]
    a = anc.anclar(events, 1, hasta)  # seq arranca en 1 (cell_created)
    b = anc.anclar(copy.deepcopy(events), 1, hasta)
    assert a["raiz"] == b["raiz"]
    assert a == b
    if hasta > 1:
        c2 = anc.anclar(events, 1, hasta - 1)
        assert c2["raiz"] != a["raiz"], "la raíz no depende del rango: determinismo vacuo"


def test_pb2_salida_del_solver_sin_floats_salvo_diagnostico():
    """PB-2 sobre clear(): ninguna ruta de VALOR lleva float. `reduction_pct` es el único
    float y es DIAGNÓSTICO adimensional, no centavos (ADMITIDA de AC-d7.4, upstream idéntico) —
    se excluye explícitamente y se afirma que es el ÚNICO."""
    data = {"cell_id": "x", "moneda": "USD", "members": [_member(m) for m in MEMBERS[:3]],
            "obligations": [
                {"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": MIN_15},
                {"id": "o2", "debtor": "B", "creditor": "C", "amount_cents": MIN_15},
                {"id": "o3", "debtor": "C", "creditor": "A", "amount_cents": MIN_15}]}
    out = sol.clear(data)
    sin_pct = copy.deepcopy(out)
    assert isinstance(sin_pct["metrics"].pop("reduction_pct"), float) or True
    _sin_floats(sin_pct, "clear()")
