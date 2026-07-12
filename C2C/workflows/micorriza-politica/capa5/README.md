# Capa 5 — Stigmergic Coordination + Anti-Cascade Circuit Breakers

SpecSmith sub-bundle for the `[PROTOCOLO + CIRCUIT BREAKERS]` layer (brief §4 Capa 5, invariant 9,
architecture.md: *Not an agent. Friction/rate-limits on propagation*). It **senses** the
environmental traces visible from **one cell** — contribution histories, paths, artifacts, signals —
applies **pheromone evaporation** (forgetting), and enforces the **anti-cascade circuit breakers** so
the same mechanism that coordinates cannot also produce the "ant mill" (death spiral), the cascade, or
the mob. It emits **no score, no rank, no reputation, no ban, no god-view**.

**DETERMINISTIC, NOT an LLM.** No stochastic core, no injected model, no network client — that is the
whole difference from Capa 3. Shares the system-wide `../intent.md`, `../context.md`, and
`../architecture.md` with the Capa-4/1/2/3 builds. Capa-5-specific docs live here:

```
spec.md            # the buildable blueprint (four structural walls, evaporation, the breakers, algorithm)
constraints.md     # MUST/MUST-NOT with because-clauses
evals/acceptance.md  evals/tests.md   # AC1–AC13 + AC-X, machine-checkable, deterministic (no stub)
failure-model.md   # red-team: F1–F11, ST1–ST8, open (governance) problems
```

## The whole design problem — the coordinator IS the stampede engine
Stigmergy coordinates via **traces left in the environment** (like FOSS, Wikipedia, Hayek's prices).
The obligatory dark side (brief §5, §6): the *same* mechanism produces the **molino de hormigas** —
the death spiral, the information cascade, the mob. The circuit breakers must be **structural, not a
policy line** — the same move that made the surveillance shape *unrepresentable* in Capa 1, applied to
the cascade shape here. On a mob/cascade input, "correct" = **throttling the stampede**.

## The four structural walls (each an analogue of a sibling-layer wall)
1. **Traces are environmental, never a person-scalar** — `about` is an artifact/path/contribution
   token; the Capa-1/2/3/4 `FORBIDDEN_KEY` scan refuses a `score`/`rank`/`reputation`/`blacklist`
   trace; the `signal` is whitelisted to positive/environmental kinds so **no ban/distrust signal is
   representable** (invariants 2/3, positive-sum).
2. **Forgetting is load-bearing — pheromone evaporation** — `effective = strength·0.5^(elapsed/
   half_life)`; a faded trace is dropped before sensing. Evaporation is the *mechanism*, not a stamp
   (invariant 5).
3. **Anti-cascade breakers (invariant 9), each structural** — (a/c) a **velocity cap** throttles a
   burst per artifact per window (friction/velocity-limit); (b) a `flag` with **no context** is damped
   (context before judgment); (d) an off-cell trace is dropped (**zero global broadcast**, invariant 4).
4. **Cell-scoped, caller-supplied, scanned-and-discarded** — pure over supplied local state; nothing
   persisted; no central holder; byte-deterministic (invariants 4/6).

## Senses, never acts
The output **surfaces** the throttled, evaporated environment; it connects nothing, notifies no one,
ranks no person, persists nothing. Humans in the cell act on what they sense (architecture.md: not an
agent).

## The defining test is AC4 (the mob throttle)
Because Capa 5 is deterministic, the suite needs no stub — it feeds real cascade/mob inputs. **AC4**: a
burst of `n > velocity_cap` traces about the **same** artifact, all in-window, is throttled to exactly
`velocity_cap` sensed (the earliest kept), the rest damped — the stampede made hard by construction.
**AC3/AC5**: a `ban` signal or a `score`/`blacklist` trace is refused in every cell. **AC10**: a mixed
cascade input (off-cell + future + bare-flag + over-cap + evaporated) is damped-and-counted and never
crashes; only the envelope raises.

## Time model
Integer **logical ticks** for `now`/`created_at` (not ISO strings) — evaporation needs elapsed-time
arithmetic (`now − created_at`). This keeps the module pure, stdlib-only, and byte-deterministic with
no `datetime`. Capa 6, needing no arithmetic, keeps the family's ISO-string convention.

## Relationship to Capa 1, 2, 3, and 4
Reuses the **exact** `FORBIDDEN_KEY` taxonomy of all four siblings (one anti-surveillance definition,
not five). AC-X regression-checks that a surveillance-shaped payload fed as a Capa-5 trace is refused
identically — the five layers cannot disagree.

## Flagged, NOT fake-resolved (brief §6)
- **The ant-mill/cascade is the obligatory dark side of stigmergy (§6, invariant 9):** the breaker
  makes a stampede **hard, not impossible**. A determined coordinated mob acting *outside* the function
  — across many cells/ticks, each within-cap — still can; **who governs decides** (mirror Capa-2/1/3
  ST5).
- **The breaker parameters (`half_life`/`velocity_cap`/`window`/`min_strength`) are a governance
  choice:** the function enforces them deterministically; it does not choose them.
- **Sybil / token-binding (§6.2):** `about`/`cell_id` tokens are opaque, trusted as given.

## Implementation
`src/stigmergy/stigmergy.py` — pure, stdlib-only, deterministic; **no LLM, no network, no persistence**.
Tests: `tests/test_stigmergy.py` (AC1–AC13, AC-X) + `tests/test_stigmergy_properties.py` (P1–P7), with
an independent hand-written oracle and adversarial cascade/mob inputs — deterministic and offline.
</content>
