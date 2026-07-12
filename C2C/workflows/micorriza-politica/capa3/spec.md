# Specification — Capa 3 Prosocial-Affordance Matcher ("el emparejador")

> Produced by engineer-spec. Self-contained blueprint; an agent can build from this alone.
> Sibling of the Capa-4, Capa-1, and Capa-2 `spec.md`. This is **THE FIRST LLM IN THE STACK**
> (brief §4 Capa 3, invariant 8, architecture.md: *Species 2 / Tool-assistant, NOT Dark
> Factory, capped at proposal level per FWK-030*). The stochastic model **proposes**; a
> **deterministic wrapper validates, bounds, and shapes**; a **human disposes**. It routes
> through the Capa-1 membrane's `FORBIDDEN_KEY` taxonomy verbatim so the four layers cannot
> disagree on the surveillance shape.

## Purpose
Surface, for a given asker and within that asker's own declared cells, a **bounded list of
candidate matches**, each carrying a **human-readable reason** — "who near you needs what you
offer," "who shares this goal," or a **translation of a need across two of your contexts." It is
the *kula* function (brief §4 Capa 3): build the substrate of trust on which real exchange rides.
It can only **SURFACE**; it can never **act, notify-optimize, auto-connect, or rank people**.

The matcher is a **stochastic proposer wrapped in a deterministic guardrail**. The LLM is
**injected** behind a `Matcher`/callable interface — never imported at module top, so the core
module stays importable and testable without network or keys. The LLM is **never trusted
blindly**: everything it returns is validated against a strict schema and dropped if it is
off-schema, off-cell, surveillance-shaped, engagement-shaped, or proposes a non-consenting party.

This is the `[ESTOCÁSTICO · LLM — propone, no impone]` component (brief §4 Capa 3). Its whole
design problem is: **the first place a non-deterministic component touches the system, and the
gravitational pull of every recommender is engagement optimization (invariant 8, the platform
original sin).** The answer is structural, not a policy line: the objective is **cooperation
INITIATED**, and no engagement signal is even *representable* as an input.

## The design move — the objective is made structural, the LLM is boxed
Five structural walls, each the analogue of a wall in the deterministic layers:

1. **Engagement is unrepresentable (invariant 8, the whole point).** No click/dwell/watch-time/
   virality/impression/feed-rank field is an accepted input to the matcher. Declarations are key-
   **whitelisted** (only `token`/`cell_id`/`offers`/`needs`/`goals`/`consent`/`facts`/`expires_at`),
   and an `ENGAGEMENT_KEY` taxonomy is scanned over the whole input and refused. There is **no
   feedback loop, no outcome signal, no counter** that a model could learn to maximize time-in-app
   against. The *only* inputs are declared offers/needs/goals. (F1, invariant 8.)
