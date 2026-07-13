# Failure Model + Stress Report

> Produced by red-team. Hostile review of the Layer-1 solver spec.

## Failure modes (F#)
- **F1 — Rounding/float drift.** Money as float → cents lost, conservation silently broken. *Mitigation:* M1 integer cents; AC5.
- **F2 — Net-position mutation.** A buggy cycle cancellation changes a member's net. *Mitigation:* M2 hard assert; AC1 independent recompute.
- **F3 — Non-determinism.** Dict/set iteration order changes which cycle is found first → different (still valid) but non-reproducible output, defeating audit. *Mitigation:* M3 sort ids; AC4.
- **F4 — Non-termination.** Cycle search loops forever. *Mitigation:* each cancellation removes ≥1 edge → monotone decrease → terminates (spec §2).
- **F5 — Silent credit-bound clamp.** Solver "fixes" a breach by clamping, hiding it. *Mitigation:* M6/N4/E1 flag-not-clamp; AC6.
- **F6 — Scope creep onto value path.** Someone adds an LLM "to optimize matching" inside the solver. *Mitigation:* N1; architecture multi-species table; README interaction pattern.
- **F7 — Cross-cell leakage.** Obligations from two cells netted together, breaking the contagion firewall. *Mitigation:* N2; spec input is single `cell_id`.

## Stress findings (ST#)
- **ST1 — Parallel edges.** Two A→B obligations must net correctly and back-allocate deterministically. *Found gap:* spec must define back-allocation order → added (id-ascending). Test C covers.
- **ST2 — Overlapping cycles sharing an edge.** Order of cancellation affects intermediate state but not final net. *Verify:* AC1 + AC4 on Test C.
- **ST3 — Self-loop / unknown member / zero amount.** Malformed input. *Mitigation:* E2 reject, no repair.
- **ST4 — Large graph performance.** Power-law dense cluster, thousands of edges. *Note:* cycle-cancellation is polynomial; acceptable for cell scale (50–500 members). Flag for benchmark before federation scale.
- **ST5 — Self-confirmation.** Solver's own net-position calc agrees with its own bug. *Mitigation:* independent `networkx` oracle cross-check (tests.md), AGD-045.

## Open (system-level, NOT solver) — do not fake-resolve (§7)
- Cold-start density (§7.1), protocol governance capture (§7.2), cross-border haircuts eating clearing gains (§7.3). These are governance/business problems; flagged, not coded.
