# Acceptance Criteria — Layer 1 Clearing Solver

> Produced by design-evals. Binary Done (AGD-028): verify the artifact, not a self-report.

- **AC1 — Conservation (recomputed independently).** For every test input, recompute each member's net position from the raw obligations and from the residual obligations; they must be **bit-identical**. Pass/fail: equal dicts. (Targets invariant 1; highest-risk tier.)
- **AC2 — Debt strictly reduced when a cycle exists.** For any input containing at least one directed cycle, `gross_debt_after < gross_debt_before`. For an acyclic input, `gross_debt_after == gross_debt_before`. Pass/fail: numeric.
- **AC3 — Residual graph is acyclic.** The residual obligations contain no directed cycle (a DAG). Pass/fail: cycle-detection returns none.
- **AC4 — Determinism.** Running the solver twice on the same input yields byte-identical JSON output. Pass/fail: string equality.
- **AC5 — Exactness / no floats.** All monetary fields in output are Python `int`; no float appears in any amount. Settlements sum, per obligation, never exceeds the original amount. Pass/fail: type + bound check.
- **AC6 — Credit-bound flagging (tail case, AGD-016).** Given an input where clearing leaves a member's net position outside its `[credit_min, credit_max]`, the output flags that member and does not silently clamp. Pass/fail: flag present.

Every AC is machine-executable with zero human judgment (Dark-Factory-grade for this deterministic component).
