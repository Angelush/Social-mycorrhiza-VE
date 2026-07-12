# Micorriza Política — social C2C / B2C / C2B protocol

Implementation of the social design synthesis in
[`micorriza-politica-brief-social.md`](micorriza-politica-brief-social.md),
built with a spec-driven engineering method (an intent/context/architecture/spec/constraints/failure-model/evals bundle).
Sibling of the B2B variant (`../B2B`).

> **North star (brief §0):** infrastructure for a literate society to organize
> *across its differences*. The goal is **fertility** (conditions under which
> trust and cooperation reproduce themselves), NOT efficiency. You are a
> **gardener**, not an engineer — prepare the soil and step back (wu wei).
>
> **The defining constraint (§7, inversion of Chinese social credit):** build
> first the parts that *cannot become a surveillance score*; add legibility
> last, with maximum care. The B2B clearing engine **does not transfer** here
> (people have no graph of denominated debts to net — brief §2.1).

## Layout
```
micorriza-politica-brief-social.md   # the source design brief (social branch)
workflows/micorriza-politica/        # spec bundle (upstream: what to build + how to know it's right)
  architecture.md  intent.md  context.md  spec.md  constraints.md   # spec.md etc. = Capa-4
  evals/{acceptance,tests}.md  evals/golden-set/*.json
  failure-model.md  audit.md  README.md  .specsmith.json
  capa1/                             # Capa-1 sub-bundle (shares intent/context/architecture)
    spec.md  constraints.md  failure-model.md  README.md  evals/{acceptance,tests}.md
  capa2/                             # Capa-2 sub-bundle (shares intent/context/architecture)
    spec.md  constraints.md  failure-model.md  README.md  evals/{acceptance,tests}.md
  capa3/                             # Capa-3 sub-bundle (shares intent/context/architecture)
    spec.md  constraints.md  failure-model.md  README.md  evals/{acceptance,tests}.md
  capa5/                             # Capa-5 sub-bundle (shares intent/context/architecture)
    spec.md  constraints.md  failure-model.md  README.md  evals/{acceptance,tests}.md
  capa6/                             # Capa-6 sub-bundle (shares intent/context/architecture)
    spec.md  constraints.md  failure-model.md  README.md  evals/{acceptance,tests}.md
src/assurance/assurance_engine.py    # Capa-4 deterministic assurance-contract engine
src/partition/membrane.py            # Capa-1 relational-mode partition firewall ("las habitaciones")
src/legibility/legibility_query.py   # Capa-2 trust-legibility query (razor's edge, asker-relative)
src/matcher/matcher.py               # Capa-3 deterministic wrapper around a proposal-only LLM ("el emparejador")
src/matcher/claude_matcher.py        # Capa-3 injected Claude-backed proposer (lazy import; never needed to test)
src/stigmergy/stigmergy.py           # Capa-5 stigmergic sensing + anti-cascade circuit breakers (deterministic, no LLM)
src/governance/governance.py         # Capa-6 sociocratic governance: consent-not-consensus (deterministic, no LLM)
tests/                               # acceptance + property + golden-set + cross-layer tests (293 passing)
  test_cross_layer_taxonomy.py       # pins ALL SIX FORBIDDEN_KEYS equal (incl. Capa-4, which the per-capa AC-X net missed) + every scanner descends into tuples
```

## Build status (sequencing per brief §7)
- [x] spec bundle (Deep route)
- [x] **Capa-4 assurance-contract / quorum engine** — "I do it if N others do,"
      with exact sponsor-bonus distribution on failure (dominant assurance
      contract, Tabarrok). No LLM, integer cents, deterministic, proposal-only,
      and anti-surveillance *by shape within each resolution* (no person-score; refuses inputs of
      that shape, recursively). Cross-campaign forgetting is a caller/storage
      convention (per-campaign token rotation, `expires_at`), not something a
      pure function can enforce. 46/46 tests pass (incl. D-06: strict binary-amount typing).
- [x] **Relational-mode partition ("las habitaciones," Capa 1)** as a type-system/firewall — §7 Etapa 1.
      Pure, deterministic, proposal-only membrane: gates one *interaction* against its declared
      room (`communal_gift` / `equality_matching` / `market_price`). Refuses (never strips) a
      market instrument leaking into the gift/equality rooms (kula/gimwali wall, invariant 1);
      the wall is *directional* (market→gift/equality only); the reciprocity *ledger* is barred in
      the gift room but balanced-in-kind reciprocity is allowed in the equality room. The
      anti-surveillance shape scan runs in **all** rooms and reuses the Capa-4 forbidden-key
      taxonomy verbatim, so the two layers cannot disagree on the membrane (Capa-4's AC6 is a
      special case; regression-checked by AC-X). A breach raises — there is no stored `admitted:false`
      record of a person (whitelist-not-blacklist, invariant 3). 47/47 tests pass (incl. D-01: envelope whitelist).
