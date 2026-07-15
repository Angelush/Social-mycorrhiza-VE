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
    "paused": False
}

PARAMS_VES = {
    "neg_line_bp": 100,
    "pos_line_bp": 1000,
    "velocity_window_s": 86400,
    "velocity_max_cents": 5000000,
    "moneda": "VES",
    "expira_en_dias": 30,
    "paused": False
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
    statement = led.member_statement(state, "A")
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
    
    render_usd = led.render_statement(state_usd, "A")
    assert "$" in render_usd
    assert "€" not in render_usd
    assert "Bs." not in render_usd

    # Célula VES
    state_ves, _ = led.create_cell("cell-ves-render", PARAMS_VES, ratified_by="admin", ts=1000)
    state_ves, _ = led.add_member(state_ves, {"id": "A", "turnover_cents": 100000000}, ratified_by="admin", ts=1001)
    state_ves, _ = led.add_member(state_ves, {"id": "B", "turnover_cents": 100000000}, ratified_by="admin", ts=1002)
    state_ves, _ = led.record_obligation(state_ves, {"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 5000}, ts=1003)
    
    render_ves = led.render_statement(state_ves, "A")
    assert "Bs." in render_ves
    assert "€" not in render_ves
    assert "$" not in render_ves
