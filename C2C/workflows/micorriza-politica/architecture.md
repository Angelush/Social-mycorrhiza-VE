# Architecture — Agent Species classification

> Produced by classify-architecture. Source brief: `micorriza-politica-brief-social.md`.

## Diagnosis (orient)
- **Maturity:** Architect. The brief is a spec-grade synthesis with invariants, layer natures, a negative anchor (Chinese social credit), and named open problems.
- **Weakest rung (routing key):** Specification Engineering. Intent/context are richly formed; the gap is a self-contained, buildable, *non-surveillance* blueprint with enforceable guardrails.
- **Real bottleneck:** **Relationship + clarity**, NOT execution. The brief is explicit (§0, §6.3): you cannot manufacture the will to cooperate; social capital is cultivated, never injected. Code only *scaffolds* (wu wei). We build a small honest technical core; we refuse to pretend the protocol fabricates trust.
- **Stakes & reuse:** **Highest.** §6 is blunt: the failure mode here is worse than B2B's "dead network" — it is a **surveillance cage**. Recurring, high-consequence, touches identity, reputation, civic power.
- **Route:** **Deep.**

## This is a MULTI-SPECIES system — and the dominant species is HUMAN, not agent.
Classify per component. The defining design move (inversion of Chinese social credit, §7) is to build first the parts that **cannot be turned into a surveillance score**, and add legibility last, with maximum care.

| Component (brief layer) | Nature | Agent Species | Human-in-loop |
|---|---|---|---|
| Capa 0 — La célula / círculo | `[HUMANO · LOCAL]` | Not an agent. Dunbar-bounded local trust. | Human owns entirely |
| **Capa 1 — Partición por modo relacional ("las habitaciones")** | `[INVARIANTE ARQUITECTÓNICA]` | Not an agent. A firewall/type-system — the most important layer. Deterministic, pure, proposal-only membrane check; reuses the Capa-4 forbidden-key taxonomy. **THIS BUILD (spec: `capa1/spec.md`).** | Architectural membrane |
| **Capa 4 — Quórum / aseguramiento (assurance contracts)** | `[DETERMINISTA]` | **Not an LLM.** Threshold logic + exact bonus arithmetic. Lowest rung that clears the bar (FWK-004). **THIS BUILD.** | Proposes resolution; protocol/humans execute |
| **Capa 2 — Legibilidad de la confianza** | `[EL FILO DE LA NAVAJA]` | Not an LLM. Relational web-of-trust *query*, contextual, with forgetting, over a caller-supplied local graph. Emits no score/rank/god-view; the god-view is made structurally unrepresentable (asker required, graph never stored, hop-bounded, output = paths/facts, absence = "no info"). Reuses the Capa-1/Capa-4 forbidden-key taxonomy. Built **last, with maximum care**, §7 Etapa 2. **THIS BUILD (spec: `capa2/spec.md`).** | Consulted from a position; never a god-view |
| **Capa 3 — Afordancia / emparejamiento ("el emparejador")** | `[ESTOCÁSTICO · LLM]` | **Species 2 framed as Tool-assistant**, NOT Dark Factory, capped at **proposal** level (FWK-030). **The FIRST LLM in the stack.** A stochastic proposer **boxed inside a deterministic wrapper**: the model proposes matches; the wrapper validates/bounds/canonically-sorts and **drops** anything off-cell, non-consenting, off-schema, surveillance-shaped, or engagement-shaped; a human disposes. Objective is **cooperation initiated, never engagement** — made structural (invariant 8): no engagement signal is a representable input, no feedback loop. Reuses the Capa-1/2/4 forbidden-key taxonomy. The LLM client is **injected**, never imported at module top. **THIS BUILD (spec: `capa3/spec.md`).** | Human approves every proposal; proposes-never-imposes |
| **Capa 5 — Estigmergia + cortacircuitos** | `[PROTOCOLO + CIRCUIT BREAKERS]` | **Not an LLM.** Deterministic sensing of environmental traces with pheromone evaporation + structural anti-cascade breakers (friction/velocity-cap per window, context-before-judgment, cell-scope/zero-broadcast). Traces are about artifacts/paths, never a person-scalar; no ban/distrust signal representable; the mob/cascade is throttled by construction. Reuses the Capa-1/2/3/4 forbidden-key taxonomy. **THIS BUILD (spec: `capa5/spec.md`).** | Anti-cascade gates (invariant 9); senses, humans act |
| **Capa 6 — Gobernanza sociocrática** | `[HUMANO → CONSENT-NOT-CONSENSUS]` | **Not an LLM.** Deterministic consent resolution: `adopted` iff no paramount (reasoned) objection, else `revisit` — categorical, never a majority/tally. Voice independent of reputation made structural (invariant 7): one token one voice, and the weighting cannot be phrased (`VOTE_WEIGHT_KEY` refuse-list + whitelist). An objection is a pause that surfaces its reason, never a mark of the objector; circle-local, no auto-propagation; per-round forgetting. Reuses the Capa-1/2/3/4/5 forbidden-key taxonomy. **THIS BUILD (spec: `capa6/spec.md`).** | Humans decide; the code enforces the procedure, not good faith |
| Capa 7 — Sustrato simbólico | `[HUMANO · PLURAL]` | Not an agent. Multiple opt-in symbol layers; never one imposed. | Humans |

## The build harness (how WE build this)
**Species 1b — Coding Harness (Project).** Human is the manager; judgment is the gate. File-level agent tasks, reviewer one tier above executor. Two-tier planner→worker, no 3+ layers (AGD-008).

## Complexity-floor gate (FWK-004 / FWK-030)
- The assurance-contract engine is **deliberately the lowest rung**: deterministic threshold + integer-cent arithmetic, no ML, no LLM, no reputation. Adding an LLM here would invite exactly the score/optimization creep the brief forbids.
- The matcher (Capa 3) is the only place an LLM earns its keep, capped at **Tool-assistant / proposal** level (FWK-030) — and its objective is *cooperation initiated, never engagement* (invariant 8).

## The anti-surveillance gate (the species-defining constraint)
This system's primary hazard is not a bad output — it is the **right output in the wrong shape**: any artifact that aggregates into a global scalar of a person (invariant 2), a blacklist (invariant 3), or a central trust ledger (invariant 6). Every component must pass a **shape check**: it must be structurally incapable of emitting a cross-context person-score, a ban, or a god-view *in any single output*. The Capa-4 engine is the cleanest case — it resolves *one campaign* and forgets (cross-output correlation, if outputs are stored, is a governance/storage concern the pure function cannot foreclose).

## Human-involvement model
Agent proposes, human disposes. Hard human gates: any judgment of a person, sanction/exclusion (invariant 3 — hard and bounded), governance (invariant 7, one-person-one-voice). Nothing stochastic decides about a person; nothing produces a persistent dossier. Exit is always available (invariant 10).
