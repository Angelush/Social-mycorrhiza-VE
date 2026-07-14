"""
Capa-1 relational-mode partition firewall for the Micorriza social protocol.

This module implements a pure, deterministic, side-effect-free membrane that
classifies and gates interactions based on their relational-mode room.
The firewall enforces three room modes with distinct instrumentation rules:
 - communal_gift: forbids market instruments and reciprocity-ledger keys
 - equality_matching: forbids market instruments; allows reciprocity-in-kind
 - market_price: permits market instruments

Surveillance shapes (FORBIDDEN_KEYS) are rejected in ALL rooms.
Key matching is case-insensitive substring matching, performed recursively
through dicts, lists, and tuples at any depth (a nested container never hides
a shape from the scan).

Specification: workflows/micorriza-politica/capa1/spec.md

Provenance: drafted by Mistral via multi-model-orchestration, reviewed by Claude.
"""
import re
import unicodedata


class MembraneBreachError(Exception):
    """Raised when an interaction breaches the membrane firewall."""
    pass


# === BEGIN shared firewall machinery (byte-identical across all six capas; AC-X) ===
# Tokenizing + normalizing key-match, plus identity-pattern value-scan. Fixed by
# workflows/micorriza-politica-ve/area-a-firewall-bilingue/{spec,constraints}.md.
# Defined locally in each layer (NOT a shared import — every capa must load standalone
# by file path); the six layers are held byte-for-byte in agreement by the AC-X test.

_CAMEL_BOUNDARY_RE = re.compile(r'(?<=[a-z0-9])(?=[A-Z])')
_NON_ALNUM_RE = re.compile(r'[^0-9a-zA-Z]+')

# Patrones exactos fijados en constraints.md (cedula/RIF/telefono venezolanos).
_CEDULA_RE = re.compile(r'\b[VE]-?\d{1,2}\.?\d{3}\.?\d{3}\b')
_RIF_RE = re.compile(r'\b[JGVEP]-?\d{8}-?\d\b')
_TELEFONO_RE = re.compile(r'\b(\+58|0058|0)(4\d{2}|2\d{2})[\s.\-]?\d{7}\b')
_IDENTITY_VALUE_PATTERNS = (_CEDULA_RE, _RIF_RE, _TELEFONO_RE)

# Surveillance shapes: forbidden in ALL inputs, all six capas, byte-identical taxonomy.
FORBIDDEN_KEYS = [
    'score', 'puntuacion', 'puntaje', 'rating', 'calificacion',
    'reputation', 'reputacion', 'rank', 'ranking', 'clasificacion',
    'blacklist', 'lista_negra', 'ban', 'veto', 'penalty', 'penalizacion',
    'sancion', 'karma', 'global_id', 'dni', 'cedula', 'rif', 'pasaporte',
]


def _strip_diacritics(s):
    """NFD-normalize and drop combining marks (accents), leaving base letters."""
    nfd = unicodedata.normalize('NFD', s)
    return ''.join(ch for ch in nfd if not unicodedata.combining(ch))


def _tokenize_key(key):
    """Strip diacritics FIRST (so an accented run is not split by the ASCII-only
    non-alnum regex), then split by camelCase boundaries and non-alphanumeric
    runs, lowercase. Returns a list of normalized tokens."""
    s = _strip_diacritics(str(key))
    s = _CAMEL_BOUNDARY_RE.sub('_', s)
    parts = _NON_ALNUM_RE.split(s)
    tokens = [p.lower() for p in parts if p != '']
    return tokens


def _key_token_set(key):
    """Candidates for exact matching: single tokens, adjacent-token bigrams (so a
    compound forbidden entry like lista_negra matches lista+negra split across two
    tokens), and the full underscore-joined key (so a 3+-token compound like
    poder_de_voto still matches a single taxonomy entry)."""
    tokens = _tokenize_key(key)
    grams = set(tokens)
    for i in range(len(tokens) - 1):
        grams.add(tokens[i] + '_' + tokens[i + 1])
    if len(tokens) > 1:
        grams.add('_'.join(tokens))
    return grams


