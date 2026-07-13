# Test Cases — Layer 1 Clearing Solver

> Produced by design-evals. Each: input, expected output, verification rule. Golden pairs live in `golden-set/`.

## Test A — Normal: a single 3-cycle
- **Input:** members A,B,C (generous bounds). Obligations A→B 100€, B→C 100€, C→A 100€ (cents: 10000 each).
- **Expected:** all three netted to zero; `cycles_cancelled=1`; `gross_debt_before=30000`, `gross_debt_after=0`, `reduction_pct=100`. Net positions all 0 before and after.
- **Verify:** residual empty; conservation holds (AC1); AC2, AC3.

## Test B — Edge: partial cycle + chain (asymmetric amounts)
- **Input:** A→B 100, B→C 60, C→A 40, plus D→A 25 (cents ×100). Cycle A→B→C→A nets min=40 → A→B 60, B→C 20, C→A 0 removed. D→A 25 untouched (chain, no cycle).
- **Expected:** `cycles_cancelled=1`, gross before 22500, after = (6000+2000+2500)=10500. Residual: A→B 6000, B→C 2000, D→A 2500. Net positions identical before/after.
- **Verify:** AC1, AC2 (strict reduction), AC3 (residual acyclic), AC5 (exact cents).

## Test C — Adversarial / tail (AGD-016): multiple overlapping cycles + credit-bound breach + parallel edges
- **Input:** dense graph with two overlapping cycles sharing an edge, parallel edges A→B (two obligations 30 + 70), and a member E whose `credit_max` is small enough that netting leaves its net position above the cap.
- **Expected:** deterministic netting independent of edge insertion order (AC4); parallel A→B reductions back-allocated to the two obligation ids in id-ascending order; E flagged for credit-bound breach, **not clamped** (AC6); conservation still exact (AC1).
- **Verify:** run twice → byte-identical (AC4); recompute net positions independently (AC1); assert E flag present (AC6). This is the tail case where "correct" (flag + preserve) contradicts the naive "make it fit."

## Cross-check (independent oracle)
For Tests A/B, build the same graph in `networkx` and verify net positions via `in_degree(weight)`−`out_degree(weight)`; compare to solver's `net_positions`. Disagreement = fail (catches implementation self-confirmation, AGD-045).

## Golden set
Serialize A, B, C inputs + expected outputs as JSON pairs in `golden-set/`. Re-run on any solver change. Treat the solver as a hypothesis scored against these (DVH-007/008).
