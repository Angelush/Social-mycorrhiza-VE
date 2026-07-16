# -*- coding: utf-8 -*-
"""D10 (TB.9) — el vocabulario del producto y la honestidad del README (la parte mecanizable).

AC-9 y AC-d10.5 son GATE HUMANO y no se fingen aquí (ST-d10.3): un humano lee el README frase
por frase. Lo que sí tiene máquina:

- AC-d10.1: vocabulario prohibido ausente de TODO lo legible (README, docs/, docstrings y
  literales de src/, y las salidas de los cuatro renders).
- AC-d10.2: el celo no rompió el esquema — `params["moneda"]` sigue existiendo y admitida
  (F-d10.2: la palabra no es el problema; lo es qué nombra).
- AC-d10.3: el README referencia sus fuentes únicas, no las copia (la parte comprobable).
"""

import importlib.util
import re
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


led = _load("mutual_credit_ledger_d10", "src/ledger/mutual_credit_ledger.py")
sol = _load("clearing_solver_d10", "src/clearing/clearing_solver.py")
exp = _load("exportes_d10", "src/ledger/exportes.py")
mul = _load("multisig_d10", "src/gobernanza/multisig.py")

# N-d10.1 — lenguaje de producto prohibido. Nota: «moneda» A SECAS no está aquí (N-d10.2:
# `params["moneda"]` describe la unidad de cuenta, no promete un activo); lo prohibido son
# las FRASES de producto. `\b` en los términos ingleses para no cazar `tokenize` (léxico).
_PROHIBIDOS = [
    r"\bcoins?\b",
    r"\btokens?\b",
    r"\bpetro\b",
    r"\bcomunal(es)?\b",
    r"\bbilletera",
    r"\bwallets?\b",
    r"\bpuntos\b",
    r"la moneda de",
    r"nuestra moneda",
]

# ADMITIDAS con motivo (patrón AC-d7.4: no se relaja la regla; se documenta la excepción):
#   herencia.py — «token(s)» LÉXICO (tokenizador del firewall) dentro del bloque compartido
#   congelado (md5 5d693ec, AC-d9.1 lo fija byte a byte: no se puede reescribir sin romper
#   las 7 copias) + su cabecera, que describe ese mismo tokenizador.
_ADMITIDAS = {
    ("src/firewall/herencia.py", r"\btokens?\b"),
}


def _hits(texto, origen, admitidas=()):
    encontrados = []
    for pat in _PROHIBIDOS:
        if (origen, pat) in admitidas:
            continue
        for m in re.finditer(pat, texto, re.IGNORECASE):
            linea = texto.count("\n", 0, m.start()) + 1
            encontrados.append(f"{origen}:{linea}: «{m.group(0)}» ({pat})")
    return encontrados


def test_acd101_vocabulario_limpio_en_archivos_legibles():
    """AC-d10.1 sobre README, docs/ y todo src/ (docstrings, comentarios y mensajes:
    el vocabulario del producto es lo que se lee CADA DÍA, no la portada — F-d10.1)."""
    archivos = [_BASE / "README.md"] + sorted((_BASE / "docs").rglob("*.md")) \
        + sorted((_BASE / "src").rglob("*.py"))
    assert (_BASE / "README.md").exists(), "el README de D10 no existe"
    assert len(archivos) >= 8
    problemas = []
    for f in archivos:
        origen = str(f.relative_to(_BASE))
        problemas += _hits(f.read_text(encoding="utf-8"), origen, _ADMITIDAS)
    assert problemas == [], "vocabulario prohibido:\n" + "\n".join(problemas)


# Política sintética (mismas direcciones de prueba que test_d4_multisig, ver su docstring).
_DIR = [
    "TAvEzRk9LX7iwR9EvakMSWyiMgG9J8zf5h", "TMWQbr8H1B3BqgK8Egp422x3aVUBPzB8KT",
    "TV7KoXDKerjpwXmDGENf5HtcmJGmK6MNZf", "TDMTfeAY54RVdwA8pLQDz3mMGTyUbm6kSY",
    "TBV72QXCMyGojKyNvSPW1otNMLf3U5eA4f",
]
_POLITICA_3DE5 = {
    "umbral": 3, "total": 5, "cadena": "TRC20",
    "firmantes": [
        {"alias": f"firmante-{i}", "direccion": _DIR[i], "cadena": "TRC20",
         "rol": "diaspora" if i == 4 else "local", "cargo": f"cargo-{i}",
         "localidad": ["L1", "L1", "L2", "L2", "L3"][i]}
        for i in range(5)
    ],
}

