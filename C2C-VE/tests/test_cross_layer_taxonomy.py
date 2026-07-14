"""Cross-layer invariant: the six capas share ONE anti-surveillance taxonomy and
ONE scan behaviour — even though each defines them locally (so every capa loads
standalone by file path, with no shared import that could be tampered with once
to weaken all layers).

The per-capa AC-X tests each pin a subset of layers equal:
  - test_legibility  : legibility == membrane
  - test_matcher     : matcher   == membrane == legibility
  - test_stigmergy   : stigmergy == membrane == legibility == matcher
  - test_governance  : governance == membrane == legibility == matcher == stigmergy

None of them include Capa-4 (assurance_engine.py) — so before this file a silent
edit to the assurance frozenset would have diverged from the other five layers
undetected. This test closes that hole: it pins ALL SIX FORBIDDEN_KEYS equal to a
single canonical set, and verifies every layer's recursive scanner descends into
dicts, lists AND tuples (a nested container must never hide a surveillance shape).
"""
import importlib.util
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"

# The one taxonomy. If a capa's spec legitimately changes this, update it HERE and
# in all six modules in the same commit — that is the point of the pin.
CANONICAL_FORBIDDEN = frozenset({
    "score", "puntuacion", "puntaje", "rating", "calificacion",
    "reputation", "reputacion", "rank", "ranking", "clasificacion",
    "blacklist", "lista_negra", "ban", "veto", "penalty", "penalizacion",
    "sancion", "karma", "global_id", "dni", "cedula", "rif", "pasaporte",
})

# (module attribute name, relative path). Every capa that carries the taxonomy.
_LAYERS = {
    "assurance":   "assurance/aseguramiento.py",      # Capa-4 — the one the AC-X net missed
    "membrane":    "partition/membrana.py",           # Capa-1
    "legibility":  "legibility/legibilidad.py",       # Capa-2
    "matcher":     "matcher/emparejador.py",          # Capa-3
    "stigmergy":   "stigmergy/estigmergia.py",        # Capa-5
    "governance":  "governance/gobernanza.py",        # Capa-6
}


def _load(rel):
    """Load a capa module standalone by file path — mirrors every other test file,
    and proves the module still has no import that breaks isolated loading."""
    path = _SRC / rel
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_MODULES = {name: _load(rel) for name, rel in _LAYERS.items()}


def test_all_six_forbidden_taxonomies_are_the_canonical_set():
    """All six layers — Capa-4 included — carry exactly the canonical taxonomy."""
    for name, module in _MODULES.items():
        assert set(module.FORBIDDEN_KEYS) == set(CANONICAL_FORBIDDEN), (
            f"{name}.FORBIDDEN_KEYS diverges from the canonical anti-surveillance "
            f"taxonomy: {set(module.FORBIDDEN_KEYS) ^ set(CANONICAL_FORBIDDEN)}"
        )


def test_no_layer_has_extra_or_missing_keys_versus_any_other():
    """Pairwise equality across all six — a redundant but explicit 'cannot disagree'."""
    reference = set(_MODULES["assurance"].FORBIDDEN_KEYS)
    for name, module in _MODULES.items():
        assert set(module.FORBIDDEN_KEYS) == reference, (
            f"{name} disagrees with assurance on the surveillance taxonomy"
        )


# --- Every scanner recurses dict + list + tuple ------------------------------
# A forbidden key hidden inside a TUPLE value must still be found. Before the fix,
# four layers (assurance, membrane, legibility, matcher) recursed dict+list only,
# so a tuple-nested dossier slipped past their scan while Capa-5/6 caught it.
_TUPLE_NESTED_SHAPE = {"envelope": ({"reputation": 99},)}


def _found_in(module):
    """Invoke each layer's private scanner (names/signatures differ) and normalise
    to a bool: did it detect the forbidden key nested inside the tuple?"""
    m = module
    if hasattr(m, "_forbidden_key_path"):                 # assurance: -> str | None
        return m._forbidden_key_path(_TUPLE_NESTED_SHAPE) is not None
    if hasattr(m, "_contains_forbidden_key"):             # membrane / legibility: -> (bool, key)
        return m._contains_forbidden_key(_TUPLE_NESTED_SHAPE, list(m.FORBIDDEN_KEYS))[0]
    if hasattr(m, "_scan_forbidden"):                     # matcher / stigmergy: -> (bool, key)
        return m._scan_forbidden(_TUPLE_NESTED_SHAPE)[0]
    if hasattr(m, "_scan_keys"):                          # governance: (obj, taxonomy) -> (bool, key)
        return m._scan_keys(_TUPLE_NESTED_SHAPE, list(m.FORBIDDEN_KEYS))[0]
    raise AssertionError(f"{m.__name__}: no known scanner function")


def test_every_layer_scans_into_tuples():
    for name, module in _MODULES.items():
        assert _found_in(module), (
            f"{name}'s scanner did not descend into a tuple — a surveillance shape "
            f"nested in a tuple would evade the scan (scanner drift regression)"
        )


# --- Shared tokenizer/normalizer/value-scanner are byte-identical everywhere -------
# Every layer defines these locally (not imported), but AC-X pins their *behavior*
# (and, separately, `test_cross_layer.sh`-style diff in review, their exact text).

def test_tokenizer_normalizer_identical_behavior_across_all_six():
    """PB-a1-flavored spot check: every layer's tokenizer/normalizer produces the
    identical token set for a representative bilingual, accented, camelCase key."""
    sample_keys = ["puntuación", "banco_de_tiempo", "bancoDeTiempo", "lista_negra", "listaNegra"]
    reference = _MODULES["membrane"]
    for key in sample_keys:
        expected = reference._key_token_set(key)
        for name, module in _MODULES.items():
            assert module._key_token_set(key) == expected, (
                f"{name}._key_token_set({key!r}) diverges from membrane's: "
                f"{module._key_token_set(key)} != {expected}"
            )


_VALUE_NESTED_IDENTITY_SHAPES = [
    {"envelope": {"nested": ["V-12.345.678"]}},
    {"envelope": ({"deep": "J-12345678-9"},)},
    {"envelope": [["0412-1234567"]]},
]


def _value_scan_found(module, payload):
    """Invoke each layer's private scanner and normalise to a bool: did it detect
    the identity-shaped VALUE nested inside the payload?"""
    m = module
    if hasattr(m, "_forbidden_key_path"):
        return m._forbidden_key_path(payload) is not None
    if hasattr(m, "_contains_forbidden_key"):
        return m._contains_forbidden_key(payload, list(m.FORBIDDEN_KEYS))[0]
    if hasattr(m, "_scan_forbidden"):
        return m._scan_forbidden(payload)[0]
    if hasattr(m, "_scan_keys"):
        return m._scan_keys(payload, list(m.FORBIDDEN_KEYS))[0]
    raise AssertionError(f"{m.__name__}: no known scanner function")


def test_every_layer_scans_values_for_identity_patterns_nested_in_tuples_lists_dicts():
    """AC-T3 cross-layer parity: a cedula/RIF/telefono hidden in a VALUE, nested
    inside dict/list/tuple combinations, is rejected by every one of the six layers."""
    for name, module in _MODULES.items():
        for payload in _VALUE_NESTED_IDENTITY_SHAPES:
            assert _value_scan_found(module, payload), (
                f"{name}'s value-scanner missed an identity-shaped value nested in "
                f"{payload!r}"
            )
