# Intent — the real objective + correctness contract

> Produced by engineer-intent.

## The real objective (frame audit, CAR-002)
Stated task: "turn the social brief into code." The frame underneath (§0): build **infrastructure for a literate society to organize across its differences** — where the goal is *fertility* (conditions under which trust and cooperation reproduce themselves), **not efficiency**. The wrong-frame version to reject, hard: "Sardex for people" / a favor-bank with points / a reputation score. The brief calls this the original category error (§2.1→§2.2): treating the social as a market to optimize **destroys what it means to protect**, often irreversibly (Gneezy–Rustichini daycare; Titmuss). The metaphor is mandatory: **gardener, not engineer** (wu wei) — prepare the soil and step back.

## Mini-Me check (AGD-014)
Do not encode "a community organizer, but faster and tracking everyone." Build a purpose-built track: automate only the *combinatorial, value-neutral plumbing* (does a collective action reach its threshold? distribute a sponsor's refund-bonus exactly). Leave judgment, trust, sanction, and meaning **human**. The challenge: scaffold coordination **without building the seat from which people are watched** (invariant 6 — no central holder, no throne to capture).

## Scope of THIS build (sequencing per §7 — the inversion of China)
China builds the score first, services after. We do the opposite: **build first what CANNOT become a surveillance score; add legibility last.** So:
1. **Capa 4 — assurance-contract / quorum engine** (this iteration). The cleanest non-surveillance primitive: it resolves one collective-action campaign and forgets. No reputation, no cross-context identity, no ranking.
2. Then the relational-mode partition ("las habitaciones," Capa 1) as a type-system/firewall, and local mutual-aid tooling — still **no score** (§7 Etapa 1).
3. Trust-legibility (Capa 2) and the LLM matcher (Capa 3) come **last and with maximum care** (§7 Etapa 2–3), only after fertility is demonstrated.

Out of scope now, permanently antipatterns: a global person-scalar, any blacklist, a central trust-graph holder, reputation-weighted voice, engagement optimization, an imposed single symbol layer, mandatory/no-exit participation. (§1 invariants; §2 category errors.)

## Correctness contract (AGD-031) — for the assurance-contract engine
- **Truthfulness:** The campaign's pledges are the single source of truth. Threshold resolution is deterministic; one correct answer exists.
- **No-loss guarantee:** If the threshold is not met, **every committer is made whole** (full refund) — the entire point of an assurance contract (Tabarrok). For the *dominant* variant, committers also receive the sponsor's bonus. Nobody is ever worse off for having committed.
- **Conservation:** The sponsor bonus is distributed exactly (sum of allocations == bonus; integer cents; deterministic remainder). No value created or lost.
- **Shape (the C2C-defining clause):** Output must contain **no per-person score, no cross-campaign aggregate, no ranking, no blacklist, no god-view.** Participants are opaque per-campaign tokens. *Within a single resolution* the artifact is *structurally incapable* of becoming surveillance (invariants 2, 3, 6); across campaigns that property is a caller/storage convention (per-campaign token rotation, `expires_at`), which a pure function cannot enforce.
- **Policy compliance:** Enabling only — it can *fire* an action (whitelist, invariant 3); it has no mechanism to exclude or penalize a person. Operates within one cell/campaign (local-bounded, invariant 4).
- **Speed-vs-precision:** **Exact, always.** Money (refunds, bonus) uses integer cents; no float.
- **Auditability + forgetting:** The resolution is reconstructable from the campaign input, AND the output is ephemeral (carries an expiry; no permanent dossier — invariant 5). Auditability without a permanent record is the needle to thread.

## Flashlight beam (scope edges)
- **Bright center:** count distinct committers (dedup by opaque token — one *token*, one weight; person-binding/Sybil is out of scope, §6.2 — invariant 7); decide fire vs. refund against the threshold; on refund, allocate the sponsor bonus exactly and deterministically.
- **Edges (NOT this):** no reputation, no scoring of who pledged, no carrying state across campaigns, no exclusion mechanism, no LLM, no broadcast beyond the cell, no irreversible commit inside the engine (it proposes a resolution).
