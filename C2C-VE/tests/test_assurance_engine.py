"""Pruebas de aceptación para el motor de aseguramiento (contrato de garantía /
quorum) de la Capa 4.

Corresponde a evals/acceptance.md AC1-AC6. Usa un oráculo INDEPENDIENTE
(collections.Counter + división entera, escrito a mano) para que el motor no
pueda autoconfirmar un error (AGD-045).
"""
import copy
import importlib.util
import json
from collections import Counter
from pathlib import Path

import pytest

_ENGINE = Path(__file__).resolve().parent.parent / "src" / "assurance" / "aseguramiento.py"
_spec = importlib.util.spec_from_file_location("aseguramiento", _ENGINE)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)
resolver = mod.resolver

FORBIDDEN = ("score", "rating", "reputation", "rank", "blacklist", "ban",
             "penalty", "global_id", "dni")


# ---- oráculo independiente ---------------------------------------------------
def oracle(campana):
    compromisos = campana["compromisos"]
    tokens = [p["ficha_participante"] for p in compromisos]
    distinct = len(set(tokens))
    estado = "se_activa" if distinct >= campana["umbral"] else "reembolsa"
    sums = Counter()
    if campana["tipo"] == "monetario":
        for p in compromisos:
            sums[p["ficha_participante"]] += p["monto_centavos"]
    return distinct, estado, sums


