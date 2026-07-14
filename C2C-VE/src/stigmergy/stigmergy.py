"""Capa-5 stigmergic coordination + anti-cascade circuit breakers for the Micorriza social protocol.

This module implements a pure, deterministic, side-effect-free read of the environmental traces
visible from ONE cell — contribution histories, paths, artifacts, signals — the way FOSS, Wikipedia,
or Hayek's prices coordinate without a commander (brief §4 Capa 5, §5 estigmergia). It applies
pheromone EVAPORATION (forgetting) and the anti-cascade CIRCUIT BREAKERS (invariant 9) so the same
mechanism that coordinates cannot also produce the "ant mill" (death spiral), the information cascade,
or the mob.

It is DETERMINISTIC, NOT an LLM: no stochastic core, no injected model, no network client — that is
the whole difference from Capa 3.

Four structural walls (spec.md):
 1. Traces are ENVIRONMENTAL, never a person-scalar. `about` is an artifact/path/contribution token;
    the shared FORBIDDEN_KEY taxonomy refuses a score/rank/reputation/blacklist trace; the `signal`
    is whitelisted to positive/environmental kinds so no ban/distrust signal is representable
    (invariants 2/3, positive-sum).
 2. Forgetting is LOAD-BEARING — pheromone evaporation: effective = strength * 0.5^(elapsed/half_life);
    a faded trace is dropped before sensing. Evaporation is the mechanism, not a stamp (invariant 5).
 3. Anti-cascade breakers (invariant 9), each structural: (a/c) a VELOCITY CAP throttles a burst per
    artifact per window (friction/velocity-limit); (b) a `flag` with no context is DAMPED (context
    before judgment); (d) an off-cell trace is dropped (ZERO global broadcast, invariant 4).
 4. Cell-scoped, caller-supplied, scanned-and-discarded: pure over supplied local state; nothing
    persisted; no central holder; byte-deterministic (invariants 4/6).

On any ENVELOPE/SHAPE breach (bad type, non-whitelisted key/signal, a FORBIDDEN key) the module RAISES
StigmergyBreachError (never repairs, never strips). Cascade-shaped CONTENT (off-cell, future, bare
flag, over-cap, evaporated) is DROPPED-and-counted, never raised — the breaker must not be crashable
by a mob. Time is integer logical ticks (now/created_at) because evaporation needs elapsed-time
arithmetic; this keeps the module stdlib-only with no datetime dependency.

Specification: workflows/micorriza-politica/capa5/spec.md

Provenance: drafted by Mistral via multi-model-orchestration (vibe, headless), reviewed and corrected
by Claude (defaultdict import removed for stdlib-no-import parity with sibling layers; docstring and
audit trace finalized; time-model and drop/damp taxonomy confirmed against spec).
"""
import re
import unicodedata


