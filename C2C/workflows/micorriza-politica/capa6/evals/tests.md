# Test Cases — Capa 6 Sociocratic Governance (consent, not consensus)

> Produced by design-evals. Each: input, expected result, verification rule. The component is
> **deterministic** — no stub model, no network. `now`/`expires_at` are normalized-UTC ISO-8601
> (`…Z`), compared lexicographically. Tokens are opaque per-circle strings.

## Builders
- `_disp(token, disposition="consent", reason=None, paramount=None, circle="c1", expires_at=None)` —
  builds a disposition; for `object`, attach `objection={"paramount":paramount,"reason":reason}`.
- `_req(dispositions, circle="c1", proposal="p1", now=NOW, expires_at=SOON)`.
- `NOW="2026-07-07T00:00:00Z"`, `SOON="2026-08-01T00:00:00Z"`, `PAST="2020-01-01T00:00:00Z"`.

## Test A — Consent adopts (AC2)
- **A1:** three `consent` dispositions, no objection → `verdict="adopted"`, `paramount_objections==[]`,
  `concerns==[]`, `expires_at==SOON`.
- **A2 (empty circle):** `dispositions=[]` → `verdict="adopted"` (vacuous consent; ST2), not an error.
- **Verify:** AC2, AC9.

## Test B — A single paramount objection blocks (AC4, consent-not-consensus)
- **B1:** five `consent` + one `object` `paramount=true` `reason="no budget until Q3"` → `verdict=
  "revisit"`, `paramount_objections==[{"reason":"no budget until Q3"}]`. The five consents do **not**
  out-vote the one objection.
- **B2 (remove the objection):** same but the one objection removed → `verdict="adopted"`. Verdict
  flips on the single objection alone.
- **B3 (non-paramount concern):** four `consent` + one `object` `paramount=false` `reason="prefer a
  trial"` → `verdict="adopted"` (a concern does not block), `concerns==[{"reason":"prefer a trial"}]`.
- **Verify:** AC4 — one reasoned block is decisive; a concern is surfaced but non-blocking.

## Test C — Voice independent of reputation (AC1) — the defining test
- **C1 (weighted-voice refused):** a disposition with `weight=10` → **refused**. Same for `shares`,
  `voting_power`, `vote_count`, `proxy`, `majority`, `quorum`.
- **C2 (identical verdict regardless of reputation):** the SAME dispositions decided twice; there is no
  way to attach reputation (it is unrepresentable), so the verdict is identical. Construct two
  requests that differ only in token *labels* that a naive weighting might read as "senior" — the
  verdict is unchanged (there is no weighting path).
- **C3 (one token one voice):** a token appearing on two dispositions → **refused**.
- **Verify:** AC1, AC8 — the god-view weighting cannot be phrased.

## Test D — No majority / no tally (AC2b)
- **D1:** for B1's `revisit` and A1's `adopted`, scan the whole output — there is **no** percentage,
  **no** "for/against" count, **no** consent tally that is the verdict (only reason lists + process
  counts in `audit_trace`, none of which is a majority verdict).
- **Verify:** AC2b — the verdict is categorical, never a number.

## Test E — No person-scalar in (AC3)
- **E1:** a disposition nested `{"objection":{"paramount":true,"reason":"r","reputation":5}}` →
  **refused** (`reputation` is a `FORBIDDEN_KEY`; also `objection` sub-keys are constrained).
- **E2:** a request-level `{"member":{"trust_score":88}}` → **refused**.
- **Verify:** AC3.

## Test F — An objection is a pause, never a mark (AC5, invariant 3)
- **F1:** B1's `revisit` output — scan recursively: the surfaced `paramount_objections`/`concerns`
  carry **reasons only**; there is **no** objector `token`, no "blocked_by", no per-person field.
- **Verify:** AC5 — surface the reason, never mark the person; no dossier of dissent.

## Test G — Circle-local; no auto-propagation (AC6, invariants 4/6)
- **G1 (off-circle dropped):** a paramount `object` tagged `circle_id="c2"` in a `c1` round → dropped
  (`dropped_off_circle>=1`), does **not** send the round to `revisit`.
- **G2 (no escalation field):** the output has no `parent`/`escalate`/`global`/`propagate` key.
- **Verify:** AC6.

