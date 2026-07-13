# Audit — every finding → an enforceable requirement

> Produced by audit-feedback-loop (the judge). Proves each F#/ST# became a constraint, AC, or task — not just a report line.

| Finding | Became enforceable as | Enforced? |
|---|---|---|
| F1 float drift | M1 (int cents) + AC5 | ✅ |
| F2 net mutation | M2 (assert) + AC1 (independent recompute) | ✅ |
| F3 non-determinism | M3 (sort ids) + AC4 (twice → byte-identical) | ✅ |
| F4 non-termination | spec §2 monotone argument + (test: bounded iterations) | ✅ |
| F5 silent clamp | M6 + N4 + E1 + AC6 | ✅ |
| F6 LLM on value path | N1 + architecture table + README pattern | ✅ |
| F7 cross-cell leak | N2 + spec single-cell input | ✅ |
| ST1 parallel edges | spec back-allocation order + Test C | ✅ |
| ST2 overlapping cycles | AC1 + AC4 on Test C | ✅ |
| ST3 malformed input | E2 (reject) | ✅ |
| ST4 large-graph perf | failure-model note + task: benchmark before federation | ⚠️ deferred (not a cell-scale blocker) |
| ST5 self-confirmation | independent networkx oracle — specified in tests.md, enforced in `tests/test_clearing_solver.py::test_networkx_oracle_net_positions` (AGD-045) | ✅ |

**Verdict:** All correctness/safety findings are enforced by a constraint AND covered by an acceptance criterion. ST4 (performance at federation scale) is explicitly deferred with a tracked task, not silently dropped. Bundle is ready to build.
