"""Capa-2 trust-legibility query for the Micorriza social protocol.

This module implements a pure, deterministic, side-effect-free legibility query
that answers the single question: from the asker's position, do the people I trust
vouch for X, here, now? It returns specific vouch-paths and facts reachable from
the asker within the cell, or the neutral verdict no_info_from_your_position
when none are reachable.

The component is a web-of-trust query over a caller-supplied local graph. It emits
no score, no rank, no reputation number, and no moral verdict. It classifies
reachability from a position; it never rates a person. The god-view is made
structurally unrepresentable: the asker is required, the graph is caller-supplied
and discarded, traversal is hop-bounded, and output is paths/facts not a scalar.

Surveillance shapes (FORBIDDEN_KEYS) are refused outright using the exact
Capa-1/Capa-4 taxonomy, scanned recursively over the whole input (graph included).
Key matching is case-insensitive substring matching at any depth.

Specification: workflows/micorriza-politica/capa2/spec.md

Provenance: drafted by Mistral via multi-model-orchestration, reviewed by Claude.
"""


class LegibilityBreachError(Exception):
    """Raised when a request breaches legibility rules (envelope or surveillance-shape).
    
    The query rejects the input outright and never repairs or strips fields.
    """
    pass


# Surveillance shapes: forbidden in ALL inputs, scanned over the WHOLE request.
# Exact same taxonomy as Capa-1 membrane.py and Capa-4 assurance_engine.py, verbatim.
FORBIDDEN_KEYS = [
    'score', 'rating', 'reputation', 'rank',
    'blacklist', 'ban', 'penalty', 'global_id', 'dni'
]

# Upper bound on the concrete vouch-paths enumerated for illustration (D-02). The meaningful
# answers — reachable, nearest_hops, and vouched_by_people_you_trust — are computed exactly via a
# linear reverse BFS and are NEVER capped; only the concrete path SAMPLE is bounded, so a dense
# caller-supplied graph can no longer blow up into an exponential number of paths. When the sample
# is capped, audit_trace.paths_truncated is True (the reachability answer is still complete).
_MAX_VOUCH_PATHS = 256


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


def _is_unexpired(expires_at, now):
    """Check if an item is unexpired at `now`.
    
    Unexpired = expires_at is None/absent, OR (string) expires_at > now
    by plain lexicographic comparison.
    """
    if expires_at is None:
        return True
    return expires_at > now


