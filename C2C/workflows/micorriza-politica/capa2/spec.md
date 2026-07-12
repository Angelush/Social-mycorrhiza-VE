# Specification — Capa 2 Trust-Legibility Query ("legibilidad de la confianza")

> Produced by engineer-spec. Self-contained blueprint; an agent can build from this alone.
> Sibling of the Capa-4 and Capa-1 `spec.md`. This is **THE RAZOR'S EDGE** (brief §4 Capa 2,
> §6.1): the layer that most easily slides into the surveillance-score pole. It is built
> **last and with maximum care** (§7 Etapa 2) and routes through the Capa-1 membrane's
> `FORBIDDEN_KEY` taxonomy verbatim so the layers cannot disagree.

## Purpose
Answer, deterministically and **from the asker's own position**, the only legibility question
that stays on the right side of the razor: **"do the people I trust vouch for X, here, now?"**
Not *"how trustworthy is X?"* — that question has no answer in this system, by construction.
The component is a **web-of-trust query** over a *caller-supplied local graph*: given an
`asker`, a `target`, and a `cell_id`, it returns the **specific vouch-paths and facts** reachable
from the asker within the cell, or — when none are reachable — the neutral verdict
`no_info_from_your_position` (which is *not a mark against anyone*). It emits **no score, no
rank, no reputation number, no global view**. It classifies reachability from a position; it
never rates a person.

This is the `[EL FILO DE LA NAVAJA]` component (brief §4 Capa 2). No LLM. Pure function. No
stored state. **The god-view is made structurally unrepresentable** (see "Anti-god-view" below),
the same move that made the surveillance shape unrepresentable in Capa 1.

## The six principles that keep it on the right side of the razor (brief §4 Capa 2)
| # | Principle | How the API enforces it structurally |
|---|---|---|
| 1 | **Contextual, not global** | The query is scoped to one `cell_id`; only edges/facts tagged with that cell are considered. Nothing "follows a person" across cells — there is no cross-cell query. |
| 2 | **Relational, not absolute** | `asker` is a **required** parameter; traversal starts *from* the asker. There is no entrypoint that omits the asker, so there is no absolute/god-view answer to return. |
| 3 | **Specific, not totalizing** | Output is a list of vouch-*paths* and specific *facts* (`"completed 12 exchanges"`, `"vouched by t7"`), each carrying its own cell + expiry provenance. There is **no scalar** and **no moral verdict**. |
| 4 | **Forgetting built in** | Every edge and fact carries `expires_at`; the query takes `now` and **drops expired items before traversal**. Expiry is native, not a caller courtesy. |
| 5 | **Positive-sum** | The graph has **only `vouches` (whitelist) edges**; there is no representable distrust/blacklist edge (and such a key would trip the surveillance scan). Absence of a path yields `no_info`, never a negative mark — you *cannot lower* anyone through this API. |
| 6 | **No central holder** | The graph is a **caller-supplied argument**, scanned and then discarded; nothing is stored. There is no throne, no global graph, no dossier. |

## Anti-god-view (the razor, made structural — the defining design move)
The god-view is not *forbidden by policy*; it is **unrepresentable in the API** — exactly how
Capa 1 made the surveillance shape unrepresentable:
- **Asker required.** `query()` cannot be called without an `asker`; there is no "view of X" —
  only "view of X *from where you stand*." The absolute question cannot be phrased.
- **Graph caller-supplied, never stored.** The function receives the local graph as an argument
  and holds nothing after returning. There is no accumulating trust ledger to capture.
- **Hop-bounded.** Traversal is capped at `max_hops`; the query sees a Dunbar-local neighborhood
  from the asker, never the whole component (invariant 4, local-bounded visibility).
- **Output is paths/facts, not a scalar.** No field ranks, scores, or totalizes the target. The
  count of vouchers is a count *of the specific returned items relative to the asker*, not a
  global reputation (and it diverges by asker — proven by AC7).
- **Absence = "no info", not a mark.** Unreachable ⇒ `no_info_from_your_position`; there is no
  `distrusted`/`low` verdict to emit. Positive-sum by shape (principle 5).
- **No enumeration.** `target` must be a single concrete token; a wildcard/list/`null` target is
  **refused** — the API cannot be turned into "list everyone and their standing" (that is the
  god-view by another door). Single `(asker, target)` per call.
- **Refuses the surveillance shape recursively at any depth**, in the whole input (graph included),
  reusing the Capa-1/Capa-4 `FORBIDDEN_KEY` taxonomy verbatim.

