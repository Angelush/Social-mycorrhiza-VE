# Engine spec — the shared ABM + auto-research core (spec'd once, instantiated per domain)

> Produced by engineer-spec. This is the domain-agnostic core that Sim-B2B, Sim-C2C, and
> Sim-Integrated all instantiate. It contains **no** B2B or C2C business logic — only the loop, the
> actor protocol, the world container, the researcher, the journal, and the two-track measurement
> base classes. Business logic lives in the SUT adapters (per-domain) and in the measurement
> subclasses (per-domain).

## Purpose
One reusable agent-based-model + auto-research harness. A *domain* supplies: (a) a **SUT adapter**
that imports and drives the real system code, (b) a set of **actor policies**, (c) a **world**
definition (what state exists, what a "tick" does), and (d) **measurement subclasses** for Track A
(integrity oracles) and Track B (welfare statistics). The engine supplies everything else.

**Numbering:** "engine inv. N" ≡ simulation-brief §1 invariant N ("sim inv. N") — one namespace,
referenced from two places (audit V12).

## Components (each tagged by nature)

### `World` `[HARNESS]`
Holds: the SUT adapter instance(s), the actor population, the environment state (domain-specific:
obligations graph for B2B; rooms/trust-graph for C2C), a **seeded** RNG, and the current tick. Pure
container + scheduler. `world.step()` runs one tick: every actor observes its **bounded** view (no
god-view — an actor sees only what the protocol would expose to it), forms an intention, submits a
proposal; the SUT adjudicates; the world applies the adjudicated result and appends to the trace.

### `SUTAdapter` `[SUT]` (abstract; domain supplies concrete)
Thin wrapper that **imports the real module** and exposes a driving interface. MUST NOT reimplement
any adjudication (engine inv. 1). Imported **read-only for the whole campaign** — the adapter records
a **content hash** of the SUT sources at campaign start (plus the git commit when the SUT lives in a
repo — B2B does, C2C currently does not; audit V5) and refuses to run if it changes (engine inv. 2).
Value-path calls (clearing, ledger apply, membrane gate, legibility query) go straight to the real
code.

**Adapter methods are exactly the real module's public operations — one-to-one, no invented verbs.**
If a domain wants an actor behaviour the SUT has no operation for (e.g. B2B "draw credit" or "exit"),
that behaviour is a **composite of real operations sequenced by the actor policy**, never a new
adapter primitive. The moment an adapter method has to *compute* a balance/bound/netting to fake a
missing operation, it has become a second copy of the mechanism (inv. 1). Sequencing real ops is what
an actor does; computing value-path results is what the adapter must never do. (This is why the B2B
adapter surface is `add_member` / `record_obligation` / `settle_obligation` / `run_clearing` /
`apply_clearing` / `update_member` / `pause_cell` / `resume_cell` — plus `create_cell` for world
setup and the ledger's read-only view accessors, which observe and adjudicate nothing — and no other
verbs; see sim-b2b, audit V4.)

### `Policy` / actor `[DETERMINISTIC | STOCHASTIC·LLM]` (abstract; domain supplies archetypes)
`act(view, rng) -> Proposal`. Two concrete families:
- **`RulePolicy` `[DETERMINISTIC]`** — seeded, pure, byte-reproducible. The bulk of every population.
- **`LLMPolicy` `[STOCHASTIC·LLM]`** — an **injected**, **boxed**, **proposal-only** model call that
  turns a persona + view into a fuzzy intention/description (the input side of matching only — never
  a value adjudication, engine inv. 8). Injected exactly like the C2C `claude_matcher.py`: never
  imported at module top, always stubbable, so the suite runs offline. Under a reproducible campaign
  its calls are served from a **cassette** (record once, replay by hash) — engine inv. 3.

### `Researcher` `[RESEARCHER]` (abstract; strategy is pluggable)
`next(history, search_space) -> WorldDiff`. Reads the accumulated reports and proposes the next
round's world (actor-mix ratios, parameter values, adversary intensity, scenario template) **within
the declared `search_space`**. Strategies: `GridResearcher`, `BanditResearcher`,
`EvolutionaryResearcher`, or `LLMResearcher` (reads the report, writes a hypothesis + diff). ALL are
**proposal-only over the world and blind to the SUT source** (engine inv. 2). The diff passes through
`apply_within_gate`, which validates it against the search space and **rejects any field touching the
SUT** — structurally, not by convention.

