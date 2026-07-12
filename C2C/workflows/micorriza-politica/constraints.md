# Constraint Architecture

> Produced by author-constraints. Each rule carries a "because" clause (AGD-029).

## MUSTs
- **M1** Use integer cents for all monetary values — *because* float arithmetic introduces rounding drift and the no-loss guarantee must be exact (a refund short by a cent breaks the contract).
- **M2** Guarantee no-loss: when `status == refunds`, every committer's `refund_cents` equals the full sum they pledged — *because* nobody may be worse off for committing; that is the entire assurance-contract mechanism (Tabarrok, §4 Capa 4).
- **M3** Distribute the sponsor bonus exactly: `sum(bonus_cents) == sponsor_bonus_cents`, remainder allocated deterministically by ascending `participant_token` — *because* conservation and auditability (invariant 5/§4).
- **M4** Dedup committers by `participant_token` (one *token* → one weight; token↔person binding / Sybil resistance is out of scope, §6.2) — *because* voice/standing is independent of how many times you pledge; this is the seed of invariant 7 (one person, one voice).
- **M5** Be byte-deterministic for identical input (sort tokens/ids before traversal) — *because* the resolution is an auditable proposal; non-reproducible output cannot be audited.
- **M6** Return a proposal only; perform no commit/side-effect/persistence — *because* the agent proposes, the human/protocol disposes; firing an action is a one-way door.
- **M7** Carry `expires_at` through to the output — *because* forgetting is native, not a patch (invariant 5); the resolution must not become a permanent record.

## MUST-NOTs
- **N1** No LLM / stochastic process anywhere on this path — *because* this is value-neutral threshold plumbing; stochastic creep here invites the optimization/score drift the brief forbids.
- **N2** No per-person score, rating, ranking, or reputation in the output — *because* there is no global scalar of a person (invariant 2); this is the inversion of the social-credit DNI.
- **N3** No blacklist / ban / penalty / exclusion mechanism — *because* reputation opens doors, it cannot easily close them; whitelist-not-blacklist (invariant 3).
- **N4** No cross-campaign state, no persistent dossier, no cross-context join key; `participant_token` stays opaque and per-campaign — *because* no central holder of the trust graph (invariant 6) and no permanent dossier (invariant 5) — the decisive firewall.
- **N5** No market instrument inside a `binary`/equality campaign — neither per-pledge prices **nor a `sponsor_bonus_cents > 0`** — *because* market logic must never leak into the gift/equality room (kula/gimwali membrane, invariant 1); monetization is often irreversible (Gneezy). The bonus ban is also anti-Sybil: with no stake, a binary failure-bonus is a zero-cost faucet (§6.2).
- **N6** No broadcast beyond the cell; the engine operates on one `cell_id` — *because* local-bounded visibility, never global (invariant 4).
- **N7** No silent failure: on any invariant/validation violation, reject or abort and surface — never emit a resolution that fails no-loss or conservation. Input errors raise `ValueError`; internal no-loss/conservation violations raise `AssuranceInvariantError` (a distinct type, so a caller catching input errors cannot swallow an engine-is-broken signal).

## PREFERENCES
- **P1** Prefer stdlib-only core for auditability; `hypothesis` only in tests.
- **P2** Prefer a human-readable Markdown resolution summary alongside JSON.
- **P3** Prefer property-based tests for no-loss, conservation, and the M-shape (no forbidden field can ever appear).

## ESCALATION TRIGGERS (reject + surface)
- **E1** Input contains a forbidden field (`score`, `rating`, `reputation`, `blacklist`, `ban`, `penalty`, `global_id`, `dni`, or similar) at any nesting depth (recursive scan) → **reject** — refuse to even accept the surveillance shape (invariants 2, 3).
- **E2** Malformed input (empty ids, `threshold <= 0`, duplicate `pledge_id`, non-int/negative amount, monetary pledge missing amount, binary pledge carrying a price) → reject, do not repair.
- **E3** Conservation or no-loss assert fails → abort run (raise `AssuranceInvariantError`), emit diagnostic, never output a resolution.

## Reversibility framing
- The engine itself is a **two-way door** (pure computation, no side effects) → fully autonomous.
- The downstream *fire-action / move-refunds* step is a **one-way door** → draft + escalate, human/protocol ratifies (AGD-018).

## Constraint × Execution-Mode matrix
| ID | Engine (Live) | Simulation/Backtest | Notes |
|----|---------------|---------------------|-------|
| M1 exact cents | Enforce | Enforce | always |
| M2 no-loss | Enforce (abort) | Enforce (abort) | hard |
| M3 bonus conservation | Enforce (abort) | Enforce (abort) | hard |
| M5 determinism | Enforce | Enforce | |
| M6 proposal-only | Enforce | Skip (sim may apply to a copy) | sim mutates a sandbox |
| N2/N3/N4 anti-surveillance shape | Enforce (reject) | Enforce (reject) | never relax — the defining hazard |
| E1 forbidden field | Reject | Reject | never measure-only |
