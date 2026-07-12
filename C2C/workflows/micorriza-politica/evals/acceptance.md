# Acceptance Criteria — Capa 4 Assurance-Contract Engine

> Produced by design-evals. Binary Done (AGD-028): verify the artifact, not a self-report.

- **AC1 — Threshold correctness (recomputed independently).** For every test input, recompute `distinct_committers` by independently deduping `participant_token` and compare to the engine; `status` must equal `fires` iff `distinct >= threshold`. Pass/fail: equality. (Targets the core rule.)
- **AC2 — No-loss guarantee.** For any input where `status == refunds`, each committer's `refund_cents` equals the independently-summed total they pledged; nobody is short a cent. For `fires`, the refund list is empty. Pass/fail: per-committer equality. (Targets invariant: nobody worse off.)
- **AC3 — Bonus conservation + exactness.** When refunding, `sum(bonus_cents) == sponsor_bonus_cents` exactly; the split differs by at most 1 cent across committers and the first `rem` (by ascending token) get the extra cent. When firing, all bonus is 0. All monetary fields are `int`; no float appears. Pass/fail: numeric + type.
- **AC4 — Determinism.** Running the engine twice on the same input yields byte-identical JSON. Pass/fail: string equality.
- **AC5 — Anti-surveillance shape (the C2C-defining tail case, AGD-016).** (a) No output field anywhere scores/ranks/rates/persists a person (recursive key scan rejects `score|rating|reputation|rank|blacklist|ban|penalty|global_id|dni`). (b) An input carrying any such forbidden field **at any nesting depth** is **rejected** (recursive input scan), not processed. (c) Two campaigns sharing a `participant_token` produce outputs with no cross-campaign aggregate. Pass/fail: key-scan + rejection. This is the case where "correct" means *refusing to produce the surveillance-shaped artifact*.
- **AC6 — Membrane (kula/gimwali wall).** A `binary`/equality campaign whose pledges carry positive prices, **or that carries a `sponsor_bonus_cents > 0`**, is **rejected** — no market instrument (a price *or* a monetary failure-bonus) may leak into the equality room (invariant 1); the bonus ban is also anti-Sybil (a zero-stake failure-bonus is a free faucet, §6.2). Pass/fail: rejection raised.

Every AC is machine-executable with zero human judgment.
