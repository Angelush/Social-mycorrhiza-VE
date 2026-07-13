# Context — information environment (Sim-B2B)

> Produced by build-context. Data room before the work.

## Domain
An agent-based simulation of a B2B mutual-credit / multilateral-clearing cell, driving the real
Micorriza B2B code. The world is a single cell (50–500 firms) whose members generate directed EUR
obligations by trading; the SUT nets them (clearing) and accounts them (mutual-credit ledger with
per-member credit lines). We inject actor archetypes and study integrity + welfare.

## The system under test (the real code — do NOT reimplement)
Verified against the shipping source (`clear` / `render_report`; the ledger's public ops). The sim
drives exactly these; where the brief's design vocabulary and the shipped code diverge, the code wins
and the divergence is a *finding*.
- **`B2B/src/clearing/clearing_solver.py`** — one entrypoint `clear(data) -> dict` over a **single
  cell** (`data = {cell_id, members, obligations}`); deterministic cycle-cancellation netting; integer
  cents; conservation-preserving (it **self-raises** if a net changes — relevant to the negative
  control, spec §7); byte-deterministic (sorted traversal); **proposal-only** (returns a settlement,
  commits nothing). Emits `credit_flags` = members whose *post-net* is out of bounds — it **flags,
  never rejects or clamps** (clearing can't change a net, so it only surfaces a pre-existing breach).
  Strict validation (rejects self-loop / unknown member / zero-or-negative / non-int). **No cross-cell
  concept:** obligations carry no cell tag; a foreign member is rejected as "unknown member" — the
  firewall (B2B inv. 6) is the single-`cell_id` input contract, not solver logic.
- **`B2B/src/ledger/mutual_credit_ledger.py`** — EUR mutual-credit ledger, **single cell**:
  event-sourced, zero-sum balances, hash-chained audit log with byte-exact `replay`/`verify_chain`,
  **integer `ts` input (no clock, no RNG → genuinely reproducible)**. Public ops: `add_member`,
  `record_obligation`, `settle_obligation`, `apply_clearing` (human-gated one-way door — requires
  `ratified_by`, independently re-verifies per-member conservation before committing), `update_member`
  (the graduated-sanctions **ladder** — enforces ordering, rejects rung-skips upward), `pause_cell` /
  `resume_cell`. Credit-line bounds are **rejected (raise), never clamped**, at record/settle/apply.
  Velocity breaker = **per-debtor `velocity_max_cents` within `velocity_window_s`, rejected on breach**
  (a **sliding** window — records with `ts > now − window` count; a rate limit, *not* a cascade
  breaker; there is no cascade in the SUT — and *not* automatic: the brief's "pausa automática" has no
  code counterpart, X7). Record ops are **status-gated**: debtor *and* creditor must be
  `active`/`warned`/`line_reduced`; settlement has **no status gate**, so a suspended defaulter's
  obligations can still be settled down (audit V19). **No `draw` and no `exit`
  op:** a negative balance arises from record+settle; a defaulter's balance **persists** (mutualised).

## Terminology (stable, inherited from the B2B brief)
- **Cell:** the permissioned unit; 50–500 firms; the credit firewall boundary.
- **Obligation:** directed debt edge `debtor → creditor`, EUR integer cents. **Not cell-tagged in the
  shipped code** — cell membership is implicit in the single-cell ledger instance (the brief's design
  vocabulary says cell-tagged; the code wins, and the divergence is part of the single-cell finding,
  T1c — audit V11).
- **Clearing / netting:** cancel the minimum around directed cycles; **net position unchanged**.
- **Net position:** `sum(incoming) − sum(outgoing)`; invariant under clearing.
- **Credit line:** per-member bounds (~−1% turnover negative cap, ~+10% positive cap; positive cap
  mandatory — anti-hoarding / redistribution).
- **Graduated sanctions:** warning → line reduction → suspension → expulsion (in code:
  `active → warned → line_reduced → suspended → expelled`). **Appeal is brief-only — it has no code
  counterpart** (human-layer, flagged via X5; audit V11).
- **Actor / policy:** a simulation agent submitting proposals (trades, settlements, clearing
  requests) each tick; "draw" and "exit/default" are **composite behaviours** sequenced from real ops
  (M1a / H1) — the ledger has no such primitives.

## Anchor data (calibration targets — do not over-promise; brief §6.5)
- Real Sardex: net internal debt reduced **≈25% by clearing alone, ≈50% combined with mutual credit.**
  A cooperative-mix campaign **reports** this alongside its **sensitivity to the topology generator** —
  it is a sanity check (off by an order of magnitude ⇒ X2 modelling-error flag), **not a build gate**:
  `reduction_pct` is a property of the synthetic graph, not the exact solver, so gating on it would
  reward tuning the generator to the anchor (calibration ≠ validation; H4). The gate is the negative
  control.
- Clearing benefit is **power-law-unequal** (best-connected nodes net more) → Track B must report the
  **Gini of benefit**, not just the mean.
- The system's advantage is **contracyclical and marginal** (brief §7.4) → a credit-crunch scenario is
  a first-class Track-B experiment.

## Actor archetypes (the seven; brief §2)
Circulator (good) · Hoarder (neutral) · Wallflower (neutral) · Defrauder (bad) · Sybil-hopper (bad) ·
Velocity attacker (bad) · Cell-leaker (bad). Each maps to an invariant/failure-mode it probes.

## Environment generators (hypotheses — flag as synthetic; brief §6.5)
- **Trade-relationship graph:** power-law / preferred-attachment topology (real commercial networks
  are power-law; the exact shape is unknown to us → declared a hypothesis, swappable).
- **Obligation stream:** per-tick trades drawn from each actor's policy over its trade neighbours.
- **Turnover:** per-firm scale parameter that sets its credit-line bounds.
- **Credit-crunch switch:** a scenario flag that removes an exogenous "bank credit" alternative, to
  test the contracyclical hypothesis.

## Stack (proposed, stable for this iteration)
- **Python 3.11+**, shares the repo-root `.venv` with B2B/C2C. Imports the B2B `src` package directly
  (path-adds or installs it editable). Integer cents on the value path.
- `pytest` + `hypothesis` for the harness's own tests (conservation of the *harness*, determinism).
- LLM probe (optional) injected + cassette-backed; suite runs offline by default.

## Examples of good/bad (harness quality)
- **Good:** a campaign that — against a copy of the solver with a **silent** conservation bug (a cent
  dropped *and* the solver's own conservation assert disabled) — **halts on the first round with the
  independent oracle's exploit trace** (the real gate, negative control); and separately reports the
  Sardex-band reduction with its topology-sensitivity and a non-trivial Gini of benefit.
- **Bad:** a harness that reimplements netting to "speed things up" (tests a fiction), averages an
  invariant violation into a 99.7% pass rate, or emits a per-firm "trustworthiness score" (a value-path
  system has no such thing; and it is a C2C anti-goal — do not import that shape here).

## Honesty flags (heuristics; brief §6)
- A green campaign falsifies nothing it did not try; report **coverage, not safety** (§6.1).
- Synthetic topologies are hypotheses, not the real network; calibration ≠ validation (§6.5).
