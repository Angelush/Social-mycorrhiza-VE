# Context — information environment

> Produced by build-context. Data room before the work (Axiom 5).

## Domain
The **social** branch of Micorriza ("micorriza política"): infrastructure for interpersonal cooperation, C2C/C2B commerce, and civic collaboration. Sibling of the B2B brief but made of **different material**: the interpersonal "nutrient" is mostly *non-fungible and non-denominated* — care, attention, trust, knowledge, time, belonging. The B2B clearing engine **does not transfer** (people have no graph of denominated debts to net). What transfers is governance, reputation (as contextual legibility), and matching.

## The negative anchor (design by inversion)
Where B2B used Sardex as a *positive* anchor, this system uses the **Chinese social-credit apparatus as a negative anchor** — every architecture decision inverts one of its choices (§3). Correction of the myth (China Law Translate / J. Daum): it is **not** a single national Black-Mirror score; it is mainly an administrative compliance tool (business-credit registry + court-judgment enforcement + regulatory lists). But the coercive part is real and architectural: blacklists (esp. *laolai* defaulters) restrict travel/finance/market access. The invariants invert exactly these teeth.

## Terminology (stable)
- **Cell / círculo (Capa 0):** a local, Dunbar-bounded (~150) trust context — a neighborhood, guild, mutual-aid association, ROSCA. The atom. Reputation means something here *because* it is contextual and face-to-face.
- **Las habitaciones (Capa 1):** explicitly separated "rooms" running different logics (Fiske's relational models): **communal gift** (no score, no denomination, no reciprocity tracking), **equality matching** (turns, time-banks, ROSCAs — symmetric, balanced, *not* priced), **market pricing** (real C2C/C2B trade — denomination appropriate). The cardinal rule (kula/gimwali wall): market logic NEVER leaks into the gift/equality rooms.
- **Assurance contract (Capa 4):** "I do it if N others do." A **dominant** assurance contract (Tabarrok) pays a sponsor's bonus to committers *if the threshold is NOT met* — removing the risk of committing in vain, which solves the cold-start of public goods.
- **Threshold / quórum:** the minimum number of distinct committers for the action to fire. Biomimetic anchor: bacterial quorum sensing (Vibrio fischeri lights up only past a density threshold).
- **Trust-legibility (Capa 2):** contextual, relational, specific, forgetting-by-default, positive-sum (opens doors), no central holder. The razor's edge vs. social credit. **Built last.**

## Anchor data / proven vs. speculative (Apéndice)
- **PROVEN historically:** ROSCAs (global, millennial); social capital → institutions (Putnam); Quaker/sociocratic consent (centuries); gift/market separation (kula/gimwali, replicated by Gneezy, Titmuss, Tetlock); federation-in-difference (Haudenosaunee).
- **MODEL/HEURISTIC only:** all biomimetic models (immune tolerance, boids, quorum, stigmergy) — design lenses, not validated systems at scale.
- **SPECULATIVE / frontier:** trust-legibility-without-surveillance (the razor's edge), global federation of trust-worlds, LLM prosocial matching, the full protocol.
- **REFUTED as mechanism:** astrology as prediction (Carlson 1985) — admitted ONLY as one optional shared-symbol layer (Capa 7), never as a predictor (that would be fraud).

## Hard constraints from environment (stable)
- **Scale is fatal to density.** Both ROSCAs and Sardex fail to scale for the same reason: the social collateral *is* the dense local network and dilutes when stretched. → Local-bounded by design (invariant 4); global work is *translation between local worlds*, never one planetary graph (§2.4).
- **Social capital accumulates slowly, is destroyed fast** (Putnam). Not injectable by decree or app — only cultivated. → No growth-hacking; fertility, not throughput.
- **Irreversibility of monetization** (Gneezy daycare: removing the fine did not restore the moral contract). → The membrane (invariant 1) is non-negotiable.

## Tools / stack (proposed, stable for this iteration)
- Language: **Python 3.11+** for the engine (clear, testable, exact integer-cent arithmetic). No floats for money.
- Tests: `pytest`; property-based via `hypothesis` for the conservation/no-loss invariants.
- No external services, no LLM, no chain, no database of persons in this component. The engine is a pure function over a single campaign.

## Examples of good/bad
- **Good:** engine takes one campaign's pledges, returns "fires" or "refunds + exact bonus split," carries an expiry, and contains **nothing** that could rank or identify a person across campaigns.
- **Bad:** engine returns a "reliability score" for each committer, keeps a list of who failed to follow through, or sums commitment across campaigns into a profile. **Inadmissible** — that is the social-credit shape (invariants 2, 3, 5, 6).

## Honesty flags (heuristics)
- The biomimetic names (quorum, mycorrhiza, immune tolerance) are **design heuristics, not proofs** (Apéndice). The "wood-wide-web" is scientifically disputed; use as metaphor only.
- The deepest risk is **not technical** (§6.1): a benign protocol with a malign governor is the nightmare. Architecture removes the throne (invariant 6) and keeps exit open (invariant 10) — the closest design can get to a guarantee, but it cannot guarantee its own use.
