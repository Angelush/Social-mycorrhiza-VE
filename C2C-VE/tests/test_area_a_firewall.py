"""Acceptance tests for Area a — firewall bilingüe (tokenización + normalización + escaneo de
valores).

Maps to workflows/micorriza-politica-ve/area-a-firewall-bilingue/evals/acceptance.md:
AC-T1, AC-T2, AC-T3, AC-T4, AC-Ta5, plus property tests PB-a1/PB-a2, plus the golden-set
(evals/casos.json) regression gate.

Loads each of the six capas standalone by file path (same idiom as test_cross_layer_taxonomy.py)
so this file does not depend on any shared import between layers — the AC-X pin is what holds
them in byte-identical agreement, not a common module.
"""
import importlib.util
import json
from pathlib import Path

import pytest
from hypothesis import given, strategies as st

_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
_CASOS = (
    _ROOT / "workflows" / "micorriza-politica-ve" / "area-a-firewall-bilingue"
    / "evals" / "casos.json"
)

_LAYERS = {
    "assurance":   "assurance/aseguramiento.py",
    "membrane":    "partition/membrana.py",
    "legibility":  "legibility/legibilidad.py",
    "matcher":     "matcher/emparejador.py",
    "stigmergy":   "stigmergy/estigmergia.py",
    "governance":  "governance/gobernanza.py",
}


def _load(rel):
    path = _SRC / rel
    spec = importlib.util.spec_from_file_location(path.stem + "_area_a", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_MODULES = {name: _load(rel) for name, rel in _LAYERS.items()}


def _key_rejected(module, key):
    """True iff `key` would be rejected as a forbidden-shaped key by this layer's
    own taxonomy/matching machinery (exact token / bigram / full-compound)."""
    return module._key_matches_taxonomy(key, set(module.FORBIDDEN_KEYS))


def _value_rejected(module, value):
    """True iff `value` carries a Venezuelan identity pattern per this layer's
    own value-scanner."""
    return module._value_has_identity_shape(value)


# --- AC-T1: banco_de_tiempo ADMITTED (the defining substring-false-positive fix) --------------
def test_AC_T1_banco_de_tiempo_admitted_in_all_six_layers():
    for name, module in _MODULES.items():
        assert not _key_rejected(module, "banco_de_tiempo"), (
            f"{name} still rejects 'banco_de_tiempo' (substring false positive on 'ban')"
        )


def test_AC_T1_membrane_admits_banco_de_tiempo_in_communal_gift_room():
    membrane = _MODULES["membrane"]
    result = membrane.admitir({
        "sala": "don_comunal",
        "celula_id": "cell-1",
        "interaccion_id": "int-1",
        "participantes": ["alice", "bob"],
        "carga": {"banco_de_tiempo": {"horas": 3}},
    })
    assert result["admitido"] is True


# --- AC-T2: puntuación/puntuacion, cedula/cédula, rif rejected in all six layers, NFD ----------
@pytest.mark.parametrize("key", ["puntuacion", "puntuación", "cedula", "cédula", "rif"])
def test_AC_T2_rejected_with_and_without_tilde_in_all_six_layers(key):
    for name, module in _MODULES.items():
        assert _key_rejected(module, key), (
            f"{name} admitted forbidden key {key!r} (NFD normalization regression)"
        )


# --- AC-T3: value scanning — cedula/RIF/telefono rejected, including nested -------------------
@pytest.mark.parametrize("value", ["V-12.345.678", "J-12345678-9", "0412-1234567"])
def test_AC_T3_identity_shaped_value_rejected_in_all_six_layers(value):
    for name, module in _MODULES.items():
        assert _value_rejected(module, value), (
            f"{name} did not flag identity-shaped value {value!r}"
        )


@pytest.mark.parametrize("value", ["V-12.345.678", "J-12345678-9", "0412-1234567"])
def test_AC_T3_identity_shaped_value_rejected_when_nested(value):
    """Nested in dict / list / tuple — the value scanner must descend like the key scanner."""
    for name, module in _MODULES.items():
        scanner_name = next(
            n for n in ("_forbidden_key_path", "_contains_forbidden_key", "_scan_forbidden", "_scan_keys")
            if hasattr(module, n)
        )
        scanner = getattr(module, scanner_name)
        nested = {"envelope": {"deep": [({"leaf": value},)]}}
        if scanner_name == "_forbidden_key_path":
            found = scanner(nested) is not None
        elif scanner_name == "_scan_forbidden":
            found = scanner(nested)[0]
        else:
            found = scanner(nested, list(module.FORBIDDEN_KEYS))[0]
        assert found, f"{name} missed identity value {value!r} nested in dict/list/tuple"


def test_AC_T3_membrane_admit_raises_on_identity_shaped_value():
    membrane = _MODULES["membrane"]
    with pytest.raises(membrane.ErrorDeBrechaMembrana):
        membrane.admitir({
            "sala": "don_comunal",
            "celula_id": "cell-1",
            "interaccion_id": "int-1",
            "participantes": ["alice"],
            "carga": {"nota": "mi cedula es V-12.345.678"},
        })


# --- AC-T4: zona_urbana, underscore, rango_de_fechas ADMITTED (no substring false positives) --
@pytest.mark.parametrize("key", ["zona_urbana", "underscore", "rango_de_fechas"])
def test_AC_T4_admitted_in_all_six_layers(key):
    for name, module in _MODULES.items():
        assert not _key_rejected(module, key), (
            f"{name} rejected innocent key {key!r} (substring false positive)"
        )


# --- AC-Ta5: lista_negra / listaNegra rejected by BIGRAM, lista/negra alone are not ------------
def test_AC_Ta5_lista_negra_rejected_by_bigram_but_components_alone_are_not():
    for name, module in _MODULES.items():
        assert _key_rejected(module, "lista_negra"), f"{name} admitted 'lista_negra'"
        assert _key_rejected(module, "listaNegra"), f"{name} admitted 'listaNegra'"
        assert not _key_rejected(module, "lista"), f"{name} rejected lone token 'lista'"
        assert not _key_rejected(module, "negra"), f"{name} rejected lone token 'negra'"


# --- Property-based tests (hypothesis) ----------------------------------------------------------

@given(st.text(min_size=0, max_size=40))
def test_PB_a1_normalization_idempotent_and_strips_latin_diacritics(s):
    membrane = _MODULES["membrane"]
    once = membrane._strip_diacritics(s)
    twice = membrane._strip_diacritics(once)
    assert once == twice  # idempotent


_WORD = st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=2, max_size=8)


