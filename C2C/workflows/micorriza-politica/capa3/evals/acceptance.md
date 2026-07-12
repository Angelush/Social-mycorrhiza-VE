# Acceptance Criteria — Capa 3 Prosocial-Affordance Matcher

> Produced by design-evals. Binary Done (AGD-028): verify the artifact, not a self-report.
> Every AC is machine-executable with zero human judgement. The correctness under test is the
> **deterministic wrapper's**, exercised with a **deterministic / adversarial stub `propose`**
> (the whole suite is offline — no live API calls).

- **AC1 — A valid in-cell, consenting, unexpired candidate the model proposes is surfaced.** Given a
  candidate `t7` in one of `cell_ids`, `consent.surfaceable=true`, unexpired at `now`, and a stub
  model that proposes `{"token":"t7","kind":"offer_meets_need","reason":"..."}`, `match()` returns
  `verdict == "proposals_surfaced"` with exactly one proposal for `t7` carrying its `kind`, `reason`,
  the candidate's `cell_id`, and the request's `expires_at`. Pass/fail: field equality.
  (Targets principle: proposes; invariants 4/5.)

- **AC2 — Proposes, never imposes / no acting surface.** The module exposes **no** function that
  connects, messages, notifies, auto-introduces, or persists a match (static: only `match(request,
  propose)`), and the output contains **no** action field (no `notify`/`connect`/`sent`/`message`).
  Pass/fail: static surface + output key scan. (Targets N1, FWK-030.)

- **AC3 — Engagement signal is unrepresentable (invariant 8).** (a) A request whose `self` or any
  candidate declaration carries an engagement-shaped key (`click`, `dwell`, `engagement`, `viral`,
  `watch_time`, `impression`, `ctr`, `feed_rank`, `time_in_app`, `notification`, `streak`) at any
  depth is **refused** (`MatcherBreachError`). (b) A candidate declaration carrying **any**
  non-whitelisted key is **refused**. Pass/fail: rejection. This is the case where "correct" means
  *refusing the feed/engagement shape at the input*. (Targets M3/N3, invariant 8, F1.)

- **AC4 — Off-cell proposals are dropped (cell-scoped).** (a) A candidate whose `cell_id ∉ cell_ids`
  is never surfaced even if the model proposes it (the token is ineligible → dropped;
  `audit_trace.dropped_unknown_token >= 1`). (b) A model proposal naming a token that is not among
  the eligible candidates is dropped. Pass/fail: proposal absent + drop counted. (Targets M1/M11,
  invariant 4, F5.)

- **AC5 — No person-scalar out; surveillance shape refused/dropped (the razor at the matcher).**
  (a) For every emitted proposal, a recursive key scan finds **zero** forbidden keys
  (`score|rating|reputation|rank|blacklist|ban|penalty|global_id|dni`) and there is **no numeric
  field that scores/ranks the person** (the only person-specific claims are echoed `cited_facts`).
  (b) A model proposal carrying a forbidden key at any depth (e.g. `{"token":"t7","kind":"shared_goal",
  "reason":"...","match_score":0.9}`) is **dropped whole (not stripped)** and counted in
  `dropped_surveillance_shape`. (c) A request carrying a forbidden key at any depth is **refused**.
  Pass/fail: key-scan + drop/rejection. (Targets M4/N2/N5, invariant 2, F2.)

- **AC6 — Non-consenting parties are never surfaced.** A candidate with `consent.surfaceable` absent
  or `false` is excluded from the model's context and never appears in the output, even if a stub
  model proposes its token (dropped as ineligible). Pass/fail: proposal absent. (Targets M6, invariant
  3, F6.)

- **AC7 — Forgetting: expired declarations dropped; proposals carry expiry.** (a) A candidate with
  `expires_at <= now` is never surfaced; the identical candidate with `expires_at > now` (or null) is
  surfaced — the verdict flips on expiry alone. (b) Every emitted proposal carries the request's
  `expires_at`. Pass/fail: verdict flip + field presence. (Targets M8, invariant 5, F4.)

- **AC8 — The model's ordering is discarded (no engagement-bait order, no people-ranking).** A stub
  model that returns the same proposals in **two different orders** yields **byte-identical** emitted
  `proposals` (canonical `(kind, token, reason)` sort). Pass/fail: `json.dumps` equality across the
  two orders. (Targets M5, invariants 2/8, F3.)

- **AC9 — Bounding.** With `max_proposals = k` and a model proposing more than `k` valid matches, at
  most `k` are emitted (the first `k` by canonical order), and `audit_trace.emitted <= k`. Pass/fail:
  length + count. (Targets M7, invariant 4.)

- **AC10 — Adversarial / hallucinated model output is refused/dropped; the wrapper never crashes.** A
  stub model that returns, in one list: an off-cell match, a non-consenting token, a person-scalar, an
  engagement-shaped proposal, an unknown/hallucinated token, and an off-schema entry → `match()`
  returns normally with **zero** of those emitted, each counted in the matching `dropped_*` field, and
  a valid proposal in the same list still surfaces. Pass/fail: only the valid one emitted + no
  exception. This is the case where "correct" = *the deterministic wrapper drops everything the
  boxed LLM should not have said.* (Targets M2/N4, F7, ST6.)

- **AC11 — Determinism.** Running `match()` twice on the same input and the same stub model yields
  byte-identical JSON. Pass/fail: string equality. (Targets M9.)

- **AC12 — Envelope validation.** Missing/empty `asker`/`cell_ids`/`now`/`expires_at`; `max_proposals`
  not `int > 0`; `self`/`candidates` wrong type; a malformed/whitelist-violating declaration; `propose`
  not callable → each **refused** (not repaired). Pass/fail: exception raised. (Targets E2/E3/N8.)

- **AC13 — The LLM client is injected, not imported at module top.** Importing `src/matcher/matcher.py`
  succeeds with **no** `anthropic`/network dependency available; `propose` is a parameter. Pass/fail:
  import succeeds under a stubbed-out `anthropic`; static check that `matcher.py` has no top-level
  `import anthropic`. (Targets M10, testability.)

## Consistency with Capa 1, 2, and 4
- **AC-X — Shared surveillance taxonomy is honored across all four layers.** Feeding a Capa-1
  surveillance-shaped payload (e.g. `{"seller": {"trust_score": 88}}`) as a Capa-3 candidate
  declaration **refuses** it — the same verdict Capa 1's membrane, Capa 2's query, and Capa 4's engine
  reach independently on that shape. Additionally, `matcher.FORBIDDEN_KEYS == membrane.FORBIDDEN_KEYS
  == legibility.FORBIDDEN_KEYS`. Pass/fail: all refuse + set equality. (Targets P2, F10.)
</content>
