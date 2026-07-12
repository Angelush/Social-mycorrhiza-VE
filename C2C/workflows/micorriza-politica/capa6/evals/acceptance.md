# Acceptance Criteria — Capa 6 Sociocratic Governance (consent, not consensus)

> Produced by design-evals. Binary Done (AGD-028): verify the artifact, not a self-report.
> Every AC is machine-executable with zero human judgement. The component is **deterministic** (no
> LLM, no stub). The defining test is **AC1**: the same proposal in the same circle yields the same
> verdict regardless of any reputation the members carry — a weighted/reputation-bearing input is
> refused, and one-token-one-voice holds.

- **AC1 — Voice independent of reputation; identical verdict regardless of reputation. THE defining
  test.** (a) Two requests identical except that members carry different (labelled) "reputation" in a
  parallel structure yield the **same** verdict — because reputation is not a representable input at
  all. (b) A disposition carrying a `weight`/`shares`/`voting_power`/`vote_count` key (or any
  `VOTE_WEIGHT_KEY`) at any depth is **refused** (`GovernanceBreachError`). (c) One token, one voice: a
  token appearing on two dispositions is **refused**. Pass/fail: verdict equality + rejection.
  (Targets M1/M2/N1, invariant 7, F1/F7.)

- **AC2 — Consent, not majority: the verdict is categorical, never a number.** (a) A proposal with **no
  paramount objection** is `adopted`; with **≥1 paramount objection** it is `revisit`. (b) The output
  contains **no** percentage, **no** for/against tally, **no** consent count that decides — a recursive
  scan finds no majority/tally number as a verdict field. Pass/fail: verdict value + absence of a
  deciding number. (Targets M4/M5/N2, invariant 7, F2.)

- **AC3 — No person-scalar in; surveillance shape refused.** A request carrying a `FORBIDDEN_KEY`
  (`score|rating|reputation|rank|blacklist|ban|penalty|global_id|dni`) at any depth is **refused**.
  Pass/fail: rejection. (Targets M3/N5, invariant 2, F3.)

- **AC4 — A single paramount objection blocks, however many consent (consent, not consensus).** Given
  many `consent` dispositions and exactly **one** `object` with `paramount=true`, the verdict is
  `revisit` and the objection's **reason** is surfaced in `paramount_objections`. Removing that one
  objection flips the verdict to `adopted`. No count of consents overrides it. Pass/fail: verdict flip
  on the single objection. (Targets M4, invariant 7, F2.)

- **AC5 — An objection is a pause, never a mark of the objector (invariant 3).** For a `revisit`
  outcome, the surfaced `paramount_objections` (and `concerns`) carry **reasons only** — a recursive
  scan of the output finds **no objector `token`** and no per-person "who-blocked" field. Pass/fail:
  no objector identity in the output. (Targets M6/N3, invariant 3, F4.)

- **AC6 — Circle-local; no auto-propagation (invariants 4/6).** (a) A disposition whose `circle_id` ≠
  the request `circle_id` is **dropped** (`dropped_off_circle >= 1`) and does not affect the verdict.
  (b) The output is scoped to `circle_id` and contains **no** field escalating to a parent/global
  authority (no `parent`/`escalate`/`global`/`propagate` key). Pass/fail: drop counted + no escalation
  field. (Targets M7/N7, invariant 4, F5.)

- **AC7 — Forgetting: expired dispositions dropped; the decision carries expiry.** (a) A disposition
  with `expires_at <= now` is **dropped** (`dropped_expired >= 1`) and does not affect the verdict; the
  identical disposition unexpired **does** (e.g. a paramount objection that has expired no longer
  blocks). (b) The decision carries the request's `expires_at`. Pass/fail: verdict flip on expiry +
  field presence. (Targets M8, invariant 5, F6.)

- **AC8 — One token, one voice (no duplicated voice).** A request where one `token` submits two
  dispositions is **refused** (`GovernanceBreachError`) — a voice cannot be duplicated. Pass/fail:
  rejection. (Targets M1, invariant 7, F7.)

- **AC9 — Determinism.** Running `decide()` twice on the same request yields byte-identical JSON
  (`json.dumps(out, sort_keys=True)`), and the `paramount_objections`/`concerns` reason lists are
  canonically sorted. Pass/fail: string equality. (Targets M9.)

- **AC10 — Envelope validation.** Missing/empty `circle_id`/`proposal_id`/`now`/`expires_at`;
  `dispositions` not a list; a disposition not a dict; a disposition with a non-whitelisted key;
  `disposition` not in `{consent, object, abstain}`; an `object` without a `{paramount, reason}`
  objection; a non-`object` carrying an objection; a paramount that is not a bool; an empty reason →
  each **refused** (not repaired). Pass/fail: exception raised. (Targets E2/E3/N8.)

- **AC11 — No LLM / no network / stdlib-only, importable offline.** Importing
  `src/governance/governance.py` succeeds with **no** `anthropic`/network dependency; a static check
  finds **no** import of `anthropic`, `requests`, `httpx`, `openai`, `urllib`, or `socket`, and **no**
  injected model/`propose` parameter on `decide`. Pass/fail: import + static scan. (Targets N4 — the
  whole difference from Capa 3.)

- **AC12 — The bad-faith blocker is enforced as procedure, not judged (§6.3, flagged).** A single
  `object` with `paramount=true` and a (possibly spurious) reason **does** send the proposal to
  `revisit` — the function enforces the procedure and does **not** second-guess the objection's good
  faith (no "is this reason valid?" logic). Pass/fail: `revisit` regardless of reason content. (Targets
  N9, §6.3, F8 — flagged, not resolved.)

## Consistency with Capa 1, 2, 3, 4, and 5
- **AC-X — Shared surveillance taxonomy is honored across all six layers.** Feeding a Capa-1
  surveillance-shaped payload (e.g. a disposition nested `{"member":{"trust_score":88}}`) into
  `decide()` **refuses** it — the same verdict Capa 1's membrane, Capa 2's query, Capa 3's matcher,
  Capa 4's engine, and Capa 5's breaker reach independently on that shape. Additionally,
  `governance.FORBIDDEN_KEYS == membrane.FORBIDDEN_KEYS == legibility.FORBIDDEN_KEYS ==
  matcher.FORBIDDEN_KEYS == stigmergy.FORBIDDEN_KEYS`. Pass/fail: all refuse + set equality.
  (Targets P2, F11.)
</content>
