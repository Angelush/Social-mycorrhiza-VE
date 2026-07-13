# Micorriza — Simulation of both approaches under good/neutral/bad actors
## Design synthesis for implementation (sibling of the B2B and C2C briefs)

> **Purpose.** Distil the design of a *simulation harness* that drives the **real** Micorriza
> code (B2B mutual-credit clearing; C2C social protocol) with a population of good, neutral,
> and adversarial actors, inside a **Karpathy-style auto-research loop** (a fixed-budget round
> produces measurements to study; a researcher reads them, mutates the next round, and the loop
> compounds). Two sibling simulations, built to later **integrate** so B2B and C2C run at once
> and cross-effects on microeconomics become observable. This is a **spec to build later**, not
> code. *(Status 2026-07-11: since built — engine + all three harnesses live under `src/` with
> 120/120 tests green against the real SUTs; this brief remains the design record.)* It follows the same method as its siblings: conclusions as principles, hard principles as
> **invariants** (→ guardrails and tests), architecture as components tagged by nature
> (`[HARNESS]` / `[SUT — system under test]` / `[DETERMINISTIC]` / `[STOCHASTIC·LLM]` / `[RESEARCHER]`).

---

## 0. Guiding thesis (the pole star for every design decision)

**The simulation's job is to see the systems the way an honest adversary and an honest economist
would — not to flatter them.** It exists to answer two questions that the design documents can only
assert: *(A) do the non-negotiable invariants actually hold when live actors attack them?* and
*(B) how does surplus, liquidity, and trust actually distribute across a population that is not all
well-behaved?* Everything else is scaffolding.

Two disciplines are inherited wholesale from the parent projects and are **not optional**:

1. **The system under test is the real code, never a toy re-implementation.** The harness *imports
   and drives* `src/clearing/clearing_solver.py`, `src/ledger/mutual_credit_ledger.py`, and the C2C
   `src/*` modules. If the sim reimplements the logic, it tests a fiction and its findings do not
   transfer. The sim is a *driver and an oracle*, never a second copy of the mechanism.

2. **The harness obeys the laws of the thing it tests.** The parent invariant "the agent proposes,
   the human disposes" is *the exact shape of the research loop*: the auto-researcher proposes the
   next round; a boundary disposes of what may change. Under the chosen **autonomous-rounds** mode
   that boundary is not a human keystroke every round — it is a **hard structural gate**: the
   researcher may reshape the *world* (actor mix, parameters, scenarios, adversary intensity) freely
   within a declared search space, but it **may never patch the system under test.** A finding that
   "the code should change" is surfaced as a flagged recommendation in the research journal, for a
   human to dispose of between campaigns — never applied mid-loop. Autonomy over the world; the
   one-way door over the mechanism stays shut. (§1, inv. 2 & 3.)

---

## 1. Invariants of the simulation (NON-negotiable → guardrails and tests)

1. **The SUT is driven, never mocked.** Every value-path result (a clearing, a ledger apply, a
   membrane decision, a legibility query) comes from the real module. The harness contributes
   *inputs, timing, and adversaries* — never a substitute mechanism. *(Because: a sim that
   reimplements the logic proves nothing about the logic.)*
2. **The researcher proposes; the gate disposes — and the gate over the SUT never opens inside the
   loop.** Autonomous rounds mutate the world within a declared, bounded search space; the SUT
   source is imported read-only for the whole campaign. *(Inheritance of parent inv. 2 — the
   one-way door.)*