def _key_matches_taxonomy(key, taxonomy):
    """Exact-token (or adjacent-bigram / full-compound) match of a key against a
    normalized taxonomy set. Never substring."""
    return bool(_key_token_set(key) & set(taxonomy))


def _value_has_identity_shape(value):
    """A string value matching a Venezuelan identity pattern (cedula/RIF/telefono) —
    a dossier shape hiding in a VALUE rather than a key."""
    if not isinstance(value, str):
        return False
    return any(p.search(value) for p in _IDENTITY_VALUE_PATTERNS)
# === END shared firewall machinery ===


# Market instruments: forbidden in communal_gift and equality_matching rooms (bilingual)
MARKET_KEYS = [
    'price', 'precio', 'cost', 'costo', 'coste', 'fee', 'tarifa',
    'cents', 'centavos', 'centimos', 'currency', 'moneda', 'divisa',
    'valuation', 'valoracion', 'denominat', 'denominacion',
    'pago', 'cobro', 'usd', 'ves', 'dolar', 'dolares', 'bolivar', 'bolivares',
]

# Reciprocity ledger: forbidden only in communal_gift room (bilingual)
RECIPROCITY_LEDGER_KEYS = [
    'debt', 'deuda', 'owed', 'debe', 'balance', 'saldo',
    'credit', 'credito', 'reciprocity', 'reciprocidad', 'iou',
    'favor_balance', 'saldo_de_favores',
]

# Envelope keys: the interaction's structural fields are whitelisted (D-01). The envelope has a
# fixed schema; free-form content belongs in `payload`, which IS shape-scanned. Any other top-level
# key is refused — so a market instrument can't ride in as a sibling of `payload` (the market scan
# is payload-scoped and would miss it). Whitelist-not-blacklist, matching Capa-3/5/6, which already
# whitelist their structural keys; Capa-1 was the lone layer that didn't.
_ENVELOPE_KEYS = ('mode', 'cell_id', 'interaction_id', 'expires_at', 'participants', 'payload')


def _contains_forbidden_key(obj, taxonomy):
    """Recursively check if any dict key in obj matches a taxonomy entry by EXACT
    token (or adjacent-bigram / full-compound), and scan every string VALUE for a
    Venezuelan identity pattern (cedula/RIF/telefono).

    Args:
        obj: The object to scan (dict, list, tuple, or other).
        taxonomy: Iterable of normalized (lowercase, no-diacritics) forbidden tokens.

    Returns:
        Tuple (found: bool, matching_key: str or None).
        Returns at the first match found (depth-first order).
    """
    taxonomy = set(taxonomy)
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_str = str(key)
            if _key_matches_taxonomy(key_str, taxonomy):
                return True, key_str
            if _value_has_identity_shape(value):
                return True, key_str
            # Recurse into value
            found, match_key = _contains_forbidden_key(value, taxonomy)
            if found:
                return True, match_key
        return False, None
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            if _value_has_identity_shape(item):
                return True, str(item)
            found, match_key = _contains_forbidden_key(item, taxonomy)
            if found:
                return True, match_key
        return False, None
    return False, None


def _count_keys(obj):
    """Recursively count all dict keys in obj.
    
    Args:
        obj: The object to count keys in (dict, list, or other).
    
    Returns:
        int: Total number of dict keys found recursively.
    """
    count = 0
    if isinstance(obj, dict):
        count += len(obj)
        for value in obj.values():
            count += _count_keys(value)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            count += _count_keys(item)
    return count


