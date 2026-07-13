# Specification — Mutual-Credit Ledger (EUR, no chain)

> Produced by engineer-spec (second component; brief §10 step 1: "contabilidad de crédito mutuo simple, denominación en euros, líneas individuales"). Self-contained: an autonomous agent could build this without asking a clarifying question. Compute-cost profile: **Low** (classical code, single process, no model).

## 1. Core mechanics

### Nature and role
`[DETERMINISTA]` **event-sourced system-of-record for one cell**: members, credit lines, mutual-credit balances, open obligations, hash-chained audit log. The core is purely functional: every operation is `op(state, ...) -> (new_state, event)` with no I/O, no clock, no randomness — time enters only as an integer field on commands. The ledger hosts the **one-way door** the proposal-only solver deliberately lacks: `apply_clearing` commits a solver proposal only with explicit human ratification (M5 / invariant 2).

### Value semantics (the meaning an agent cannot infer)
- **Balances** are mutual-credit EUR cents. No token, no interest, no demurrage in step 1 (brief §5: skirts MiCA; §8: 0% credit). Sum of all balances is **always exactly 0** — that is the definition of mutual credit (L1).
- **Obligations** are trade credit not yet settled (invoices). Clearing (Capa 1) extinguishes circular obligations **without any balance movement** — netted debt costs nothing to settle; that is the entire point. Residual obligations settle via zero-sum balance transfer bounded by credit lines.
- **Credit lines** bound the **projected position** at record time and the **actual balance** at settle time, where `projected(m) = balance(m) + owed_to(m) − owed_by(m)` over open obligations. Breaches **reject with the exact numbers in the error** — never clamp (M6).
- **Automated rejection vs invariant 9 (RGPD Art. 22):** the ledger deterministically enforces lines that a *human ratified* (`add_member`/`update_member` carry `ratified_by`). Enforcing a ratified rule is arithmetic, not an automated credit decision; line *changes* and sanctions always require ratification.

### State schema (JSON-serializable; canonical form defined in §2)
```json
{
  "cell_id": "string",
  "params": {
    "neg_line_bp": int,        // default credit_min = -(turnover * neg_line_bp) // 10000   (100 bp = 1%)
    "pos_line_bp": int,        // default credit_max =  (turnover * pos_line_bp) // 10000   (1000 bp = 10%)
    "velocity_window_s": int,  // circuit breaker (inv. 8): sliding-window length, seconds
    "velocity_max_cents": int, // max gross obligations one debtor may record inside the window
    "paused": bool
  },
  "members": { "<id>": { "turnover_eur_cents": int, "credit_min_cents": int, "credit_max_cents": int,
                          "status": "active|warned|line_reduced|suspended|expelled", "balance_cents": int } },
  "obligations": { "<id>": { "debtor": "member_id", "creditor": "member_id", "amount_cents": int, "ts": int } },
  "recent_recorded": [ { "ts": int, "debtor": "member_id", "amount_cents": int } ],
  "applied_proposals": [ "sha256-hex" ],
  "seq": int,
  "last_ts": int,
  "head_hash": "sha256-hex of last event, \"\" when empty"
}
```
`obligations` holds the **open remainder only** (fully cleared/settled ids are removed). `recent_recorded` is pruned on every `record_obligation` to entries with `ts > now_ts - velocity_window_s` (deterministic prune). Events are **not** stored in state; callers persist the event stream and `replay(events)` must rebuild the state byte-identically (L4).

### Operations (module `src/ledger/mutual_credit_ledger.py`, stdlib only)
Every mutating op: validates fully, builds the candidate state, runs the §3 post-condition asserts, and only then returns `(new_state, event)`. On **any** violation raise `ValueError` with a terse message naming the offending id — never repair, never partially apply, never mutate the input state (E2/N4).

