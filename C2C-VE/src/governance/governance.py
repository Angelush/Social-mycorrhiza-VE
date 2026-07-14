"""Capa-6 sociocratic governance (consent, not consensus) for the Micorriza social protocol.

This module implements a pure, deterministic, side-effect-free resolution of ONE proposal in ONE
local circle by CONSENT — the absence of a paramount (reasoned) objection — not by consensus, and not
by majority (brief §4 Capa 6; lineage: Haudenosaunee Great Law of Peace, Quaker meeting, sociocracy).
Each participant contributes exactly ONE disposition; the proposal is `adopted` iff no paramount
objection stands, else `revisit` with the objection's REASON surfaced — a whitelist-shaped pause that
opens revision, never a blacklist of the objector.

It is DETERMINISTIC, NOT an LLM: no stochastic core, no injected model, no network client — that is
the whole difference from Capa 3. It enforces the PROCEDURE of consent; it cannot manufacture the
will to cooperate.

Five structural walls (spec.md):
 1. VOICE INDEPENDENT OF REPUTATION (invariant 7, the defining move): one token, one voice (deduped;
    a duplicate token is refused); the VOTE_WEIGHT_KEY taxonomy AND the shared FORBIDDEN_KEY taxonomy
    refuse any weighted / reputation-bearing input; disposition keys are whitelisted. The god-view
    weighting cannot even be phrased.
 2. Consent, not consensus, not majority: `adopted` iff no paramount objection, else `revisit`. The
    verdict is CATEGORICAL — never a percentage, never a tally; one reasoned block is decisive.
 3. An objection is a whitelist-shaped PAUSE (invariant 3): it surfaces the REASON and opens revision;
    it never marks the objector. The output carries reasons, never objector tokens.
 4. Circles are LOCAL and do not auto-propagate (invariants 4/6): scoped to circle_id; off-circle
    dispositions dropped; no escalation to a parent/global authority.
 5. Forgetting: per-round expires_at; expired dispositions dropped; no dossier of who objected
    (invariant 5).

On any ENVELOPE/SHAPE/integrity breach (bad type, non-whitelisted key, a FORBIDDEN or VOTE_WEIGHT key,
a duplicate token) the module RAISES GovernanceBreachError (never repairs, never strips). Circle-scope
and expiry filtering DROP-and-count, never raise. Time is ISO-8601 strings compared lexicographically
(as Capa 1/2/3); Capa 6 needs no elapsed-time arithmetic.

Specification: workflows/micorriza-politica/capa6/spec.md

Provenance: spec authored by Claude; a Mistral draft was dispatched via multi-model-orchestration
(vibe, headless) but returned empty, so this module was implemented directly and reviewed by Claude
(one-token-one-voice enforced by refusal; VOTE_WEIGHT gate added to the shared FORBIDDEN scan;
objector tokens kept out of every output; verdict kept categorical with no tally).
"""
import re
import unicodedata


class GovernanceBreachError(Exception):
    """Raised when a governance round breaches the envelope, a shape scan, or ballot integrity.

    The function rejects the input outright and never repairs or strips fields. Out-of-circle and
    expired dispositions are dropped-and-counted, not raised.
    """
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


# Vote-weight shapes: the anti-plutocracy firewall (invariant 7). No weight/share/voting-power/tally
# field is a representable input, so reputation cannot weight a voice. Biased to over-refuse (a false
# refusal is safe; a false admit is a plutocracy leak) — see failure-model ST1. (bilingual)
VOTE_WEIGHT_KEYS = [
    'weight', 'peso', 'shares', 'acciones', 'voting_power', 'poder_de_voto',
    'vote_count', 'conteo', 'tally', 'recuento', 'majority', 'mayoria',
    'percent', 'porcentaje', 'proxy', 'seats', 'escanos', 'quorum', 'cuota',
]

_ALLOWED_DISPOSITIONS = ('consent', 'object', 'abstain')
_DISPOSITION_KEYS = ('token', 'disposition', 'objection', 'circle_id', 'expires_at')
_OBJECTION_KEYS = ('paramount', 'reason')


