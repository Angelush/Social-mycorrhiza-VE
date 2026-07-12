# Constraint Architecture — Capa 1 Relational-Mode Partition

> Produced by author-constraints. Each rule carries a "because" clause (AGD-029).
> Sibling of the Capa-4 `constraints.md`; the anti-surveillance rules are deliberately the same.

## MUSTs
- **M1** Enforce the membrane by *shape*, recursively at any nesting depth of `payload` — *because* a market instrument hidden one level down is still a leak; the wall is architectural, not a top-level courtesy (invariant 1).
- **M2** Refuse (raise `MembraneBreachError`), never repair/strip — *because* monetizing a communal relationship is often *irreversible* (Gneezy–Rustichini); silently stripping a price would admit a corrupted interaction as if clean.
- **M3** Make the membrane **directional**: bar market instruments in `communal_gift`/`equality_matching` only; the market room accepts gift-shaped content freely — *because* the kula/gimwali wall forbids market→gift, not the reverse.
- **M4** Ban the reciprocity **ledger** (denominated debt) in `communal_gift`, but allow balanced-in-kind reciprocity in `equality_matching` — *because* tracking reciprocity kills the gift (§4 Capa 1), while balanced exchange *is* the equality room's logic.
- **M5** Run the surveillance-shape scan in **every** room, recursively — *because* there is no global scalar of a person in any relational mode (invariants 2/6); this is the inversion of the social-credit DNI.
- **M6** Be byte-deterministic for identical input — *because* the admission verdict is an auditable proposal; a non-reproducible gate cannot be audited (mirrors Capa-4 M5).
- **M7** Return a verdict only; perform no commit/side-effect/persistence; carry `expires_at` through — *because* the firewall proposes, the caller disposes (two-way door), and forgetting is native (invariant 5).
- **M8** Emit no per-person field and echo no payload content in the verdict — *because* the output must be structurally incapable of becoming a dossier or a score (invariants 2/3/6).

## MUST-NOTs
- **N1** No LLM / stochastic process on this path — *because* room classification is value-neutral typing; stochastic creep invites the score/optimization drift the brief forbids (mirrors Capa-4 N1).
- **N2** No per-person score/rating/ranking/reputation in the verdict — *because* no global scalar of a person (invariant 2).
- **N3** No blacklist/ban/penalty and **no stored "refused" verdict about a person** — *because* reputation opens doors, it cannot easily close them (invariant 3); a refusal gates an interaction's shape, never a person, and a persisted refusal record would be a dossier (F4).
- **N4** No cross-context state, no persistent record, no cross-context join key; `participants` stay opaque tokens — *because* no central holder of the trust graph (invariant 6), no permanent dossier (invariant 5).
- **N5** No **stripping/normalizing** a market field out of a gift/equality interaction to "fix" it — *because* that would admit a corrupted interaction silently; the only correct responses are admit-as-is or refuse (see M2).
- **N6** No broadcast beyond the cell; the firewall operates on one `cell_id` — *because* local-bounded visibility, never global (invariant 4).
- **N7** No silent failure: on any envelope-validation error or membrane/surveillance breach, **raise** and surface — never return a partial or "admitted-with-warnings" verdict.

## PREFERENCES
- **P1** Prefer stdlib-only core for auditability; `hypothesis` only in tests.
- **P2** Share the exact `FORBIDDEN_KEY` taxonomy with the Capa-4 engine (one anti-surveillance definition, not two).
- **P3** Prefer property-based tests: no market key can ever survive admission into a non-market room; no forbidden key can ever appear in a verdict.

## ESCALATION TRIGGERS (reject + surface)
- **E1** Interaction (any depth) contains a forbidden surveillance-shaped key → **refuse** — refuse to even accept the dossier shape (invariants 2/3).
- **E2** `communal_gift`/`equality_matching` interaction whose `payload` carries a market instrument (price/cost/fee/currency/`*_cents`/valuation), or a `communal_gift` carrying a reciprocity ledger → **refuse** (kula/gimwali wall, invariant 1).
- **E3** Malformed envelope (unknown `mode`, empty ids, non-list participants, non-dict payload) → reject, do not repair.

## Reversibility framing
- The firewall itself is a **two-way door** (pure classification, no side effects) → fully autonomous.
- Acting on the verdict (routing or dropping the interaction) is the **caller's** step → the firewall only proposes (AGD-018).

## Constraint × Execution-Mode matrix
| ID | Firewall (Live) | Simulation/Backtest | Notes |
|----|-----------------|---------------------|-------|
| M1 recursive membrane | Enforce (refuse) | Enforce (refuse) | always |
| M2 refuse-not-repair | Enforce | Enforce | hard; never strip |
| M3 directionality | Enforce | Enforce | market room stays permissive |
| M5 surveillance scan | Enforce (refuse) | Enforce (refuse) | never relax — the defining hazard |
| M6 determinism | Enforce | Enforce | |
| N3 no stored refusal | Enforce | Enforce | a refusal is not a person-record |
| E1 forbidden field | Refuse | Refuse | never measure-only |
