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
    "score", "rating", "reputation", "rank",
    "blacklist", "ban", "penalty", "global_id", "dni",
})

# (module attribute name, relative path). Every capa that carries the taxonomy.
_LAYERS = {
    "assurance":   "assurance/assurance_engine.py",   # Capa-4 — the one the AC-X net missed
    "membrane":    "partition/membrane.py",           # Capa-1
    "legibility":  "legibility/legibility_query.py",  # Capa-2
    "matcher":     "matcher/matcher.py",              # Capa-3
    "stigmergy":   "stigmergy/stigmergy.py",          # Capa-5
    "governance":  "governance/governance.py",        # Capa-6
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
