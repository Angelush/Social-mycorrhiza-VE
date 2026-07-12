# Failure Model + Stress Report — Capa 3 Prosocial-Affordance Matcher

> Produced by red-team. Hostile review of the Capa-3 matcher spec. This is the FIRST LLM in the
> stack; the failure mode is not a dead network, it is a **surveillance/engagement machine that
> proposes people to each other** — the platform original sin (invariant 8) reappearing at the one
> stochastic rung.

## Failure modes (F#)
- **F1 — Engagement optimization (invariant 8, the gravitational pull).** The matcher grows a
  feedback loop — clicks, accepts, dwell, "relevance" — and quietly begins optimizing time-in-app;
  the shortest path there is outrage/virality. *Mitigation:* M3/N3; the engagement signal is
  **unrepresentable** — declaration keys are whitelisted, an `ENGAGEMENT_KEY` taxonomy is refused,
  and there is **no outcome/feedback input at all**. The objective is cooperation initiated because
  the system cannot see anything else. AC3 refuses engagement-shaped input; AC-order proves the
  model's (potentially engagement-bait) ordering is discarded. **This is the gravity, not a solved
  problem — flagged: a future maintainer who adds an "accept rate" input reopens it.**
- **F2 — The synthesized person-scalar.** The model returns `{"token":"t7","match_score":0.92}` or
  the wrapper "summarizes" fit into a relevance number → the social-credit shape reappears at the
  matcher (inverts invariant 2). *Mitigation:* M4/N2; the `FORBIDDEN_KEY` scan runs over the model's
  output and such a proposal is **dropped**; the output schema has **no** number that scores a
  person (only `cited_facts` echoed from Capa 2). AC5 scans every emitted proposal.
- **F3 — Engagement-bait ordering / people-ranking.** The model returns proposals ordered to
  maximize a click (most provocative first) → an implicit ranking of people. *Mitigation:* M5;
  the wrapper **discards the model's order** and imposes a canonical `(kind, token, reason)` sort;
  AC-order asserts a shuffled model output yields byte-identical emitted order.
- **F4 — Stale/persistent dossier.** Expired declarations still surface, or the matcher stores a
  match history and correlates it → a permanent record of who-was-matched-to-whom (inverts
  invariants 5/6). *Mitigation:* M8; expired declarations dropped before proposing; every proposal
  carries `expires_at`; the function is pure and persists nothing. AC7 flips on expiry.
- **F5 — Off-cell / global-feed leak.** The model proposes a candidate outside the asker's cells,
  or the wrapper merges cells into one graph → reputation/visibility follows the person globally
  (inverts invariant 4). *Mitigation:* M1/M6/M11; eligibility requires `cell_id ∈ cell_ids` **before**
  the model sees a candidate, and a proposal whose token/cell is off-cell is **dropped**. AC4.
- **F6 — Proposing a non-consenting party.** The model proposes someone who did not set
  `consent.surfaceable` → a person surfaced without consent (a soft outing). *Mitigation:* M6;
  non-consenting candidates are excluded from the model's context, and any proposal for an
  ineligible token is **dropped** (it is not in the eligible set). AC6.
- **F7 — Trusting the LLM (hallucinated token / off-schema).** The model invents a token, omits a
  reason, or emits garbage → a fabricated or malformed match reaches a human. *Mitigation:* M2/N4;
  every proposal is validated against a strict schema and unknown/off-schema proposals are
  **dropped-and-counted**; a fully-adversarial model yields **zero** emitted proposals and **never a
  crash** (AC-adversarial). The wrapper — not the model — is the correctness surface under test.
