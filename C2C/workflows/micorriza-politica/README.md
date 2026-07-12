# Workflow: Micorriza Política — social C2C/B2C/C2B protocol

> A Specsmith **workflow bundle**. The durable asset is the *habit* (task + context + interaction pattern + review step), not a prompt string (Axiom 8).

## The task
Turn the social design synthesis in `micorriza-politica-brief-social.md` into a buildable, verifiable system that scaffolds cooperation **without ever becoming a surveillance score** — the systematic inversion of the Chinese social-credit apparatus. The brief is explicit that the B2B clearing engine **does not transfer**; what transfers is governance, contextual reputation, and matching. This bundle specs the whole multi-species system and fully specifies + builds the **Capa-4 assurance-contract / quorum engine** first (the cleanest non-surveillance primitive, §7 Etapa-1 sequencing).

## How to run it
1. Load `context.md` (domain, negative anchor, terminology).
2. Read `spec.md` + `constraints.md` for the component being built.
3. Build against the bundle, with review one tier above the executor.
4. Review every output against `evals/acceptance.md`; re-run `evals/golden-set/` on any change.

## The interaction pattern (what transfers)
The non-negotiable correction you keep making: **"this must not become a score."** The moment a design drifts toward a per-person rating, a blacklist, a central trust-ledger, reputation-weighted voice, cross-campaign persistence, or engagement optimization — stop and redesign. Those are the §1/§2 category errors. The second correction: **gardener, not engineer** — the goal is fertility, not efficiency; tracking reciprocity in a gift room *kills* it (Gneezy/Titmuss).

## The review gate
Claude reviews free-model output against the six acceptance criteria. The two things most likely to be wrong: (1) the **anti-surveillance shape** — a stray score/reputation/persistence field, or accepting a forbidden input (AC5); (2) **no-loss / bonus conservation** broken by float or a bad remainder split (AC2/AC3).

## Build status
- [x] upstream spec bundle (architecture, intent, context, spec, constraints, evals, red-team, audit)
- [x] **Capa-4 assurance-contract engine** — `src/assurance/assurance_engine.py`. Drafted by a free model (orchestrated), reviewed + corrected by Claude. Tests in `tests/`.
- [ ] Relational-mode partition ("las habitaciones," Capa 1) as a type-system/firewall — §7 Etapa 1
- [ ] Trust-legibility query (Capa 2) and LLM matcher (Capa 3) — §7 Etapa 2–3, last and with maximum care

## What's in this bundle
| File | What it is |
|------|------------|
| context.md | reusable context layer (Axiom 5) |
| architecture.md | Agent Species classification (multi-species, human-dominant) |
| spec.md | self-contained spec of the assurance engine + meaning layer |
| constraints.md | MUST / MUST-NOT / PREFERENCE / ESCALATION + species-mode matrix |
| evals/ | acceptance criteria, A/B/C tests, golden set |
| failure-model.md | predicted failures + stress findings + mitigations |
| audit.md | proof every finding became an enforceable requirement |
| .specsmith.json | provenance |