def query(request: dict) -> dict:
    """Single trust-legibility query from an asker about a single target.
    
    Pure, deterministic, side-effect-free function. On any breach,
    raises LegibilityBreachError. Never repairs, never returns partial results.
    
    Args:
        request: dict with:
            - asker: non-empty str (REQUIRED)
            - target: a single non-empty str; list/dict/None/"*"/"" -> refused
            - cell_id: non-empty str
            - now: non-empty str (ISO-8601)
            - max_hops: int > 0 (reject bool, <= 0, non-int)
            - graph: dict with:
                - vouches: list of dicts, each {"from": str, "to": str, "cell_id": str, "expires_at": str|null}
                - facts: list of dicts, each {"about": str, "statement": str, "cell_id": str, "expires_at": str|null}
    
    Returns:
        dict with exact output shape specified in spec.md:
            - asker, target, cell_id echoed from input
            - from_your_position: dict with reachable, nearest_hops, vouch_paths, vouched_by_people_you_trust, facts
            - verdict: "known_via_trust" or "no_info_from_your_position"
            - note: fixed string
            - audit_trace: dict with rule, considered_vouches, considered_facts, max_hops
    
    Raises:
        LegibilityBreachError: On any envelope-validation error or surveillance-shape breach.
    """
    # 1. Validate the whole envelope; reject (raise), never repair
    if not isinstance(request, dict):
        raise LegibilityBreachError("request must be a dict")

    # Validate asker
    asker = request.get('asker')
    if not isinstance(asker, str) or asker == '':
        raise LegibilityBreachError("asker must be a non-empty string")

    # Validate target — must be a single non-empty str; refuse list/dict/None/*/empty
    target = request.get('target')
    if target is None:
        raise LegibilityBreachError("target is required and must be a non-empty string")
    if isinstance(target, bool):
        raise LegibilityBreachError("target must be a non-empty string; got bool")
    if not isinstance(target, str):
        raise LegibilityBreachError(
            f"target must be a single non-empty string; got {type(target).__name__}"
        )
    if target == '':
        raise LegibilityBreachError(
            "target must be a non-empty string; got empty string"
        )
    if target == '*':
        raise LegibilityBreachError(
            "target must be a single concrete token; wildcard '*' is not allowed"
        )

    # Validate cell_id
    cell_id = request.get('cell_id')
    if not isinstance(cell_id, str) or cell_id == '':
        raise LegibilityBreachError("cell_id must be a non-empty string")

    # Validate now
    now = request.get('now')
    if not isinstance(now, str) or now == '':
        raise LegibilityBreachError("now must be a non-empty ISO-8601 string")

    # Validate max_hops — must be int > 0, reject bool, reject <= 0, reject non-int
    max_hops = request.get('max_hops')
    if isinstance(max_hops, bool):
        raise LegibilityBreachError("max_hops must be an int > 0; got bool")
    if not isinstance(max_hops, int):
        raise LegibilityBreachError("max_hops must be an int > 0")
    if max_hops <= 0:
        raise LegibilityBreachError("max_hops must be an int > 0")

    # Validate graph
    graph = request.get('graph')
    if not isinstance(graph, dict):
        raise LegibilityBreachError("graph must be a dict")

    # Validate vouches
    vouches = graph.get('vouches')
    if not isinstance(vouches, list):
        raise LegibilityBreachError("graph['vouches'] must be a list")
    for i, v in enumerate(vouches):
        if not isinstance(v, dict):
            raise LegibilityBreachError(f"graph['vouches'][{i}] must be a dict")
        for field in ('from', 'to', 'cell_id'):
            val = v.get(field)
            if not isinstance(val, str) or val == '':
                raise LegibilityBreachError(
                    f"graph['vouches'][{i}]['{field}'] must be a non-empty string"
                )
        # expires_at is optional, can be str or None
        expires_at = v.get('expires_at')
        if expires_at is not None and not isinstance(expires_at, str):
            raise LegibilityBreachError(
                f"graph['vouches'][{i}]['expires_at'] must be a string or null"
            )

    # Validate facts
    facts = graph.get('facts')
    if not isinstance(facts, list):
        raise LegibilityBreachError("graph['facts'] must be a list")
    for i, f in enumerate(facts):
        if not isinstance(f, dict):
            raise LegibilityBreachError(f"graph['facts'][{i}] must be a dict")
        for field in ('about', 'cell_id'):
            val = f.get(field)
            if not isinstance(val, str) or val == '':
                raise LegibilityBreachError(
                    f"graph['facts'][{i}]['{field}'] must be a non-empty string"
                )
        statement = f.get('statement')
        if not isinstance(statement, str) or statement == '':
            raise LegibilityBreachError(
                f"graph['facts'][{i}]['statement'] must be a non-empty string"
            )
        # expires_at is optional, can be str or None
        expires_at = f.get('expires_at')
        if expires_at is not None and not isinstance(expires_at, str):
            raise LegibilityBreachError(
                f"graph['facts'][{i}]['expires_at'] must be a string or null"
            )

    # 2. Surveillance-shape scan over the WHOLE request (graph included), recursive
    found, match_key = _contains_forbidden_key(request, FORBIDDEN_KEYS)
    if found:
        raise LegibilityBreachError(
            f"Surveillance shape detected in request: key {match_key!r}"
        )

    # 3. Filter: keep only vouches/facts whose cell_id == cell_id AND unexpired at now
    # Apply BEFORE traversal
    filtered_vouches = [
        v for v in vouches
        if v['cell_id'] == cell_id and _is_unexpired(v.get('expires_at'), now)
    ]
    filtered_facts = [
        f for f in facts
        if f['cell_id'] == cell_id and _is_unexpired(f.get('expires_at'), now)
    ]
    considered_vouches = len(filtered_vouches)
    considered_facts = len(filtered_facts)

    # 4. Traverse the surviving in-cell vouch edges from the asker's position.
    # Build de-duplicated adjacency (D-05: identical edges must not yield identical duplicate
    # paths). `adj` is forward (from -> sorted unique tos); `radj` is reverse (to -> {froms}),
    # used to compute distances TO the target without enumerating any path.
    adj = {}
    radj = {}
    for v in filtered_vouches:
        fr = v['from']
        to = v['to']
        adj.setdefault(fr, set()).add(to)
        radj.setdefault(to, set()).add(fr)
    adj = {k: sorted(tos) for k, tos in adj.items()}

    paths_truncated = False

    # Special case: asker == target yields NO path (self-vouch is not legibility).
    if asker == target:
        vouch_paths = []
        nearest_hops = None
        vouched_by_people_you_trust = []
    else:
        # (a) Reverse BFS from the target over reversed edges gives dist_to_target[node] for every
        # node within max_hops — LINEAR in the graph, no path enumeration. This yields reachability,
        # nearest_hops, and (below) the exact set of direct trustees on a shortest path, none of
        # which can explode on a dense graph (D-02). A shortest path is inherently simple, so no
        # cycle guard is needed here.
        dist_to_target = {target: 0}
        frontier = [target]
        for hop in range(1, max_hops + 1):
            next_frontier = []
            for node in frontier:
                for pred in radj.get(node, ()):        # nodes with an edge INTO `node`
                    if pred not in dist_to_target:
                        dist_to_target[pred] = hop
                        next_frontier.append(pred)
            if not next_frontier:
                break
            frontier = next_frontier

        nearest_hops = dist_to_target.get(asker)
        if nearest_hops is None or nearest_hops > max_hops:
            nearest_hops = None
            vouch_paths = []
            vouched_by_people_you_trust = []
        else:
            # (b) Direct trustees of the asker on SOME shortest path — EXACT and complete (never
            # capped): a neighbour n qualifies iff dist_to_target[n] == nearest_hops - 1.
            vouched_by_people_you_trust = sorted(
                n for n in adj.get(asker, ())
                if dist_to_target.get(n) == nearest_hops - 1
            )
            # (c) A DETERMINISTIC, BOUNDED sample of concrete shortest paths. We walk only
            # distance-decreasing edges (dist_to_target strictly drops by 1 each step, so every
            # branch reaches the target — no dead ends) and stop at _MAX_VOUCH_PATHS. Only target
            # carries dist 0, so `dist == 0` is exactly the target. Discovery order is deterministic;
            # the final sort makes the output canonical regardless.
            vouch_paths = []
            stack = [[asker]]
            while stack and not paths_truncated:
                path = stack.pop()
                remaining = nearest_hops - (len(path) - 1)   # edges still needed to reach target
                for nb in sorted(adj.get(path[-1], ()), reverse=True):  # reverse: pop() yields asc
                    if dist_to_target.get(nb) != remaining - 1:
                        continue                              # off the shortest-path front
                    new_path = path + [nb]
                    if nb == target:
                        vouch_paths.append(new_path)
                        if len(vouch_paths) >= _MAX_VOUCH_PATHS:
                            paths_truncated = True
                            break
                    else:
                        stack.append(new_path)
            vouch_paths.sort()

    # 5. Gather surviving in-cell facts whose about == target, sorted deterministically
    target_facts = [
        f for f in filtered_facts
        if f['about'] == target
    ]
    target_facts.sort(key=lambda x: x['statement'])

    # 6. Build output
    reachable = nearest_hops is not None   # exact (from the reverse BFS), not the capped sample
    has_facts = len(target_facts) > 0
    verdict = "known_via_trust" if (reachable or has_facts) else "no_info_from_your_position"

    return {
        'asker': asker,
        'target': target,
        'cell_id': cell_id,
        'from_your_position': {
            'reachable': reachable,
            'nearest_hops': nearest_hops,
            'vouch_paths': vouch_paths,
            'vouched_by_people_you_trust': vouched_by_people_you_trust,
            'facts': [
                {
                    'statement': f['statement'],
                    'cell_id': f['cell_id'],
                    'expires_at': f.get('expires_at')
                }
                for f in target_facts
            ]
        },
        'verdict': verdict,
        'note': "Absence of a path is 'no information from where you stand', never a mark against anyone.",
        'audit_trace': {
            'rule': "in-cell, unexpired vouch-paths from the asker within max_hops; facts about the target",
            'considered_vouches': considered_vouches,
            'considered_facts': considered_facts,
            'max_hops': max_hops,
            'max_vouch_paths': _MAX_VOUCH_PATHS,
            'paths_truncated': paths_truncated
        }
    }
