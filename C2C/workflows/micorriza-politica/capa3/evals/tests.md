# Test Cases — Capa 3 Prosocial-Affordance Matcher

> Produced by design-evals. Each: input, stub-model output, expected result, verification rule.
> Tokens are opaque per-cell strings; `now`/`expires_at` are normalized-UTC ISO-8601 (`...Z`).
> Every test injects a **deterministic stub `propose`** — the suite is fully offline.

## Stub models (deterministic, injected)
- `stub_echo(context)` — proposes one clean `offer_meets_need` match for each eligible candidate.
- `stub_fixed(proposals)` — returns a caller-fixed list regardless of context (for order/adversarial tests).
- `stub_adversarial(...)` — returns off-cell / non-consenting / scalar / engagement / hallucinated /
  off-schema proposals mixed with one valid proposal (AC10 / ST6).
- `stub_empty` — returns `[]`.

## Test A — Normal: a valid candidate is surfaced (AC1)
- **A1:** `cell_ids=["barrio-1"]`; candidate `t7` in `barrio-1`, `consent.surfaceable=true`,
  `expires_at=FUTURE`; `self.offers=["bike repair"]`, `t7.needs=["bike fixed"]`; `now=NOW`,
  `expires_at(req)=SOON`, `max_proposals=3`; stub proposes `t7/offer_meets_need`.
  → `verdict="proposals_surfaced"`, one proposal for `t7`, `cell_id="barrio-1"`,
  `expires_at="SOON"`, `kind="offer_meets_need"`, `reason` non-empty.
- **A2 with a cited fact:** candidate declares `facts=[{"statement":"completed 12 exchanges",...}]`;
  stub cites it → `cited_facts` echoes it verbatim; scanning finds no scalar.
- **Verify:** AC1, AC5a, AC11.

## Test B — Proposes, never imposes (AC2)
- **B1 (static surface):** the module exposes exactly `match` (+ helpers/`FORBIDDEN_KEYS`); assert no
  `connect`/`notify`/`introduce`/`send`/`persist`/`rank` public function.
- **B2 (output has no action field):** scan output keys — no `notify`/`connect`/`sent`/`message`/`action`.
- **Verify:** AC2.

## Test C — Engagement unrepresentable (AC3, invariant 8)
- **C1 (engagement key in candidate):** candidate declares `click_count=40` → **refused**.
- **C2 (engagement nested in self):** `self={"offers":[...],"needs":[],"goals":[],"meta":{"dwell_ms":9}}`
  → **refused** (also a whitelist violation).
- **C3 (non-whitelisted key):** candidate has `priority=9` → **refused** (whitelist).
- **C4 (feed_rank at depth):** `...{"x":{"feed_rank":1}}` → **refused**.
- **Verify:** AC3 — the feed/engagement shape cannot enter.

## Test D — Off-cell dropped (AC4)
- **D1:** candidate `t9` in `otro-barrio`, `cell_ids=["barrio-1"]`; stub proposes `t9`
  → not surfaced; `audit_trace.dropped_unknown_token >= 1` (t9 was never eligible).
- **D2:** stub proposes token `ghost` present nowhere → dropped, counted.
- **Verify:** AC4 (cell-scoped, no global feed).

## Test E — No scalar out; surveillance shape dropped/refused (AC5)
- **E1 (verdict scan):** for A1/A2, recursive key scan of every proposal finds **zero** FORBIDDEN keys
  and no person-scoring number.
- **E2 (model returns a scalar):** `stub_fixed([{"token":"t7","kind":"shared_goal","reason":"r",
  "match_score":0.9}])` → the proposal is **dropped** (not stripped), `dropped_surveillance_shape>=1`,
  output empty of it.
- **E3 (scalar nested):** `...,"meta":{"reputation":5}` on a proposal → dropped.
- **E4 (request-level surveillance):** candidate declares `{"about":..,"trust_score":88}` (via facts)
  → **refused** at input.
- **Verify:** AC5 (a,b,c).

## Test F — Non-consenting never surfaced (AC6)
- **F1:** candidate `t8` with `consent.surfaceable=false`; stub proposes `t8` → not surfaced (ineligible).
- **F2:** candidate `t8` with `consent` absent → treated ineligible → not surfaced.
- **Verify:** AC6 (surfaced only by consent).

## Test G — Forgetting (AC7)
- **G1 expired:** candidate `t7` `expires_at=PAST` (< now); stub proposes it → not surfaced,
  `no_matches_from_your_position`.
- **G2 fresh:** identical candidate `expires_at=FUTURE` → surfaced. Verdict flips on expiry alone.
- **G3 stamp:** every emitted proposal carries the request's `expires_at`.
- **Verify:** AC7.

