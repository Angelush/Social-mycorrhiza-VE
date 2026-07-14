"""Pruebas de aceptación para el cortafuegos de partición por modo relacional (Capa 1).

Corresponde a workflows/micorriza-politica/capa1/evals/acceptance.md AC1-AC8 + AC-X.
Usa un oráculo INDEPENDIENTE de recorrido recursivo de claves (escrito a mano, no el
propio escáner del cortafuegos) para que el cortafuegos no pueda autoconfirmar un error (AGD-045).
"""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

_MOD = Path(__file__).resolve().parent.parent / "src" / "partition" / "membrana.py"
_spec = importlib.util.spec_from_file_location("membrana", _MOD)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)
admitir = mod.admitir
ErrorDeBrechaMembrana = mod.ErrorDeBrechaMembrana

FORBIDDEN = ("score", "rating", "reputation", "rank", "blacklist", "ban",
             "penalty", "global_id", "dni")
MARKET = ("price", "cost", "fee", "_cents", "currency", "valuation", "denominat")


# ---- oráculo independiente --------------------------------------------------
def any_key_matches(obj, tokens):
    """Detecta independientemente si alguna clave de dict (recursivamente) contiene un token."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if any(t in str(k).lower() for t in tokens):
                return True
            if any_key_matches(v, tokens):
                return True
    elif isinstance(obj, list):
        return any(any_key_matches(v, tokens) for v in obj)
    return False


def scan_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from scan_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from scan_keys(v)


def _mk(sala, carga, **kw):
    base = {"sala": sala, "celula_id": "barrio-1", "interaccion_id": "ix1",
            "expira_en": "2026-12-31T00:00:00Z", "participantes": ["t1", "t2"],
            "carga": carga}
    base.update(kw)
    return base


# ---- AC1: interacciones bien tipadas son admitidas --------------------------
def test_ac1_gift_admits():
    out = admitir(_mk("don_comunal", {"offer": "help moving", "nota": "no strings"}))
    assert out["admitido"] is True
    assert out["sala"] == "don_comunal"
    assert out["celula_id"] == "barrio-1"
    assert out["interaccion_id"] == "ix1"
    assert out["expira_en"] == "2026-12-31T00:00:00Z"


def test_ac1_equality_in_kind_admits():
    out = admitir(_mk("igualdad", {"turns_taken": 1, "turns_owed_in_kind": 1}))
    assert out["admitido"] is True


def test_ac1_market_with_price_admits():
    out = admitir(_mk("precio_de_mercado", {"item": "bike", "amount_cents": 8000, "currency": "EUR"}))
    assert out["admitido"] is True


def test_ac1_expires_at_absent_carries_null():
    ix = _mk("don_comunal", {"offer": "x"})
    del ix["expira_en"]
    assert admitir(ix)["expira_en"] is None


# ---- D-01: el sobre está en lista blanca (ninguna clave de mercado puede colarse) --
def test_d01_market_key_on_envelope_refused_in_gift_room():
    ix = _mk("don_comunal", {"offer": "help moving"})
    ix["fee_cents"] = 100  # un instrumento de mercado como hermano de primer nivel de la carga
    with pytest.raises(ErrorDeBrechaMembrana):
        admitir(ix)


def test_d01_arbitrary_unknown_envelope_key_refused():
    ix = _mk("precio_de_mercado", {"item": "bike"})
    ix["extra_metadata"] = {"anything": 1}
    with pytest.raises(ErrorDeBrechaMembrana):
        admitir(ix)


def test_d01_all_whitelisted_envelope_keys_still_admits():
    ix = {"sala": "igualdad", "celula_id": "c1", "interaccion_id": "i1",
          "expira_en": "2026-12-31T00:00:00Z", "participantes": ["t1"],
          "carga": {"turn": 1}}
    assert admitir(ix)["admitido"] is True


# ---- AC2: una fuga de mercado hacia una sala no de mercado es rechazada -----
@pytest.mark.parametrize("sala", ["don_comunal", "igualdad"])
@pytest.mark.parametrize("carga", [
    {"offer": "childcare", "price": 500},
    {"swap": {"terms": {"fee_cents": 200}}},          # anidado un nivel más abajo
    {"help": "ride", "currency": "USD"},
    {"deal": {"cost": 10}},
])
def test_ac2_market_leak_refused(sala, carga):
    with pytest.raises(ErrorDeBrechaMembrana):
        admitir(_mk(sala, carga))
    # el oráculo coincide en que la carga lleva una clave de mercado
    assert any_key_matches(carga, MARKET)


# ---- AC3: libro de reciprocidad rechazado en don, permitido en especie en igualdad ----
def test_ac3_ledger_refused_in_gift():
    with pytest.raises(ErrorDeBrechaMembrana):
        admitir(_mk("don_comunal", {"care": "meals", "balance_owed": 3}))


def test_ac3_in_kind_counter_admitted_in_equality():
    out = admitir(_mk("igualdad", {"slot": 2, "counter_in_kind": 2}))
    assert out["admitido"] is True


# ---- AC4: direccionalidad (contenido con forma de don se admite en la sala de mercado) -----
def test_ac4_gift_shaped_in_market_admits():
    out = admitir(_mk("precio_de_mercado", {"gift_note": "free with purchase",
                                     "description": "no charge sample"}))
    assert out["admitido"] is True


# ---- AC5: forma anti-vigilancia (todas las salas) ---------------------------
def test_ac5a_no_forbidden_keys_in_verdict():
    for ix in (_mk("don_comunal", {"offer": "x"}),
               _mk("precio_de_mercado", {"amount_cents": 100})):
        out = admitir(ix)
        keys = {str(k).lower() for k in scan_keys(out)}
        assert keys.isdisjoint(FORBIDDEN)


def test_ac5a_verdict_echoes_no_payload():
    out = admitir(_mk("don_comunal", {"secret_offer_detail": "sensitive"}))
    assert "secret_offer_detail" not in json.dumps(out)


@pytest.mark.parametrize("sala", ["don_comunal", "igualdad", "precio_de_mercado"])
@pytest.mark.parametrize("carga", [
    {"reputation": 0.9},
    {"seller": {"trust_score": 88}},                  # anidado, incluida la sala de mercado
    {"note": "ok", "user_rank": 3},
])
def test_ac5b_surveillance_refused_in_every_room(sala, carga):
    with pytest.raises(ErrorDeBrechaMembrana):
        admitir(_mk(sala, carga))


def test_ac5b_surveillance_in_envelope_refused():
    ix = _mk("precio_de_mercado", {"item": "x"}, blacklist=["t9"])
    with pytest.raises(ErrorDeBrechaMembrana):
        admitir(ix)


# ---- AC6: sin rechazo almacenado / lista blanca, no lista negra -------------
def test_ac6_only_admitted_true_is_returned():
    out = admitir(_mk("don_comunal", {"offer": "x"}))
    assert out["admitido"] is True
    # una brecha es una excepción, nunca un veredicto retornado admitido:false
    with pytest.raises(ErrorDeBrechaMembrana):
        admitir(_mk("don_comunal", {"price": 1}))


# ---- AC7: determinismo -------------------------------------------------------
@pytest.mark.parametrize("ix", [
    _mk("don_comunal", {"offer": "help"}),
    _mk("precio_de_mercado", {"amount_cents": 500, "item": "bread"}),
])
def test_ac7_determinism(ix):
    a = admitir(copy.deepcopy(ix))
    b = admitir(copy.deepcopy(ix))
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# ---- AC8: validación del sobre -----------------------------------------------
@pytest.mark.parametrize("mutate", [
    lambda i: i.update(sala="gift"),          # no es uno de los 3 literales
    lambda i: i.update(sala="market"),
    lambda i: i.update(interaccion_id=""),
    lambda i: i.update(celula_id=""),
    lambda i: i.update(participantes="t1"),    # str, no list
    lambda i: i.update(participantes=["", "t2"]),
    lambda i: i.update(carga=[]),           # list, no dict
    lambda i: i.update(expira_en=""),        # presente pero vacío
])
def test_ac8_envelope_validation(mutate):
    ix = _mk("don_comunal", {"offer": "x"})
    mutate(ix)
    with pytest.raises(ErrorDeBrechaMembrana):
        admitir(ix)


# ---- AC-X: consistencia con Capa 4 (campaña binaria == interacción de igualdad) -
def test_acx_capa4_binary_bonus_shape_refused():
    # una campaña binaria de Capa-4 que lleva un bono de patrocinador es una interacción
    # de igualdad con un instrumento de mercado -> rechazada aquí, igual que el propio rechazo de Capa-4 AC6.
    with pytest.raises(ErrorDeBrechaMembrana):
        admitir(_mk("igualdad", {"threshold": 3, "sponsor_bonus_cents": 500}))


def test_acx_capa4_priced_binary_shape_refused():
    with pytest.raises(ErrorDeBrechaMembrana):
        admitir(_mk("igualdad", {"threshold": 3, "pledge_amount_cents": 500}))