def admit(interaction: dict) -> dict:
    """Classify and gate a single interaction through the Capa-1 membrane firewall.
    
    This is a pure, deterministic, side-effect-free function. On any breach,
    it raises MembraneBreachError. It never repairs or strips fields, never
    returns admitted=False, and never persists anything.
    
    Args:
        interaction: A dict with the interaction envelope:
            - mode: str, one of 'communal_gift', 'equality_matching', 'market_price'
            - cell_id: non-empty str
            - interaction_id: non-empty str
            - expires_at: optional non-empty str or absent
            - participants: list of non-empty str (may be empty list)
            - payload: dict (may be empty)
    
    Returns:
        dict with keys: mode, cell_id, interaction_id, expires_at (or None),
        admitted (always True), and audit_trace dict.
        The audit_trace contains:
            - rule: str describing the enforced rules
            - checked_keys: int count of payload keys visited recursively
    
    Raises:
        MembraneBreachError: If the interaction breaches any firewall rule.
    """
    # 1. Validate envelope (reject/raise, do not repair)
    if not isinstance(interaction, dict):
        raise MembraneBreachError("Interaction must be a dict")

    # Whitelist the envelope: any unexpected top-level key is refused (D-01), closing the
    # gap where a market key on the envelope (a sibling of payload) was neither whitelisted
    # nor caught by the payload-scoped market scan.
    for key in interaction:
        if key not in _ENVELOPE_KEYS:
            raise MembraneBreachError(
                f"unknown top-level key in interaction envelope: {key!r} "
                f"(the envelope is whitelisted; put free-form content in payload)"
            )

    mode = interaction.get('mode')
    if mode not in ('communal_gift', 'equality_matching', 'market_price'):
        raise MembraneBreachError(
            f"mode must be one of 'communal_gift', 'equality_matching', 'market_price'; got {mode!r}"
        )

    cell_id = interaction.get('cell_id')
    if not isinstance(cell_id, str) or cell_id == '':
        raise MembraneBreachError("cell_id must be a non-empty string")

    interaction_id = interaction.get('interaction_id')
    if not isinstance(interaction_id, str) or interaction_id == '':
        raise MembraneBreachError("interaction_id must be a non-empty string")

    participants = interaction.get('participants')
    if not isinstance(participants, list):
        raise MembraneBreachError("participants must be a list")
    for i, p in enumerate(participants):
        if not isinstance(p, str) or p == '':
            raise MembraneBreachError(
                f"participants[{i}] must be a non-empty string; got {p!r}"
            )

    expires_at = interaction.get('expires_at')
    if expires_at is not None:
        if not isinstance(expires_at, str) or expires_at == '':
            raise MembraneBreachError("expires_at must be a non-empty string or absent")

    payload = interaction.get('payload')
    if not isinstance(payload, dict):
        raise MembraneBreachError("payload must be a dict")

    # 2. Surveillance scan over the WHOLE interaction
    found, match_key = _contains_forbidden_key(interaction, FORBIDDEN_KEYS)
    if found:
        raise MembraneBreachError(
            f"Surveillance shape detected in interaction: key {match_key!r}"
        )

    # 3. Membrane scan over payload (recursive)
    if mode == 'communal_gift':
        # FORBID market instruments AND reciprocity-ledger keys
        found, match_key = _contains_forbidden_key(payload, MARKET_KEYS)
        if found:
            raise MembraneBreachError(
                f"Market instrument detected in communal_gift room: key {match_key!r}"
            )
        found, match_key = _contains_forbidden_key(payload, RECIPROCITY_LEDGER_KEYS)
        if found:
            raise MembraneBreachError(
                f"Reciprocity ledger key detected in communal_gift room: key {match_key!r}"
            )
    elif mode == 'equality_matching':
        # FORBID market instruments only
        found, match_key = _contains_forbidden_key(payload, MARKET_KEYS)
        if found:
            raise MembraneBreachError(
                f"Market instrument detected in equality_matching room: key {match_key!r}"
            )
    # market_price: no membrane restrictions on payload

    # 4. Count payload keys visited recursively (all keys, since no breach)
    checked_keys = _count_keys(payload)

    # 5. Admit with audit trace
    return {
        'mode': mode,
        'cell_id': cell_id,
        'interaction_id': interaction_id,
        'expires_at': expires_at,
        'admitted': True,
        'audit_trace': {
            'rule': 'no market instrument in a non-market room; no surveillance shape in any room',
            'checked_keys': checked_keys
        }
    }