def _scan_keys(obj, taxonomy):
    """Recursively scan dict KEYS (exact token/bigram, any depth) against a taxonomy,
    and every string VALUE for a Venezuelan identity pattern.

    Returns (found, matching_key). Keys only for taxonomy — mirrors the other layers.
    """
    taxonomy = set(taxonomy)
    if isinstance(obj, dict):
        for key, value in obj.items():
            if _key_matches_taxonomy(key, taxonomy):
                return True, str(key)
            if _value_has_identity_shape(value):
                return True, str(key)
            found, match = _scan_keys(value, taxonomy)
            if found:
                return True, match
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            if _value_has_identity_shape(item):
                return True, str(item)
            found, match = _scan_keys(item, taxonomy)
            if found:
                return True, match
    return False, None


def _is_expired(expires_at, now):
    """A disposition is expired iff it carries an expires_at and expires_at <= now (lexicographic)."""
    if expires_at is None:
        return False
    return expires_at <= now


def _validate_envelope(request):
    if not isinstance(request, dict):
        raise GovernanceBreachError("request must be a dict")

    circle_id = request.get('circle_id')
    if not isinstance(circle_id, str) or circle_id == '':
        raise GovernanceBreachError("circle_id must be a non-empty string")

    proposal_id = request.get('proposal_id')
    if not isinstance(proposal_id, str) or proposal_id == '':
        raise GovernanceBreachError("proposal_id must be a non-empty string")

    now = request.get('now')
    if not isinstance(now, str) or now == '':
        raise GovernanceBreachError("now must be a non-empty ISO-8601 string")

    expires_at = request.get('expires_at')
    if not isinstance(expires_at, str) or expires_at == '':
        raise GovernanceBreachError("expires_at must be a non-empty ISO-8601 string")

    dispositions = request.get('dispositions')
    if not isinstance(dispositions, list):
        raise GovernanceBreachError("dispositions must be a list")

    for i, d in enumerate(dispositions):
        if not isinstance(d, dict):
            raise GovernanceBreachError(f"dispositions[{i}] must be a dict")
        for key in d:
            if key not in _DISPOSITION_KEYS:
                raise GovernanceBreachError(f"dispositions[{i}] contains disallowed key: {key!r}")

        token = d.get('token')
        if not isinstance(token, str) or token == '':
            raise GovernanceBreachError(f"dispositions[{i}]['token'] must be a non-empty string")

        disposition = d.get('disposition')
        if disposition not in _ALLOWED_DISPOSITIONS:
            raise GovernanceBreachError(
                f"dispositions[{i}]['disposition'] must be one of {_ALLOWED_DISPOSITIONS}; "
                f"got {disposition!r}"
            )

        d_circle = d.get('circle_id')
        if not isinstance(d_circle, str) or d_circle == '':
            raise GovernanceBreachError(f"dispositions[{i}]['circle_id'] must be a non-empty string")

        d_exp = d.get('expires_at')
        if d_exp is not None and (not isinstance(d_exp, str) or d_exp == ''):
            raise GovernanceBreachError(
                f"dispositions[{i}]['expires_at'] must be a non-empty string or null"
            )

        objection = d.get('objection')
        if disposition == 'object':
            if not isinstance(objection, dict):
                raise GovernanceBreachError(
                    f"dispositions[{i}]: an 'object' disposition must carry an objection dict"
                )
            for key in objection:
                if key not in _OBJECTION_KEYS:
                    raise GovernanceBreachError(
                        f"dispositions[{i}]['objection'] contains disallowed key: {key!r}"
                    )
            paramount = objection.get('paramount')
            if not isinstance(paramount, bool):
                raise GovernanceBreachError(
                    f"dispositions[{i}]['objection']['paramount'] must be a bool"
                )
            reason = objection.get('reason')
            if not isinstance(reason, str) or reason == '':
                raise GovernanceBreachError(
                    f"dispositions[{i}]['objection']['reason'] must be a non-empty string"
                )
        else:
            if objection is not None:
                raise GovernanceBreachError(
                    f"dispositions[{i}]: only an 'object' disposition may carry an objection"
                )


