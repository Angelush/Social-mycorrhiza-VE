# Capa 6 — Sociocratic Governance (consent, not consensus)

SpecSmith sub-bundle for the `[HUMANO → CONSENT-NOT-CONSENSUS]` layer (brief §4 Capa 6, invariant 7,
architecture.md: *Not an agent. Consent-not-consensus; voice independent of reputation*). It resolves
**one proposal in one local circle** by **consent — the absence of a paramount (reasoned) objection —
not by consensus, and not by majority** (lineage: Haudenosaunee Great Law of Peace, Quaker meeting,
sociocracy). It emits **no weight, no tally, no majority, no score, no mark of the objector, no
god-view**.

**DETERMINISTIC, NOT an LLM.** No stochastic core, no injected model, no network client — that is the
whole difference from Capa 3. Shares the system-wide `../intent.md`, `../context.md`, and
`../architecture.md` with the Capa-4/1/2/3/5 builds. Capa-6-specific docs live here:

```
spec.md            # the buildable blueprint (five structural walls, consent resolution, algorithm)
constraints.md     # MUST/MUST-NOT with because-clauses
evals/acceptance.md  evals/tests.md   # AC1–AC12 + AC-X, machine-checkable, deterministic (no stub)
failure-model.md   # red-team: F1–F11, ST1–ST7, open (governance) problems
```

## The whole design problem — voice independent of reputation
If reputation weights the voice, then **reputation → power → discipline**, and you have rebuilt social
credit through the governance door (invariant 7, §6.3). The move is the Capa-6 analogue of Capa-2's
unrepresentable god-view: **one person, one voice**, and the weighting **cannot even be phrased** — no
`weight`/`shares`/`voting_power`/`tally` field exists, disposition keys are whitelisted, and a
high-"reputation" member gets exactly the same single voice.

## The five structural walls (each an analogue of a sibling-layer wall)
1. **Voice independent of reputation** — one token, one voice (deduped; a duplicate token is refused);
   a `VOTE_WEIGHT_KEY` taxonomy **and** the shared `FORBIDDEN_KEY` taxonomy refuse any weighted /
   reputation-bearing input (invariant 7, the defining move).
2. **Consent, not consensus, not majority** — `adopted` iff **no paramount objection**, else `revisit`;
   the verdict is **categorical**, never a percentage or tally; one reasoned block is decisive.
3. **An objection is a whitelist-shaped pause** — it surfaces the **reason** and opens revision; it
   **never marks the objector** (invariant 3). The output carries reasons, never objector tokens.
4. **Circles are local and do not auto-propagate** — the decision is scoped to `circle_id`; off-circle
   dispositions are dropped; there is no escalation to a parent/global authority (invariants 4/6).
5. **Forgetting** — per-round `expires_at`; expired dispositions dropped; **no dossier of who objected**
   (invariant 5).

## Enforces the procedure, not good faith
`decide()` enforces the **procedure** of consent. It cannot manufacture the will to cooperate (a
low-trust circle may not bootstrap), and consent is capturable by a bad-faith blocker (tyranny of the
minority). **The code enforces the procedure, not good faith** — who participates and why decides
(§6.3, flagged, not coded).

## The defining test is AC1 (voice independent of reputation)
Because Capa 6 is deterministic, the suite needs no stub. **AC1**: the same proposal in the same circle
yields the **same verdict regardless of any reputation the members carry** — a weighted / reputation-
bearing input is **refused**, and one-token-one-voice holds. **AC4**: a single paramount objection
sends the round to `revisit` however many consent — consent, not majority. **AC5**: an objection
surfaces its reason and **never marks the objector**.

## Time model
ISO-8601 string convention (as Capa 1/2/3), compared lexicographically — Capa 6 needs no elapsed-time
arithmetic. (Capa 5, which needs evaporation, is the one layer using integer ticks.)

## Relationship to Capa 1, 2, 3, 4, and 5
Reuses the **exact** `FORBIDDEN_KEY` taxonomy of all five siblings (one anti-surveillance definition,
not six). AC-X regression-checks that a surveillance-shaped payload fed as a Capa-6 disposition is
refused identically — the six layers cannot disagree. Adds one gate the others do not need: the
`VOTE_WEIGHT_KEY` taxonomy — the Capa-6-specific anti-plutocracy firewall (invariant 7), the analogue
of Capa-3's `ENGAGEMENT_KEY` and Capa-5's signal whitelist.

## Flagged, NOT fake-resolved (brief §6.3)
- **You cannot manufacture the will to cooperate (§6.3):** a low-trust circle may not bootstrap consent;
  the protocol scaffolds the procedure, not the good faith.
- **Consent is capturable by a bad-faith blocker (tyranny of the minority):** the function enforces the
  procedure (an objection carries a reason and opens revision); whether it is in good faith is a human
  judgement the pure function cannot make.
- **Sybil / token-binding (§6.2):** one *token*, one voice ≠ one *person*, one voice; tokens are opaque,
  trusted as given.

## Implementation
`src/governance/governance.py` — pure, stdlib-only, deterministic; **no LLM, no network, no
persistence**. Tests: `tests/test_governance.py` (AC1–AC12, AC-X) + `tests/test_governance_properties.py`
(P1–P7), with an independent hand-written oracle and adversarial weighted-voice / bad-faith-blocker
inputs — deterministic and offline.
</content>
