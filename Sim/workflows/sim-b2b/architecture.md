# Architecture — components by nature (Sim-B2B)

> Produced by classify-architecture. Multi-species harness. Each component is tagged so it is
> unambiguous what is deterministic code, what is the system under test, what is stochastic, and what
> is the research controller. Mixing these is the root design error the parent projects warn against.

## The stack (bottom = the real system, top = the research loop)

### SUT layer — `[SUT · DETERMINISTIC]` (imported, read-only, NOT reimplemented)
`B2BAdapter` imports and drives the real `clearing_solver` and `mutual_credit_ledger`. Its methods are
**one-to-one with the real modules' public operations** — no invented verbs: `add_member`,
`record_obligation`, `settle_obligation`, `run_clearing` (= `ledger.to_clearing_input` →
`solver.clear`, returns a proposal), `apply_clearing` (→ ledger's human-gated commit, requires
`ratified_by`), `update_member` (sanctions ladder), `pause_cell`, `resume_cell` — plus `create_cell`
(**world setup only**, a ratified real op, never an actor proposal) and the ledger's **read-only**
accessors (`member_statement`, `cell_metrics`) that back the bounded `FirmState` views (audit V4).
**There is no
`draw_credit` and no `exit_member`** — the ledger has no such operation; "draw to the negative cap" and
"default/exit" are *composite actor behaviours* sequenced from `record_obligation` + `settle_obligation`
by the policy, never adapter primitives that fake a missing op (H1). Every method delegates to the real
module; the adapter adds **no** adjudication. The adapter pins the SUT commit hash at campaign start and
refuses to run if it changes (engine inv. 2 — the one-way door over value stays shut inside the loop).

### World layer — `[HARNESS · DETERMINISTIC]`
`B2BWorld` holds the adapter, the firm population, the obligations environment, and a seeded RNG.
`step()`: each firm observes its **bounded** view (its own balance + line, its trade neighbours, the
public settlement report — never a god-view of everyone's books), emits a `Proposal`, the adapter
adjudicates, the world applies the result and appends to the trace.

### Actor layer — `[DETERMINISTIC core + STOCHASTIC·LLM probes]`
Seven archetype policies. The **core is `RulePolicy`** (seeded, reproducible) — this is the bulk of
every population and the whole adversary set, because attacks are precise, not fuzzy. The **optional
`LLMProbe`** is an injected, boxed, proposal-only model that generates a firm's *fuzzy trade
intention* — never a value decision (sim inv. 8). **Inert in B2B:** no B2B SUT module parses free text
(the matcher is C2C's Capa 3, out of scope here), so the probe's output has no value-path consumer and
at most biases which concrete `Trade` the rule policy then emits. Off by default; its live consumer is
Sim-C2C's `claude_matcher.py`. Injected the same way; cassette-backed under replay.

### Measurement layer — `[ORACLE + STATISTICS]` (two tracks, never mixed — engine inv. 7)
- **`B2BTrackA` `[ORACLE]`** independently re-derives, from the trace:
  - **Conservation** — each firm's net position pre==post every clearing, via a second,
    differently-implemented recompute (not the solver's own number). The strongest oracle (B2B F2).
  - **Credit-bound integrity** — the *solver* **flags** a pre-existing out-of-bounds net (and cannot
    create or clamp one, since clearing preserves net position); the *ledger* **rejects** (raises) any
    op that would breach a bound. Assert both, and that **neither clamps** (B2B inv. 4 / B2B F5).
  - **Firewall (single-cell SUT)** — the SUT has no cross-cell op, so assert the **harness never mixes
    two cells** into one input and the SUT **rejects** foreign-member obligations (and `apply_clearing`
    rejects a mismatched `cell_id` — audit V18). The real two-cell
    contagion firewall (B2B inv. 6) is a Sim-Integrated oracle (B2B F7 — single-`cell_id` contract).
  - **Velocity breaker** — under a burst, the over-cap `record_obligation` is **rejected** and no
    debtor exceeds `velocity_max_cents` in a window; `pause_cell` halts mutation (manual +
    human-ratified — the brief's *automatic* pause has no code counterpart, flagged via X7). Reports
    the **rejection boundary vs. intensity** — *not* a cascade depth (the SUT has no cascade — B2B
    inv. 8).
  - **Sanction ladder** — every status transition obeyed the ladder ordering (the SUT rejects
    rung-skips); sanctioning is a harness compliance policy (human-layer, flagged). **Appeal is not in
    the code** — flagged, not asserted. Surfaces two real findings: line-reduction **raises** against a
    drawn-down member; the ladder allows **unrestricted downward** (silent rehab) (B2B inv. 5).
  Output: per-invariant red/green + minimal exploit trace on red.
- **`B2BTrackB` `[STATISTICS]`** computes **aggregate-only** welfare distributions (no agent-indexed
  dimension by type): net-debt-reduced % (reported with topology-sensitivity, not gated), Gini of
  clearing benefit, credit-enabled liquidity, **positive-cap effect** (does the cap redistribute or
  merely block? — honest open question, escalated if it only blocks), contracyclical delta, **default
  mutualisation** (how a defrauder's persisted negative balance distributes across creditors —
  identity-free by type, audit V13). Runs
  `assert_no_person_scalar` as a **secondary lint** on top of the type guard (symmetry with C2C N2;
  sim C14).

### Research layer — `[RESEARCHER]` (autonomous within bounds)
`B2BResearcher` reads the accumulated two-track reports and proposes the next round's world within the
declared `search_space` (archetype ratios, credit-line calibration, clearing cadence, adversary
intensity, topology parameters, credit-crunch on/off). Default strategy: evolutionary/bandit over the
mix + a small LLM-in-the-loop option that writes the round's hypothesis. **Proposal-only over the
world, blind to the SUT source**; its diff passes `apply_within_gate`, which rejects any SUT-touching
field. Runs unattended until budget/convergence/violation.

### Journal — `[HARNESS]`
Hash-chained, append-only, one entry per round (same discipline as the ledger audit log). The campaign
replays identically from journal + seed + SUT commit + cassette.

## Interaction pattern (one round)
```
instantiate world (real SUT inside, seeded)
  └─ for tick in 1..T:
        each firm: observe bounded view → propose (trade / settle / request-clearing;
                   compliance-policy → sanction-step; breaker-policy → pause)
        adapter: adjudicate via REAL solver + ledger (draw/default = composite of trade+settle)
        world: apply + append to trace
measure: TrackA (integrity oracle)  ┊  TrackB (welfare stats)      # separate
journal.append(config, TrackA, TrackB)
if TrackA.violation: HALT + surface exploit trace                  # not averaged
researcher: propose next world within search_space (SUT untouched)
```

## Why this shape (design rationale)
- **SUT imported, not copied** → findings transfer to the shipping system (brief §0.1).
- **Rule core, LLM at the edges** → the loop is cheap and reproducible where it must be (the bulk and
  all adversaries), fuzzy only where realism needs it (need-descriptions), and never stochastic on
  value (engine inv. 8).
- **Two tracks, never mixed** → "efficient but broken" and "safe but useless" stay distinguishable
  (engine inv. 7).
- **Autonomy over the world, one-way door over the mechanism** → honours the parent projects'
  defining discipline even under the chosen fully-autonomous mode (brief §0.2, §6.2).