def decide(request: dict) -> dict:
    """Resolve one proposal in one circle by consent (absence of a paramount objection).

    Pure, deterministic, side-effect-free. On any envelope/shape/integrity breach, raises
    GovernanceBreachError; out-of-circle and expired dispositions are dropped-and-counted (never
    raised). Persists nothing. Returns the decision envelope specified in capa6/spec.md.
    """
    # 1. Validate envelope (reject, never repair).
    _validate_envelope(request)

    circle_id = request['circle_id']
    proposal_id = request['proposal_id']
    now = request['now']
    proposal_expiry = request['expires_at']
    dispositions = request['dispositions']

    # 2. Surveillance + vote-weight scan over the WHOLE request (keys, recursive). A shape
    #    violation is refused broadly, before any filtering — as in every layer.
    found, match_key = _scan_keys(request, FORBIDDEN_KEYS)
    if found:
        raise GovernanceBreachError(f"Surveillance shape detected in request: key {match_key!r}")
    found, match_key = _scan_keys(request, VOTE_WEIGHT_KEYS)
    if found:
        raise GovernanceBreachError(
            f"Vote-weight shape detected in request (voice is independent of reputation): "
            f"key {match_key!r}"
        )

    # 3. Circle scope + forgetting (drop-and-count, never raise). An off-circle or expired
    #    disposition is NOT part of this circle's round — it is dropped, never fatal.
    considered_dispositions = len(dispositions)
    dropped_off_circle = 0
    dropped_expired = 0
    survivors = []
    for d in dispositions:
        if d['circle_id'] != circle_id:            # circle-local; no cross-circle vote
            dropped_off_circle += 1
            continue
        if _is_expired(d.get('expires_at'), now):  # per-round forgetting
            dropped_expired += 1
            continue
        survivors.append(d)

    # 4. One token, one voice — a PER-CIRCLE invariant (invariant 7; D-03). Uniqueness is
    #    enforced only among the surviving (in-circle, unexpired) voices: a repeated token on
    #    an off-circle or expired disposition is already dropped and must not veto this round
    #    (that would let a straggler scoped to another circle block a legitimate decision).
    seen_tokens = set()
    for d in survivors:
        tok = d['token']
        if tok in seen_tokens:
            raise GovernanceBreachError(
                f"one token, one voice: token {tok!r} appears on more than one "
                f"in-circle disposition"
            )
        seen_tokens.add(tok)

    # 5. Resolve consent (categorical, NO tally) over the surviving voices.
    paramount_reasons = []
    concern_reasons = []
    for d in survivors:
        if d['disposition'] == 'object':
            objection = d['objection']
            if objection['paramount']:
                paramount_reasons.append(objection['reason'])
            else:
                concern_reasons.append(objection['reason'])

    # 6. Surface reasons, never people. Canonical (deterministic) sort by reason.
    paramount_objections = [{'reason': r} for r in sorted(paramount_reasons)]
    concerns = [{'reason': r} for r in sorted(concern_reasons)]

    # Consent = the ABSENCE of a paramount objection. One reasoned block is decisive; a thousand
    # consents do not out-vote it. No count decides.
    verdict = 'revisit' if paramount_objections else 'adopted'

    # 7. Assemble output. Scope to the circle; do not propagate to any parent. Persist nothing.
    return {
        'circle_id': circle_id,
        'proposal_id': proposal_id,
        'verdict': verdict,
        'paramount_objections': paramount_objections,
        'concerns': concerns,
        'note': ("Consent is the absence of a paramount objection, never a majority. An objection is "
                 "a reasoned pause that opens revision, never a mark against anyone. Scoped to this "
                 "circle; it does not propagate."),
        'expires_at': proposal_expiry,
        'audit_trace': {
            'rule': ("adopted iff no paramount objection; one token one voice; voice independent of "
                     "reputation; no tally, no majority; circle-local; per-round forgetting"),
            'considered_dispositions': considered_dispositions,
            'dropped_off_circle': dropped_off_circle,
            'dropped_expired': dropped_expired,
            'paramount_objections': len(paramount_objections),
            'concerns': len(concerns),
        },
    }