- [x] **Trust-legibility query (Capa 2, the razor's edge)** — §7 Etapa 2, built last and with maximum
      care. A pure, deterministic, proposal-only web-of-trust *query* answering only "do the people
      **I** trust vouch for X, here, now?" — evaluated **from the asker's position** over a
      *caller-supplied local graph* that is scanned and discarded. The **god-view is made structurally
      unrepresentable**, not merely disallowed (the same move as Capa-1's surveillance shape): the
      `asker` is required (no absolute-view entrypoint), the graph is never stored, traversal is
      hop-bounded, the output is **vouch-paths and specific facts — never a score/rank/reputation
      number**, absence is `no_info_from_your_position` (not a mark, whitelist-not-blacklist), and a
      wildcard/list target is refused (no enumeration). Forgetting is enforced *here* (expired
      edges/facts dropped before traversal); cells are honored (no cross-cell leak). Reuses the exact
      Capa-1/Capa-4 forbidden-key taxonomy (AC-X). Proven by the **two-askers divergence test** (AC7):
      the same `(target, cell)` returns different results for different askers. **Flagged, not
      fake-resolved:** Sybil/token-binding (§6.2), the razor's edge as a governance-not-code question
      (§6.1), and newcomer/bootstrapping exclusion. 45/45 tests pass (incl. D-02 bounded reverse-BFS, D-05 edge dedup).
- [x] **Prosocial-affordance matcher (Capa 3, "el emparejador")** — §7 Etapa 3, the **FIRST LLM in the
      stack**. A **deterministic wrapper around a proposal-only LLM**: the stochastic model *proposes* a
      bounded list of candidate matches (each carrying its human-readable reason — "who near you needs what
      you offer", "who shares this goal", a cross-context *translation*), the deterministic wrapper
      *validates, bounds, and canonically-sorts*, and a **human disposes**. The whole design problem is that
      this is the first stochastic component, and the gravity of every recommender is engagement optimization
      (invariant 8, the platform original sin) — so the objective *cooperation initiated* is made
      **structural, not a policy line**: no engagement/click/dwell/virality signal is a representable input
      (declaration keys are whitelisted + an `ENGAGEMENT_KEY` scan), and there is **no feedback loop** to
      learn time-in-app against. The LLM is **boxed, not trusted**: given hallucinated/adversarial output —
      an off-cell match, a synthesized person-scalar, an engagement-bait ordering, a non-consenting or
      unknown token, an off-schema entry — the wrapper **drops it and never crashes** (the wrapper is the
      guardrail; AC10 is the defining test; a fully-adversarial model yields zero emitted proposals). No
      person-scalar still holds (reuses the Capa-1/2/4 forbidden-key taxonomy verbatim on **both** the LLM's
      input and its output; a shaped proposal is refused, not stripped — AC-X); it may **cite** a Capa-2 fact
      but never **synthesize** a rating; matches are cell-scoped with translation as the one thin, human-gated
      bridge; proposals are ephemeral (`expires_at`) and nothing is persisted. The LLM client (Claude) is
      **injected**, never imported at module top, so the module and the whole suite run offline with a stub.
      **Flagged, not fake-resolved:** engagement optimization as the recommender's gravity (§6, inv 8),
      translation as a recentralizing bottleneck (§6.5), and filter-bubble/homophily (§6.1/§6.4). 49/49 tests pass.
- [x] **Stigmergic coordination + anti-cascade breakers (Capa 5)** — §7 Etapa 3, `[PROTOCOLO + CIRCUIT
      BREAKERS]`. **DETERMINISTIC, NOT an LLM** (no stochastic core, no injected model, no network — the whole
      difference from Capa 3). A pure `sense()` reads the environmental traces visible from **one cell** —
      contribution histories, paths, artifacts — applies **pheromone evaporation** (forgetting is the
      *mechanism*: `strength·0.5^(elapsed/half_life)`, faded traces dropped before sensing), and enforces the
      **anti-cascade circuit breakers structurally, not as a policy line** (invariant 9): a **velocity cap**
      throttles a burst per artifact per window (friction/velocity-limit), a `flag` with **no context** is damped
      (context before judgment), and an off-cell trace is dropped (**zero global broadcast**, invariant 4). The
      same move that made the surveillance shape unrepresentable in Capa 1, applied to the *cascade* shape: on a
      mob/cascade input, "correct" = **throttling the stampede** (AC4, the defining test). Traces are
      **environmental, never a person-scalar**; the `signal` is whitelisted so **no ban/distrust signal is
      representable** (positive-sum, invariant 3); reuses the Capa-1/2/3/4 forbidden-key taxonomy verbatim on the
      whole request (AC-X). Cell-scoped, caller-supplied, scanned-and-discarded; byte-deterministic; senses,
      humans act. **Flagged, not fake-resolved:** the ant-mill/cascade as the obligatory dark side of stigmergy
      (§6) — the breaker makes a stampede *hard, not impossible*; a determined off-protocol mob still can, who
      governs decides — and the breaker parameters as a governance choice. 55/55 tests pass (incl. D-04: per-window-bucket cap).
- [x] **Sociocratic governance: consent, not consensus (Capa 6)** — §7 Etapa 3, `[HUMANO →
      CONSENT-NOT-CONSENSUS]`. **DETERMINISTIC, NOT an LLM.** A pure `decide()` resolves **one proposal in one
      local circle** by **consent — the absence of a paramount (reasoned) objection — not by consensus, not by
      majority** (Haudenosaunee / Quaker / sociocracy): `adopted` iff no paramount objection, else `revisit` with
      the objection's **reason surfaced**. The defining move is **voice independent of reputation made
      structural** (invariant 7, the Capa-6 analogue of Capa-2's unrepresentable god-view): **one token, one
      voice** (deduped; a duplicate token is refused), and the weighting **cannot even be phrased** — no
      `weight`/`shares`/`voting_power`/`tally` field exists (a `VOTE_WEIGHT_KEY` refuse-list + a disposition-key
      whitelist + the shared forbidden-key taxonomy). The verdict is **categorical, never a percentage/majority/
      tally** (AC2); a **single** paramount objection blocks however many consent (AC4). An objection is a
      **whitelist-shaped pause** that surfaces its reason and **never marks the objector** (invariant 3) — the
      output carries reasons, never objector tokens, no dossier of dissent (invariant 5). Circle-local, **no
      auto-propagation** to a parent/global authority (invariants 4/6); per-round `expires_at`. The same proposal
      in the same circle yields the **same verdict regardless of any reputation the members carry** (AC1, the
      defining test). **Flagged, not fake-resolved (§6.3):** you cannot manufacture the will to cooperate (a
      low-trust circle may not bootstrap), and consent is capturable by a bad-faith blocker (tyranny of the
      minority) — the code enforces the **procedure, not good faith**; who participates and why decides. 48/48
      tests pass (incl. D-03: one-token-one-voice enforced per-circle among survivors).

## Run the tests
```bash
# shares the repo-root .venv with the B2B variant
../.venv/bin/python -m pytest tests/ -q     # or: python3 -m venv ../.venv && ../.venv/bin/pip install pytest hypothesis
```

## Non-negotiable invariants (enforced in code + tests)
1. **Separation of relational modes is sacred** — market logic never leaks into the gift/equality rooms (a priced binary campaign — or a binary campaign carrying a sponsor bonus — is rejected; AC6).
2. **No global scalar of the person** — the engine emits no score/rank/reputation and *refuses to accept* an input bearing one (AC5).
3. **Reputation opens doors, can't easily close them** — the engine can only *enable* (fire an action); it has no ban/penalty/exclusion mechanism (whitelist, not blacklist). In Capa 5 no ban/distrust *signal* is even representable (positive-sum signal whitelist); in Capa 6 an objection is a *pause* that surfaces its reason, never a mark of the objector.
4. **Local-bounded visibility, never global broadcast** — every layer is cell/circle-scoped (Dunbar): a Capa-1 interaction, a Capa-2 vouch, a Capa-3 candidate, a Capa-4 campaign, a Capa-5 trace, a Capa-6 disposition. Capa 5 drops any off-cell trace (**zero global broadcast** — the anti-stampede wall); Capa 6 does not auto-propagate a circle's decision to any parent/global authority.
5. **Forgetting is native** — every resolution carries `expires_at`; no cross-campaign state, no dossier. In Capa 5 forgetting is the *evaporation mechanism itself* (`strength·0.5^(elapsed/half_life)`, faded traces dropped); in Capa 6 it is per-round with **no dossier of who objected**.
6. **No central holder of the trust graph** — pure per-campaign/per-cell/per-round function; opaque tokens; no throne to capture. Capa 5 keeps no central trace-field; Capa 6 has no central authority that aggregates circles.
7. **Voice in governance is independent of reputation** — the Capa-6 defining move: **one token, one voice** (deduped; a duplicate token refused), and the weighting **cannot be phrased** — no `weight`/`shares`/`voting_power`/`tally` field is representable (`VOTE_WEIGHT_KEY` refuse-list + whitelist), so reputation → power → discipline is structurally blocked (AC1). *(In Capa 4 the same one-token-one-weight rule dedupes committers; Sybil / one-*person*-one-voice is out of scope, §6.2.)*
8. **The matcher optimizes cooperation INITIATED, never *engagement*** — the platform original sin. Made *structural*: no engagement/click/dwell/virality signal is a representable input to Capa 3, and there is no feedback loop to learn time-in-app against; the matcher proposes, a human disposes (AC3/AC10).
9. **Anti-cascade circuit breakers are mandatory where there is propagation** — the Capa-5 defining move: friction before propagation (a **velocity cap** per artifact per window), context before judgment (a `flag` with no context is damped), a velocity limit on virality, and **zero global broadcast** (invariant 4). The stigmergic mechanism that coordinates is the *same* one that produces the "molino de hormigas" (death spiral) / cascade / mob, so on a mob/cascade input "correct" = **throttling the stampede** (AC4). The breaker makes a stampede *hard, not impossible* — a determined off-protocol mob still can; who governs decides (§6, flagged).

See `workflows/micorriza-politica/constraints.md` for the full guardrail set with because-clauses.
