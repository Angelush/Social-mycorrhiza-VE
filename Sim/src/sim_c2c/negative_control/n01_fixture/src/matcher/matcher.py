"""Capa-3 prosocial-affordance matcher ("el emparejador") for the Micorriza social protocol.

This module is the deterministic guardrail wrapped around the FIRST LLM in the stack. The
stochastic model *proposes* candidate matches; this pure, deterministic wrapper *validates,
bounds, and shapes* them; a human *disposes*. The model is injected behind a `propose`
callable and is NEVER trusted blindly: everything it returns is validated against a strict
schema and DROPPED if it is off-schema, off-cell, for an ineligible (non-consenting / expired /
out-of-cell / unknown) token, surveillance-shaped, or engagement-shaped.

The whole design problem is that this is the first LLM, and the gravitational pull of every
recommender is engagement optimization (invariant 8, the platform original sin). The answer is
structural, not a policy line: the engagement signal is made UNREPRESENTABLE — declaration keys
are whitelisted, an ENGAGEMENT_KEY taxonomy is refused, and there is no feedback/outcome input.
The objective is cooperation initiated because the system cannot see anything else.

Five structural walls (spec.md):
 1. Engagement unrepresentable (whitelist + ENGAGEMENT_KEYS scan; only declared offers/needs/goals).
 2. No person-scalar (FORBIDDEN_KEYS scan over both the model's input and its output; a surveillance-
    shaped proposal is dropped, not stripped; cite a Capa-2 fact, never synthesize a rating).
 3. The LLM cannot rank people (the model's order is discarded; a canonical (kind, token, reason)
    sort is imposed — engagement-bait ordering destroyed by construction).
 4. Cell-scoped, thin translation bridge (matches only within the asker's own declared cells).
 5. Forgetting + no dossier (expired declarations dropped; proposals carry expires_at; pure).

The LLM client is INJECTED via `propose`; nothing is imported at module top that touches the
network, so this module stays importable and the whole test suite runs offline with a stub.

Specification: workflows/micorriza-politica/capa3/spec.md

Provenance: drafted by Mistral via multi-model-orchestration (vibe, headless), reviewed and
corrected by Claude (consent-absence made ineligible rather than fatal; declaration list fields
made lenient; cited-facts verbatim matching completed; audit trace finalized).
"""


class MatcherBreachError(Exception):
    """Raised when a match REQUEST breaches the wrapper (envelope or surveillance/engagement shape).

    Note: bad *model output* is never raised — it is dropped-and-counted. The guardrail must not be
    crashable by a bad (or prompt-injected) model. Only a malformed request raises.
    """
    pass


# Surveillance shapes: refused in ALL inputs. Identical to the taxonomy in Capa-1 membrane.py,
# Capa-2 legibility_query.py, and Capa-4 assurance_engine.py. It is defined locally in each layer
# (NOT imported from a shared module — every capa must load standalone by file path); the layers
# are held byte-for-byte in agreement by the AC-X cross-layer test, not by a single source.
FORBIDDEN_KEYS = [
    'score', 'rating', 'reputation', 'rank',
    'blacklist', 'ban', 'penalty', 'global_id', 'dni'
]

# Engagement shapes: the platform original sin (invariant 8). No click/dwell/outcome/virality
# signal is a representable input to the matcher, and no such shape may return from the model.
# Biased to over-refuse (a false refusal is safe; a false admit is an engagement leak) — see ST1.
ENGAGEMENT_KEYS = [
    'click', 'dwell', 'engagement', 'viral', 'watch_time', 'impression',
    'ctr', 'feed', 'time_in_app', 'notification', 'streak', 'like_count', 'follower'
]

_ALLOWED_KINDS = ('offer_meets_need', 'shared_goal', 'translation')
_SELF_KEYS = ('offers', 'needs', 'goals')
_CANDIDATE_KEYS = ('token', 'cell_id', 'offers', 'needs', 'goals', 'consent', 'facts', 'expires_at')


def _matches_taxonomy(key, taxonomy):
    key_lower = str(key).lower()
    for substr in taxonomy:
        if substr in key_lower:
            return True, str(key)
    return False, None