3. **Reproducible to the byte, given the inputs.** A campaign is a pure function of
   `(scenario, seed, actor_mix, params, SUT commit, LLM-cassette)`. The rule-based core is
   seeded and deterministic like the SUT itself; LLM probes are **recorded and replayed** (cassette)
   so a campaign re-runs identically offline. *(Because: an auditable finding must be reconstructable;
   this mirrors the SUT's own byte-determinism.)*
4. **A found invariant violation is a headline, not a data point.** If any Track-A oracle catches
   the SUT violating one of its own invariants, the campaign **halts and surfaces the exploit
   trace** — it is not averaged into a success rate. *(Because: one real conservation break or one
   silent credit-bound clamp is a system-defining bug; smoothing it into a percentage hides it.)*
5. **The C2C measurement layer cannot emit a person-scalar.** Track-B welfare metrics for the social
   sim are **position-relative, contextual, and forgetting-native only.** The structural guarantee is
   the **output *type***: a Track-B metric object has *no agent-indexed dimension* — it can hold only
   aggregate distributions (histograms, quantiles, graph-level statistics sampled from positions) and
   has no slot keyed by an agent identity, so a per-person score is *unrepresentable*, not merely
   un-named. The reused C2C `FORBIDDEN_KEYS` substring scan runs on top as **defense-in-depth lint**:
   it catches an honestly-named mistake (a field called `trust_score`) but **not** a neutrally-named
   per-person scalar (a field called `fertility`, `reachability`, or `centrality` passes it), so it is
   necessary but **not sufficient** and is never itself claimed as the structural guarantee. *(Because:
   a sim that scores each person's trust to study "fertility" rebuilds the exact god-view surveillance
   shape the C2C system exists to prevent — brief-social inv. 2 & §6.4. Measuring it wrong is not a
   smaller version of the goal; it is the anti-goal — and a substring blacklist the researcher can
   rename around is not a wall.)*
6. **Adversaries are drawn from the threat catalog, not invented ad hoc — on the correct axis.** Every
   "bad actor" strategy maps to either an **invariant it stresses** (e.g. B2B inv. 4/5/8/10), an
   **input-contract rule** (B2B F7, single-cell), or a **documented open problem** — and every
   *implementation defect* in the failure catalog that no in-world actor can induce (B2B F1–F6:
   float/determinism/termination/clamp/scope-creep) is exercised by the **negative control**, not by
   an actor. Coverage is auditable against the red-team work already done, *and* the two axes are kept
   distinct (§2). *(Because: the threat catalog exists; a sim that invents its own threats tests the
   designer's imagination — but a sim that files a live actor under a planted-defect number mislabels
   what it actually covered.)*
7. **The two tracks never contaminate each other.** Track A (invariant integrity: red/green +
   exploit trace) and Track B (microeconomics: welfare distributions) are computed and reported
   **separately**. A welfare number is never used to excuse an integrity failure, and vice versa.
   *(Because: "efficient but broken" and "safe but useless" are different verdicts and must stay
   legible as such.)*
8. **The harness never introduces an LLM on the value path.** LLM probes generate *fuzzy actor
   intentions and descriptions* (the input side of matching), never adjudicate value. This preserves
   parent B2B inv. 1 inside the sim: no stochastic process executes irreversibly on value. *(Because:
   if the sim lets an LLM decide a clearing or a ledger apply, it is testing a different, forbidden
   system.)*

---

## 2. What "good / neutral / bad" means (the actor taxonomy)

An **actor** is a policy that, each tick, observes what it can see (bounded — no god-view), forms an
intention, and submits a *proposal* to the SUT, which adjudicates. Archetypes are tagged by intent,
and **bad ≠ buggy**: a bad actor is playing the game to extract or to break, within the rules the
protocol actually enforces.

**Two axes, not one (correction to a tempting conflation).** "Bad actors *are* the failure models"
is only half true, and the wrong half misdirects the build. The numbered B2B failure modes **F1–F6**
(float drift, net mutation, non-determinism, non-termination, silent clamp, LLM scope-creep) are
*implementation defects a developer could plant* — an in-world actor cannot induce them through the
SUT's interface. They are exercised by the **negative control** (§7), which runs a deliberately-broken
copy of the SUT. The **live adversaries** below instead stress the **invariants** (B2B inv. 4/5/8/10)
and the input contract (B2B F7, the single-`cell_id` rule). So coverage has two ledgers: *planted
defects caught* (negative control ⇒ F-modes) and *invariants withstood under load* (live adversaries ⇒
inv. 4/5/8/10). A sim that files a live adversary under "F1 float drift" is miscategorising what it
tests.

### B2B actors (drive the clearing solver + mutual-credit ledger)
Live adversaries stress **invariants** (a behaviour the shipping code must withstand); planted
implementation defects (B2B F1–F6) are the job of the **negative control**, not of an in-world actor
(see the two-axes note below). Each row cites the invariant it stresses, verified against the real
SUT surface (`record_obligation` / `settle_obligation` / `clear` / `apply_clearing` / `update_member`
/ `pause_cell`).

| Archetype | Intent | Behaviour (real SUT ops) | Invariant stressed |
|---|---|---|---|
| **Circulator** (good) | cooperative | trades within lines, settles obligations, keeps net near zero | baseline / calibration |
| **Hoarder** (neutral) | self-interested, legal | accumulates toward the positive cap | B2B inv. 4 — *open question:* does the positive cap redistribute strong→weak, or does it only **block** further accumulation? (the code rejects the over-cap obligation; it moves no value — Track B measures which) |
| **Wallflower** (neutral) | passive | low trade density, few overlaps | B2B brief §7.1 cold-start / thin cycles |
| **Defrauder** (bad) | extract | draws the negative line to its cap (records obligations as debtor + settles), then ceases activity without repaying — there is no `exit` op; the negative balance persists on the books | B2B inv. 4/5 (loss bounded to the negative cap + graduated sanctions) **and the mutualization question** (Track B: the default is absorbed by the *creditors* holding the offsetting positive balances — measure how it distributes, don't assert "bounded to the defrauder") |
| **Sybil-hopper** (bad) | extract | asks the membership layer to admit throwaway firm identities to multiply credit lines | B2B inv. 10 permissioned membership — the gate is a **human/policy layer the SUT only stubs** (`add_member` accepts any `ratified_by`); A5's "success" is a finding about the boundary of code-enforceable vs. human-enforceable, not a SUT break |
| **Velocity attacker** (bad) | break | machine-speed burst of `record_obligation` from one debtor within a window to exceed the velocity cap | B2B inv. 8 — the ledger's real breaker is a **per-debtor velocity cap** (`velocity_max_cents`/`velocity_window_s`) that **rejects** the over-cap obligation, plus a manual `pause_cell`. There is **no cascade and no depth-cap**: clearing preserves net positions, so no flash-loan/value-extraction surface exists |
| **Cell-leaker** (bad) | break | tries to move value between two cells | B2B inv. 6 cell firewall — but the SUT is **single-cell** (`clear()` takes one `cell_id`; obligations carry no cell tag; a foreign member is *rejected* as "unknown member"). The firewall holds **by the input contract**, not by solver logic. A genuine two-cell contagion-firewall test needs ≥2 cell instances and belongs to **Sim-Integrated**; in Sim-B2B it reduces to "the harness never assembles a mixed-cell batch + the SUT rejects foreign members" (§5) |

### C2C actors (drive the membrane, legibility, matcher, assurance, stigmergy, governance)
*Provisional mapping — verified against the real C2C modules when the Sim-C2C bundle is built (§7.2),
the same way the B2B rows above were checked against the shipping solver/ledger. `C2C inv. N` = the
social brief §1; `C2C F#` = the C2C failure model.*

| Archetype | Intent | Behaviour | Invariant / failure mode probed |
|---|---|---|---|
| **Reciprocator** (good) | cooperative | vouches truthfully, reciprocates in the equality room, initiates cooperation | baseline / fertility proxies |
| **Newcomer** (neutral) | wants in | no vouches yet, seeks bootstrapping | C2C brief §6.2 bootstrapping / exclusion |
| **Lurker** (neutral) | passive | consumes, rarely contributes | stigmergy sensing floor |
| **Surveillor** (bad) | totalize | queries legibility from many positions to reconstruct a god-view / person-score | C2C F1 surveillance-creep, C2C inv. 2/6 |
| **Sybil-voucher** (bad) | extract | mints tokens to fake vouches / drain assurance bonuses | C2C F8 Sybil bonus-extraction, C2C brief §6.2 |
| **Engagement-baiter** (bad) | capture | crafts inputs to make the matcher optimize attention/outrage | C2C F7 / C2C inv. 8 (platform original sin) |
| **Mob-instigator** (bad) | cascade | seeds a stampede / pile-on across cells | C2C inv. 9 anti-cascade breakers, "molino de hormigas" |
| **Room-leaker** (bad) | corrupt | smuggles market pricing into the gift/equality rooms | C2C inv. 1 kula/gimwali wall, C2C F5 |
| **Bad-faith blocker** (bad) | capture | abuses consent-not-consensus to veto everything | C2C Capa-6 F8 consent capture / tyranny of the minority (flagged, not solved; C2C brief §6.3) |

**Mix, not monoculture.** A scenario is a *ratio* of archetypes (e.g. 70/20/10 good/neutral/bad).
The research loop's most important knob is this ratio and the adversary intensity: the interesting
findings are at the phase boundaries where a system that holds at 5% bad actors breaks at 25%.

---

## 3. The Karpathy auto-research loop (the outer engine)

A campaign is a sequence of rounds under a fixed budget; each round is one simulated world run to
conclusion, measured, and fed to the researcher, which mutates the next round.

```
campaign(scenario_template, search_space, budget, seed):
  history = []
  while budget remains and not converged and no invariant violation:
      world   = instantiate(scenario, actor_mix, params, seed)     # real SUT inside
      trace   = run(world, ticks=T)                                # actors propose, SUT adjudicates
      report  = measure(trace)                                     # Track A (integrity) + Track B (welfare)
      journal.append(round, config, report)                       # append-only, hash-chained
      if report.trackA.violation:  halt_and_surface(report)       # inv. 4 — a headline, not a point
      proposal = researcher.next(history + report, search_space)  # mutate world only, within bounds
      scenario, actor_mix, params = apply_within_gate(proposal)   # SUT source untouched (inv. 2)
      history.append(report)
  return journal, frontier   # the pareto frontier of (integrity, welfare) over the explored space
```

- **Budget** = wall-clock or total ticks or rounds; declared up front. The "limited time gives some
  output to study" is exactly this.
- **Researcher `[RESEARCHER]`** = a bounded search/optimization strategy over the declared
  `search_space` (archetype ratios, parameter ranges, adversary intensities, scenario templates). It
  may be a simple evolutionary/bandit strategy or an LLM-in-the-loop that reads the report and writes
  the next hypothesis — but in **both** cases it is proposal-only over the world and blind to the SUT
  source. Its output each round is a *hypothesis + a world diff*, logged.
- **Convergence / stop** = budget exhausted, search converged (no knob improves the frontier), or an
  invariant violation halts the campaign. These are the loop's circuit breakers — thematically the
  same discipline the systems themselves enforce.
- **The journal is the deliverable of a campaign**, not a single number: an append-only, hash-chained
  research log (same shape as the ledger's audit log) that another person can replay.

---

## 4. Two tracks of measurement (never mixed — inv. 7)

### Track A — invariant integrity `[ORACLE]`
Independent re-derivation of each SUT invariant from the trace, computed by code that does **not**
trust the SUT's own bookkeeping (the same discipline as the solver's `networkx` cross-check oracle).
Output is **red/green per invariant + the minimal exploit trace** on red.
- B2B: conservation (net position pre==post — the strongest oracle, an independent recompute);
  credit-bound integrity (the *solver* **flags** a pre-existing out-of-bounds net; the *ledger*
  **rejects** any op that would breach a bound; **neither clamps** — the oracle confirms rejection,
  not a clamped-and-continued balance); velocity breaker (per-debtor burst beyond
  `velocity_max_cents`/window is **rejected**, `pause_cell` halts mutation — not a cascade-depth cap);
  cell firewall *held by the input contract* (single-cell SUT — the multi-cell contagion firewall is
  an integration oracle, §5); sanctions *ladder-ordered* (the SUT rejects rung-skips; **appeal is a
  human-layer concept absent from the code**, flagged not asserted).
- C2C: no person-scalar emitted, market logic *did not* leak rooms, legibility answers stayed
  position-relative, forgetting actually dropped expired data, consent surfaced reasons not objector
  identities, anti-cascade breakers throttled the induced stampede (C2C inv. 9).

### Track B — microeconomics `[STATISTICS]`
Welfare distributions across the population and across actor mixes.
- **B2B (denominated, so real welfare metrics exist):** net internal debt reduced % (**reported with
  its sensitivity to the topology generator, not gated** — see §6.5 and §7.1: `reduction_pct` is a
  function of how much gross debt sits on cycles in the *synthetic* graph, so hitting Sardex's
  ≈25%/≈50% band shows the generator is not-obviously-miscalibrated, never that the SUT is validated;
  a value off by an order of magnitude trips a modelling-error flag, X2); Gini of clearing benefit
  (power-law-unequal → measure the distribution; this is a per-firm *economic* figure, legitimately
  aggregated, **not** a reputation scalar); liquidity enabled by credit lines (trade that could not
  have cleared without them); **contracyclical test** (a "credit-crunch" scenario → does the system's
  relative advantage rise? brief §7.4); **positive-cap effect** — the honest open question: does the
  cap redistribute value strong→weak (B2B inv. 4's *claim*), or does it only **block** accumulation
  (what the code *does* — it rejects the over-cap obligation and moves no value)? Report which; a gap
  is a flagged recommendation for the humans between campaigns, not a number to paper over; **default
  mutualization** — when a defrauder walks, measure how the negative balance distributes across the
  creditor side (the real distributional cost, since there is no exit op that erases it; the
  distribution is identity-free by the Track-B type — per-event identities live only in the trace).
- **C2C (NON-denominated → constrained, sim inv. 5):** only position-relative, contextual, Goodhart-
  flagged proxies — e.g. *reachability of cooperation from a random position* (did a newcomer find a
  match?), *diversity of the vouch graph seen from sampled positions*, *cascade damping ratio*, *cost
  of bootstrapping*. Every C2C welfare number ships with an explicit **Goodhart flag**. The
  no-person-scalar guarantee is structural in the output *type* (no agent-indexed dimension), with the
  `FORBIDDEN_KEYS` substring scan as a secondary lint that the researcher could rename around (sim
  inv. 5). When a proxy cannot be honestly measured, the sim says so rather than inventing one —
  measuring nothing beats measuring the anti-goal.

---

## 5. Integration (later, but designed for now)

The B2B and C2C sims share **one engine** (`workflows/engine`) — the loop, the actor/policy protocol,
the world, the researcher, the journal, the two-track measurement base. Only the *world contents* and
the *SUT adapters* differ. The integration study is enabled by a single seam:

- **A shared actor identity that lives in both worlds.** A "business" is simultaneously a firm in a
  B2B cell and an org in a C2C market room; a "person" is a C2C member who may also be a sole-trader
  firm. The integrated sim runs both SUTs over one population and measures cross-effects: does C2C
  trust legibility change who defaults in B2B? Does B2B liquidity stress change C2C cooperation? These
  are the microeconomic cross-questions the user wants — and they are only askable once one identity
  spans both. **Constraint:** the firewall between the *value path* (B2B, denominated) and the
  *social path* (C2C, non-denominated) is itself an invariant to test — the integration must **not**
  become a channel that leaks a denominated debt into a gift room, or a person-scalar into a credit
  decision. The integration seam is a *place a new failure mode lives*, and the sim's job is to find
  it. (This is why C2C ships stubbed-with-seams now, integrated stubbed-with-seams now, and B2B full
  now — §7 sequencing.)
- **The B2B *cell-to-cell* firewall (B2B inv. 6) is also a multi-instance concern and lives here.**
  The shipping B2B SUT is single-cell: `clear()` takes one `cell_id`, obligations carry no cell tag,
  and a foreign member is rejected as "unknown member" — so *within* one Sim-B2B world there is no
  cross-cell operation to attack, and the firewall holds trivially by the input contract (B2B F7's own
  mitigation is "the input is a single `cell_id`"). A real default-contagion firewall test needs **two
  ledger/solver instances** and an actor that tries to make a default in cell A move value or a bound
  breach into cell B. That is the same multi-instance shape as the value/social firewall above, so it
  is specced here, not in Sim-B2B. In Sim-B2B the "Cell-leaker" degrades to a **harness-partition
  guard** (the harness must never assemble a batch mixing two cells) plus a check that the SUT rejects
  foreign-member obligations — a test of the harness's own correctness, labelled as such.

---

## 6. Open problems (do NOT fake-resolve in code or in the pitch)

1. **A green sim is not a safe system.** The simulation can only falsify, never verify. Passing every
   Track-A oracle under every explored mix means *no explored adversary broke it*, not *it is
   unbreakable*. The search space is finite; the real adversary is not. Report coverage, never
   safety. *(This is the sim's own version of parent §7.5 "lo irreducible".)*
2. **Fully-autonomous rounds trade oversight for throughput.** The chosen mode lets the researcher run
   unattended within bounds. The mitigation is structural (SUT immutable, hash-chained journal, halt-
   on-violation) — but a mis-specified search space can still spend the whole budget in an
   uninteresting corner. The search space is a human design act; the autonomy does not remove it.
3. **The C2C fertility metric is Goodhart-prone by construction (inherited §6.4).** Any proxy the sim
   optimizes toward will be gamed by the researcher's own mutations — the sim can *discover* the
   gaming (that is a valid finding) but cannot declare a "fertility score." Track-B for C2C is
   descriptive, never an objective the loop maximizes.
4. **LLM probes reintroduce non-determinism.** Mitigated by cassette record/replay (inv. 3), but a
   probe's persona is a modelling choice that colours results; an adversarial persona the modeller
   did not think of is an adversary the sim did not test. The LLM widens realism and narrows
   reproducibility; the trade is declared, not hidden.
5. **Calibration is not validation.** Reproducing Sardex's ≈25%/≈50% numbers shows the B2B sim is not
   obviously wrong; it does **not** show it is right. Real commercial-network topology is unknown to
   us; the sim's graph generators are hypotheses. Flag every synthetic topology as such.

---

## 7. What to build first (sequencing — mirrors the parent projects)

0. **Validate the harness question before the harness** (this spec): confirm the two tracks and the
   actor taxonomy answer questions the design docs cannot. *Threshold:* at least one invariant per
   system that a plausible actor could plausibly attack. (Met — see §2.)
1. **Shared engine + Sim-B2B, full** (this iteration's deliverable): the loop, world, actor protocol,
   researcher, journal, two-track measurement, and the B2B SUT adapter driving the *real* solver and
   ledger. Rule-based actor core first; LLM probes injected and stubbable (offline by default).
   *Build gate (what makes it trustworthy):* the **negative control** — against a deliberately-broken
   copy of the SUT that commits a *silent* conservation breach (drops a cent **and** bypasses its own
   internal conservation assert), the independent oracle halts on the first round and surfaces the
   exploit trace (§7 of the B2B spec). Reproducing the Sardex ≈25%/≈50% band on a cooperative mix is
   *reported with its topology-sensitivity as a sanity check, not a gate*: the number is a property of
   the synthetic generator, so gating on it would reward tuning the generator to the anchor —
   calibration ≠ validation (§6.5).
2. **Sim-C2C, full** (next): instantiate the same engine over the C2C SUT modules; build the
   constrained, person-scalar-free Track-B measurement (the hard part). Only after B2B proves the
   engine.
3. **Sim-Integrated** (last): one population spanning both SUTs; the value/social firewall as a tested
   invariant; the cross-effect microeconomic study the user is really after.

---

### Conversation map (what this brief covers)
1. Simulating both approaches under good/neutral/bad actors → §0, §2
2. Actors as live executions of the existing failure models → §1 inv. 6, §2
3. Karpathy limited-budget auto-research loop, compounding rounds → §3
4. Two separated tracks: invariant integrity vs. microeconomics → §1 inv. 7, §4
5. The C2C measurement trap (do not rebuild the god-view) → §1 inv. 5, §4, §6.3
6. Two sibling sims, one engine, later integrated for cross-effects → §5, §7
7. Autonomous rounds with a structural gate over the SUT → §0, §1 inv. 2, §6.2

> **Anchor discipline:** the simulation is a *driver and an oracle*, never a second copy of the
> mechanism, and it obeys the same laws it tests — the agent proposes, the gate disposes, and the
> one-way door over value never opens inside the loop.
