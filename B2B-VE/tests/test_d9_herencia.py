# -*- coding: utf-8 -*-
"""
Pruebas unitarias para la herencia y compartición de la maquinaria de firewall
en el ledger de crédito mutuo (d9).
"""

import hashlib
import re
import sys
import importlib.util
from pathlib import Path
import pytest

# Carga de módulos según el árbol especificado
_BASE = Path(__file__).resolve().parent.parent
def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, _BASE / rel)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m

fw = _load("herencia_d9", "src/firewall/herencia.py")
led = _load("mutual_credit_ledger_d9", "src/ledger/mutual_credit_ledger.py")


def test_ac_d9_1_bloque_compartido_identico():
    """
    AC-d9.1 — el bloque compartido es byte-idéntico.
    Extrae el bloque de src/firewall/herencia.py y verifica su integridad por MD5 y tamaño.
    También verifica que el marcador de inicio aparezca exactamente una vez.
    """
    path_herencia = _BASE / "src/firewall/herencia.py"
    contenido = path_herencia.read_text(encoding="utf-8")

    # Verificar que el marcador de inicio aparezca exactamente una vez
    inicio_marcador = "# === BEGIN shared firewall machinery"
    assert contenido.count(inicio_marcador) == 1, (
        f"El marcador de inicio '{inicio_marcador}' debe aparecer exactamente una vez."
    )

    # Extraer el bloque usando regex re.S
    pattern = r"(# === BEGIN shared firewall machinery.*?# === END shared firewall machinery ===\n)"
    match = re.search(pattern, contenido, re.S)
    assert match is not None, "No se encontró el bloque compartido de firewall en herencia.py"

    bloque = match.group(1)
    bloque_bytes = bloque.encode("utf-8")

    BLOQUE_MD5 = "5d693ecf1833fb760e173ee3db30a263"
    BLOQUE_BYTES = 3023

    m = hashlib.md5()
    m.update(bloque_bytes)
    obtenido_md5 = m.hexdigest()

    assert obtenido_md5 == BLOQUE_MD5, f"MD5 incorrecto. Esperado: {BLOQUE_MD5}, Obtenido: {obtenido_md5}"
    assert len(bloque_bytes) == BLOQUE_BYTES, f"Tamaño en bytes incorrecto. Esperado: {BLOQUE_BYTES}, Obtenido: {len(bloque_bytes)}"


def test_ac_d9_2_nada_fuera_del_bloque_heredado():
    """
    AC-d9.2 — nada de fuera del bloque se heredó.
    Verifica que variables/funciones no compartidas no estén presentes en el módulo fw.
    """
    nombres_excluidos = [
        "MARKET_KEYS",
        "CLAVES_MERCADO",
        "RECIPROCITY_LEDGER_KEYS",
        "TASA_KEYS",
        "_ENVELOPE_KEYS",
        "_contains_forbidden_key"
    ]
    for nombre in nombres_excluidos:
        assert not hasattr(fw, nombre), f"El módulo herencia.py no debería tener el atributo '{nombre}'."


def test_ac_d9_3_maquinaria_heredada_funciona():
    """
    AC-d9.3 — la maquinaria heredada funciona.
    Verifica los casos específicos de coincidencia taxonómica y validación de formas de identidad.
    """
    # no colisiona con 'ban'
    assert fw._key_matches_taxonomy("bancoDeTiempo", fw.FORBIDDEN_KEYS) is False

    # bigrama lista_negra
    assert fw._key_matches_taxonomy("lista_negra_local", fw.FORBIDDEN_KEYS) is True

    # token score
    assert fw._key_matches_taxonomy("descripción_del_score_musical", fw.FORBIDDEN_KEYS) is True

    # Formato de identidad
    assert fw._value_has_identity_shape("V-12.345.678") is True
    assert fw._value_has_identity_shape(12345) is False


@pytest.mark.parametrize("clave", [
    "moneda", "expira_en_dias", "referencias_comerciales", "avalista", "relacion_declarada",
    "antiguedad_meses", "comite_credito", "salida_con_saldo", "puente_pausar", "anclar"
])
def test_ac_d9_4_centinela_colision_dominio(clave):
    """
    AC-d9.4 — centinela de colisión de dominio.
    Si alguna da True se RENOMBRA LA CLAVE, jamás FORBIDDEN_KEYS (es compartida con las 6 capas C2C-VE).
    """
    assert fw._key_matches_taxonomy(clave, fw.FORBIDDEN_KEYS) is False


def test_ac_d9_6_esquemas_cerrados_no_se_escanean():
    """
    AC-d9.6 — los esquemas cerrados NO se escanean.
    Crea una célula, añade un miembro y verifica que update_member permite claves válidas de
    lista blanca y rechaza claves inválidas por lista blanca, no por taxonomía.
    """
    params_validos = {
        "neg_line_bp": 100,
        "pos_line_bp": 1000,
        "velocity_window_s": 86400,
        "velocity_max_cents": 5000000,
        "moneda": "USD",
        "paused": False
    }
    member_valido = {"id": "A", "turnover_cents": 100000000}

    # Crear célula
    state, envelope_cell = led.create_cell(cell_id="c-1", params=params_validos, ratified_by="ana", ts=1000)

    # Añadir miembro
    state, envelope_memb = led.add_member(state, member=member_valido, ratified_by="ana", ts=1500)

    # led.update_member completa sin lanzar cuando la clave está permitida
    res_state, res_env = led.update_member(state, "A", {"credit_max_cents": 20000000}, "ana", 2000)
    assert res_state is not None

    # led.update_member lanza ValueError por cualquier otra clave no permitida por allowed_keys
    with pytest.raises(ValueError):
        led.update_member(state, "A", {"cualquier_cosa": 1}, "ana", 2000)
