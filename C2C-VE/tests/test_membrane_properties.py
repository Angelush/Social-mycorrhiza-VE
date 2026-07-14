"""Pruebas basadas en propiedades para el cortafuegos de partición de Capa 1 (P1-P4).

Impulsadas por hypothesis: ninguna clave de mercado sobrevive jamás la admisión en una
sala no de mercado; ninguna clave de vigilancia sobrevive jamás en ninguna sala ni en un veredicto.
"""
import importlib.util
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

_MOD = Path(__file__).resolve().parent.parent / "src" / "partition" / "membrana.py"
_spec = importlib.util.spec_from_file_location("membrana", _MOD)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)
admitir = mod.admitir
ErrorDeBrechaMembrana = mod.ErrorDeBrechaMembrana

FORBIDDEN = ("score", "rating", "reputation", "rank", "blacklist", "ban",
             "penalty", "global_id", "dni")
MARKET = ("price", "cost", "fee", "_cents", "currency", "valuation", "denominat")
LEDGER = ("debt", "owed", "balance", "credit", "reciprocity", "iou", "favor_balance")
_ALL_BAD = FORBIDDEN + MARKET + LEDGER

# claves garantizadas de no contener ninguna subcadena prohibida/de mercado/de libro
_clean_keys = st.sampled_from(["offer", "need", "nota", "help", "care", "item",
                               "slot", "turn", "topic", "when", "where", "kind_of"])
_clean_scalars = st.one_of(st.integers(), st.booleans())


def _clean_payload():
    return st.dictionaries(_clean_keys, _clean_scalars, max_size=5)


def _nest(inner_key, inner_val, depth):
    node = {inner_key: inner_val}
    for i in range(depth):
        node = {f"wrap{i}": node}
    return node


def _scan_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _scan_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _scan_keys(v)


def _mk(sala, carga, **kw):
    ix = {"sala": sala, "celula_id": "c1", "interaccion_id": "ix1",
          "participantes": ["t1"], "carga": carga}
    ix.update(kw)
    return ix


# P1: las cargas limpias se admiten en todas las salas
@settings(max_examples=100)
@given(sala=st.sampled_from(["don_comunal", "igualdad", "precio_de_mercado"]),
       carga=_clean_payload())
def test_p1_clean_payload_admits(sala, carga):
    assert admitir(_mk(sala, carga))["admitido"] is True


# P2: una clave de mercado a cualquier profundidad siempre se rechaza en las dos salas no de mercado
@settings(max_examples=100)
@given(sala=st.sampled_from(["don_comunal", "igualdad"]),
       market_key=st.sampled_from(["price", "cost", "fee", "unit_cents", "currency"]),
       depth=st.integers(min_value=0, max_value=4))
def test_p2_market_key_always_refused(sala, market_key, depth):
    try:
        admitir(_mk(sala, _nest(market_key, 1, depth)))
        assert False, "una clave de mercado sobrevivió en una sala no de mercado"
    except ErrorDeBrechaMembrana:
        pass


# P3: una clave prohibida (de vigilancia) a cualquier profundidad se rechaza en TODAS las salas
@settings(max_examples=100)
@given(sala=st.sampled_from(["don_comunal", "igualdad", "precio_de_mercado"]),
       bad=st.sampled_from(FORBIDDEN),
       depth=st.integers(min_value=0, max_value=4))
def test_p3_surveillance_key_always_refused(sala, bad, depth):
    try:
        admitir(_mk(sala, _nest(bad, 1, depth)))
        assert False, "una clave de vigilancia sobrevivió"
    except ErrorDeBrechaMembrana:
        pass


# P4: todo veredicto admitido está libre de claves prohibidas
@settings(max_examples=100)
@given(sala=st.sampled_from(["don_comunal", "igualdad", "precio_de_mercado"]),
       carga=_clean_payload())
def test_p4_verdict_has_no_forbidden_keys(sala, carga):
    out = admitir(_mk(sala, carga))
    keys = {str(k).lower() for k in _scan_keys(out)}
    assert all(not any(t in k for t in _ALL_BAD) for k in keys)
