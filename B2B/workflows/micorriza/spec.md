# Specification — Layer 1 Clearing Solver

> Produced by engineer-spec. Self-contained: an autonomous agent could build this without asking a clarifying question. Compute-cost profile: **Low/Medium** (classical algorithm, single process, no model).

## 1. Core mechanics

### Inputs
A clearing run receives:
```json
{
  "cell_id": "string",
  "members": [
    {"id": "string", "turnover_eur_cents": int,
     "credit_min_cents": int,   // negative cap, e.g. -1% turnover (<=0)
     "credit_max_cents": int}   // positive cap, e.g. +10% turnover (>=0)
  ],
  "obligations": [
    {"id": "string", "debtor": "member_id", "creditor": "member_id",
     "amount_cents": int}       // strictly > 0, integer cents
  ]
}
```
- All money is **integer cents** (no floats — invariant: exact arithmetic).
- All obligations within a single `cell_id` (cross-cell handled later by bilateral net settlement, invariant 6).

### Outputs
```json
{
  "cell_id": "string",
  "settlements": [               // the netting instructions (a PROPOSAL)
    {"obligation_id": "string", "reduce_by_cents": int}
  ],
  "residual_obligations": [ {"debtor","creditor","amount_cents"} ],
  "metrics": {
    "gross_debt_before_cents": int,
    "gross_debt_after_cents": int,
    "reduction_pct": float,
    "cycles_cancelled": int
  },
  "net_positions": { "member_id": int },   // before == after (asserted)
  "credit_flags": [ "member_id" ],          // net position outside [credit_min, credit_max] — flagged, never clamped (I5/M6)
  "audit_trace": [ {"cycle": ["m1","m2","m3"], "min_edge_cents": int} ]
}
```
- Output format: **JSON** (machine) + a rendered Markdown settlement report (human).
- The result is a **proposal**: it is not committed. A separate gated step applies it (invariant 2).

### Dependencies
Python 3.11+, stdlib only for the core (optional `networkx` for cross-check tests). `pytest` + `hypothesis` for tests.

### Assumptions
- Member ids referenced by obligations exist in `members`.
- Amounts are positive integers; the graph may contain parallel edges and self-loops are rejected.

### Scope limits (out)
No credit *decisions*, no scoring, no cross-cell transfer, no persistence/DB, no network, no LLM, no chain. Those are other components.

## 2. Algorithm (deterministic)
1. Build a directed multigraph of obligations; collapse parallel debtor→creditor edges into a single weighted edge (keep id map for settlement back-allocation).
2. **Cycle-cancellation netting:** repeatedly find a directed cycle; cancel `min` edge weight around it (reduce every edge on the cycle by that min, removing zeroed edges). This is the core of multilateral clearing. Equivalent formulation: min-cost-flow where keeping `net_position` fixed and minimizing total flow yields the minimal residual.
3. Stop when the graph is acyclic (a DAG → no more circular debt to net).
4. Back-allocate each collapsed edge's reduction across its original obligation ids (deterministic order: by obligation id ascending) to produce `settlements`.
5. Compute metrics, assert conservation, emit audit trace.

**Determinism requirement:** given identical input, byte-identical output. Cycle search must use a fixed traversal order (sort node ids) so results are reproducible and auditable.

## 3. Meaning layer (CAR-001 — what the agent can't infer)
- **Invariants (must always hold):**
  - I1 *Conservation:* `net_position(m)` identical before and after. (Hard assert; failure = abort, never emit.)
  - I2 *No value creation:* `gross_debt_after <= gross_debt_before`; reductions are non-negative.
  - I3 *Exactness:* integer cents end-to-end; no float money.
  - I4 *Proposal-only:* function returns a proposal; it performs no commit/side-effect.
  - I5 *Credit bounds:* residual net positions must lie within `[credit_min, credit_max]`; if clearing would push a member past a bound, flag it in output (do NOT silently clamp — escalate).
- **Hazards to prevent:** rounding drift; non-determinism from dict/set ordering; integer overflow (use Python big ints — fine); infinite loop on cycle detection (each cancellation strictly removes ≥1 edge → terminates).
- **Work-primitive semantics (AGD-052):** KIND=compute-proposal, OWNER=solver, REVERSIBILITY=fully reversible (no commit), BLAST-RADIUS=none until a separate apply step. The apply step (future) is KIND=write, irreversible, high blast → tightest gate + human ratify.

## 4. Contract-first echo (PRM-024)
`deliverable: exact deterministic multilateral-clearing solver (Python) + tests | key inclusion: conservation-preserving cycle cancellation with audit trace | hard constraint: integer-cents exactness, proposal-only, byte-deterministic, no LLM`.

## 5. Compute-cost
Low/Medium. Single LLM call? **No.** This is classical code. Use of any model on this path is a spec violation.