def _scan_keys(obj):
    """Recorre recursivamente y produce cada clave de diccionario en una estructura anidada."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _scan_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _scan_keys(v)


# ---- fixtures -----------------------------------------------------------------
TEST_A = {
    "campana_id": "campA", "celula_id": "barrio-1", "tipo": "binario",
    "umbral": 3, "bono_patrocinador_centavos": 0, "expira_en": "2026-12-31T00:00:00Z",
    "compromisos": [{"compromiso_id": f"p{i}", "ficha_participante": t}
                     for i, t in enumerate(["t1", "t2", "t3", "t4"])],
}
TEST_B = {
    "campana_id": "campB", "celula_id": "barrio-1", "tipo": "monetario",
    "umbral": 5, "bono_patrocinador_centavos": 1000, "expira_en": "2026-12-31T00:00:00Z",
    "compromisos": [
        {"compromiso_id": "p1", "ficha_participante": "t1", "monto_centavos": 2000},
        {"compromiso_id": "p2", "ficha_participante": "t2", "monto_centavos": 3000},
        {"compromiso_id": "p3", "ficha_participante": "t1", "monto_centavos": 500},
        {"compromiso_id": "p4", "ficha_participante": "t3", "monto_centavos": 1500},
    ],
}


# ---- AC1: corrección del umbral (recálculo independiente) --------------------
@pytest.mark.parametrize("camp", [TEST_A, TEST_B])
def test_ac1_threshold(camp):
    out = resolver(copy.deepcopy(camp))
    distinct, estado, _ = oracle(camp)
    assert out["comprometidos_distintos"] == distinct
    assert out["estado"] == estado


def test_ac1_boundary_exact():
    camp = copy.deepcopy(TEST_A)
    camp["umbral"] = 4  # distinct == umbral debe ACTIVARSE (>=)
    assert resolver(camp)["estado"] == "se_activa"
    camp["umbral"] = 5
    assert resolver(camp)["estado"] == "reembolsa"


# ---- AC2: garantía de no-pérdida ----------------------------------------------
def test_ac2_no_loss():
    out = resolver(copy.deepcopy(TEST_B))
    _, _, sums = oracle(TEST_B)
    reembolsos = {r["ficha_participante"]: r["reembolso_centavos"]
                  for r in out["resolucion"]["reembolsos"]}
    for token, total in sums.items():
        assert reembolsos[token] == total  # restitución completa, incl. re-compromiso sumado


def test_ac2_fires_has_empty_refunds():
    out = resolver(copy.deepcopy(TEST_A))
    assert out["resolucion"]["reembolsos"] == []


# ---- AC3: conservación y exactitud del bono -----------------------------------
def test_ac3_bonus_conservation():
    out = resolver(copy.deepcopy(TEST_B))
    bonos = [r["bono_centavos"] for r in out["resolucion"]["reembolsos"]]
    assert sum(bonos) == TEST_B["bono_patrocinador_centavos"]
    assert max(bonos) - min(bonos) <= 1  # el reparto difiere a lo sumo en 1 centavo
    # los primeros rem (por orden ascendente de token) reciben el centavo extra
    reembolsos = out["resolucion"]["reembolsos"]
    by_token = sorted(reembolsos, key=lambda r: r["ficha_participante"])
    rem = TEST_B["bono_patrocinador_centavos"] % out["comprometidos_distintos"]
    base = TEST_B["bono_patrocinador_centavos"] // out["comprometidos_distintos"]
    for i, r in enumerate(by_token):
        assert r["bono_centavos"] == base + (1 if i < rem else 0)


def test_ac3_no_bonus_when_fires():
    out = resolver(copy.deepcopy(TEST_A))
    assert out["resolucion"]["se_activa"]["total_comprometido_centavos"] == 0


def test_ac3_all_int_no_float():
    for camp in (TEST_A, TEST_B):
        out = resolver(copy.deepcopy(camp))
        s = json.dumps(out)
        assert "." not in s.replace("2026-12-31", "")  # sin literales flotantes en dinero
        for r in out["resolucion"]["reembolsos"]:
            assert isinstance(r["reembolso_centavos"], int)
            assert isinstance(r["bono_centavos"], int)


# ---- AC4: determinismo ---------------------------------------------------------
@pytest.mark.parametrize("camp", [TEST_A, TEST_B])
def test_ac4_determinism(camp):
    a = resolver(copy.deepcopy(camp))
    b = resolver(copy.deepcopy(camp))
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# ---- AC5: forma anti-vigilancia -------------------------------------------------
@pytest.mark.parametrize("camp", [TEST_A, TEST_B])
def test_ac5a_no_forbidden_keys_in_output(camp):
    out = resolver(copy.deepcopy(camp))
    keys = {k.lower() for k in _scan_keys(out)}
    assert keys.isdisjoint(FORBIDDEN)


def test_ac5b_reject_forbidden_field_campaign():
    bad = copy.deepcopy(TEST_B)
    bad["global_score"] = {"t1": 0.9}
    with pytest.raises(ValueError):
        resolver(bad)


def test_ac5b_reject_forbidden_field_pledge():
    bad = copy.deepcopy(TEST_B)
    bad["compromisos"][0]["reputation"] = 0.9
    with pytest.raises(ValueError):
        resolver(bad)


def test_ac5c_cross_campaign_independence():
    c1 = {"campana_id": "c1", "celula_id": "b2", "tipo": "binario", "umbral": 2,
          "bono_patrocinador_centavos": 0, "expira_en": "2026-12-31T00:00:00Z",
          "compromisos": [{"compromiso_id": "p1", "ficha_participante": "t1"},
                           {"compromiso_id": "p2", "ficha_participante": "t9"}]}
    c2 = {"campana_id": "c2", "celula_id": "b3", "tipo": "binario", "umbral": 4,
          "bono_patrocinador_centavos": 0, "expira_en": "2026-12-31T00:00:00Z",
          "compromisos": [{"compromiso_id": "p1", "ficha_participante": "t1"},
                           {"compromiso_id": "p2", "ficha_participante": "t5"}]}
    o1, o2 = resolver(c1), resolver(c2)
    assert o1["estado"] == "se_activa" and o2["estado"] == "reembolsa"
    # ningún campo agrega t1 a través de las dos campañas
    assert "t1" not in json.dumps(o1["traza_auditoria"])


# ---- AC6: membrana (muro kula/gimwali) ----------------------------------------
def test_ac6_reject_priced_binary():
    bad = copy.deepcopy(TEST_A)
    bad["compromisos"][0]["monto_centavos"] = 500  # precio de mercado en una sala de igualdad
    with pytest.raises(ValueError):
        resolver(bad)


# ---- D-06: monto_centavos binario está estrictamente tipado (sin coerción ==) --
@pytest.mark.parametrize("bad_amount", [False, True, 0.0, 1.0, 500, -1])
def test_d06_binary_rejects_nonstrict_amount(bad_amount):
    # False/0.0 antes se colaban por `amount not in (0, None)` vía la coerción == de
    # Python; ahora bool/float y cualquier precio distinto de cero son brecha de membrana.
    bad = copy.deepcopy(TEST_A)
    bad["compromisos"][0]["monto_centavos"] = bad_amount
    with pytest.raises(ValueError):
        resolver(bad)


@pytest.mark.parametrize("ok_amount", [None, 0])
def test_d06_binary_accepts_explicit_no_price(ok_amount):
    camp = copy.deepcopy(TEST_A)
    camp["compromisos"][0]["monto_centavos"] = ok_amount
    resolver(camp)  # None o un int estricto 0 es un no-precio explícito -> no debe lanzar


# ---- validación de entrada -----------------------------------------------------
@pytest.mark.parametrize("mutate", [
    lambda c: c.update(umbral=0),
    lambda c: c.update(campana_id=""),
    lambda c: c.update(celula_id=""),
    lambda c: c.update(bono_patrocinador_centavos=-1),
    lambda c: c["compromisos"].append({"compromiso_id": "p1", "ficha_participante": "tx", "monto_centavos": 1}),  # compromiso_id duplicado
    lambda c: c.update(tipo="weird"),
])
def test_input_validation_rejects(mutate):
    bad = copy.deepcopy(TEST_B)
    mutate(bad)
    with pytest.raises(ValueError):
        resolver(bad)


def test_monetary_missing_amount_rejected():
    bad = copy.deepcopy(TEST_B)
    del bad["compromisos"][0]["monto_centavos"]
    with pytest.raises(ValueError):
        resolver(bad)


# ---- membrana / anti-Sybil: sin instrumento de mercado (bono) en sala de igualdad -
def test_reject_bonus_on_binary_campaign():
    bad = copy.deepcopy(TEST_A)          # binaria, conteo de cabezas, sin apuesta
    bad["bono_patrocinador_centavos"] = 500  # una prima monetaria adjunta
    with pytest.raises(ValueError):
        resolver(bad)


# ---- AC5b extendido: una clave prohibida anidada a CUALQUIER profundidad se rechaza -
def test_ac5b_reject_nested_forbidden_field():
    bad = copy.deepcopy(TEST_B)
    bad["meta"] = {"nested": {"reputation": 0.9}}  # dossier oculto un nivel abajo
    with pytest.raises(ValueError):
        resolver(bad)


# ---- los abortos de conservación son una señal distinta, NO un ValueError de usuario -
def test_invariant_error_is_not_valueerror():
    assert issubclass(mod.ErrorDeInvarianteAseguramiento, Exception)
    assert not issubclass(mod.ErrorDeInvarianteAseguramiento, ValueError)
