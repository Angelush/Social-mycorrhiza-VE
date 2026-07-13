# Acceptance Criteria — Mutual-Credit Ledger

> Binary Done (AGD-028): verify the artifact, not a self-report. Every AC is machine-executable.

- **AC-L1 — Zero-sum.** After any accepted operation sequence, `sum(balance_cents) == 0` and `cell_metrics(...)["sum_balances_cents"] == 0`. Pass/fail: numeric.
- **AC-L2 — Bounds enforced, never clamped.** No accepted state contains a balance outside its member's `[credit_min, credit_max]`; a `record_obligation` whose projection breaches, or a `settle_obligation` whose balance move breaches, raises `ValueError` naming the member — and leaves the state unchanged. Pass/fail: raise + state equality.
- **AC-L3 — Clearing conservation (independent recompute).** `apply_clearing(state, clear(to_clearing_input(state)), …)` succeeds; per-member net open positions are identical before/after; **no balance changes**. A tampered proposal (any single `reduce_by_cents` altered by ±1) is rejected. Pass/fail: dict equality + raise.
- **AC-L4 — Determinism / replayability.** The same op sequence run twice yields byte-identical canonical states and event streams; `replay(events)` equals the live state; `verify_chain` passes; corrupting any one event field makes `replay`/`verify_chain` raise. Pass/fail: string equality + raise.
- **AC-L5 — Human gates.** Each of `create_cell, add_member, update_member, apply_clearing, pause_cell, resume_cell` raises `ValueError` when `ratified_by` is empty or not a str. Pass/fail: raise.
- **AC-L6 — Circuit breakers.** On a paused cell every mutating op except `resume_cell` raises; a debtor exceeding `velocity_max_cents` within `velocity_window_s` raises; a `ts` lower than `last_ts` raises. Pass/fail: raise.
- **AC-L7 — Exactness.** Every monetary field in states and events is Python `int` (bools rejected); no float appears anywhere in state or events. Pass/fail: type walk.
- **AC-L8 — Pilot-flow integration (métrica clave, brief §10.1).** End-to-end: create cell → vet members → record obligations → `clear(to_clearing_input(state))` → `apply_clearing` → settle a residual. The % of gross open debt reduced by clearing equals the solver's `reduction_pct`. Pass/fail: numeric.
- **AC-L9 — Graduated sanctions.** `update_member` accepts only adjacent forward status moves (e.g. `active→warned`), any backward move, and rejects jumps (e.g. `active→expelled`); suspended/expelled members cannot record new obligations but their open obligations can still be settled. Pass/fail: raise + accepted ops.