PARAMS_USD = {"neg_line_bp": 100, "pos_line_bp": 1000, "velocity_window_s": 86400,
              "velocity_max_cents": 5_000_000, "moneda": "USD",
              "sal_seudonimo": "sal-d10", "paused": False}


def _celula():
    state, ev = led.create_cell("cell-d10", PARAMS_USD, ratified_by="ana", ts=1000)
    events = [ev]
    for i, mid in enumerate("ABC"):
        state, ev = led.add_member(state, {"id": mid, "turnover_cents": 100_000_000},
                                   "ana", 1001 + i)
        events.append(ev)
    for i, (d, c) in enumerate([("A", "B"), ("B", "C"), ("C", "A")]):
        state, ev = led.record_obligation(
            state, {"id": f"o{i}", "debtor": d, "creditor": c, "amount_cents": 5000},
            1010 + i)
        events.append(ev)
    return state, events


def test_acd101_vocabulario_limpio_en_las_salidas_vivas():
    """AC-d10.1 sobre lo que los cuatro renders EMITEN, no solo sobre la fuente: un f-string
    compone en runtime lo que ningún grep estático ve."""
    state, events = _celula()
    salidas = {
        "render_statement": led.render_statement(state, "A", scope="comite_credito"),
        "render_report": sol.render_report(sol.clear(led.to_clearing_input(state))),
        "exportar_registros(csv)": exp.exportar_registros(
            state, events, "A", 0, 2000, scope="comite_credito", formato="csv"),
        "exportar_registros(json)": exp.exportar_registros(
            state, events, "A", 0, 2000, scope="comite_credito", formato="json"),
        "describir_politica": mul.describir_politica(_POLITICA_3DE5),
    }
    problemas = []
    for origen, texto in salidas.items():
        assert isinstance(texto, str) and texto
        problemas += _hits(texto, origen)
    assert problemas == [], "vocabulario prohibido en salida viva:\n" + "\n".join(problemas)


def test_acd102_el_celo_no_rompio_el_esquema():
    """AC-d10.2 / F-d10.2 — `params["moneda"]` sigue existiendo y ADMITIDA. El riesgo de D10
    es el celo, no la laxitud: N-d10.1 leído literalmente renombraría la clave y rompería D1."""
    state, _ = led.create_cell("cell-esquema", dict(PARAMS_USD), ratified_by="ana", ts=1000)
    assert state["params"]["moneda"] == "USD"
    assert led.cell_metrics(state)["moneda"] == "USD"
    # y sin ella la célula NO se crea — la clave no es decorativa
    sin = {k: v for k, v in PARAMS_USD.items() if k != "moneda"}
    with pytest.raises(ValueError, match="moneda"):
        led.create_cell("cell-sin", sin, ratified_by="ana", ts=1000)


def test_acd103_el_readme_referencia_no_copia():
    """AC-d10.3 — la parte comprobable a máquina: los enlaces a las fuentes únicas EXISTEN y
    apuntan a archivos reales; y el README no re-teclea la tabla de invariantes upstream
    (canario: ninguna fila de definición «| L2 |»..«| L6 |» — L1 puede CITARSE, es la
    definición de crédito mutuo, pero la tabla entera solo vive upstream)."""
    readme = (_BASE / "README.md").read_text(encoding="utf-8")
    for destino in [
        "../B2B/workflows/micorriza/spec-ledger.md",
        "../B2B/workflows/micorriza/constraints.md",
        "../B2B/workflows/micorriza-ve/context.md",
        "../B2B/workflows/micorriza-ve/d1-unidad-de-cuenta/",
        "../docs/verificaciones/2026-07-15-cripto.md",
        "docs/gobernanza-multisig.md",
    ]:
        assert destino in readme, f"falta el enlace a la fuente única: {destino}"
        assert (_BASE / destino.rstrip("/")).exists(), f"enlace roto: {destino}"
    for fila in ["| L2 |", "| L3 |", "| L4 |", "| L5 |", "| L6 |", "| I2 |", "| I3 |"]:
        assert fila not in readme, f"tabla de invariantes RE-TECLEADA en el README: {fila}"
    # el volátil corregido apunta a la verificación fechada, no duplica el análisis
    assert "2026-07-15-cripto.md" in readme