## Test H — Model order discarded (AC8)
- **H:** three valid candidates `t1,t2,t3`; `stub_fixed` returns them in order `[t3,t1,t2]` in run 1
  and `[t2,t3,t1]` in run 2 → both emit byte-identical `proposals` (canonical `(kind,token,reason)`).
- **Verify:** AC8 — engagement-bait ordering is structurally destroyed.

## Test I — Bounding (AC9)
- **I:** five valid candidates, `max_proposals=2`, stub proposes all five → exactly 2 emitted (first 2
  by canonical order), `audit_trace.emitted == 2`.
- **Verify:** AC9.

## Test J — Adversarial model output (AC10, ST6) — THE wrapper-correctness test
- **J:** one eligible candidate `good` (in-cell, consenting, unexpired) plus an ineligible off-cell
  `t9`, a non-consenting `t8`, both present as candidates. `stub_adversarial` returns:
  `[{good, offer_meets_need, r},   # valid`
  ` {t9, shared_goal, r},          # off-cell (ineligible token)`
  ` {t8, shared_goal, r},          # non-consenting (ineligible token)`
  ` {good, shared_goal, r, match_score:1.0},   # scalar`
  ` {good, shared_goal, r, click_rate:9},      # engagement`
  ` {ghost, offer_meets_need, r}, # hallucinated token`
  ` {"kind":"offer_meets_need","reason":"r"},  # off-schema (no token)`
  ` {good, not_a_kind, r}]        # bad kind`
  → returns normally (no raise); **only the one valid `good/offer_meets_need`** emitted; each drop
  category counted (`dropped_unknown_token>=3` for t9/t8/ghost, `dropped_surveillance_shape>=1`,
  `dropped_off_schema>=2`).
- **Verify:** AC10 — a fully-adversarial (or prompt-injected, ST6) model cannot get anything bad past
  the wrapper, and the wrapper never crashes.

## Test K — Determinism (AC11)
- **K:** run A1 twice with the same stub → byte-identical `json.dumps(out, sort_keys=True)`.
- **Verify:** AC11.

## Test L — Envelope validation (AC12)
- Missing/empty `asker`, `cell_ids=[]`, empty `now`/`expires_at`; `max_proposals=0`/`-1`/`"3"`/`True`;
  `self=[]` (not dict); `candidates="x"` (not list); a malformed declaration (missing `token`); a
  declaration with a non-whitelisted key; `propose` not callable → each **refused**.
- **Verify:** AC12.

## Test M — Injected client, importable offline (AC13)
- **M1:** import `src/matcher/matcher.py` with no `anthropic` installed → succeeds.
- **M2 (static):** assert `matcher.py` source has no top-level `import anthropic`.
- **Verify:** AC13.

## Test N — Cross-layer consistency (AC-X)
- **N1:** feed a Capa-1 surveillance-shaped payload as a Capa-3 candidate fact node:
  `facts=[{"statement":"s","cell_id":"barrio-1","seller":{"trust_score":88}}]` → **refused**.
- **N2 (taxonomy identity):** `matcher.FORBIDDEN_KEYS == membrane.FORBIDDEN_KEYS ==
  legibility.FORBIDDEN_KEYS`.
- **Verify:** AC-X — the four layers agree on the forbidden-key taxonomy.

## Property tests (Test P — hypothesis)
- **P1 (no scalar/engagement out):** for any clean random candidate set + `stub_echo`, the output
  scanned recursively contains zero FORBIDDEN and zero ENGAGEMENT keys and no person-scoring number.
- **P2 (model order irrelevant):** for any list of valid proposals, permuting the stub's return order
  never changes the emitted `proposals` (canonical sort).
- **P3 (ineligible never surfaces):** for any random mix, no proposal is ever emitted for an off-cell,
  non-consenting, expired, or unknown token — whatever the (adversarial) stub returns.
- **P4 (surveillance/engagement refused at any depth):** a request with any FORBIDDEN/ENGAGEMENT key
  nested at random depth is always **refused**.
- **P5 (bounded):** the emitted count never exceeds `max_proposals`, for any stub output.
- **P6 (never crashes on model output):** for any arbitrary (even garbage) stub return value, `match()`
  either returns normally or — only on a malformed **request** — raises `MatcherBreachError`; it never
  raises anything else. The boxed LLM cannot crash the guardrail.

## Cross-check (independent oracle, AGD-045)
Re-derive the eligible-token set and the may-survive proposal set with a **hand-written** filter +
key-scanner (separate from the module) and assert the module emits a subset of exactly the
independently-eligible, shape-clean proposals. Disagreement = fail (catches self-confirmation).
</content>
