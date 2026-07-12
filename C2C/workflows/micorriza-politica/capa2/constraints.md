# Constraint Architecture — Capa 2 Trust-Legibility Query

> Produced by author-constraints. Each rule carries a "because" clause (AGD-029).
> Sibling of the Capa-4 / Capa-1 `constraints.md`; the anti-surveillance rules are deliberately identical.

## MUSTs
- **M1** Require an `asker` and evaluate **from that position**; traverse the web of trust starting at the asker — *because* reputation here is relational, consulted-from-a-position, never absolute (principle 2, invariant 2). No asker ⇒ no answer.
- **M2** Scope every considered edge and fact to the query's `cell_id`; ignore out-of-cell items — *because* legibility is contextual, never a number that follows a person across cells (principle 1, invariant 4).
- **M3** Emit **only** vouch-paths, direct vouchers, specific facts, and a categorical relative verdict — **never a score/rank/reputation number or a moral judgement** — *because* the output must be structurally incapable of being a person-scalar (principle 3, invariant 2). This is the razor's edge (§6.1).
- **M4** Drop expired edges/facts (`expires_at <= now`, ISO-8601 string compare) **before** traversal — *because* forgetting is native and must be enforced here, not left to the caller; legibility that cannot forget is a dossier (principle 4, invariant 5).
- **M5** Represent **only positive `vouches` (whitelist) edges**; treat absence of a path as `no_info_from_your_position`, never a negative mark — *because* the system opens doors and structurally cannot easily close them; there is no distrust edge and no negative verdict (principle 5, invariant 3).
- **M6** Accept the graph as a **caller-supplied argument** and store nothing after returning — *because* there is no central holder of the trust graph, no throne to capture (principle 6, invariant 6).
- **M7** Bound traversal by `max_hops` from the asker — *because* visibility is local (Dunbar), never the whole component (invariant 4).
- **M8** Run the surveillance-shape scan over the **whole input (graph included), recursively**, using the exact Capa-1/Capa-4 `FORBIDDEN_KEY` taxonomy — *because* no global scalar of a person in any layer (invariants 2/6); one anti-surveillance definition, not three.
- **M9** Be byte-deterministic for identical input (sorted path/fact enumeration) — *because* an auditable proposal that is non-reproducible cannot be audited (mirrors Capa-4/Capa-1 M6).
- **M10** Refuse a wildcard/list/`null`/non-str `target` — *because* the API must not become "enumerate everyone and their standing," which is the god-view by another door (Anti-god-view, spec).

## MUST-NOTs
- **N1** No LLM / stochastic process on this path — *because* legibility must be a value-neutral graph query; stochastic creep invites the scoring/optimization drift the brief forbids (mirrors Capa-4/Capa-1 N1).
- **N2** No score/rating/ranking/reputation/aggregate number in the output — *because* no global scalar of the person (invariant 2). Not even a "trust %", not even a normalized voucher count as a rating.
- **N3** No god-view entrypoint: no function that answers about a target **without** an asker, and no function that ranks or lists multiple targets — *because* the absolute/global question must be **unrepresentable**, not merely discouraged (principle 2/6).
- **N4** No distrust/blacklist/negative edge and **no negative verdict** — *because* reputation opens doors, it cannot easily close them (invariant 3); you cannot lower anyone through this API (principle 5).
- **N5** No stored graph, no cross-call state, no cross-cell join key; tokens stay opaque — *because* no central holder (invariant 6), no permanent dossier (invariant 5).
- **N6** No **repair** of a surveillance-shaped or malformed input — refuse (raise), never strip-and-answer — *because* silently stripping a `reputation` field would answer over a corrupted, dossier-shaped input as if clean (mirrors Capa-1 N5).
- **N7** No broadcast beyond the cell; the query operates on one `cell_id` — *because* local-bounded visibility, never global (invariant 4).
- **N8** No silent failure: on any envelope-validation error or surveillance breach, **raise** and surface — never return a partial or "answered-with-warnings" verdict.
- **N9** No caching of a target's result independent of the asker — *because* position-relativity is the proof there is no god-view; an asker-independent cache **is** a god-view (principle 2).

## PREFERENCES
- **P1** Prefer stdlib-only core for auditability; `hypothesis` only in tests.
- **P2** Share the exact `FORBIDDEN_KEY` taxonomy with the Capa-4 engine and Capa-1 membrane (one anti-surveillance definition, not three).
- **P3** Prefer property-based tests: no forbidden key ever appears in a verdict; the same `(target, cell)` from two askers can diverge; expired items never affect the result.

## ESCALATION TRIGGERS (reject + surface)
- **E1** Input (any depth, graph included) contains a forbidden surveillance-shaped key → **refuse** — refuse to even accept the dossier shape (invariants 2/3/6).
- **E2** `target` is a wildcard/list/dict/`None`/empty, or `asker`/`cell_id`/`now` missing/empty → **refuse** — no enumeration and no god-view (M10/N3).
- **E3** Malformed envelope (`max_hops` not int>0, `graph`/`vouches`/`facts` wrong type, malformed edge/fact) → reject, do not repair.

## Reversibility framing
- The query itself is a **two-way door** (pure, no side effects) → fully autonomous.
- Acting on the verdict (deciding to transact / trust) is the **human's** step → the query only informs a position (AGD-018).

## Constraint × Execution-Mode matrix
| ID | Query (Live) | Simulation/Backtest | Notes |
|----|--------------|---------------------|-------|
| M1 asker-relative | Enforce | Enforce | no asker ⇒ no answer |
| M3 no scalar out | Enforce | Enforce | the razor's edge; never relax |
| M4 forgetting | Enforce (drop) | Enforce (drop) | expiry applied before traversal |
| M5 whitelist-only | Enforce | Enforce | no negative edge/verdict |
| M8 surveillance scan | Enforce (refuse) | Enforce (refuse) | never relax — the defining hazard |
| M10 no enumeration | Refuse | Refuse | single concrete target only |
| N9 no asker-blind cache | Enforce | Enforce | position-relativity is the proof |
