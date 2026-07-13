"""Track A — C2C integrity oracles. Red/green, halt-on-violation, position-relative.

Independence discipline (N-03 style, AST-checked in the tests): this module imports NO C2C module.
It re-derives every property from the recorded ModuleCall(request, output) pairs using its OWN copy
of the taxonomies and its OWN recompute — never the SUT's numbers or its scan. The six taxonomies
below are duplicated verbatim from the six Capa layers on purpose: an oracle that imported the
layer it checks would be self-confirmation, not an independent check.
"""
from __future__ import annotations

from collections.abc import Sequence

from engine.measurement import IntegrityReport, InvariantResult, TrackA, Verdict
from engine.types import TraceEvent
from .world import ModuleCall, Rejected

# --- independent copies of the six taxonomies (NOT imported from C2C) ------------------------
FORBIDDEN_KEYS = ['score', 'rating', 'reputation', 'rank',
                  'blacklist', 'ban', 'penalty', 'global_id', 'dni']
MARKET_KEYS = ['price', 'cost', 'fee', '_cents', 'currency', 'valuation', 'denominat']
RECIPROCITY_LEDGER_KEYS = ['debt', 'owed', 'balance', 'credit', 'reciprocity', 'iou', 'favor_balance']
ENGAGEMENT_KEYS = ['click', 'dwell', 'engagement', 'viral', 'watch_time', 'impression',
                   'ctr', 'feed', 'time_in_app', 'notification', 'streak', 'like_count', 'follower']

# Known descriptive output schemas — the oracle's own knowledge of each module's LEGAL output shape.
# A silent per-person scalar (e.g. a 'reachability' table that carries no forbidden substring) shows
# up as a key OUTSIDE this closed schema — that is how T-A1 catches it structurally, not by name.
_TOP_SCHEMA = {
    "admit": {"mode", "cell_id", "interaction_id", "expires_at", "admitted", "audit_trace"},
    "query": {"asker", "target", "cell_id", "from_your_position", "verdict", "note", "audit_trace"},
    "match": {"asker", "cell_ids", "proposals", "verdict", "note", "audit_trace"},
    "resolve": {"campaign_id", "cell_id", "status", "distinct_committers", "threshold",
                "expires_at", "resolution", "audit_trace"},
    "sense": {"cell_id", "now", "sensed", "verdict", "note", "audit_trace"},
    "decide": {"circle_id", "proposal_id", "verdict", "paramount_objections", "concerns",
               "note", "expires_at", "audit_trace"},
}
_FROM_POSITION_SCHEMA = {"reachable", "nearest_hops", "vouch_paths",
                         "vouched_by_people_you_trust", "facts"}