1. `create_cell(cell_id, params, ratified_by, ts) -> (state, event)` — validates params (all ints, not bool; `neg_line_bp >= 0`, `pos_line_bp >= 0`, `velocity_window_s > 0`, `velocity_max_cents > 0`; `paused` starts False).
2. `add_member(state, member, ratified_by, ts)` — `member = {id, turnover_eur_cents, [credit_min_cents], [credit_max_cents]}`. Missing lines default from params by the integer formulas above. Always enforce `credit_min_cents <= 0 <= credit_max_cents`. New member: `status="active"`, `balance_cents=0`. Vetted membership (inv. 10) → requires `ratified_by`.
3. `update_member(state, member_id, changes, ratified_by, ts)` — `changes` may set `credit_min_cents`, `credit_max_cents`, `status`. Status moves along the **graduated ladder** `active → warned → line_reduced → suspended → expelled` (inv. 5): forward moves only to the **adjacent** status; backward moves (de-escalation) to any earlier status. Line changes must keep the current balance within the new bounds (else reject — a line change may not instantly strand a member outside its own bounds).
4. `record_obligation(state, obligation, ts)` — `obligation = {id, debtor, creditor, amount_cents}`. Requires: not paused; id unused (also unused by any *past* obligation — ids are never recycled: keep a `"used_obligation_ids"`? NO — openness check + `applied/settled` removal makes reuse ambiguous; therefore the event log is the authority: maintain state key `"obligation_ids_seen"`: [ids…] and reject reuse); debtor ≠ creditor; both members exist with status in {active, warned, line_reduced}; `amount_cents` int (not bool) > 0; `ts` monotone (≥ `last_ts`). **Velocity breaker:** debtor's `recent_recorded` sum inside the window + this amount ≤ `velocity_max_cents`. **Projection bounds:** with the new obligation included, `projected(debtor) >= debtor.credit_min_cents` and `projected(creditor) <= creditor.credit_max_cents`.
5. `apply_clearing(state, proposal, ratified_by, ts)` — `proposal` is the verbatim dict returned by `clearing_solver.clear`. Checks, in order: not paused; `ratified_by` non-empty; `proposal["cell_id"] == state["cell_id"]`; `proposal_hash = sha256(canonical(proposal))` not in `applied_proposals` (idempotency / replay guard); aggregate `settlements` per `obligation_id` (a proposal may legitimately split one obligation across entries), then for each: obligation open, total reduction int (not bool) > 0 and ≤ open amount; **independent conservation check (M2/L3):** for every member, the summed reductions where it is debtor equal the summed reductions where it is creditor (balanced per-member flow ⇔ cycle-decomposable, so this exactly characterizes legitimate clearing without re-running the solver). Effect: reduce obligations (delete at zero), record `proposal_hash`. **Balances unchanged.**
6. `settle_obligation(state, obligation_id, amount_cents, ts)` — not paused; obligation open; amount int (not bool), 0 < amount ≤ open; ts monotone. Effect: `debtor.balance -= amount`, `creditor.balance += amount`, obligation reduced (delete at zero). **Bounds:** debtor's new balance ≥ its `credit_min_cents`, creditor's new balance ≤ its `credit_max_cents`, else reject. Settling is allowed **regardless of member status** (sanctions never trap debt; paying what you owe is always legal).
7. `pause_cell(state, ratified_by, ts)` / `resume_cell(state, ratified_by, ts)` — circuit-breaker switch (inv. 8). While paused every mutating op except `resume_cell` rejects. Pausing a paused cell (or resuming a running one) rejects.
8. **Views (pure, read-only):**
   - `to_clearing_input(state) -> dict` — the exact Capa-1 solver input schema: all members (sorted by id) with turnover + lines; all open obligations (sorted by id). This is the bridge that makes `clear(to_clearing_input(state))` the cell's clearing run.
   - `member_statement(state, member_id) -> dict` — balance, lines, status, open owed_by/owed_to totals, projected position.
   - `render_statement(state, member_id) -> str` — Markdown, euro amounts via the same integer-divmod format as the solver's `render_report` (sign + `abs//100`.`abs%100:02d` + " €").
   - `cell_metrics(state) -> dict` — member count, open obligation count, `gross_open_cents`, `sum_balances_cents` (must be 0), `paused`.
9. `replay(events) -> state` — folds the event stream through the same op logic (dispatch on `event["kind"]`), verifying the hash chain (`prev_hash`/`hash`) as it goes; any mismatch raises ValueError. `verify_chain(events) -> None` — chain check alone.

### Event schema
`{"seq": int, "ts": int, "kind": str, "payload": {…}, "prev_hash": str, "hash": str}` where `hash = sha256(canonical({seq, ts, kind, payload, prev_hash}))`. Kinds: `cell_created, member_added, member_updated, obligation_recorded, clearing_applied, obligation_settled, cell_paused, cell_resumed`. The payload carries the full command (including `ratified_by` where applicable) — sufficient for `replay` to be exact. `clearing_applied.payload` embeds the whole proposal (audit: the ratified artifact is on the record, M4/inv. 7).

## 2. Determinism and canonical form
`canonical(x) = json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")`; hashes are `hashlib.sha256(...).hexdigest()`. Identical op sequences yield byte-identical states and event streams (M3). `ts` is integer epoch seconds, **monotone non-decreasing** per cell; a regression rejects (breaker against clock skew and window games).

## 3. Invariants (L-set) — asserted after every mutating op; failure = raise, never emit
- **L1 Zero-sum:** `sum(balance_cents) == 0`.
- **L2 Bounds:** every balance within its member's `[credit_min, credit_max]`.
- **L3 Clearing conservation:** `apply_clearing` leaves every member's net open position identical (checked independently per §1.5) and moves no balance.
- **L4 Replayability:** `replay(events)` reproduces the state byte-identically; hash chain verifies; corrupting any event breaks it.
- **L5 Human gates:** `create_cell`, `add_member`, `update_member`, `apply_clearing`, `pause_cell`, `resume_cell` require non-empty `ratified_by` (str).
- **L6 Breakers:** paused blocks mutation; velocity cap enforced; ts monotone.
- **Hazards to prevent:** float creep (no float anywhere in state/events); dict-order nondeterminism (canonical json, sorted views); partial application (validate → candidate → assert → return); proposal replay (hash registry); id recycling (`obligation_ids_seen`).

## 4. Contract-first echo (PRM-024)
`deliverable: event-sourced mutual-credit ledger (Python, stdlib) + tests | key inclusion: human-gated apply_clearing with independent per-member conservation check, hash-chained audit log, credit-line + circuit-breaker enforcement, to_clearing_input bridge to Capa 1 | hard constraint: integer cents, zero-sum balances, byte-deterministic replay, ValueError on any malformed or violating input, no LLM (N1)`

## 5. Scope limits (out)
No persistence/DB, no network/API, no auth (upstream), no matching, no credit *scoring* (human/Capa-2), no cross-cell settlement (Capa 3), no fiat bridge (Capa 4), no on-chain anchoring (the hash chain is its future attachment point), no interest/demurrage.