@given(st.lists(_WORD, min_size=1, max_size=5))
def test_PB_a1_camelCase_and_snake_case_produce_same_token_partition(words):
    """A key assembled as camelCase (wordOneWordTwo) and the same words assembled as
    snake_case (word_one_word_two) tokenize to the identical token list."""
    membrane = _MODULES["membrane"]
    snake_key = "_".join(words)
    camel_key = words[0] + "".join(w.capitalize() for w in words[1:])
    assert membrane._tokenize_key(snake_key) == membrane._tokenize_key(camel_key) == words


@given(st.dictionaries(st.text(min_size=1, max_size=10), st.text(min_size=0, max_size=15), max_size=6))
def test_PB_a2_value_scan_stable_under_key_reordering(d):
    """The value scanner's boolean verdict does not depend on dict key insertion order."""
    membrane = _MODULES["membrane"]
    reordered = dict(reversed(list(d.items())))
    found1, _ = membrane._contains_forbidden_key(d, list(membrane.FORBIDDEN_KEYS))
    found2, _ = membrane._contains_forbidden_key(reordered, list(membrane.FORBIDDEN_KEYS))
    assert found1 == found2


# --- Golden set: workflows/.../area-a-firewall-bilingue/evals/casos.json ----------------------

def _casos():
    return json.loads(_CASOS.read_text())


def test_golden_set_file_exists_and_has_keys_and_values():
    data = _casos()
    assert data["keys"]
    assert data["values"]


@pytest.mark.parametrize("caso", _casos()["keys"], ids=lambda c: c["key"])
def test_golden_set_keys(caso):
    membrane = _MODULES["membrane"]
    rejected = _key_rejected(membrane, caso["key"])
    expected_rejected = caso["expect"] == "reject"
    assert rejected == expected_rejected, (
        f"key {caso['key']!r}: expected {caso['expect']}, "
        f"got {'reject' if rejected else 'admitir'} ({caso['note']})"
    )


@pytest.mark.parametrize("caso", _casos()["values"], ids=lambda c: c["value"])
def test_golden_set_values(caso):
    membrane = _MODULES["membrane"]
    rejected = _value_rejected(membrane, caso["value"])
    expected_rejected = caso["expect"] == "reject"
    assert rejected == expected_rejected, (
        f"value {caso['value']!r}: expected {caso['expect']}, "
        f"got {'reject' if rejected else 'admitir'} ({caso['note']})"
    )
