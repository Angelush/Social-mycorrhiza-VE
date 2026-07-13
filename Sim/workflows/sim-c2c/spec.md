# Sim-C2C — spec (the compact bundle)

Instantiates the **shared, proven engine** (`../../src/engine/`, `../engine/spec.md`) over the C2C
social protocol, exactly as Sim-B2B did. This file states only what is *C2C-specific*; the engine
contracts (two clocks are a domain choice, `WelfareReport`'s no-agent-slot type-guard,
`Cassette`/`LLMPolicy`, the one-way-door gate, `SearchSpace`) are NOT restated here — read
`../engine/spec.md` and the capa bundles (`../../../C2C/workflows/micorriza-politica/capa{1..6}/`).

## 0. The one hard trap (why this is not "B2B-for-people")
B2B is denominated: one obligations graph, a clean welfare scalar. **C2C is not.** The parent brief
is explicit (C2C inv. 2): **there is no global scalar of the person.** Therefore the load-bearing
Sim-invariant here is that **Track-B cannot emit a per-person scalar** — guaranteed structurally by
the engine `WelfareReport` *type* (no agent-indexed dimension → a per-person score is
*unrepresentable*, `measurement.WelfareReport.__post_init__`), with `assert_no_person_scalar` (the
`FORBIDDEN_KEYS` substring lint) as **defense-in-depth only**: it catches `trust_score` but NOT a
scalar named `fertility` / `reachability` / `centrality` — precisely the proxies the brief warns the
researcher will Goodhart. A blacklist the researcher can rename around is not the wall; the type is.

## 1. World state model
The 6 real SUT modules are **pure, stateless functions** — each takes its full input envelope per
call and discards it. So the harness `C2CWorld` (`../../src/sim_c2c/world.py`) owns **ALL**
accumulation and passes the relevant slice into every call. It never re-implements adjudication.

Accumulated state:
- **Trust graph**: `vouches` (from→to, cell, expires_at) and `facts` (about, statement, cell,
  expires_at). Fed into `legibility.query` and cited by `matcher.match`.
- **Declarations**: per-token `offers/needs/goals`, `consent.surfaceable`, `cell_id`, `expires_at`
  — the eligibility surface `matcher.match` filters over.
- **Traces**: environmental stigmergy traces (`about/signal/strength/created_at/cell_id/context`)
  passed into `stigmergy.sense`.
- **Dispositions**: per-circle `governance.decide` ballots (`token/disposition/objection/…`).
- **Rooms / cells**: mode per cell (`communal_gift | equality_matching | market_price`) for
  `membrane.admit`; membership for cell-scoping every layer.
- **Campaigns**: assurance pledge sets for `assurance.resolve`.

