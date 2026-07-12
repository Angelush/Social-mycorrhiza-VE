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


class MembraneBreachError(Exception):
    """Raised when an interaction breaches the membrane firewall."""
    pass


# Surveillance shapes: forbidden in ALL rooms, scanned over the WHOLE interaction
FORBIDDEN_KEYS = [
    'score', 'rating', 'reputation', 'rank',
    'blacklist', 'ban', 'penalty', 'global_id', 'dni'
]

# Market instruments: forbidden in communal_gift and equality_matching rooms
MARKET_KEYS = [
    'price', 'cost', 'fee', '_cents',
    'currency', 'valuation', 'denominat'
]

# Reciprocity ledger: forbidden only in communal_gift room
RECIPROCITY_LEDGER_KEYS = [
    'debt', 'owed', 'balance', 'credit',
    'reciprocity', 'iou', 'favor_balance'
]

# Envelope keys: the interaction's structural fields are whitelisted (D-01). The envelope has a
# fixed schema; free-form content belongs in `payload`, which IS shape-scanned. Any other top-level
# key is refused — so a market instrument can't ride in as a sibling of `payload` (the market scan
# is payload-scoped and would miss it). Whitelist-not-blacklist, matching Capa-3/5/6, which already
# whitelist their structural keys; Capa-1 was the lone layer that didn't.
_ENVELOPE_KEYS = ('mode', 'cell_id', 'interaction_id', 'expires_at', 'participants', 'payload')


def _contains_forbidden_key(obj, substrings):
    """Recursively check if any dict key in obj matches any substring (case-insensitive).
    
    Args:
        obj: The object to scan (dict, list, or other).
        substrings: List of substring patterns to match against keys.
    
    Returns:
        Tuple (found: bool, matching_key: str or None).
        Returns at the first match found (depth-first order).
    """
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_str = str(key)
            key_lower = key_str.lower()
            for substr in substrings:
                if substr in key_lower:
                    return True, key_str
            # Recurse into value
            found, match_key = _contains_forbidden_key(value, substrings)
            if found:
                return True, match_key
        return False, None
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            found, match_key = _contains_forbidden_key(item, substrings)
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
