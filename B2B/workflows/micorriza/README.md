# Workflow: Micorriza — B2B mutual-credit clearing system

> A Specsmith **workflow bundle**. The durable asset is the *habit* (task + context + interaction pattern + review step), not a prompt string (Axiom 8).

## The task
Turn the design synthesis in `micorriza-brief-diseno.md` into a buildable, verifiable system: a federated B2B mutual-credit network whose deterministic core (multilateral clearing) nets circular debt exactly, whose stochastic layer (matching) only *proposes*, and whose relational/governance layer stays human. This bundle specs the whole system and fully specifies + builds the **Layer-1 deterministic clearing solver** first (lowest risk, §10 sequencing).

## How to run it
1. Load `context.md` (domain, terminology, constraints).
2. Read `spec.md` + `constraints.md` for the component being built.
3. Build against the bundle, with review one tier above the executor.
4. Review every output against `evals/acceptance.md`; re-run `evals/golden-set/` on any change.

## The interaction pattern (what transfers)
The non-negotiable correction you keep making: **"no LLM on the value path; the solver proposes, a human disposes."** Push back the moment a design drifts toward a token, permissionless membership, "1 token = 1 vote," or an LLM deciding credit. Those are the §2 red-flag stop conditions — stop and redesign.

## The review gate
Claude reviews free-model output against the six acceptance criteria. The two things most likely to be wrong: (1) **conservation** broken by rounding or net-position drift; (2) **non-determinism** from dict/set ordering. Both are caught by AC1 and AC4.

## Build status
- [x] upstream spec bundle (architecture, intent, context, spec, constraints, evals)
- [x] **Layer-1 clearing solver** — `src/clearing/clearing_solver.py`. Drafted by Mistral devstral-small (orchestrated), reviewed + corrected by Claude; validation hardening + `render_report` added in a second orchestrated pass. **64/64 tests pass** (`tests/`: 1200 random property examples, golden-set regression wired into pytest, independent networkx oracle).
- [x] **Mutual-credit ledger + credit-line accounting** (EUR, no chain — §10 step 1) — `src/ledger/mutual_credit_ledger.py`. Spec'd first (`spec-ledger.md`, `evals/{acceptance,tests}-ledger.md`), drafted by agy-gemini-3-flash + Mistral (orchestrated), reviewed + corrected by Claude. **128/128 tests pass** incl. ledger↔solver integration, proposal-forgery battery, and golden flow pin (`evals/golden-set/ledger_flow.json`).
- [ ] Matcher (LLM, proposal-only) — past §10 thresholds
- [ ] On-chain audit ledger, federation protocol, fiat bridge, commons — later

## What's in this bundle
| File | What it is |
|------|------------|
| context.md | reusable context layer (Axiom 5) |
| intent.md | engineered intent: goal hierarchy, policy compliance, speed-vs-precision (engineer-intent) |
| architecture.md | Agent Species classification (multi-species) + human-involvement model |
| spec.md | self-contained spec of the clearing solver + meaning layer |
| spec-ledger.md | self-contained spec of the mutual-credit ledger (+ `evals/acceptance-ledger.md`, `evals/tests-ledger.md`) |
| constraints.md | MUST / MUST-NOT / PREFERENCE / ESCALATION + species-mode matrix |
| evals/ | acceptance criteria, A/B/C tests, golden set |
| failure-model.md | predicted failures + stress findings + mitigations |
| audit.md | proof every finding became an enforceable requirement |
| .specsmith.json | provenance |
| optimization-log.md, production-prompt.md, simulation.md, style-profile.md, tasks.md | placeholder stubs — outputs not yet generated for this bundle |