## Input (one query, JSON)
```json
{
  "asker": "str (non-empty) — the querying position; REQUIRED (relational, principle 2)",
  "target": "str (non-empty) — a single concrete token; wildcard/list/null REFUSED (no enumeration)",
  "cell_id": "str (non-empty) — the local context; only in-cell edges/facts count (principle 1)",
  "now": "str (ISO-8601) — evaluation time; items with expires_at <= now are dropped (principle 4)",
  "max_hops": "int > 0 — hop bound from the asker (principle: local-bounded, invariant 4)",
  "graph": {
    "vouches": [
      {"from": "str", "to": "str", "cell_id": "str", "expires_at": "str|null"}
    ],
    "facts": [
      {"about": "str", "statement": "str", "cell_id": "str", "expires_at": "str|null"}
    ]
  }
}
```
- `vouches` are **directed whitelist edges only** (`from` vouches for `to`). There is no distrust
  edge type — it is not representable (principle 5).
- `graph` is the **caller's local graph**, passed in and never stored (principle 6). Tokens are
  opaque, per-cell; the function never binds a token to a person (Sybil out of scope, §6.2).
- `expires_at: null` (or absent) means "no expiry declared" — the item is kept. A **string**
  `expires_at <= now` (lexicographic ISO-8601 compare) means expired → dropped **before** traversal.

## Output (a from-your-position verdict, JSON) — always returns (no "false" verdict)
```json
{
  "asker": "...",
  "target": "...",
  "cell_id": "...",
  "from_your_position": {
    "reachable": true,
    "nearest_hops": 2,
    "vouch_paths": [["<asker>", "t7", "<target>"]],
    "vouched_by_people_you_trust": ["t7"],
    "facts": [{"statement": "completed 12 exchanges", "cell_id": "...", "expires_at": "..."}]
  },
  "verdict": "known_via_trust",
  "note": "Absence of a path is 'no information from where you stand', never a mark against anyone.",
  "audit_trace": {
    "rule": "in-cell, unexpired vouch-paths from the asker within max_hops; facts about the target",
    "considered_vouches": 4,
    "considered_facts": 2,
    "max_hops": 3
  }
}
```
- `verdict` is **categorical and relative**: `known_via_trust` (≥1 path OR ≥1 in-cell fact) or
  `no_info_from_your_position` (neither). **Never a number, never a moral judgement.**
- `nearest_hops` is `null` when unreachable. It is a property of the path *from this asker*, not
  a global rank (it diverges by asker — AC7).
- **The verdict contains no field that scores/ranks/reputes a person and no cross-cell join key.**
- When unreachable and no facts: `reachable: false`, empty `vouch_paths`/`vouched_by`/`facts`,
  `verdict: "no_info_from_your_position"`. This is **not** a blacklist entry — the function still
  returns normally; it simply has nothing to report from that position (principle 5).

## Algorithm (deterministic)
1. **Validate envelope** (reject, do not repair): non-empty `asker`, `cell_id`, `now`; `target`
   a single non-empty **str** (a list/dict/`None`/`"*"` → refuse — no enumeration); `max_hops`
   an `int > 0`; `graph` a dict with list `vouches`/`facts` (each entry a well-formed dict).
2. **Surveillance-shape scan (whole input, recursive):** if any key (case-insensitive substring)
   matches a `FORBIDDEN_KEY` (`score`, `rating`, `reputation`, `rank`, `blacklist`, `ban`,
   `penalty`, `global_id`, `dni`) at any depth → **refuse** (`LegibilityBreachError`). Refuse to
   accept the dossier shape (invariants 2/3/6) — identical taxonomy to Capa 1/Capa 4.
3. **Filter by cell + forgetting:** keep only `vouches`/`facts` whose `cell_id == query cell_id`
   (principle 1) **and** that are unexpired at `now` (`expires_at` is `null`/absent, or the string
   `expires_at > now`) (principle 4). Do this **before** traversal.
