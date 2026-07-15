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
import hashlib
import importlib.util
import re
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


# --- The shared firewall block is byte-identical across all six layers ------------
# Everything above pins BEHAVIOR (the taxonomy set, the tokenizer, the scanners'
# descent). None of it pins BYTES: adding an extra list INSIDE the BEGIN/END block
# in ONE layer only changes no observable behavior these tests check, so nothing
# caught it. That is the hole this closes.
#
# SPAN CONVENTION — the whole lesson of the md5 episode. The block is the complete
# BEGIN…END text INCLUDING its trailing "\n" = 3023 bytes = 5d693ecf18…  Extracting
# with .strip() yields 3022 bytes and a different md5: the SAME block under a
# different convention, not a different block. So we assert byte-count and md5
# SEPARATELY — a convention change must fail differently from a content change.
# A published md5 without its span is not verifiable: two honest readers get two
# numbers and each believes the other is lying.
#
# The regex, the literal and the byte-count below are COPIED from
# B2B-VE/tests/test_d9_herencia.py (AC-d9.1) — do not reinvent them, that is what
# makes the two files comparable.
#
# WHY NO TEST SPANS BOTH TREES: C2C-VE/ and B2B-VE/ are separate pytest roots. This
# test pins the 6 C2C-VE copies against the literal; AC-d9.1 pins the 7th (B2B-VE's
# herencia.py) against THE SAME literal, THE SAME span and THE SAME byte-count.
# All 7 are therefore byte-identical BY TRANSITIVITY. The decomposition is sound
# because both ends fix the same constants — not because a test walks both trees.

_FIREWALL_MD5 = "5d693ecf1833fb760e173ee3db30a263"
_FIREWALL_BYTES = 3023

_BEGIN_MARKER = "# === BEGIN shared firewall machinery"
_BLOCK_PATTERN = r"(# === BEGIN shared firewall machinery.*?# === END shared firewall machinery ===\n)"

# Listed EXPLICITLY, never discovered by grep: B2B-VE/tests/test_d9_herencia.py
# contains the marker too (it is the literal of its own regex), so a `grep -rl`
# enumeration counts 8 files, not 7 copies.
_FIREWALL_CARRIERS = [
    "partition/membrana.py",       # Capa-1
    "legibility/legibilidad.py",   # Capa-2
    "matcher/emparejador.py",      # Capa-3
    "assurance/aseguramiento.py",  # Capa-4
    "stigmergy/estigmergia.py",    # Capa-5
    "governance/gobernanza.py",    # Capa-6
]


def _extract_block(rel):
    """Extract the shared firewall block from a capa, under the canonical span."""
    contenido = (_SRC / rel).read_text(encoding="utf-8")
    assert contenido.count(_BEGIN_MARKER) == 1, (
        f"{rel}: the marker {_BEGIN_MARKER!r} must appear EXACTLY once — a header or "
        f"docstring quoting it verbatim makes the regex over-extract past the block."
    )
    match = re.search(_BLOCK_PATTERN, contenido, re.S)
    assert match is not None, f"{rel}: no shared firewall block found"
    return match.group(1).encode("utf-8")


def test_firewall_block_bytes_pinned_in_every_layer():
    """Each of the six copies matches the canonical byte-count AND md5 — asserted
    separately so a span/convention drift fails differently from a content edit."""
    for rel in _FIREWALL_CARRIERS:
        bloque = _extract_block(rel)
        assert len(bloque) == _FIREWALL_BYTES, (
            f"{rel}: firewall block is {len(bloque)} bytes, expected {_FIREWALL_BYTES}. "
            f"Exactly 3022 means a SPAN mismatch: the block was extracted with .strip(), "
            f"dropping the trailing newline — same block, other convention. Fix the "
            f"extraction, never the literal or the span. Any OTHER value means CONTENT "
            f"was added or removed inside BEGIN…END."
        )
        assert hashlib.md5(bloque).hexdigest() == _FIREWALL_MD5, (
            f"{rel}: firewall block CONTENT diverges (byte-count is correct, so this is "
            f"a real edit inside BEGIN…END, not a span mismatch). The block is copied "
            f"verbatim into all 7 carriers; edit it in ALL of them in the same commit."
        )


def test_firewall_block_identical_between_the_six_layers():
    """Pairwise byte-identity — explicit 'the six cannot disagree', independent of
    the literal above (this one still fails if the literal itself were changed)."""
    reference = _extract_block(_FIREWALL_CARRIERS[0])
    for rel in _FIREWALL_CARRIERS[1:]:
        assert _extract_block(rel) == reference, (
            f"{rel}'s firewall block differs byte-for-byte from "
            f"{_FIREWALL_CARRIERS[0]}'s — the six copies have drifted apart"
        )
