# Sim-C2C — acceptance criteria (numbered, per milestone)

Every commit after M0 is held against these ACs. Real pytest against the **actual** C2C code (never
mocked; the only stub allowed is the injected matcher `propose`).

## M0 — spec bundle
- **AC0.1** spec.md, evals/acceptance.md, failure-model.md exist; spec does not restate the engine or
  capa bundles.
- **AC0.2** the 9 archetypes each map to a concrete, real-module-accepted input.
- **AC0.3** Track A oracle-arrival (exception vs dropped_/damped_ counter) stated per oracle.

## M1 — C2CAdapter
- **AC1.1** loads all 6 real modules by file path; `pin.git_commit is None`.
- **AC1.2** each of `admit/query/match/resolve/sense/decide` is a bare 1:1 pass-through (no
  validation/adjudication of its own).
- **AC1.3** `assert_pinned()` fails if a source byte changes.
- **AC1.4** cross-checked against the real modules' own behaviour (raises propagate; `match` never
  raises on bad model output).

## M2 — world / proposals / actors
- **AC2.1** `C2CWorld` owns all accumulation; both clocks advance per `step()`.
- **AC2.2** all 9 archetypes produce only whitelisted-shape proposals; a real campaign runs
  byte-deterministically.
- **AC2.3** the injected `propose` is deterministic/cassette-backed; `make_claude_propose` is never
  called in a campaign.

## M3 — Track A
- **AC3.1** all 6 oracles implemented; `measure()` returns an `IntegrityReport`.
- **AC3.2** Track A imports no C2C module (AST check).
- **AC3.3** a hand-planted breach for each oracle is caught; a clean trace passes.

## M4 — Track B
- **AC4.1** every metric is a `Distribution`/aggregate scalar — no agent-indexed slot (type-enforced).
- **AC4.2** `assert_no_person_scalar` passes on the real output; every metric ships a `goodhart` flag.

## M5 — negative control (the gate)
- **AC5.1** N-01: T-A1 catches the silent `reachability` scalar; the real module never emits it.
- **AC5.2** N-02: T-A2 catches the silent market admit; the real membrane raises on the same input.
- **AC5.3** vacuity: a naive plant (forbidden substring) is self-caught by the real SUT scan.
- **AC5.4** broken copies live only under `negative_control/`; `C2C/` is byte-unchanged.

## M6 — researcher / campaign
- **AC6.1** `C2CResearcher.next` search space contains no Track-B-derived objective (descriptive-only
  seam implemented domain-side; flagged in the commit).
- **AC6.2** full end-to-end campaign over the real C2C stack: mixed cooperative+adversarial
  population, zero integrity violations on the clean SUT, byte-reproducible.
- **AC6.3** property + golden regression tests green; whole Sim suite (B2B + C2C) green.