**Two clocks, run coherently** (memory fact #2): stigmergy uses **integer logical ticks**
(`now/created_at/window/half_life`); the other five compare **ISO-8601 strings lexicographically**.
`C2CWorld.tick` is the integer clock; `iso_now()` derives a monotone ISO string from the same tick
so a single `world.step()` advances both consistently.

Whitelist discipline (memory fact #3): trace/candidate/disposition/envelope key-sets are **CLOSED**;
an extra metadata key is a *breach*, not a passthrough. Actor proposal shapes conform exactly.

## 2. Adapter method map (verbatim real names, 1:1, no invented verbs)
`admit` → `membrane.admit` · `query` → `legibility_query.query` · `match` → `matcher.match(request,
propose)` · `resolve` → `assurance_engine.resolve` · `sense` → `stigmergy.sense` · `decide` →
`governance.decide`. Loaded by `importlib.util.spec_from_file_location` (no package install in
`C2C/`); `SutPin.git_commit` is `None` (C2C is not a git repo) — expected, not a bug.

## 3. The 9 archetypes → concrete module inputs each can produce
Each actor emits only proposal shapes the real modules actually accept (a mapping that assumes an
absent mechanism is a *finding*, not a test).

| Archetype | Kind | Drives | Concrete action |
|---|---|---|---|
| Reciprocator | good | membrane/matcher/governance | in-mode gift/equality interactions; consenting declarations; vouches for peers |
| Newcomer | neutral | legibility/matcher | joins a cell with no vouch-path; declares a need; queries from an empty position |
| Lurker | neutral | stigmergy | senses; emits low-strength `presence`/`path` traces, rarely acts |
| Surveillor | bad (F1) | membrane/legibility/matcher | attempts a `FORBIDDEN_KEYS` shape (`*_score`) AND a silent proxy (`reachability`) into a payload/declaration |
| Sybil-voucher | bad (F8) | legibility/assurance | many throwaway tokens vouching in a ring; pads an assurance head-count |
| Engagement-baiter | bad (F7/inv.8) | matcher | injects `ENGAGEMENT_KEYS` (`click`, `dwell`) via the model `propose`; bait ordering |
| Mob-instigator | bad (inv.9) | stigmergy | over-velocity-cap burst of `flag` traces on one artifact within a window |
| Room-leaker | bad (inv.1) | membrane | a `market_price` key (`price`, `_cents`) into a `communal_gift`/`equality` room |
| Bad-faith blocker | bad (Capa-6, flagged) | governance | a `paramount` objection with a bad-faith `reason` (tyranny-of-minority; not solved, surfaced) |

The matcher's injected `propose` is a **deterministic rule/cassette-backed** callable (engine
`LLMPolicy`/`Cassette`), never `claude_matcher.make_claude_propose`, inside a campaign.

## 4. Track A oracles (position-relative, red/green, halt-on-violation)
Independent re-derivation over `world.trace`; **never** imports a C2C module (AST-checked, N-03
style). Which breach arrives *how* (oracle definition):

- **T-A1 no_person_scalar** — no emitted output (any layer) carries a `FORBIDDEN_KEYS`-shaped key,
  AND no Track-B metric key is agent-indexed (enforced by `WelfareReport` type + lint). A silent
  proxy plant (`fertility`) is caught by the *type/structure*, restated here as an oracle.
- **T-A2 no_market_leak** — every `membrane.admit` that *returned* (admitted) in a
  `communal_gift`/`equality_matching` room carried no `MARKET_KEYS` (and gift rooms no
  `RECIPROCITY_LEDGER_KEYS`). A real breach arrives as a **`MembraneBreachError` exception** from
  the adapter → the world records a `Rejected`; the oracle FAILS only if an admit *succeeded* with a
  forbidden shape (i.e. the membrane's own wall was bypassed).
- **T-A3 asker_relative** — legibility answers diverge by position: two askers querying the same
  target get answers consistent with *their own* reachable subgraph (a path present for asker X's
  position must be absent for asker Y's when Y has no such edge). Divergence is the property; a
  position-independent (god-view) answer FAILS.
- **T-A4 forgetting_drops** — an expired vouch/fact/declaration/disposition/trace does **not** appear
  in any downstream output at a `now` past its `expires_at`. A survivor past expiry FAILS.
- **T-A5 consent_reasons_not_identities** — every `governance.decide` output surfaces objection
  **reasons** and carries **no objector token** anywhere. A leaked token FAILS.
- **T-A6 anti_cascade_throttle** — a stigmergy burst exceeding `velocity_cap` per artifact/window is
  reflected as `damped_velocity > 0` and the sensed count is bounded; an unthrottled stampede
  (sensed count == burst size) FAILS.

Oracle-arrival summary (Track A discipline): T-A2/T-A5 breaches surface as **adapter exceptions**
(the SUT's own wall) — the oracle's job is to catch the case where that wall was *bypassed* (the
negative control). T-A1/T-A4/T-A6 are **dropped_/damped_ counters + output-shape** checks.

## 5. Track B metrics (position-relative, descriptive-only, Goodhart-flagged)
Every metric is a `Distribution` or aggregate scalar over *sampled positions* — never an
agent-indexed slot — and ships with a `goodhart` flag string. Descriptive-only: the C2CResearcher's
search space (M6) contains **no Track-B-derived objective**, so the loop can never maximize a
fertility proxy (engine seam #3, implemented domain-side — flagged in the M6 commit).

- **B-1 reachability_of_cooperation** — from N sampled asker positions, fraction that found ≥1
  legibility path OR ≥1 surfaced match. Goodhart: "optimizing this rebuilds engagement funnels."
- **B-2 vouch_graph_diversity** — distribution of distinct nearest-hop trustees seen across sampled
  positions. Goodhart: "a centrality proxy; do not rank people by it."
- **B-3 cascade_damping_ratio** — `damped_velocity / considered_traces` aggregate. Goodhart: "high
  is not 'good moderation'; it is friction, context-dependent."
- **B-4 bootstrapping_cost** — distribution of hops a Newcomer needs before first reachable
  cooperation. Goodhart: "minimizing this incentivizes fake vouches (Sybil)."

## 6. Negative controls (the build gate — M5)
Silent plants under `../../src/sim_c2c/negative_control/nXX_fixture/src/...` mirroring C2C's real
layout, so the production `C2CAdapter` loads them **unmodified**; `C2C/` is never touched.
- **N-01 silent person-scalar** — a `legibility_query` copy that emits a `reachability` scalar per
  node (evades `FORBIDDEN_KEYS`; the README's named trap). T-A1 must catch it structurally; the real
  module never emits it; a *naive* plant using a `score` key is self-caught by the real
  `FORBIDDEN_KEYS` scan (vacuity check, ST6-style).
- **N-02 silent market leak** — a `membrane` copy that silently *admits* a `price`/`_cents` key into
  a `communal_gift` room (its market scan disabled) instead of raising. T-A2 catches the admitted
  breach; the real membrane raises `MembraneBreachError` on the same interaction.

## 7. Negative-control plants N-01/N-02 + vacuity
See failure-model.md for the harness-specific defects each plant embodies and why a passing gate is
non-vacuous.
