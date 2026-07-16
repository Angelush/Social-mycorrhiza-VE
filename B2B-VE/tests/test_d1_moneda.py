# -*- coding: utf-8 -*-
"""
Pruebas unitarias para las reglas de moneda y expiración (D1, AC-10).
Escrito exclusivamente con stdlib + pytest en castellano.
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

led = _load("mutual_credit_ledger_d1", "src/ledger/mutual_credit_ledger.py")

# Parámetros estándar para USD y VES según especificación
PARAMS_USD = {
    "neg_line_bp": 100,
    "pos_line_bp": 1000,
    "velocity_window_s": 86400,
    "velocity_max_cents": 5000000,
    "moneda": "USD",
    "sal_seudonimo": "sal-de-prueba-cell1", "paused": False
}

PARAMS_VES = {
    "neg_line_bp": 100,
    "pos_line_bp": 1000,
    "velocity_window_s": 86400,
    "velocity_max_cents": 5000000,
    "moneda": "VES",
    "expira_en_dias": 30,
    "sal_seudonimo": "sal-de-prueba-cell1", "paused": False
}


def test_ac10_vocabulario_nuclear_vivo():
    """
    AC-10 — EL VOCABULARIO NUCLEAR SIGUE VIVO.
    Prueba la admisión del flujo normal del ledger (crear célula, añadir miembros,
    registrar obligación, validar balance total y estructura de estados de cuenta).
    """
    # 1. create_cell con PARAMS_USD completa sin lanzar y cell_metrics["moneda"] == "USD"
    state, tx = led.create_cell("cell-1", PARAMS_USD, ratified_by="admin", ts=1000)
    metrics = led.cell_metrics(state)
    assert metrics["moneda"] == "USD"

    # 2. Flujo completo: crear célula, añadir miembros A y B, registrar obligación o1
    member_a = {"id": "A", "turnover_cents": 100000000}
    member_b = {"id": "B", "turnover_cents": 100000000}
    
    state, tx = led.add_member(state, member_a, ratified_by="admin", ts=1001)
    state, tx = led.add_member(state, member_b, ratified_by="admin", ts=1002)
    
    obligation = {"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 5000}
    state, tx = led.record_obligation(state, obligation, ts=1003)

    # 3. member_statement("A") devuelve balance_cents, credit_min_cents, credit_max_cents
    statement = led.member_statement(state, "A", scope="comite_credito")
    assert "balance_cents" in statement
    assert "credit_min_cents" in statement
    assert "credit_max_cents" in statement

    # 4. sum(m["balance_cents"] for m in state["members"].values()) == 0 (L1)
    suma_balances = sum(m["balance_cents"] for m in state["members"].values())
    assert suma_balances == 0


def test_d1_moneda_validaciones():
    """
    D1 — moneda:
    Verifica que se validen los parámetros de moneda correctos e incorrectos en create_cell.
    """
    # 1. create_cell con params SIN 'moneda' -> ValueError
    params_sin_moneda = PARAMS_USD.copy()
    params_sin_moneda.pop("moneda")
    with pytest.raises(ValueError, match="moneda"):
        led.create_cell("cell-err1", params_sin_moneda, ratified_by="admin", ts=1000)

    # 2. create_cell con "moneda":"EUR" -> ValueError
    params_eur = PARAMS_USD.copy()
    params_eur["moneda"] = "EUR"
    with pytest.raises(ValueError, match="moneda"):
        led.create_cell("cell-err2", params_eur, ratified_by="admin", ts=1000)

    # 3. create_cell con "moneda":"BTC" -> ValueError
    params_btc = PARAMS_USD.copy()
    params_btc["moneda"] = "BTC"
    with pytest.raises(ValueError, match="moneda"):
        led.create_cell("cell-err3", params_btc, ratified_by="admin", ts=1000)

    # 4. PARAMS_VES completa correctamente
    state, tx = led.create_cell("cell-ves", PARAMS_VES, ratified_by="admin", ts=1000)
    metrics = led.cell_metrics(state)
    assert metrics["moneda"] == "VES"
    assert metrics["expira_en_dias"] == 30


def test_d1_expira_en_dias_bicondicional():
    """
    D1 — expira_en_dias es BICONDICIONAL con VES.
    """
    # 1. moneda VES SIN expira_en_dias -> ValueError
    params_ves_sin_exp = PARAMS_VES.copy()
    params_ves_sin_exp.pop("expira_en_dias")
    with pytest.raises(ValueError, match="expira_en_dias"):
        led.create_cell("cell-err4", params_ves_sin_exp, ratified_by="admin", ts=1000)

    # 2. moneda VES con expira_en_dias=0 -> ValueError
    params_ves_zero = PARAMS_VES.copy()
    params_ves_zero["expira_en_dias"] = 0
    with pytest.raises(ValueError, match="expira_en_dias"):
        led.create_cell("cell-err5", params_ves_zero, ratified_by="admin", ts=1000)

    # 3. moneda VES con expira_en_dias=-5 -> ValueError
    params_ves_neg = PARAMS_VES.copy()
    params_ves_neg["expira_en_dias"] = -5
    with pytest.raises(ValueError, match="expira_en_dias"):
        led.create_cell("cell-err6", params_ves_neg, ratified_by="admin", ts=1000)

    # 4. moneda VES con expira_en_dias="30" (str, no int) -> ValueError
    params_ves_str = PARAMS_VES.copy()
    params_ves_str["expira_en_dias"] = "30"
    with pytest.raises(ValueError, match="expira_en_dias"):
        led.create_cell("cell-err7", params_ves_str, ratified_by="admin", ts=1000)

    # 5. moneda USD CON expira_en_dias=30 -> ValueError
    params_usd_con_exp = PARAMS_USD.copy()
    params_usd_con_exp["expira_en_dias"] = 30
    with pytest.raises(ValueError, match="expira_en_dias"):
        led.create_cell("cell-err8", params_usd_con_exp, ratified_by="admin", ts=1000)

    # 6. célula USD -> cell_metrics(...)["expira_en_dias"] is None
    state, tx = led.create_cell("cell-usd", PARAMS_USD, ratified_by="admin", ts=1000)
    metrics = led.cell_metrics(state)
    assert metrics["expira_en_dias"] is None


def test_d1_mezcla_monedas_irrepresentable():
    """
    D1 — la mezcla de monedas es IRREPRESENTABLE, no rechazada (test de FORMA, no de raise).
    
    No hay un chequeo explícito que rechace monedas mezcladas porque la estructura de datos
    está diseñada de tal manera que las obligaciones y los miembros no almacenan información
    de moneda individualmente (la moneda es a nivel de célula/ledger completo).
    """
    state, tx = led.create_cell("cell-irrep", PARAMS_USD, ratified_by="admin", ts=1000)
    
    member_a = {"id": "A", "turnover_cents": 100000000}
    member_b = {"id": "B", "turnover_cents": 100000000}
    
    state, tx = led.add_member(state, member_a, ratified_by="admin", ts=1001)
    state, tx = led.add_member(state, member_b, ratified_by="admin", ts=1002)
    
    obligation = {"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 5000}
    state, tx = led.record_obligation(state, obligation, ts=1003)

    # assert "moneda" NOT IN state["obligations"]["o1"]
    assert "moneda" not in state["obligations"]["o1"]

    # assert "moneda" NOT IN state["members"]["A"]
    assert "moneda" not in state["members"]["A"]


@pytest.mark.parametrize("clave_fx", [
    "tasa_de_cambio", "tipo_de_cambio", "exchange_rate", "fx", "paralelo", "bcv",
    "tasadecambio", "tipodecambio", "exchangerate", "tasaDeCambio"
])
def test_d1_taxonomia_fx(clave_fx):
    """
    D1 — taxonomía FX (lint secundario) sobre params de create_cell.
    Cada uno de estos parámetros extra prohíbe la creación de la célula lanzando ValueError.

    `match="tasa"` NO es decoración: pytest.raises(ValueError) atraparía CUALQUIER ValueError,
    y el test pasaría aunque el rechazo viniera de otra validación y el escáner FX estuviera
    muerto. Fijamos el motivo, no solo el hecho de que algo falle.
    """
    params_con_fx = PARAMS_USD.copy()
    params_con_fx[clave_fx] = 1
    with pytest.raises(ValueError, match="tasa"):
        led.create_cell(f"cell-{clave_fx}", params_con_fx, ratified_by="admin", ts=1000)


def test_d1_taxonomia_fx_control_negativo():
    """Control del test anterior: sin clave FX, los MISMOS params NO lanzan.

    Sin este control, `test_d1_taxonomia_fx` pasaría igual si create_cell rechazara siempre.
    Es la misma razón por la que AC-10 prueba la admisión: un muro que lo para todo satisface
    cualquier test que solo compruebe rechazos.
    """
    state, _ = led.create_cell("cell-control-fx", PARAMS_USD.copy(), ratified_by="admin", ts=1000)
    assert led.cell_metrics(state)["moneda"] == "USD"


def test_d1_simbolo_derivado():
    """
    D1 — símbolo derivado (C-d1.6):
    Verifica los símbolos mostrados en el reporte renderizado para USD y VES.
    """
    # Célula USD
    state_usd, _ = led.create_cell("cell-usd-render", PARAMS_USD, ratified_by="admin", ts=1000)
    state_usd, _ = led.add_member(state_usd, {"id": "A", "turnover_cents": 100000000}, ratified_by="admin", ts=1001)
    state_usd, _ = led.add_member(state_usd, {"id": "B", "turnover_cents": 100000000}, ratified_by="admin", ts=1002)
    state_usd, _ = led.record_obligation(state_usd, {"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 5000}, ts=1003)
    
    render_usd = led.render_statement(state_usd, "A", scope="comite_credito")
    assert "$" in render_usd
    assert "€" not in render_usd
    assert "Bs." not in render_usd

    # Célula VES
    state_ves, _ = led.create_cell("cell-ves-render", PARAMS_VES, ratified_by="admin", ts=1000)
    state_ves, _ = led.add_member(state_ves, {"id": "A", "turnover_cents": 100000000}, ratified_by="admin", ts=1001)
    state_ves, _ = led.add_member(state_ves, {"id": "B", "turnover_cents": 100000000}, ratified_by="admin", ts=1002)
    state_ves, _ = led.record_obligation(state_ves, {"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 5000}, ts=1003)
    
    render_ves = led.render_statement(state_ves, "A", scope="comite_credito")
    assert "Bs." in render_ves
    assert "€" not in render_ves
    assert "$" not in render_ves


# ============================================================================
# TB.8b — AC-d1.7 COMPLETO: el solver también dice la verdad (defecto hallado
# por TB.8: `render_report` imprimía «€» hardcodeado; el test de AC-d1.7 solo
# cubría `render_statement` → verde certificando la mitad del AC).
# ============================================================================

sol = _load("clearing_solver_d1", "src/clearing/clearing_solver.py")


def _celula_con_ciclo(params, cell_id):
    """Célula con un ciclo A→B→C→A para que la propuesta tenga contenido."""
    state, _ = led.create_cell(cell_id, params, ratified_by="admin", ts=1000)
    for i, mid in enumerate("ABC"):
        state, _ = led.add_member(state, {"id": mid, "turnover_cents": 100000000},
                                  ratified_by="admin", ts=1001 + i)
    for i, (d, c) in enumerate([("A", "B"), ("B", "C"), ("C", "A")]):
        state, _ = led.record_obligation(
            state, {"id": f"o{i}", "debtor": d, "creditor": c, "amount_cents": 72574},
            ts=1010 + i)
    return state


def test_acd17_render_report_usd_dice_dolares():
    """AC-d1.7 sobre render_report: célula USD → «$», jamás «€» ni «Bs.»."""
    state = _celula_con_ciclo(PARAMS_USD, "cell-usd-solver")
    rep = sol.render_report(sol.clear(led.to_clearing_input(state)))
    assert "725.74 $" in rep
    assert "€" not in rep
    assert "Bs." not in rep


def test_acd17_render_report_ves_dice_bolivares():
    """AC-d1.7 sobre render_report: célula VES → «Bs.», jamás «€» ni «$».

    ESTE es el defecto que TB.8 destapó: una célula VES emitía una propuesta de
    liquidación que decía «725.74 €» — la mentira exacta que C-d1.6 prohíbe, en
    el documento que el comité lee para RATIFICAR.
    """
    state = _celula_con_ciclo(PARAMS_VES, "cell-ves-solver")
    rep = sol.render_report(sol.clear(led.to_clearing_input(state)))
    assert "725.74 Bs." in rep
    assert "€" not in rep
    assert "$" not in rep


def test_acd17_solver_sin_moneda_rechaza():
    """Sin default (F-d3.1): un input sin moneda no adivina — lanza."""
    state = _celula_con_ciclo(PARAMS_USD, "cell-sin-moneda")
    data = led.to_clearing_input(state)
    del data["moneda"]
    with pytest.raises(ValueError, match="missing or invalid moneda"):
        sol.clear(data)


def test_acd17_el_euro_es_irrepresentable():
    """Control negativo: «EUR» no es moneda deprecada — es irrepresentable en el fork."""
    state = _celula_con_ciclo(PARAMS_USD, "cell-eur")
    data = led.to_clearing_input(state)
    data["moneda"] = "EUR"
    with pytest.raises(ValueError, match="missing or invalid moneda"):
        sol.clear(data)


def test_acd17_to_clearing_input_lleva_la_moneda():
    """La moneda viaja con la foto de la célula, y clear() la conserva en la propuesta."""
    state = _celula_con_ciclo(PARAMS_VES, "cell-ves-input")
    data = led.to_clearing_input(state)
    assert data["moneda"] == "VES"
    assert sol.clear(data)["moneda"] == "VES"


def test_acd17_simbolos_ledger_y_solver_no_derivan():
    """Anti-drift: `_SIMBOLO` está duplicado a propósito (el solver no importa el ledger,
    D9 los separó). Este test es lo que impide que las dos copias diverjan."""
    assert sol._SIMBOLO == led._SIMBOLO
    assert set(sol._SIMBOLO) == set(led.MONEDAS)


def test_acd17_apply_clearing_rechaza_moneda_ajena():
    """Puerta M8 × D1: el evento guarda la propuesta VERBATIM y un auditor la lee —
    una propuesta ratificada que dijera «Bs.» en una célula USD sería una mentira con
    firma. Control positivo incluido: la misma propuesta sin adulterar SÍ entra."""
    state = _celula_con_ciclo(PARAMS_USD, "cell-m8-moneda")
    proposal = sol.clear(led.to_clearing_input(state))
    adulterada = dict(proposal, moneda="VES")
    with pytest.raises(ValueError, match="proposal_moneda"):
        led.apply_clearing(state, adulterada, "admin", ts=1050)
    # control positivo: la genuina entra por la misma puerta
    state2, ev = led.apply_clearing(state, proposal, "admin", ts=1050)
    assert ev["kind"] == "clearing_applied"
    assert ev["payload"]["proposal"]["moneda"] == "USD"


def test_acd17_ningun_euro_en_el_codigo_de_src():
    """AC-d1.7, tercer punto: «ningún € en toda la salida de B2B-VE/src/». Se fija en
    la fuente: ningún literal de CÓDIGO en src/ contiene «€». Los comentarios y
    docstrings SÍ pueden nombrarlo para explicar el diseño (lección de TB.6b: un test
    que afirma algo del código no debe comprobarlo sobre la prosa) — se excluyen las
    constantes en posición de docstring y se recorre todo lo demás, f-strings incluidos.
    """
    import ast
    fuentes = sorted((_BASE / "src").rglob("*.py"))
    assert fuentes, "src/ vacío: el glob no encontró módulos"
    for f in fuentes:
        arbol = ast.parse(f.read_text(encoding="utf-8"))
        docstrings = set()
        for nodo in ast.walk(arbol):
            if isinstance(nodo, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                cuerpo = getattr(nodo, "body", [])
                if cuerpo and isinstance(cuerpo[0], ast.Expr) and \
                        isinstance(cuerpo[0].value, ast.Constant) and \
                        isinstance(cuerpo[0].value.value, str):
                    docstrings.add(id(cuerpo[0].value))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str) \
                    and "\u20ac" in nodo.value and id(nodo) not in docstrings:
                raise AssertionError(f"literal con \u20ac en {f}:{nodo.lineno}")
