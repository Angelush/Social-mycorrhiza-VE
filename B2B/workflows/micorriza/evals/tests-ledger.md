# Test Cases — Mutual-Credit Ledger

> Each: input, expected output, verification rule. Golden flow pinned in `golden-set/ledger_flow.json` after first verified build.

## Flow A — Normal pilot cycle (AC-L1/L3/L4/L8)
- `create_cell("cell1", {neg_line_bp:100, pos_line_bp:1000, velocity_window_s:86400, velocity_max_cents:5_000_000, paused:False}, "ana", ts=1000)`.
- Add members A,B,C,D, turnover 100_000_000 each, no explicit lines → defaults `credit_min=-1_000_000`, `credit_max=10_000_000` (integer bp math).
- Record: o1 A→B 10000, o2 B→C 6000, o3 C→A 4000, o4 D→A 2500 (ts 1010..1040).
- `clear(to_clearing_input(state))` → settlements o1:4000, o2:4000, o3:4000; `reduction_pct` ≈ 53.333333; **verify** `to_clearing_input` matches the solver's input schema exactly.
- `apply_clearing(..., "ana", ts=1050)` → open: o1 6000, o2 2000, o4 2500 (o3 gone); **all balances still 0**; per-member net open positions identical before/after.
- `settle_obligation("o1", 2500, ts=1060)` → A balance −2500, B +2500, o1 open 3500; `sum_balances == 0`.
- `cell_metrics` → gross_open 8000, sum_balances 0. `replay(events)` byte-identical to live state; `verify_chain` passes.

## Edge B — Rejection battery (AC-L2/L5/L6/L7/L9; each raises ValueError and leaves state unchanged)
Gates: every gated op with `ratified_by=""` or non-str. Shape: unknown debtor/creditor; self-loop; duplicate obligation id; **id reuse after the obligation was fully settled/cleared** (ids never recycle); amount bool/float/zero/negative; params/lines wrong types; `credit_min>0`; `credit_max<0`.
Breakers: any mutating op while paused (resume works); pause-while-paused, resume-while-running; velocity — record 3_000_000 then 2_500_000 in-window rejects, same amount after the window passes accepts; `ts` regression.
Bounds at record (projection): creditor with `credit_max=1000` receiving a 2000-cent obligation rejects (anti-hoarding cap, inv. 4); debtor with `credit_min=-1000` owing 2000 rejects.
Bounds at settle (reachable only via sanctioned line-tightening — this is why both checks exist): G(min −1000)→H o 800 recorded; settle 100 (G at −100); `update_member` G min → −500 (balance −100 fits, allowed); now settle 500 more rejects (−600 < −500), settle 400 accepts (G exactly −500).
Sanctions ladder: `active→line_reduced` jump rejects; `active→warned→line_reduced` accepts; suspended member cannot record (as debtor or creditor) but its open obligations still settle; backward `suspended→active` accepts.
Line change stranding balance: tightening a line below the member's **current balance** rejects.

## Adversarial C — Proposal forgery (AC-L3)
- Tampered genuine proposal (`reduce_by_cents` ±1 anywhere) → reject.
- Replay of an already-applied proposal (identical dict) → reject (hash registry).
- Globally-balanced but per-member-unbalanced forgery: reduce o1 (A→B) 1000 + o4 (D→A) 1000 — balanced for A, unbalanced for B and D → reject.
- Split entries: two settlement rows for the same obligation whose **sum** exceeds its open amount → reject (aggregate before checking).
- Proposal naming an unknown/settled-away obligation id → reject.

## Property tests (hypothesis; AC-L1/L2/L4)
Random op streams (≤4 members, ≤30 ops, mixed valid/invalid): after every *accepted* op — zero-sum holds, every balance in bounds; at the end — `replay(events)` equals live state canonically and `verify_chain` passes. Rejected ops leave state canonically unchanged.

## Cross-check (independent oracle)
Recompute `sum_balances` and per-member projections from raw events (fold without the module's own state math) for Flow A; compare. Disagreement = fail (AGD-045).