2. **No person-scalar, still (invariant 2).** The wrapper emits no score/rank/reputation of anyone,
   and the exact Capa-1/2/4 `FORBIDDEN_KEY` taxonomy is scanned over **both** the LLM's input and
   its output. A proposal that comes back carrying a surveillance-shaped field is **refused (that
   proposal is dropped), not stripped**. It may **cite** a Capa-2 fact ("vouched by t7", "completed
   12 exchanges") verbatim, but must not **synthesize** a rating. (F2/F6, invariant 2.)
3. **The LLM cannot rank people (invariants 2/8).** The wrapper **discards the model's ordering**
   entirely and imposes a **canonical, content-based sort** (`(kind, token, reason)`) that carries
   no ranking signal. Any engagement-bait ordering the model tries is destroyed by construction —
   the emitted order is semantically meaningless and explicitly *not* a ranking of people. (F3.)
4. **Cell-scoped, local-bounded, thin translation bridge (invariant 4, §6.5).** A candidate is
   eligible only if its `cell_id` is one of the **asker's own declared `cell_ids`**. `translation`
   is the one kind that bridges cells — and it bridges only **two cells the asker already belongs
   to**, never a merge into one global graph. It is a thin, explicit, human-gated bridge. The
   §6.5 recentralizing-bottleneck risk is **flagged, not resolved** (failure model F8).
5. **Forgetting + no dossier (invariants 5/6).** The matcher is **pure over the supplied inputs**;
   it persists nothing about anyone across calls. Expired candidate declarations are dropped before
   proposing (`expires_at <= now`). Every emitted proposal carries `expires_at` — proposals are
   ephemeral. There is no stored match history, no throne. (F4/F7.)

## Proposes, never imposes (invariant: propone, el humano dispone)
The output is a **bounded list of candidate matches**, each with its reason and provenance. The
matcher **surfaces**; it does not connect, message, notify, or commit. Acting on a proposal
(reaching out, accepting) is the **human's** step. The Tool-assistant has **no tool** that
connects, notifies, ranks, or persists (architecture.md, FWK-030).

## Input (one match request, JSON)
```json
{
  "asker": "str (non-empty) — the position matches are surfaced FOR; REQUIRED (relational, like Capa 2)",
  "cell_ids": ["str (non-empty)"],   // the asker's OWN declared cells; matches only within these (invariant 4)
  "now": "str (ISO-8601 UTC) — evaluation time; candidate declarations with expires_at <= now are dropped",
  "expires_at": "str (ISO-8601 UTC, non-empty) — the expiry STAMPED on every emitted proposal (forgetting)",
  "max_proposals": "int > 0 — hard bound on the surfaced list (local-bounded, anti-broadcast)",
  "self": {                          // the asker's own declared offers/needs/goals
    "offers": ["str"], "needs": ["str"], "goals": ["str"]
  },
  "candidates": [
    {
      "token": "str (non-empty) — opaque per-cell token of a candidate person",
      "cell_id": "str (non-empty) — MUST be one of cell_ids to be eligible",
      "offers": ["str"], "needs": ["str"], "goals": ["str"],
      "consent": {"surfaceable": true},   // REQUIRED true; a non-consenting candidate is never surfaced
      "facts": [{"statement": "str", "cell_id": "str", "expires_at": "str|null"}],  // optional Capa-2 facts to CITE
      "expires_at": "str|null"            // the declaration's own expiry; <= now => dropped
    }
  ]
}
```
- **Declaration keys are whitelisted.** Any key on a candidate or on `self` outside the allowed set
  is **refused** (raise) — there is no field through which an engagement/outcome signal could enter.
- `consent.surfaceable` must be **exactly `True`**. Absent/false/other → the candidate is ineligible
  (silently excluded from what the LLM even sees — never surfaced). This is not a mark; it is consent.
- `facts` are **cited verbatim** (Capa-2 shape); they are the only person-specific claims allowed,
  and they must pass the surveillance-shape scan like everything else.

## The injected proposer interface (the boxed LLM)
```python
def match(request: dict, propose: Callable[[dict], list[dict]]) -> dict
```
- `propose` is the **injected** stochastic model. The wrapper builds a **sanitized context** — only
  the eligible (in-cell, consenting, unexpired, shape-clean) candidates plus the asker's `self` — and
  hands *that* to `propose`. The model never sees an ineligible candidate, and there is no engagement
  data to see (it was refused at the input).
- `propose` returns a **list of proposed matches**, each a dict:
  `{"token": str, "kind": "offer_meets_need"|"shared_goal"|"translation", "reason": str, "cite_facts": [...optional]}`.
- The model is **never trusted**. The real client (`src/matcher/claude_matcher.py`) is a Claude-backed
  implementation of `propose`; it is imported **lazily**, never at the core module's top, so
  `matcher.py` imports and tests with **no network and no key**.

## Output (a bounded, ephemeral proposal list, JSON) — always returns
```json
{
  "asker": "...",
  "cell_ids": ["barrio-1", "huerta-norte"],
  "proposals": [
    {
      "token": "t7",
      "cell_id": "barrio-1",
      "kind": "offer_meets_need",
      "reason": "You offer bike repair; t7 near you needs a bike fixed.",
      "cited_facts": [{"statement": "completed 12 exchanges", "cell_id": "barrio-1", "expires_at": null}],
      "expires_at": "2026-07-14T00:00:00Z"
    }
  ],
  "verdict": "proposals_surfaced",           // or "no_matches_from_your_position"
  "note": "Proposals to surface, never actions taken. A human decides whether to reach out. Order is canonical, not a ranking of people.",
  "audit_trace": {
    "rule": "in-cell, consenting, unexpired candidates; LLM proposals validated/bounded/canonically-sorted; no scalar, no engagement signal",
    "eligible_candidates": 5,
    "proposed_by_model": 4,
    "dropped_off_schema": 0,
    "dropped_off_cell": 0,
    "dropped_non_consenting": 0,
    "dropped_surveillance_shape": 0,
    "dropped_unknown_token": 0,
    "emitted": 1,
    "max_proposals": 3
  }
}
```
- `verdict` is categorical: `proposals_surfaced` (≥1 emitted) or `no_matches_from_your_position`
  (none). **Never a number, never a judgement of a person.** Absence is "nothing to surface from
  where you stand," never a mark (whitelist-not-blacklist, invariant 3).
- The output contains **no field that scores/ranks/reputes a person**. `cited_facts` are echoed
  Capa-2 facts, not a synthesized rating. The proposal **order is canonical** (`(kind, token,
  reason)`), documented as *not* a ranking.
- Every proposal carries `expires_at` (from the request) — ephemeral, no dossier.

## Algorithm (deterministic wrapper around a non-deterministic core)
1. **Validate envelope** (reject, do not repair): non-empty `asker`; `cell_ids` a non-empty list of
   non-empty str; non-empty `now`/`expires_at`; `max_proposals` an `int > 0`; `self` a dict of
   list[str] `offers`/`needs`/`goals`; `candidates` a list of well-formed declaration dicts with the
   **whitelisted keys only** (unknown key → refuse). `propose` must be callable.
2. **Surveillance + engagement scan (whole input, recursive):** any key (case-insensitive substring)
   matching a `FORBIDDEN_KEY` (`score|rating|reputation|rank|blacklist|ban|penalty|global_id|dni`)
   **or** an `ENGAGEMENT_KEY` (`click|dwell|engagement|viral|watch_time|impression|ctr|feed|
   time_in_app|notification|streak|like_count|follower`) at any depth → **refuse**
   (`MatcherBreachError`). Same `FORBIDDEN_KEY` taxonomy as Capa 1/2/4, verbatim.
3. **Eligibility filter (before the model sees anything):** keep a candidate only if
   (a) `cell_id ∈ cell_ids` (invariant 4), (b) `consent.surfaceable is True`, (c) unexpired at `now`
   (`expires_at` null/absent or string `> now`). Ineligible candidates are **excluded from the
   context handed to the model** — the model cannot propose whom it cannot see.
4. **Build sanitized context and call the injected `propose`.** Hand the model only `self` + the
   eligible candidates. The model returns a list of proposed matches.
5. **Validate every proposal against the strict schema; DROP (never trust) the bad ones:**
   - not a dict, missing/empty `token`/`reason`, or `kind` not in the allowed set → **drop** (off-schema).
   - `token` not among the **eligible** candidate tokens → **drop** (unknown/hallucinated token; this
     also catches a proposal for a **non-consenting or off-cell** party — it was never eligible).
   - the proposal's resolved `cell_id` not in `cell_ids` → **drop** (off-cell).
   - the proposal carries a `FORBIDDEN_KEY`/`ENGAGEMENT_KEY` at any depth → **drop the proposal**
     (refused, **not stripped** — the field is never removed-and-kept). A surveillance/engagement
     shape from the model neutralizes that proposal.
   - `cite_facts` are accepted only if they exactly match facts declared on that candidate (verbatim
     cite, no synthesis); any non-matching "fact" → that cite is dropped.
   Count every drop in the audit trace. A fully-adversarial model → **zero emitted proposals**, never
   a bad emission and never a crash (the wrapper is the guardrail).
6. **Discard the model's order; impose the canonical sort** `(kind, token, reason)`, then **dedupe**
   by `(token, kind)`, then **bound** to `max_proposals`. This structurally destroys engagement-bait
   ordering and any people-ranking.
7. **Assemble output:** stamp each proposal's `cell_id` (from the candidate) and `expires_at` (from
   the request); `verdict = proposals_surfaced` if ≥1 emitted else `no_matches_from_your_position`;
   attach the audit trace. **Commit nothing; persist nothing.**