class StigmergyBreachError(Exception):
    """Raised when a sensing request breaches the envelope or the surveillance-shape scan.

    The function rejects the input outright and never repairs or strips fields. Cascade-shaped
    CONTENT (off-cell/future/bare-flag/over-cap/evaporated traces) is dropped-and-counted, not raised.
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

# Positive-sum signal whitelist: environmental trace kinds only. No ban/distrust/condemn signal is
# representable (invariant 3). `flag` is the one judgment-shaped signal — about an ARTIFACT, gated by
# the context-before-judgment breaker.
ALLOWED_SIGNALS = ('contribution', 'path', 'endorsement', 'presence', 'flag')
JUDGMENT_SIGNALS = ('flag',)

# Trace keys are whitelisted so no person-scalar / engagement counter / ban can enter through a field.
_TRACE_KEYS = ('about', 'signal', 'strength', 'created_at', 'cell_id', 'context')


def _scan_forbidden(obj):
    """Recursively scan dict KEYS (exact token/bigram, any depth) for a forbidden shape,
    and every string VALUE for a Venezuelan identity pattern.

    Returns (found, matching_key). Mirrors the other layers.
    """
    taxonomy = set(FORBIDDEN_KEYS)
    if isinstance(obj, dict):
        for key, value in obj.items():
            if _key_matches_taxonomy(key, taxonomy):
                return True, str(key)
            if _value_has_identity_shape(value):
                return True, str(key)
            found, match = _scan_forbidden(value)
            if found:
                return True, match
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            if _value_has_identity_shape(item):
                return True, str(item)
            found, match = _scan_forbidden(item)
            if found:
                return True, match
    return False, None


def sense(request: dict) -> dict:
    """Sense the throttled, evaporated environmental traces visible from one cell.

    Pure, deterministic, side-effect-free. On any envelope/shape breach, raises
    StigmergyBreachError; cascade-shaped content is dropped-and-counted (never raised). Persists
    nothing. Returns the sensing envelope specified in capa5/spec.md.
    """
    # 1. Validate envelope (reject, never repair).
    if not isinstance(request, dict):
        raise StigmergyBreachError("request must be a dict")

    cell_id = request.get('cell_id')
    if not isinstance(cell_id, str) or cell_id == '':
        raise StigmergyBreachError("cell_id must be a non-empty string")

    now = request.get('now')
    if not isinstance(now, int) or isinstance(now, bool):
        raise StigmergyBreachError("now must be an int (logical tick)")

    window = request.get('window')
    if not isinstance(window, int) or isinstance(window, bool) or window <= 0:
        raise StigmergyBreachError("window must be an int > 0")

    velocity_cap = request.get('velocity_cap')
    if not isinstance(velocity_cap, int) or isinstance(velocity_cap, bool) or velocity_cap <= 0:
        raise StigmergyBreachError("velocity_cap must be an int > 0")

    half_life = request.get('half_life')
    if not isinstance(half_life, int) or isinstance(half_life, bool) or half_life <= 0:
        raise StigmergyBreachError("half_life must be an int > 0")

    min_strength = request.get('min_strength')
    if isinstance(min_strength, bool) or not isinstance(min_strength, (int, float)):
        raise StigmergyBreachError("min_strength must be a number")
    if min_strength < 0:
        raise StigmergyBreachError("min_strength must be >= 0")

    traces = request.get('traces')
    if not isinstance(traces, list):
        raise StigmergyBreachError("traces must be a list")

    for i, trace in enumerate(traces):
        if not isinstance(trace, dict):
            raise StigmergyBreachError(f"traces[{i}] must be a dict")
        for key in trace:
            if key not in _TRACE_KEYS:
                raise StigmergyBreachError(f"traces[{i}] contains disallowed key: {key!r}")
        about = trace.get('about')
        if not isinstance(about, str) or about == '':
            raise StigmergyBreachError(f"traces[{i}]['about'] must be a non-empty string")
        signal = trace.get('signal')
        if signal not in ALLOWED_SIGNALS:
            raise StigmergyBreachError(
                f"traces[{i}]['signal'] must be one of {ALLOWED_SIGNALS}; got {signal!r}"
            )
        strength = trace.get('strength')
        if isinstance(strength, bool) or not isinstance(strength, (int, float)):
            raise StigmergyBreachError(f"traces[{i}]['strength'] must be a number")
        if strength <= 0:
            raise StigmergyBreachError(f"traces[{i}]['strength'] must be > 0")
        created_at = trace.get('created_at')
        if not isinstance(created_at, int) or isinstance(created_at, bool):
            raise StigmergyBreachError(f"traces[{i}]['created_at'] must be an int (logical tick)")
        trace_cell_id = trace.get('cell_id')
        if not isinstance(trace_cell_id, str) or trace_cell_id == '':
            raise StigmergyBreachError(f"traces[{i}]['cell_id'] must be a non-empty string")
        context = trace.get('context')
        if context is not None and not isinstance(context, str):
            raise StigmergyBreachError(f"traces[{i}]['context'] must be a string or null")

    # 2. Surveillance scan over the WHOLE request (keys, recursive).
    found, matching_key = _scan_forbidden(request)
    if found:
        raise StigmergyBreachError(f"Surveillance shape detected in request: key {matching_key!r}")

    # 3. Per-trace damping (drop-and-count, never raise): cell scope, future, context-before-judgment.
    considered_traces = len(traces)
    dropped_off_cell = 0
    dropped_future = 0
    damped_no_context = 0
    damped_velocity = 0
    evaporated = 0

    candidates = []
    for trace in traces:
        if trace['cell_id'] != cell_id:            # wall 3(d): zero global broadcast
            dropped_off_cell += 1
            continue
        if trace['created_at'] > now:              # future trace
            dropped_future += 1
            continue
        if trace['signal'] in JUDGMENT_SIGNALS:    # wall 3(b): context before judgment
            ctx = trace.get('context')
            if ctx is None or ctx == '':
                damped_no_context += 1
                continue
        candidates.append(trace)

    # 4. Velocity throttle (friction / velocity-limit, walls 3(a)/(c)). The cap applies per
    #    artifact PER WINDOW-BUCKET, not only the current window (D-04). A burst is a burst
    #    whatever tick it is dated to, so a burst backdated just past the window can no longer
    #    escape the throttle while a large half_life leaves it barely evaporated. Bucket 0 is
    #    the current window — the closed interval [now - window, now], preserving ST3 — and each
    #    older window is its own bucket, so genuine sustained coordination (traces spread across
    #    many windows) still passes: each bucket under the cap survives.
    def _window_bucket(created_at):
        elapsed = now - created_at            # >= 0 here (future already dropped)
        if elapsed <= window:                 # current window, closed interval (ST3)
            return 0
        return 1 + (elapsed - window - 1) // window

    groups = {}  # (about, bucket) -> [traces] (plain dict; sibling layers import nothing)
    for t in candidates:
        groups.setdefault((t['about'], _window_bucket(t['created_at'])), []).append(t)

    all_survivors = []
    for key in groups:
        group = groups[key]
        if len(group) > velocity_cap:
            group_sorted = sorted(
                group, key=lambda x: (x['created_at'], x['about'], x['signal'], x['strength'])
            )
            all_survivors.extend(group_sorted[:velocity_cap])  # keep the earliest cap per bucket
            damped_velocity += len(group) - velocity_cap
        else:
            all_survivors.extend(group)

    # 5. Evaporation (pheromone decay, wall 2): fade by half-life; drop below the floor.
    sensed = []
    for t in all_survivors:
        elapsed = now - t['created_at']            # >= 0 here (future already dropped)
        effective = round(t['strength'] * (0.5 ** (elapsed / half_life)), 6)
        if effective < min_strength:
            evaporated += 1
            continue
        sensed.append({
            'about': t['about'],
            'signal': t['signal'],
            'cell_id': t['cell_id'],
            'effective_strength': effective,
            'context': t.get('context'),
        })

    # 6. Canonical sort (a deterministic environmental read, not a people-ranking).
    sensed.sort(key=lambda x: (x['about'], x['signal'], -x['effective_strength'], str(x['context'])))

    # 7. Assemble output. Commit nothing; persist nothing.
    verdict = 'signals_sensed' if sensed else 'quiet_from_your_cell'
    return {
        'cell_id': cell_id,
        'now': now,
        'sensed': sensed,
        'verdict': verdict,
        'note': ("Traces sensed from your cell, evaporating and throttled; absence is quiet, "
                 "never a mark against anyone."),
        'audit_trace': {
            'rule': ("environmental traces only; evaporation by half-life; cell-scoped; "
                     "context-before-judgment; velocity-capped per window; no person-scalar"),
            'considered_traces': considered_traces,
            'dropped_off_cell': dropped_off_cell,
            'dropped_future': dropped_future,
            'damped_no_context': damped_no_context,
            'damped_velocity': damped_velocity,
            'evaporated': evaporated,
            'sensed': len(sensed),
            'window': window,
            'velocity_cap': velocity_cap,
            'half_life': half_life,
            'min_strength': min_strength,
        },
    }