## Test H — Forgetting (AC7, invariant 5)
- **H1 (expired objection):** a paramount `object` with `expires_at=PAST` (<= now) → dropped
  (`dropped_expired>=1`); the round `adopted` (the expired objection no longer blocks).
- **H2 (fresh objection):** identical objection `expires_at=SOON` → `revisit`. Verdict flips on expiry.
- **H3 (stamp):** the decision carries `expires_at==SOON`.
- **Verify:** AC7.

## Test I — Determinism + canonical reason order (AC9)
- **I:** two paramount objections with reasons `"z-reason"` and `"a-reason"` submitted in both orders →
  `paramount_objections` sorted `[{"reason":"a-reason"},{"reason":"z-reason"}]` in both;
  `json.dumps(out, sort_keys=True)` identical across two runs.
- **Verify:** AC9.

## Test J — Envelope validation (AC10)
- Missing/empty `circle_id`/`proposal_id`/`now`/`expires_at`; `dispositions="x"`; a disposition not a
  dict; a disposition with a non-whitelisted key (`weight` → also AC1; `priority`); `disposition=
  "veto"` (not in set); an `object` with no `objection`; an `object` whose `objection` lacks
  `paramount` or has an empty `reason`; a `consent` carrying an `objection`; `paramount="yes"` (not
  bool) → each **refused**.
- **Verify:** AC10.

## Test K — No LLM, importable offline, stdlib-only (AC11)
- **K1:** import `src/governance/governance.py` with no `anthropic` installed → succeeds.
- **K2 (static):** source has no `import anthropic|requests|httpx|openai|urllib|socket`, and `decide`
  takes only `request` (no injected model/`propose`).
- **Verify:** AC11.

## Test L — Bad-faith blocker enforced as procedure (AC12, §6.3 flagged)
- **L1:** one `object` `paramount=true` with a spurious reason `"I just don't like it"` → `verdict=
  "revisit"` (the function does **not** judge the reason's quality; it enforces the procedure). The
  reason is surfaced verbatim so humans can weigh its good faith.
- **Verify:** AC12 — consent is capturable by a bad-faith blocker; flagged, not coded.

## Test M — Cross-layer consistency (AC-X)
- **M1:** feed a Capa-1 surveillance-shaped payload as a Capa-6 disposition node
  (`{"member":{"trust_score":88}}`) → **refused**.
- **M2 (taxonomy identity):** `governance.FORBIDDEN_KEYS == membrane.FORBIDDEN_KEYS ==
  legibility.FORBIDDEN_KEYS == matcher.FORBIDDEN_KEYS == stigmergy.FORBIDDEN_KEYS`.
- **Verify:** AC-X — the six layers agree on the forbidden-key taxonomy.

## Property tests (Test P — hypothesis)
- **P1 (verdict invariant to reputation):** there is no representable reputation, so for any random
  disposition set the verdict depends only on the presence of a paramount objection — never on token
  labels, order, or count of consents.
- **P2 (one paramount always blocks):** for any number `n` of `consent` dispositions plus exactly one
  paramount `object`, the verdict is always `revisit` (a majority never overrides consent).
- **P3 (weighted-voice always refused):** a request with any `VOTE_WEIGHT_KEY` nested at random depth
  is always **refused**.
- **P4 (duplicate token always refused):** any request with a repeated token is always **refused**.
- **P5 (no objector token out):** for any random disposition set, the output never contains any
  disposition's `token` (surface reasons only).
- **P6 (surveillance refused at any depth):** a request with any `FORBIDDEN_KEY` nested at random depth
  is always **refused**.
- **P7 (never crashes on scoped content):** for any random mix of off-circle / expired dispositions (no
  envelope breach, no duplicate token), `decide()` returns normally; it only raises on a malformed
  **envelope** or an integrity breach (weight/forbidden/duplicate).

## Cross-check (independent oracle, AGD-045)
Re-derive the surviving-disposition set (circle scope → expiry drop) and the verdict (`revisit` iff any
surviving paramount object, else `adopted`) with a **hand-written** filter **separate from the
module**, and assert the module's verdict and surfaced reasons equal the independently-derived ones.
Disagreement = fail (catches self-confirmation, ST4).
</content>