def _find_key(obj, substrings):
    """Recursive case-insensitive key-substring scan (the oracle's own, mirrors the layers)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            kl = str(k).lower()
            for s in substrings:
                if s in kl:
                    return str(k)
            hit = _find_key(v, substrings)
            if hit is not None:
                return hit
    elif isinstance(obj, (list, tuple)):
        for it in obj:
            hit = _find_key(it, substrings)
            if hit is not None:
                return hit
    return None


def _contains_str(obj, needle: str) -> bool:
    if isinstance(obj, str):
        return obj == needle
    if isinstance(obj, dict):
        return any(_contains_str(k, needle) or _contains_str(v, needle) for k, v in obj.items())
    if isinstance(obj, (list, tuple)):
        return any(_contains_str(it, needle) for it in obj)
    return False


def _unexpired(expires_at, now) -> bool:
    return expires_at is None or expires_at > now


def _window_bucket(created_at: int, now: int, window: int) -> int:
    elapsed = now - created_at
    if elapsed <= window:
        return 0
    return 1 + (elapsed - window - 1) // window


class C2CTrackA(TrackA):
    def measure(self, trace: Sequence[TraceEvent]) -> IntegrityReport:
        calls = [(e, e.result) for e in trace if isinstance(e.result, ModuleCall)]

        v1, t1 = Verdict.PASS, None   # no_person_scalar
        v2, t2 = Verdict.PASS, None   # no_market_leak
        v3, t3 = Verdict.PASS, None   # asker_relative
        v4, t4 = Verdict.PASS, None   # forgetting
        v5, t5 = Verdict.PASS, None   # consent_privacy
        v6, t6 = Verdict.PASS, None   # anti_cascade

        for event, mc in calls:
            out = mc.output
            if isinstance(out, Rejected):
                # the module's own wall fired — nothing was emitted; oracles judge only what a
                # SUCCESSFUL call returned (a bypassed wall is exactly what they must catch).
                continue

            # T-A1: no surveillance-shaped key AND no out-of-schema (person-scalar) key emitted.
            if v1 is Verdict.PASS:
                hit = _find_key(out, FORBIDDEN_KEYS + ENGAGEMENT_KEYS)
                if hit is not None:
                    v1, t1 = Verdict.FAIL, {"kind": "forbidden_key_in_output",
                                            "method": mc.method, "key": hit}
                else:
                    extra = set(out) - _TOP_SCHEMA.get(mc.method, set(out))
                    if extra:
                        v1, t1 = Verdict.FAIL, {"kind": "out_of_schema_output",
                                                "method": mc.method, "extra": sorted(extra)}
                    elif mc.method == "query":
                        fp = out.get("from_your_position", {})
                        fextra = set(fp) - _FROM_POSITION_SCHEMA
                        if fextra:
                            v1, t1 = Verdict.FAIL, {"kind": "person_scalar_leak",
                                                    "method": "query", "extra": sorted(fextra)}

            # T-A2: an admitted interaction in a non-market room must carry no market/reciprocity key.
            if v2 is Verdict.PASS and mc.method == "admit" and out.get("admitted") is True:
                mode = mc.request.get("mode")
                payload = mc.request.get("payload", {})
                if mode in ("communal_gift", "equality_matching"):
                    hit = _find_key(payload, MARKET_KEYS)
                    if hit is None and mode == "communal_gift":
                        hit = _find_key(payload, RECIPROCITY_LEDGER_KEYS)
                    if hit is not None:
                        v2, t2 = Verdict.FAIL, {"kind": "market_leak_admitted",
                                                "mode": mode, "key": hit,
                                                "interaction_id": mc.request.get("interaction_id")}

            # T-A3: every returned vouch_path is asker-relative: starts at the asker, ends at target.
            if v3 is Verdict.PASS and mc.method == "query":
                asker = out.get("asker")
                target = out.get("target")
                for path in out.get("from_your_position", {}).get("vouch_paths", []):
                    if not path or path[0] != asker or path[-1] != target:
                        v3, t3 = Verdict.FAIL, {"kind": "position_independent_path",
                                                "asker": asker, "target": target, "path": path}
                        break

            # T-A4: forgetting — no expired vouch/fact may surface at request.now.
            if v4 is Verdict.PASS and mc.method == "query":
                now = mc.request.get("now")
                graph = mc.request.get("graph", {})
                cell = mc.request.get("cell_id")
                live_edges = {(v["from"], v["to"]) for v in graph.get("vouches", [])
                              if v.get("cell_id") == cell and _unexpired(v.get("expires_at"), now)}
                for path in out.get("from_your_position", {}).get("vouch_paths", []):
                    for a, b in zip(path, path[1:]):
                        if (a, b) not in live_edges:
                            v4, t4 = Verdict.FAIL, {"kind": "expired_or_off_cell_edge_surfaced",
                                                    "edge": [a, b], "now": now}
                            break
                    if v4 is Verdict.FAIL:
                        break
                if v4 is Verdict.PASS:
                    for f in out.get("from_your_position", {}).get("facts", []):
                        if not _unexpired(f.get("expires_at"), now):
                            v4, t4 = Verdict.FAIL, {"kind": "expired_fact_surfaced",
                                                    "fact": f, "now": now}
                            break

            # T-A5: governance surfaces reasons, never objector tokens.
            if v5 is Verdict.PASS and mc.method == "decide":
                objectors = [d.get("token") for d in mc.request.get("dispositions", [])
                             if d.get("disposition") == "object"]
                for tok in objectors:
                    if tok is not None and _contains_str(out, tok):
                        v5, t5 = Verdict.FAIL, {"kind": "objector_token_leaked", "token": tok}
                        break

            # T-A6: a stigmergy burst over the velocity cap must be throttled (damped_velocity > 0).
            if v6 is Verdict.PASS and mc.method == "sense":
                now = mc.request.get("now")
                window = mc.request.get("window")
                cap = mc.request.get("velocity_cap")
                cell = mc.request.get("cell_id")
                groups: dict[tuple, int] = {}
                for tr in mc.request.get("traces", []):
                    if tr.get("cell_id") != cell:
                        continue
                    if tr.get("created_at", 0) > now:
                        continue
                    if tr.get("signal") == "flag" and not (tr.get("context") or ""):
                        continue
                    key = (tr.get("about"), _window_bucket(tr["created_at"], now, window))
                    groups[key] = groups.get(key, 0) + 1
                burst = any(n > cap for n in groups.values())
                if burst and out["audit_trace"].get("damped_velocity", 0) <= 0:
                    v6, t6 = Verdict.FAIL, {"kind": "unthrottled_burst",
                                            "groups": {str(k): n for k, n in groups.items()},
                                            "cap": cap}

        results = {
            "no_person_scalar": InvariantResult(verdict=v1, exploit_trace=t1),
            "no_market_leak": InvariantResult(verdict=v2, exploit_trace=t2),
            "asker_relative": InvariantResult(verdict=v3, exploit_trace=t3),
            "forgetting": InvariantResult(verdict=v4, exploit_trace=t4),
            "consent_privacy": InvariantResult(verdict=v5, exploit_trace=t5),
            "anti_cascade": InvariantResult(verdict=v6, exploit_trace=t6),
        }
        return IntegrityReport(results=results)