- **F8 — Translation as a recentralizing bottleneck (§6.5).** The cross-context translation layer
  grows into a global "trust-translation" service that all cells must route through → the throne
  reappears as a translation monopoly (inverts invariant 6). *Mitigation (partial):* M11 keeps the
  bridge cell-local (only the asker's own two cells) and human-gated; there is no stored cross-cell
  graph. **Flagged, not solved:** who runs translation, and whether it centralizes, is a governance
  question (§6.5) the pure function cannot foreclose.
- **F9 — Filter bubble / homophily (the matcher narrowing your world).** The matcher only ever
  surfaces the like-minded → the platform bubble collapse. *Mitigation (partial):* the wrapper does
  **not** optimize similarity/relevance and **cannot learn** to narrow (no feedback loop, F1). But
  the model's proposals can still skew homophilous. **Flagged, not coded:** breadth/serendipity is a
  governance/curation matter (§6.1/§6.4), not something the wrapper resolves.
- **F10 — Taxonomy drift from Capa 1/2/4.** Capa 3 keeps a separate forbidden-key list that diverges
  → the four layers disagree on the surveillance shape (AC-X breaks). *Mitigation:* P2; share the
  exact `FORBIDDEN_KEY` set; AC-X regression-checks agreement across all four layers.
- **F11 — Repair-instead-of-refuse on input; strip-instead-of-drop on output.** Code strips a
  `reputation`/`click_count` key from the request and answers anyway, or strips the field from a
  proposal and keeps it. *Mitigation:* N5/N8; the request is **refused** (raise) on any breach; a
  shaped proposal is **dropped whole**, never stripped-and-kept.

## Stress findings (ST#)
- **ST1 — Substring false positives in the scan.** `"feedback_form"` contains `feed`;
  `"clicker_training"` contains `click`; `"bankruptcy"` contains `ban`. **Decision (inherited from
  Capa 1/2 ST1):** the taxonomy is a *shape heuristic biased to over-refuse* — a false refusal is
  safe (the caller re-labels a field), a false admit is a surveillance/engagement leak. Keep the
  shared `FORBIDDEN_KEY` set verbatim; document the `ENGAGEMENT_KEY` bias. Test `feed`/`click` (must
  trip) and a clean declaration (must not trip).
- **ST2 — Empty candidate list / no eligible candidates.** `candidates=[]`, or all filtered out →
  valid; `no_matches_from_your_position` (the bootstrapping state), never an error. AC tolerates it.
- **ST3 — Non-deterministic model.** The real Claude client is stochastic; two runs differ. **Decision:**
  determinism is a property of the **wrapper given fixed model output**; the suite injects a
  deterministic stub. Live non-determinism is expected and lives entirely behind `propose` (M9).
- **ST4 — Self-confirmation.** The wrapper's own validation agrees with its own bug. *Mitigation:* an
  **independent** eligibility+scan oracle (hand-written, separate from the module) cross-checks which
  proposals may survive, in tests (tests.md cross-check, AGD-045).
- **ST5 — Auditability vs. forgetting / no-storage (open §6.6).** The proposal set is auditable yet
  must not become a permanent record. *Partial mitigation:* the function is pure and stores nothing;
  `expires_at` stamps each proposal. **Flagged:** enforcing that the *caller* does not persist and
  correlate match sets is outside this pure function (mirrors Capa-4/1/2 ST5).
- **ST6 — Prompt-injection via declaration text.** A candidate's `offers`/`goals` free-text tries to
  jailbreak the model into emitting a scalar or an off-cell match. **Decision:** the **wrapper is the
  guard, not the prompt** — even a fully-jailbroken model cannot get a scalar, an off-cell token, or a
  non-consenting party past the deterministic validation (that is the whole point of boxing the LLM).
  AC-adversarial exercises exactly this: a stub that returns the injected-attack output, dropped.
- **ST7 — ISO-8601 lexicographic compare.** As in Capa 2: `expires_at`/`now` must be normalized-UTC
  (`...Z`). Document it; test with `...Z` only.

## Open (system-level, NOT this matcher) — do not fake-resolve (§6)
- **Engagement optimization is the gravity of every recommender (invariant 8, §6, the original sin).**
  The API removes the signal *per call* (nothing to maximize). But a **malign governor** who adds an
  outcome feedback loop, or logs accepts and trains on them, rebuilds the engagement machine *outside*
  the function. Structure makes it hard, not impossible; *who governs and for what* decides. **Stakes:
  a cage/feed, not just a failure.** Flagged.
- **Federation / translation as a recentralizing bottleneck (§6.5).** The "translation between trust
  worlds" layer can become the new throne. The bridge is kept thin, cell-local, human-gated; whether
  it centralizes is governance, not code. Flagged (F8).
- **Filter-bubble / homophily (§6.1/§6.4).** A matcher can narrow the world it shows you. No feedback
  loop means it cannot *learn* to narrow, but the model's proposals can still skew. Breadth/serendipity
  is a curation/governance question. Flagged, not coded (F9).
- **Sybil / token↔person binding (§6.2).** Tokens are opaque and trusted as given; a Sybil can declare
  offers/needs from throwaway tokens to manufacture matches. Not detected here (as in Capa 2/4). Flagged.
- **The truthfulness/aptness of the model's reasons.** The wrapper bounds and shapes but cannot verify
  the model's prose is apt, kind, or unbiased — only that it carries no scalar/engagement shape and
  points at a consenting in-cell token. Reason-quality is a governance/curation matter. Flagged.
</content>