## Determinism
The wrapper is pure and deterministic. Given the **same input and the same (stubbed) model output**,
it produces **byte-identical** JSON (canonical sort + fixed taxonomy + deterministic bounding). The
non-determinism lives entirely behind the injected `propose`; the *correctness under test* is the
wrapper's, exercised with a deterministic fake matcher (the whole suite is offline).

## Termination & cost
Bounded: O(candidates) filtering, one model call, O(proposals · depth) validation, one sort, a
head-slice to `max_proposals`. No loops over model output beyond its (bounded) length.

## Meaning layer (Axiom 6 — what the agent cannot infer)
- **This is the first LLM, and the gravity is engagement (invariant 8, the original sin).** Every
  recommender slides toward optimizing time-in-app, and the shortest path to engagement is outrage.
  The correct move is not a "don't optimize engagement" policy line — it is to make the engagement
  signal **unrepresentable** (no click/dwell/outcome input, no feedback loop) so there is *nothing to
  maximize*. The objective is **cooperation initiated**; the system cannot learn otherwise because it
  cannot see otherwise. **Flagged, not fake-resolved** — the pull is real and structural (F1).
- **The LLM is boxed, not trusted.** Stochastic creativity is welcome at the *proposal* rung and
  nowhere else. The deterministic wrapper is the guardrail: it validates, drops, sorts, bounds, and
  stamps. A hallucinated off-cell match, a smuggled person-scalar, an engagement-bait ordering, or a
  proposal for someone who never consented are all **refused/dropped by construction**, not by the
  model's good behavior.
