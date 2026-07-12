# Constraint Architecture — Capa 3 Prosocial-Affordance Matcher

> Produced by author-constraints. Each rule carries a "because" clause (AGD-029).
> Sibling of the Capa-4 / Capa-1 / Capa-2 `constraints.md`; the anti-surveillance rules are
> deliberately identical. This is the FIRST LLM: the constraints box the stochastic core.

## MUSTs
- **M1** Require an `asker` and surface matches **for that position**, within the asker's own declared `cell_ids` — *because* affordance here is relational and local, never a global feed (principle 4, invariants 2/4). No asker ⇒ no matches.
- **M2** Wrap the LLM in a **deterministic guardrail** that validates the model's output against a strict schema and **drops** anything off-schema/off-cell/non-consenting/unknown-token/surveillance-shaped/engagement-shaped — *because* the LLM is a proposer capped at proposal level and is **never trusted blindly**; the wrapper is the guardrail (architecture.md, FWK-030).
- **M3** Make the engagement signal **unrepresentable**: whitelist declaration keys and scan+refuse an `ENGAGEMENT_KEY` taxonomy over the whole input; accept **only** declared offers/needs/goals — *because* the objective is **cooperation initiated, never engagement** (invariant 8, the platform original sin); there must be no signal a model could learn to maximize time-in-app against.
- **M4** Emit **no score/rank/reputation of any person**; scan the exact Capa-1/2/4 `FORBIDDEN_KEY` taxonomy over **both** the model's input and its output; a surveillance-shaped proposal is **refused (dropped), not stripped** — *because* no global scalar of the person (invariant 2). May **cite** a Capa-2 fact verbatim; must never **synthesize** a rating.
- **M5** **Discard the model's ordering** and impose a canonical content-based sort `(kind, token, reason)` — *because* the LLM must not rank people and any engagement-bait ordering must be destroyed structurally (invariants 2/8, principle 3). The emitted order is *not* a ranking.
- **M6** Surface a candidate **only** if `consent.surfaceable is True`, in-cell, and unexpired; exclude ineligible candidates from what the model even sees — *because* a person is surfaced only by consent; the model cannot propose whom it cannot see (proposes-never-imposes; invariant 3).
- **M7** Bound the surfaced list to `max_proposals` — *because* visibility is local and anti-broadcast (invariant 4); a matcher that floods is a feed.
- **M8** Drop expired candidate declarations before proposing and **stamp every emitted proposal with `expires_at`**; persist nothing across calls (pure over supplied inputs) — *because* forgetting is native and there is no dossier / no central holder (invariants 5/6).
- **M9** Be byte-deterministic for identical input **and identical (stubbed) model output** (canonical sort, fixed taxonomy, deterministic bounding) — *because* an auditable proposal that is non-reproducible cannot be audited; the wrapper's correctness must be testable offline (mirrors Capa-4/1/2 M9).
- **M10** Keep the LLM client **injected**, never imported at the core module's top — *because* the core must stay importable and the whole suite must run with a stub, with no network and no keys.
- **M11** Confine cross-cell reach to `translation`, and only between two of the **asker's own** declared cells, human-gated — *because* translation is the one bridge, and merging cells into one global graph is the §6.5 recentralizing bottleneck (invariant 4).

## MUST-NOTs
- **N1** No **acting**: no connect, message, notify, auto-introduce, or persist — the Tool-assistant has no such tool — *because* it **proposes, the human disposes** (FWK-030, invariant: propone-no-impone).
- **N2** No score/rating/ranking/reputation/relevance number of a person in the output — *because* no global scalar (invariant 2). Not even a "match %", not even a normalized similarity as a rating.
- **N3** No engagement/click/dwell/watch-time/virality/impression/feed-rank input, and **no feedback loop / outcome signal** of any kind — *because* the objective is cooperation initiated, not time-in-app (invariant 8). The matcher cannot learn to narrow because it cannot see outcomes.
- **N4** No trusting the LLM output: never emit a model proposal that is off-schema, off-cell, for a non-consenting/unknown token, or carrying a forbidden/engagement shape — *because* the wrapper is the guardrail; a stochastic core is boxed, not believed (M2).
- **N5** No **stripping** of a surveillance/engagement-shaped proposal (remove the field, keep the proposal) — **drop the whole proposal** — *because* answering over a silently-cleaned dossier-shaped artifact launders it (mirrors Capa-1/2 N6).
- **N6** No stored match history, no cross-call state, no cross-cell join key, no global match graph; tokens stay opaque — *because* no central holder (invariant 6), no permanent dossier (invariant 5), no recentralizing throne (§6.5).
- **N7** No broadcast beyond the asker's cells; no global feed/timeline; bounded by `max_proposals` — *because* local-bounded visibility, never global (invariant 4).
- **N8** No silent failure on the **input**: on any envelope-validation error or surveillance/engagement breach in the request, **raise** and surface — never repair, never answer over a corrupted input. (Bad **model output**, by contrast, is dropped-and-counted, never raised — the guardrail must not be crashable by a bad model.)
- **N9** No synthesizing a "fact" about a person; cite only facts the candidate declared, verbatim — *because* the matcher must not manufacture the person-scalar Capa 2 refuses to compute.

## PREFERENCES
- **P1** Prefer stdlib-only core for auditability; the LLM client is injected; `hypothesis` only in tests.
- **P2** Share the exact `FORBIDDEN_KEY` taxonomy with the Capa-4 engine, Capa-1 membrane, and Capa-2 query (one anti-surveillance definition, not four).
- **P3** Prefer property-based tests: no forbidden/engagement key ever survives into output; an adversarial stub model can never make the wrapper emit an off-cell/non-consenting/scalar/engagement-shaped proposal; the model's order never affects the output (canonical sort); expired/ineligible candidates never surface.

## ESCALATION TRIGGERS (reject + surface)
- **E1** Request (any depth) contains a forbidden surveillance-shaped **or** engagement-shaped key → **refuse** — refuse to even accept the dossier/feed shape (invariants 2/6/8).
- **E2** `asker`/`cell_ids`/`now`/`expires_at` missing/empty, `max_proposals` not int>0, a declaration with an unknown (non-whitelisted) key, or `propose` not callable → **refuse** (M2/M3/M10).
- **E3** Malformed envelope (`self`/`candidates` wrong type, malformed declaration) → reject, do not repair.

## Reversibility framing
- The matcher itself is a **two-way door** (pure, no side effects, no persistence) → fully autonomous to *surface*.
- Acting on a proposal (reaching out, accepting, connecting) is the **human's** step → the matcher only surfaces (AGD-018, propone-no-impone).

## Constraint × Execution-Mode matrix
| ID | Match (Live) | Simulation/Backtest | Notes |
|----|--------------|---------------------|-------|
| M2 wrapper guardrail | Enforce (drop bad model output) | Enforce | the LLM is never trusted |
| M3 no engagement input | Refuse | Refuse | invariant 8; unrepresentable, never relax |
| M4 no scalar out | Enforce (drop) | Enforce | the surveillance shape; never relax |
| M5 canonical order | Enforce | Enforce | model order discarded; not a ranking |
| M6 consent-gated | Enforce | Enforce | non-consenting never surfaced |
| M8 forgetting | Enforce (drop + stamp) | Enforce | no dossier |
| N1 no acting | Enforce | Enforce | proposes, human disposes |
</content>
