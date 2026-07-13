# Micorriza — B2B mutual-credit clearing system

Implementation of the design synthesis in [`micorriza-brief-diseno.md`](micorriza-brief-diseno.md),
built with a spec-driven engineering method (an intent/context/architecture/spec/constraints/failure-model/evals bundle).

> **North star (brief §0):** this is the *coordination-and-distribution institution* for an
> era of cheap creation — not "a more powerful AI" and not "a blockchain". The AI does the
> *solver/matching* work; the human-cooperative layer does ownership, trust, and governance.
> The design discipline is never confusing the two.

## Layout
```
micorriza-brief-diseno.md     # the source design brief
workflows/micorriza/          # spec bundle (the upstream: what to build + how to know it's right)
  architecture.md  intent.md  context.md  spec.md  constraints.md
  evals/{acceptance,tests}.md  evals/golden-set/*.json
  failure-model.md  audit.md  README.md  .specsmith.json
src/clearing/clearing_solver.py   # Layer-1 deterministic clearing solver + Markdown report renderer
src/ledger/mutual_credit_ledger.py # EUR mutual-credit ledger: event-sourced, zero-sum, human-gated apply
tests/                            # acceptance, property, validation + golden-set tests (128 passing)
```

## Build status (sequencing per brief §10)
- [x] spec bundle (Deep route)
- [x] **Layer-1 deterministic clearing solver** — min-cost / cycle-cancellation netting over the
      obligations graph. No LLM, integer cents, conservation-preserving, byte-deterministic,
      proposal-only (invariants 1 & 2). Strict input validation (E2) + Markdown settlement
      report (`render_report`). 64/64 tests pass.
- [x] **EUR mutual-credit ledger + per-member credit lines** (no token, no chain — §10 step 1).
      Event-sourced, zero-sum balances, hash-chained audit log with byte-exact `replay`,
      credit-line projection/balance bounds (flag-reject, never clamp), graduated-sanctions
      ladder, velocity/pause circuit breakers, and the human-gated one-way door:
      `apply_clearing` verifies a solver proposal's per-member conservation independently
      before committing it. Spec: `workflows/micorriza/spec-ledger.md` (AC-L1–L9).
- [ ] Layer-2 matcher (LLM, proposal-only), on-chain audit ledger, federation protocol (§10 steps 2–3)

## Run the tests
```bash
python3 -m venv .venv && .venv/bin/pip install pytest hypothesis networkx
.venv/bin/python -m pytest tests/ -q
```

## Non-negotiable invariants (enforced in code + tests)
"inv. N" = brief §1 invariant number; M/N/I ids = `workflows/micorriza/{constraints,spec}.md`.

- No stochastic process on the value path — the solver is classical code, never an LLM (inv. 1 / N1).
- The agent proposes, the human disposes — the solver returns a proposal, commits nothing (inv. 2 / M5).
- Conservation — every member's net position is identical before and after clearing (M2 / I1).
- Credit-bound breaches are flagged, never silently clamped (inv. 4 / M6 / I5).
- Cells are firewalled — no cross-cell value movement inside the solver (inv. 6 / N2).

See `workflows/micorriza/constraints.md` for the full guardrail set with because-clauses.