- **Proposes, never imposes.** The output surfaces; the human disposes. There is no auto-connect, no
  notification optimizer, no ranking of people. The order is canonical and meaningless on purpose.
- **Translation is a thin bridge, and a recentralizing hazard (§6.5).** Bridging two of the asker's
  own contexts is the real work of the "global" layer — and it is exactly where a global graph / a
  translation monopoly could recentralize. The bridge is kept **human-gated and cell-local** (only
  the asker's own cells), and the recentralizing-bottleneck risk is **flagged, not coded away** (F8).
- **Filter-bubble / homophily (the matcher narrowing your world).** A matcher that only ever surfaces
  the like-minded builds a bubble — the same collapse platforms produced. The wrapper does not
  optimize for similarity or "relevance-to-you"; it surfaces declared offer/need/goal complementarity
  within consenting cellmates, bounded and canonically ordered. It cannot *learn* to narrow (no
  feedback loop). The residual homophily risk is a **governance/curation** matter — **flagged** (F9).
- **Reversibility:** the matcher is a **two-way door** (pure, no side effects, no persistence) → it may
  run autonomously to *surface*. Acting on a proposal is the human's step. It never crosses into an
  irreversible action.

## Relationship to Capa 1, 2, and 4 (reuse, not duplication)
- Reuses the **exact** `FORBIDDEN_KEY` taxonomy of Capa 1 / 2 / 4 (one anti-surveillance definition,
  not four). AC-X regression-checks that a Capa-1 surveillance-shaped payload fed as a Capa-3 candidate
  declaration is refused identically — the four layers cannot disagree on the shape ban.
- A candidate is **cell-scoped** exactly as a Capa-1 interaction, a Capa-2 vouch, and a Capa-4 campaign
  are; local-bounded visibility (invariant 4) is one idea across the stack.
- `facts` cited are Capa-2 facts, echoed verbatim; the matcher never synthesizes what Capa 2 refuses
  to compute (a person-scalar).

## Out of scope (explicitly NOT this component)
- **Any score/rank/reputation/relevance number of a person** — none, by construction (emitting one is
  the whole antipattern). The matcher never ranks people; the proposal order is canonical.
- **Engagement/outcome optimization or any feedback loop** — unrepresentable by design (invariant 8).
  There is no learning from clicks, accepts, or time-in-app; the matcher does not see them.
- **Acting: connecting, messaging, notifying, auto-introducing, persisting a match** — the Tool-assistant
  has no such tool (FWK-030). It surfaces proposals; the human disposes.
- **A global match graph / cross-cell merge** — matches stay within the asker's declared cells;
  translation bridges only the asker's own two cells, human-gated. Federation/translation as a
  recentralizing bottleneck (§6.5) is **flagged, not solved**.
- **Sybil / token↔person binding (§6.2)** — tokens are opaque and trusted as given, as in Capa 2/4.
- **Filter-bubble / homophily curation, and the truthfulness of the model's reasons** — the wrapper
  bounds and shapes but cannot guarantee the model's prose is apt or bias-free; that is a
  governance/curation matter (§6.1/§6.4), **flagged, not coded**.
</content>
</invoke>
