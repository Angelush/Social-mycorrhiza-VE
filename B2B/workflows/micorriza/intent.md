# Intent — the real objective + correctness contract

> Produced by engineer-intent.

## The real objective (frame audit, CAR-002)
The stated task is "turn the brief into code." The frame underneath (§0 tesis rectora): **build the coordination-and-distribution institution for an era of cheap creation** — NOT "a more powerful AI" and NOT "a blockchain." The wrong-frame version to reject: a crypto token economy / DAO that "decentralizes" everything. The proven value (Sardex/WIR) is **multilateral clearing + mutual credit + relational trust + active management**, not decentralization.

## Mini-Me check (AGD-014)
Do not encode "how a human broker works, but faster." Build a purpose-built track: the deterministic *clearing/matching/scoring* combinatorics get automated; the relational layer (trust, membership veto, sanction judgment) stays human. The engineering challenge (anchor quote, Littera): automate the combinatorial layer **without destroying the relational layer**.

## Scope of THIS build (sequencing per §10)
We start at the lowest-risk, highest-certainty technical core:
1. **Layer 1 — deterministic clearing solver** (this iteration's deliverable).
2. Then mutual-credit ledger + credit-line accounting (denominated in EUR, no token, no blockchain — §10 step 1).
3. Matcher (Layer 2) and on-chain audit ledger come later, only past the §10 thresholds.

Out of scope now: token of any kind, permissionless membership, on-chain settlement of value, global governance authority. (Antipatterns per §2 / red-flag stop conditions.)

## Correctness contract (AGD-031) — for the clearing solver
- **Truthfulness:** The obligations graph is the single source of truth. Output must be a *mathematically exact* netting; one correct answer exists.
- **Completeness:** Every obligation conserved — net position of each member before == after clearing. No value created or destroyed.
- **Tone/Register:** N/A. Output is structured data + a human-readable settlement report.
- **Policy compliance:** Must respect per-member credit-line bounds (invariant 4). Must not move value across cell boundaries except via explicit bilateral net settlement (invariant 6).
- **Speed-vs-precision:** **Exact, always.** A 0.1% error is inadmissible when output moves money (invariant 1).
- **Auditability:** Every netting decision reconstructable from the input graph; emit a verifiable trace. The solver **proposes** a settlement; commitment is a separate, gated step (invariant 2).

## Flashlight beam (scope edges)
- **Bright center:** detect cycles in the directed obligations graph (A→B→C→A), net the minimum of each cycle, minimize remaining gross debt.
- **Edges (NOT this):** no credit *decisions* (scoring + human), no cross-cell value transfer without bilateral settlement, no LLM anywhere in this path, no irreversible commit inside the solver.