### `Journal` `[HARNESS]`
Append-only, **hash-chained** log (same shape and discipline as the ledger audit log): one entry per
round = `(round, config_hash, report, researcher_hypothesis, diff, prev_hash)` — the hypothesis/diff
in entry *k* are the proposal that produced round *k+1*; a halted final entry carries none (audit
V12). A campaign replays
identically from the journal + seed + SUT pin + cassette. The journal is the campaign's primary
artifact (brief §3).

### Measurement base `[ORACLE | STATISTICS]` (abstract; domain supplies subclasses)
- `TrackA(trace) -> IntegrityReport` — per-invariant red/green + minimal exploit trace on red.
  Computed by code that does **not** trust the SUT's own bookkeeping (independent re-derivation).
- `TrackB(trace) -> WelfareReport` — welfare distributions. The **base class enforces engine inv. 5
  structurally, by *type*, not by string-matching:** a `WelfareReport` is a container of
  aggregate-only metrics — histograms, quantiles, Gini/graph-level statistics, position-sampled
  distributions — whose schema has **no agent-indexed dimension**. There is no map keyed by agent id
  in which a per-person scalar could be placed, so one is *unrepresentable* (a domain cannot ship
  `{agent_id: score}` because the type has no such slot). On top of that, `assert_no_person_scalar`
  runs the domain's `FORBIDDEN_KEYS` substring scan as **defense-in-depth lint** — it catches an
  honestly-named leak (`trust_score`) but is explicitly **insufficient alone**: a per-person scalar
  named `fertility`/`reachability` would pass the scan, which is exactly why the *type* is the real
  guard and the scan is only a backstop. (B2B's `WelfareReport` legitimately holds per-firm *economic*
  figures — net position, clearing benefit — which are aggregated into distributions; the type
  forbids an *identity-keyed reputation scalar*, not honest per-firm economics feeding a Gini.)
- The two are returned as **separate** objects and never combined (engine inv. 7).

## The loop (reference)
```
def campaign(scenario_template, search_space, budget, seed, sut_pin,
             sut_adapter, researcher):            # researcher strategy+config is campaign identity (inv. 3)
    assert_sut_pinned(sut_pin)                    # inv. 2: content-hash pin, read-only for the whole run
    journal, history = Journal(), []
    cfg = scenario_template.initial()
    while budget.remaining() and not converged(history):
        world  = World(sut_adapter, build_actors(cfg), build_env(cfg), rng=seed_for(cfg))
        trace  = run(world, ticks=cfg.T)
        a, b   = TrackA(trace), TrackB(trace)     # inv. 7: separate
        if a.violation:                           # inv. 4: halt, don't average
            journal.append(cfg, a, b, hypothesis=None, diff=None)   # the violating round IS journaled
            return journal.halt_and_surface(a.exploit_trace)
        hyp, diff = researcher.next(history + [(cfg, a, b)], search_space)  # inv. 2: world only
        journal.append(cfg, a, b, hyp, diff)      # entry k carries the diff that produces round k+1
        history.append((cfg, a, b)); budget.spend()
        cfg    = apply_within_gate(cfg, diff)     # rejects any SUT-touching field
    return journal, pareto_frontier(history)      # (integrity, welfare) over explored space
```
*(Audit V12: `history` pairs each round's reports with the config that produced them — appending
after `apply_within_gate` would shift them one round and mis-train the researcher; the journal entry
is written after the researcher runs so it can carry the hypothesis+diff.)*

## Reproducibility contract (engine inv. 3)
A campaign is a pure function of `(scenario_template, search_space, budget, seed, sut_pin,
researcher strategy+config, cassette)` — the researcher is pluggable, so it is part of the campaign's
identity: a Grid and a Bandit researcher diverge under the same seed (audit V17; replaying a single
round from the journal needs only the journaled config). The pin is a content hash of the SUT sources
(git commit recorded when available — V5). Rule policies + world + measurement + seeded rule-based
researchers are deterministic; LLM policies/researcher are served
from the cassette under replay. Re-running yields a byte-identical journal. (Mirrors the SUT's own
byte-determinism invariant.)

## Stack (proposed, stable for this iteration)
- **Python 3.11+**, shares the repo-root `.venv` with B2B/C2C. Integer arithmetic on the value path
  (never floats — inherited). `pytest` + `hypothesis` for the harness's own property tests.
- No network on the reproducible path; LLM access is injected and cassette-backed.
- The engine is a library; each `workflows/sim-*` provides the domain package under a future `src/`.

## Out of scope for the engine
Any B2B or C2C rule (those live in the SUT under test and in the domain adapters); any GUI; any live
deployment. The engine dry-runs systems; it does not run them in production.
