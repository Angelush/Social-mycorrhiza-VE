# Constraint Architecture

> Produced by author-constraints. Each rule carries a "because" clause (AGD-029).

## MUSTs
- **M1** Use integer cents for all monetary values — *because* float arithmetic introduces rounding drift, and a 0.1% error is inadmissible when output moves money (invariant 1).
- **M2** Preserve every member's net position exactly (assert before==after) — *because* clearing only nets circular debt; changing a net position would be silent value transfer (invariant 1, conservation).
- **M3** Be byte-deterministic for identical input (sort node/edge ids before traversal) — *because* the output is an auditable settlement proposal; non-reproducible results can't be audited (invariant 7).
- **M4** Emit an audit trace (cycles cancelled + min edge each) — *because* the ledger's only legitimate job is transparency/audit (invariant 7); every value-moving op must show its work.
- **M5** Return a proposal only; perform no commit/side-effect — *because* the agent proposes, the human disposes (invariant 2).
- **M6** Respect per-member credit bounds; flag (never clamp) a breach — *because* the positive cap is the redistribution + anti-hoarding mechanism (invariant 4) and silent clamping would corrupt it.

## MUST-NOTs
- **N1** No LLM / stochastic process anywhere on this path — *because* nothing stochastic may execute irreversibly over value (invariant 1).
- **N2** No cross-cell value movement inside the solver — *because* the network is deliberately not fully connected; contagion is firewalled at the cell boundary (invariant 6). Cross-cell is bilateral net settlement, a separate component.
- **N3** No token, no on-chain settlement of value, no float — *because* §2 antipatterns + MiCA exposure; chain is audit-only (invariant 7).
- **N4** No silent failure: on any invariant violation, abort and surface — never emit a settlement that fails conservation.

## PREFERENCES
- **P1** Prefer stdlib-only core for auditability; `networkx` allowed only in tests as an independent cross-check.
- **P2** Prefer a human-readable Markdown settlement report alongside JSON.
- **P3** Prefer property-based tests (hypothesis) for the conservation/exactness invariants.

## ESCALATION TRIGGERS (halt + human)
- **E1** A clearing result would push any member outside `[credit_min, credit_max]` → flag, do not commit (links to future credit-scoring + RGPD Art. 22 human gate, invariant 9).
- **E2** Input graph references unknown member, contains self-loop, or non-positive amount → reject input, do not attempt repair.
- **E3** Conservation assert fails → abort run, emit diagnostic, never output a settlement.

## Reversibility framing
- The solver itself is a **two-way door** (pure computation, no side effects) → fully autonomous.
- The future *apply/commit* step is a **one-way door** (moves value) → must draft + escalate, human ratifies, with undo window where possible (AGD-018). Circuit breakers (invariant 8) gate it.

## Constraint × Execution-Mode matrix
| ID | Solver (Live) | Simulation/Backtest | Notes |
|----|---------------|---------------------|-------|
| M1 exact cents | Enforce | Enforce | always |
| M2 conservation | Enforce (abort) | Enforce (abort) | hard |
| M3 determinism | Enforce | Enforce | |
| M5 proposal-only | Enforce | Skip (sim may apply to a copy) | sim mutates a sandbox |
| M6 credit bounds | Enforce (flag) | Measure only | sim records breaches as data |
| E1 bound breach | Escalate | Measure only | don't halt a backtest |
