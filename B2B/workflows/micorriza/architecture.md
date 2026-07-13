# Architecture — Agent Species classification

> Produced by classify-architecture. Source brief: `micorriza-brief-diseno.md`.

## Diagnosis (orient)
- **Maturity:** Architect. The brief is already a spec-grade synthesis with invariants, layer natures, and open problems.
- **Weakest rung (routing key):** Specification Engineering. Intent and context are well-formed in the brief; the gap is a self-contained, buildable blueprint with enforceable guardrails.
- **Real bottleneck:** Execution (turning a sound design into verifiable code) — *not* clarity. Caveat per §7/§10: the binding business bottleneck is **distribution/relationship** (cold-start density), which code cannot solve. We build the technical core; we do not pretend it bootstraps the network.
- **Stakes & reuse:** High — touches money, credit, compliance (MiCA/RGPD), irreversible value movement. Recurring system, not one-shot.
- **Route:** **Deep.**

## This is a MULTI-SPECIES system. Classify per component, never monolithically.

| Component (brief layer) | Nature | Agent Species | Human-in-loop |
|---|---|---|---|
| Capa 0 — La célula | `[HUMANO]` | Not an agent. Governance/membership/sanctions. | Human owns entirely |
| **Capa 1 — Clearing solver** | `[DETERMINISTA]` | **Not an LLM.** Classical algorithm (min-cost-flow + cycle cancellation). Lowest rung that clears the bar (FWK-004). | Output auditable; humans ratify cadence |
| Capa 2 — Matcher/discovery | `[ESTOCÁSTICO/LLM]` | **Species 2 framed as Tool-assistant**, NOT Dark Factory. Proposes only; human disposes (invariant 2). | Human approves every proposal |
| Capa 3 — Federation protocol | `[SMART CONTRACT/STANDARD]` | Thin standard, not an agent. | Council of cells (open problem §7.2) |
| Capa 4 — Fiat bridge | `[SMART CONTRACT + COMPLIANCE]` | Not an agent. Conservative, narrow. | Compliance gate |
| Capa 5 — Commons treasury | `[QUADRATIC FUNDING]` | Mechanism, not an agent. | Member vote |
| Credit-line scoring | `[ESTOCÁSTICO assist]` | Adviser only. Denial requires human (RGPD Art. 22). | Human decides credit denial |

## The build harness (how WE build this)
**Species 1b — Coding Harness (Project).** Human is the manager; judgment is the gate. Decompose into <2hr file-level agent tasks. Reviewer one tier above executor. Two-tier planner→worker, no 3+ management layers (AGD-008, simple scales well).

## Complexity-floor gate (FWK-004 / FWK-030)
- The clearing solver is **deliberately the lowest rung**: a deterministic graph algorithm, no ML, no LLM. Adding an LLM here would *violate invariant 1*. This is the #1 design-discipline win: refuse to over-build the value-moving path.
- The matcher is the only place an LLM earns its keep, capped at **Tool-assistant / proposal** level (FWK-030), never Semi-auto or Fully-autonomous over value.

## Operating surface (AG-UI / A2A)
- Every value-moving op must **show its work** (auditable ledger = blockchain's only job, invariant 7). An agent that can't show its work = supervision debt.
- Circuit breakers (invariant 8) escalate in importance with agent speed — flash-loan-class cascade risk at machine speed.

## Human-involvement model
Agent proposes, human disposes (invariant 2). Hard human gates: credit denial (RGPD), boundary/sanction judgment, constitutional governance. Everything stochastic is upstream of a human ratification step; nothing stochastic is on the liquidation path.