def _scan_forbidden(obj):
    """Recursively scan dict KEYS (case-insensitive substring, any depth) for a forbidden or
    engagement shape. Returns (found, matching_key). Keys only — mirrors the other layers."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            found, mk = _matches_taxonomy(key, FORBIDDEN_KEYS + ENGAGEMENT_KEYS)
            if found:
                return True, mk
            found, mk = _scan_forbidden(value)
            if found:
                return True, mk
        return False, None
    if isinstance(obj, (list, tuple)):
        for item in obj:
            found, mk = _scan_forbidden(item)
            if found:
                return True, mk
        return False, None
    return False, None


def _validate_str_list(value, label):
    if not isinstance(value, list):
        raise MatcherBreachError(f"{label} must be a list")
    for item in value:
        if not isinstance(item, str):
            raise MatcherBreachError(f"{label} must contain only strings")


def _validate_declaration_lists(obj, allowed_keys, label):
    """Whitelist keys and type-check the offers/needs/goals lists of a declaration (self/candidate).

    Declaration list fields are OPTIONAL (default empty); any key outside `allowed_keys` is refused
    (there is no field through which an engagement/outcome signal could enter — spec M3)."""
    for key in obj:
        if key not in allowed_keys:
            raise MatcherBreachError(f"{label} contains disallowed key: {key!r}")
    for key in _SELF_KEYS:
        if key in obj:
            _validate_str_list(obj[key], f"{label}.{key}")


def _validate_request(request):
    if not isinstance(request, dict):
        raise MatcherBreachError("request must be a dict")

    asker = request.get('asker')
    if not isinstance(asker, str) or asker == '':
        raise MatcherBreachError("asker must be a non-empty string")

    cell_ids = request.get('cell_ids')
    if not isinstance(cell_ids, list) or len(cell_ids) == 0:
        raise MatcherBreachError("cell_ids must be a non-empty list")
    for cid in cell_ids:
        if not isinstance(cid, str) or cid == '':
            raise MatcherBreachError("each cell_id must be a non-empty string")

    now = request.get('now')
    if not isinstance(now, str) or now == '':
        raise MatcherBreachError("now must be a non-empty string")

    expires_at = request.get('expires_at')
    if not isinstance(expires_at, str) or expires_at == '':
        raise MatcherBreachError("expires_at must be a non-empty string")

    max_proposals = request.get('max_proposals')
    if isinstance(max_proposals, bool) or not isinstance(max_proposals, int):
        raise MatcherBreachError("max_proposals must be an int > 0")
    if max_proposals <= 0:
        raise MatcherBreachError("max_proposals must be an int > 0")

    self_data = request.get('self')
    if not isinstance(self_data, dict):
        raise MatcherBreachError("self must be a dict")
    _validate_declaration_lists(self_data, set(_SELF_KEYS), "self")

    candidates = request.get('candidates')
    if not isinstance(candidates, list):
        raise MatcherBreachError("candidates must be a list")
    for cand in candidates:
        if not isinstance(cand, dict):
            raise MatcherBreachError("each candidate must be a dict")
        _validate_declaration_lists(cand, set(_CANDIDATE_KEYS), "candidate")
        for key in ('token', 'cell_id'):
            val = cand.get(key)
            if not isinstance(val, str) or val == '':
                raise MatcherBreachError(f"candidate {key} must be a non-empty string")
        consent = cand.get('consent')
        if consent is not None and not isinstance(consent, dict):
            raise MatcherBreachError("candidate consent must be a dict when present")
        facts = cand.get('facts')
        if facts is not None:
            if not isinstance(facts, list):
                raise MatcherBreachError("candidate facts must be a list")
            for fact in facts:
                if not isinstance(fact, dict):
                    raise MatcherBreachError("each fact must be a dict")
                for fk in ('statement', 'cell_id'):
                    if not isinstance(fact.get(fk), str) or fact.get(fk) == '':
                        raise MatcherBreachError(f"fact {fk} must be a non-empty string")
                fexp = fact.get('expires_at')
                if fexp is not None and not isinstance(fexp, str):
                    raise MatcherBreachError("fact expires_at must be a string or null")
        cexp = cand.get('expires_at')
        if cexp is not None and not isinstance(cexp, str):
            raise MatcherBreachError("candidate expires_at must be a string or null")


def _is_unexpired(expires_at, now):
    if expires_at is None:
        return True
    return expires_at > now


def match(request: dict, propose) -> dict:
    """Surface a bounded, ephemeral list of candidate matches for `request['asker']`.

    Pure, deterministic, side-effect-free. `propose(context) -> list[dict]` is the INJECTED
    stochastic model; it is never trusted. On any malformed REQUEST, raises MatcherBreachError;
    bad model output is dropped-and-counted (never raised). Persists nothing.

    Returns the proposal envelope specified in capa3/spec.md.
    """
    if not callable(propose):
        raise MatcherBreachError("propose must be a callable")

    # 1. Validate envelope (reject, never repair).
    _validate_request(request)

    # 2. Surveillance + engagement scan over the WHOLE request (keys, recursive).
    found, mk = _scan_forbidden(request)
    if found:
        raise MatcherBreachError(f"Surveillance/engagement shape detected in request: key {mk!r}")

    now = request['now']
    cell_ids = set(request['cell_ids'])
    max_proposals = request['max_proposals']
    proposal_expiry = request['expires_at']

    # 3. Eligibility filter (BEFORE the model sees anything): in-cell, consenting, unexpired.
    eligible = {}  # token -> candidate (insertion order preserved)
    eligible_context = []
    for cand in request['candidates']:
        consent = cand.get('consent') or {}
        in_cell = cand['cell_id'] in cell_ids
        consenting = consent.get('surfaceable') is True
        unexpired = _is_unexpired(cand.get('expires_at'), now)
        if in_cell and consenting and unexpired:
            eligible[cand['token']] = cand
            eligible_context.append(cand)

    # 4. Build the sanitized context and call the injected proposer.
    context = {
        'asker': request['asker'],
        'self': request['self'],
        'candidates': eligible_context,
    }
    raw = propose(context)
    if not isinstance(raw, list):
        raw = []

    # 5. Validate every proposal; DROP (never trust) the bad ones, counting each drop.
    dropped_off_schema = 0
    dropped_unknown_token = 0
    dropped_surveillance_shape = 0
    survivors = []
    for p in raw:
        if not isinstance(p, dict):
            dropped_off_schema += 1
            continue
        token = p.get('token')
        reason = p.get('reason')
        kind = p.get('kind')
        if (not isinstance(token, str) or token == ''
                or not isinstance(reason, str) or reason == ''
                or kind not in _ALLOWED_KINDS):
            dropped_off_schema += 1
            continue
        if token not in eligible:
            # unknown / hallucinated token — also catches an off-cell or non-consenting party,
            # which was never eligible and so is never in this set (spec F5/F6/F7).
            dropped_unknown_token += 1
            continue
        found, _mk = _scan_forbidden(p)
        if found:
            # surveillance/engagement shape from the model: drop the WHOLE proposal, never strip.
            dropped_surveillance_shape += 1
            continue

        cand = eligible[token]
        # cite_facts are accepted only if they exactly match a fact declared on that candidate
        # (verbatim cite, no synthesis — spec M4/N9). A non-list cite_facts is model garbage:
        # every cite is dropped, the proposal survives — the wrapper must not be crashable (F7).
        declared_facts = cand.get('facts') or []
        raw_cites = p.get('cite_facts')
        if not isinstance(raw_cites, list):
            raw_cites = []
        cited = [f for f in raw_cites if f in declared_facts]
        survivors.append({
            'token': token,
            'cell_id': cand['cell_id'],
            'kind': kind,
            'reason': reason,
            'cited_facts': cited,
            'expires_at': proposal_expiry,
        })

    # 6. Discard the model's order: canonical sort, dedupe by (token, kind), bound to max_proposals.
    survivors.sort(key=lambda x: (x['kind'], x['token'], x['reason']))
    deduped = []
    seen = set()
    for s in survivors:
        key = (s['token'], s['kind'])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(s)
    emitted = deduped[:max_proposals]

    # 7. Assemble output. Commit nothing; persist nothing.
    verdict = 'proposals_surfaced' if emitted else 'no_matches_from_your_position'
    return {
        'asker': request['asker'],
        'cell_ids': list(request['cell_ids']),
        'proposals': emitted,
        'verdict': verdict,
        'note': ("Proposals to surface, never actions taken. A human decides whether to reach out. "
                 "Order is canonical, not a ranking of people."),
        'audit_trace': {
            'rule': ("in-cell, consenting, unexpired candidates; LLM proposals "
                     "validated/bounded/canonically-sorted; no scalar, no engagement signal"),
            'eligible_candidates': len(eligible),
            'proposed_by_model': len(raw),
            'dropped_off_schema': dropped_off_schema,
            'dropped_off_cell': 0,
            'dropped_non_consenting': 0,
            'dropped_surveillance_shape': dropped_surveillance_shape,
            'dropped_unknown_token': dropped_unknown_token,
            'emitted': len(emitted),
            'max_proposals': max_proposals,
        },
    }