4. **Bounded web-of-trust traversal from the asker:** over the surviving in-cell vouch edges
   (de-duplicated — an edge listed twice must not yield a path twice, D-05), determine reachability
   `asker → … → target` within `max_hops`. `reachable`, `nearest_hops` (min hop count, or `null`),
   and `vouched_by_people_you_trust` (the asker's direct trustees on a shortest path) are computed
   **exactly** by a reverse BFS from the target in O(V+E) — never by enumerating paths, so a dense
   caller-supplied graph cannot explode them (D-02). `vouch_paths` is a **deterministic sample** of
   the shortest paths, capped at `_MAX_VOUCH_PATHS`; when the cap bites, `audit_trace.paths_truncated`
   is `true` (the reachability answer stays complete). A direct self-query (`asker == target`) is
   **not** a vouch and yields no path (you don't vouch for yourself into legibility).
5. **Gather target facts:** the surviving in-cell facts whose `about == target`, sorted deterministically.
6. **Assemble verdict:** `reachable` = (≥1 path); `verdict = known_via_trust` if (≥1 path OR ≥1
   fact) else `no_info_from_your_position`. Echo `asker`/`target`/`cell_id`, the paths, the direct
   vouchers on those paths, the facts, and the audit trace. **Commit nothing.**

## Determinism
Pure traversal over a fixed taxonomy with sorted enumeration; no iteration order affects the
output. Same input → byte-identical JSON output.

## Termination & cost
Reachability / `nearest_hops` / `vouched_by` via a reverse BFS: O(V+E) over a caller-bounded local
graph, no path enumeration. The concrete-path sample walks only distance-decreasing edges (never a
dead branch) and stops at `_MAX_VOUCH_PATHS`, so total work is bounded (`_MAX_VOUCH_PATHS × max_hops`)
even on a graph with exponentially many shortest paths — no unbounded loops, no path-count blow-up.

## Meaning layer (Axiom 6 — what the agent cannot infer)
- **This is the razor's edge (§6.1); the stakes are a cage, not a dead network.** Every temptation
  here is toward a *helpful scalar* — "just return an overall trust %". That single number **is**
  the social-credit shape (invariant 2). The correct behavior is to refuse to compute it: emit
  paths and specific facts, never an aggregate rating.
- **The god-view is the failure, and it is made unrepresentable, not merely disallowed.** A query
  that omits the asker, or ranks a person globally, cannot be *phrased* against this API — the
  same structural move as Capa 1's surveillance-shape ban. Policy can be captured; structure cannot.
- **Position-relativity is the whole point (principle 2).** The *same* `(target, cell)` yields
  *different* results for different askers — that divergence is not a bug to smooth over; it is
  the proof there is no god-view (AC7). Never cache a target's result independent of the asker.
- **Absence is not a mark (principle 5, whitelist-not-blacklist).** `no_info_from_your_position`
  means "I can't see them from where you stand", never "they are untrustworthy." There is no
  negative edge and no negative verdict — you cannot lower anyone through this API.
- **Forgetting is native and enforced *here* (principle 4).** Unlike Capa-1/Capa-4 where expiry is
  a carried-through caller convention, this query **actively drops** expired edges/facts before
  answering — legibility that cannot forget is a dossier.
- **No central holder (principle 6).** The graph is the caller's, passed in and discarded. Across
  calls, non-surveillance is a *convention* the pure function cannot police: a caller that stores
  every result and correlates across askers rebuilds a god-view externally. That is the governance
  problem (§6.1), flagged in the failure model — structural per-call, conventional across calls
  (mirrors Capa-4/Capa-1 ST5).
- **Reversibility:** the query is a **two-way door** (pure, no side effects) → may run autonomously.
  Acting on a verdict (deciding to transact) is the human's step; the query only *informs a position*.

## Relationship to Capa 1 and Capa 4 (reuse, not duplication)
- Reuses the **exact** `FORBIDDEN_KEY` taxonomy of Capa 1 / Capa 4 (one anti-surveillance
  definition, not three). AC-X regression-checks that a Capa-1 surveillance-shaped payload fed as
  a Capa-2 graph node is refused identically — the three layers cannot disagree on the shape ban.
- A vouch/fact is **cell-scoped**, exactly as a Capa-1 interaction is `cell_id`-scoped and a
  Capa-4 campaign is; local-bounded visibility is one idea across the stack (invariant 4).

## Out of scope (explicitly NOT this component)
- **A trust score / rank / reputation number of any kind** — there is none, by construction (the
  defining out-of-scope; emitting one is the whole antipattern).
- Identity verification / **Sybil resistance** (§6.2 — flagged, not solved: fabricated vouches from
  throwaway tokens are not detected here; the graph is trusted as given).
- **The razor's edge as a governance question** (§6.1 — a benign query + a malign governor who
  stores and correlates results rebuilds surveillance; the API removes the throne per-call but
  cannot police the caller). Flagged, not coded.
- **Newcomer / bootstrapping exclusion** — a token with no in-cell vouch-paths always gets
  `no_info_from_your_position`. Positive-sum protects them from being *marked*, but leaves them
  *invisible*; making a newcomer legible without a dossier is unsolved (§6.2). Flagged, not faked.
- Persistence/database, cross-cell federation (Capa 3 translation), LLM matching (Capa 3),
  governance (Capa 6), and **any moral judgement of a person** (there is none — this reports
  reachability and facts from a position only).
