# Specification — Capa 5 Stigmergic Coordination + Anti-Cascade Circuit Breakers

> Produced by engineer-spec. Self-contained blueprint; an agent can build from this alone.
> Sibling of the Capa-4, Capa-1, Capa-2, and Capa-3 `spec.md`. This is a
> `[PROTOCOLO + CIRCUIT BREAKERS]` component (brief §4 Capa 5, invariant 9,
> architecture.md: *Not an agent. Friction/rate-limits on propagation*). It is
> **DETERMINISTIC, NOT an LLM** — no stochastic core, no injected model, no network client.
> That is the whole difference from Capa 3. It routes through the Capa-1 membrane's
> `FORBIDDEN_KEY` taxonomy verbatim so the five layers cannot disagree on the surveillance shape.

## Purpose
Coordinate a cell **through traces left in the shared environment** — contribution histories,
paths, artifacts, signals — the way FOSS, Wikipedia, or Hayek's prices coordinate without a
commander (brief §4 Capa 5, §5 estigmergia). The function **senses** the environmental traces
visible *from one cell*, applies **pheromone evaporation** (forgetting), and enforces the
**anti-cascade circuit breakers** (invariant 9) so the very same mechanism that coordinates cannot
also produce the "ant mill" (death spiral), the information cascade, or the mob.

The defining design problem (brief §4 Capa 5, §5, §6): **the same mechanism that coordinates also
produces the stampede.** Traces in the environment are how ants build a nest *and* how ants march
in a death spiral; how Wikipedia self-heals *and* how a pile-on forms. The circuit breakers must
be **structural, not a policy line** — the same move that made the surveillance shape
*unrepresentable* in Capa 1, applied to the cascade shape here.

## The design move — the breakers are structural, not a policy
Four structural walls, each an analogue of a wall in the sibling layers:

1. **Traces are ENVIRONMENTAL, never a person-scalar (invariants 2/3).** A trace is *about* a
   path / contribution / artifact token (`about`), never an aggregate rating of a person. The exact
   Capa-1/2/3/4 `FORBIDDEN_KEY` taxonomy is scanned over the whole request, so a
   `score`/`rank`/`reputation`/`blacklist` trace is **refused (raised), not stored**. And the design
   is **positive-sum**: the `signal` field is **whitelisted** to environmental/positive kinds
   (`contribution`, `path`, `endorsement`, `presence`, `flag`); there is **no `ban`/`distrust`/
   `condemn` signal representable** (invariant 3). The one judgment-shaped signal, `flag`, is about
   an **artifact**, not a person, and is gated by wall 3(b).

2. **Forgetting is LOAD-BEARING here — pheromone evaporation (invariant 5).** Trace strength
   **decays with elapsed time** (`effective = strength · 0.5^(elapsed / half_life)`), and traces
   whose evaporated strength falls below `min_strength` are **dropped before sensing**. Evaporation
   is the **mechanism**, not a courtesy: an old trace fades to nothing on its own, exactly as a
   pheromone does. This is where forgetting is *native and structural*, not a `expires_at` stamp.

3. **Anti-cascade circuit breakers (invariant 9), each structural:**
   - **(a) FRICTION before propagation / (c) VELOCITY LIMIT on virality.** A signal cannot amplify
     instantly. Per `about` artifact **per window-bucket** (bucket 0 is the current window, the closed
     interval `[now − window, now]`; each older window is its own bucket), the number of traces is
     capped at `velocity_cap`; the earliest `velocity_cap` in each bucket are kept and every later one
     in the burst is **damped** (`damped_velocity`). Bucketing by window closes the backdate bypass
     (D-04): a burst is throttled whatever tick it is dated to, so backdating it just past the current
     window no longer exempts it — yet genuinely sustained coordination, spread ≤`velocity_cap` across
     many buckets, still passes. A rapid amplification is throttled deterministically — the stampede is
     made *hard*.
   - **(b) CONTEXT before judgment.** A `flag` (the one judgment-shaped signal — a concern about an
     **artifact**) with **no attached context** is **damped**, never sensed bare (`damped_no_context`).
     A bare condemnation cannot propagate; only a flag that carries its reasons survives.
   - **(d) ZERO global broadcast.** A trace whose `cell_id` is not the sensing cell is **dropped**
     (`dropped_off_cell`). Propagation is confined to the cell / Dunbar neighborhood (invariant 4);
     there is no global timeline.

4. **Cell-scoped, caller-supplied, scanned-and-discarded (invariants 4/6).** The trace-field is
   **supplied by the caller**, scanned, sensed, and **discarded**; nothing is persisted across calls;
   there is no central holder. The function is **byte-deterministic** for identical input.

## Senses, never acts (protocol, not an agent)
`sense()` **surfaces** the throttled, evaporated traces visible from one cell. It **connects nothing,
notifies no one, ranks no person, and persists nothing.** It is a protocol read of the shared
environment with the breakers applied; humans in the cell act on what they sense.

## Time model (why integer ticks, not ISO strings)
Unlike Capa 1/2/3 (which only *compare* `expires_at` lexicographically), evaporation requires
**elapsed-time arithmetic** (`now − created_at`). So Capa 5 uses **integer logical ticks** for `now`
and `created_at` (epoch seconds, round numbers, or any monotone integer clock the caller supplies).
This keeps the module **pure, stdlib-only, and byte-deterministic** with no `datetime` dependency.
Capa 6, which needs no arithmetic, keeps the family's ISO-string convention.

## Input (one sensing request, JSON)
```json
{
  "cell_id": "str (non-empty) — the sensing cell / Dunbar neighborhood (invariant 4)",
  "now": "int — logical tick (monotone integer clock); evaluation time",
  "window": "int > 0 — the velocity window in ticks (friction/velocity breaker)",
  "velocity_cap": "int > 0 — max traces per artifact that may land within the window",
  "half_life": "int > 0 — evaporation half-life in ticks (pheromone decay)",
  "min_strength": "number >= 0 — evaporation floor; evaporated strength below it is dropped",
  "traces": [
    {
      "about": "str (non-empty) — an ARTIFACT / PATH / CONTRIBUTION token, NEVER a person aggregate",
      "signal": "one of contribution | path | endorsement | presence | flag (whitelist)",
      "strength": "number > 0 — the trace's deposited strength before evaporation",
      "created_at": "int — the tick the trace was deposited",
      "cell_id": "str (non-empty) — MUST equal the request cell_id to be sensed (no broadcast)",
      "context": "str | null — REQUIRED (non-empty) when signal is a judgment signal (flag)"
    }
  ]
}
```
- **Trace keys are whitelisted** (`about`/`signal`/`strength`/`created_at`/`cell_id`/`context`). Any
  other key on a trace is **refused** (raise) — there is no field through which a person-scalar,
  an engagement counter, or a ban could enter.
- `signal` must be one of the **five whitelisted environmental kinds**; a `ban`/`distrust`/`condemn`
  signal is **not representable** (invariant 3, positive-sum).
- `about` is an **artifact/path** token. The module never treats it as a person and never emits a
  scalar of a person.

## Output (the throttled, evaporated sense, JSON) — always returns
```json
{
  "cell_id": "barrio-1",
  "now": 1000,
  "sensed": [
    {
      "about": "wiki:article-42",
      "signal": "contribution",
      "cell_id": "barrio-1",
      "effective_strength": 3.535534,
      "context": null
    }
  ],
  "verdict": "signals_sensed",
  "note": "Traces sensed from your cell, evaporating and throttled; absence is quiet, never a mark.",
  "audit_trace": {
    "rule": "environmental traces only; evaporation by half-life; cell-scoped; context-before-judgment; velocity-capped per window; no person-scalar",
    "considered_traces": 6,
    "dropped_off_cell": 1,
    "dropped_future": 0,
    "damped_no_context": 1,
    "damped_velocity": 2,
    "evaporated": 1,
    "sensed": 1,
    "window": 100,
    "velocity_cap": 3,
    "half_life": 50,
    "min_strength": 0.5
  }
}
```
- `verdict` is categorical: `signals_sensed` (≥1 sensed) or `quiet_from_your_cell` (none). **Never a
  number that scores a person.** Absence is "nothing propagating in your cell right now," never a mark
  (whitelist-not-blacklist, invariant 3).
- `effective_strength` is the **evaporated strength of an ARTIFACT trace**, not a person-scalar. It is
  a property of a path/contribution, not an aggregate rating of anyone.
- The `sensed` list is **canonically sorted** `(about, signal, −effective_strength, str(context))` —
  a deterministic environmental read, explicitly *not* a ranking of people.

## Algorithm (deterministic)
1. **Validate envelope** (reject, do not repair): `cell_id` non-empty str; `now` int; `window`,
   `velocity_cap`, `half_life` int `> 0`; `min_strength` number `>= 0`; `traces` a list of
   well-formed trace dicts with **whitelisted keys only** (unknown key → refuse), `about` non-empty
   str, `signal` in the whitelist, `strength` number `> 0`, `created_at` int, `cell_id` non-empty
   str, `context` str/None. Reject `bool` where an `int`/number is required.
2. **Surveillance scan (whole request, recursive):** any key (case-insensitive substring) matching a
   `FORBIDDEN_KEY` at any depth → **refuse** (`StigmergyBreachError`). Same taxonomy as Capa 1/2/3/4,
   verbatim.
3. **Per-trace damping (drop-and-count, never raise):**
   - `cell_id ≠` request `cell_id` → drop (`dropped_off_cell`) — **zero global broadcast, wall 3(d)**.
   - `created_at > now` (future trace) → drop (`dropped_future`).
   - `signal ∈ {flag}` and `context` empty/None → drop (`damped_no_context`) — **context before
     judgment, wall 3(b)**.
4. **Velocity throttle (friction / velocity-limit, walls 3(a)/(c)):** among the survivors that are
   **in-window** (`now − window ≤ created_at ≤ now`), group by `about`; if a group exceeds
   `velocity_cap`, sort it by `(created_at, about, signal, strength)`, keep the first `velocity_cap`,
   and **damp** the rest (`damped_velocity`). Survivors **older than the window** are not
   velocity-throttled (they are not part of a current burst) but still face evaporation.
5. **Evaporation (pheromone decay, wall 2):** for each velocity-surviving trace,
   `elapsed = now − created_at` (`≥ 0` here); `effective = round(strength · 0.5^(elapsed/half_life), 6)`;
   if `effective < min_strength` → drop (`evaporated`); else **sense** it as
   `{about, signal, cell_id, effective_strength, context}`.
6. **Canonical sort** the sensed list by `(about, signal, −effective_strength, str(context))`.
7. **Assemble output.** `verdict = signals_sensed` if ≥1 sensed else `quiet_from_your_cell`; attach the
   audit trace with all counts and the breaker parameters. **Persist nothing.**

## Determinism
Pure and deterministic: given the same request it produces **byte-identical** JSON (fixed taxonomy +
integer-tick arithmetic + `round(...,6)` + canonical sort + deterministic throttle tie-breaks). No
clock, no randomness, no I/O.

## Termination & cost
Bounded: O(traces) validation and damping, O(groups · gsize·log gsize) throttle sort, O(traces)
evaporation, one final sort. No unbounded loops.

## Meaning layer (Axiom 6 — what the agent cannot infer)
- **The coordinator IS the stampede engine (brief §4 Capa 5, §5, §6).** Stigmergy is not "good
  coordination with an occasional bug"; the *same* trace-in-the-environment mechanism that lets a
  colony build without a commander is what makes it march in a death spiral. So the breakers are not
  an add-on policy — they are the **shape of the mechanism**: friction (velocity cap), context (flag
  needs its reasons), locality (cell scope), and forgetting (evaporation) are what make the
  coordinating read *not* a virality engine. The correct behavior on a mob/cascade input is to
  **throttle the stampede** — damping is the feature, not a failure.
- **Evaporation is the anti-dossier and the anti-death-spiral at once.** A trace that never fades is
  a permanent record (inverts invariant 5) *and* a signal that can accumulate without bound into a
  runaway. Decay solves both: the environment forgets natively, and no signal can compound forever.
- **No person-scalar, still (invariant 2).** `effective_strength` is a property of an *artifact
  trace*. There is no field that aggregates a person; a `score`/`reputation`/`blacklist` trace is
  refused at the door, and no `ban`/`distrust` signal is even representable (invariant 3).
- **Senses, never acts.** The output surfaces the throttled environment; humans in the cell act. There
  is no auto-amplify, no notification optimizer, no broadcast.
- **Reversibility:** `sense()` is a **two-way door** (pure, no side effects, no persistence) → it may
  run autonomously to *surface*. It never crosses into an irreversible action.

## Flagged, NOT fake-resolved (brief §6)
- **The ant-mill / cascade is the obligatory dark side of stigmergy (§6).** The breaker makes a
  stampede **hard, not impossible**: a determined, coordinated mob acting *outside* this function —
  many real cells, many real ticks, coordinated off-protocol — still can. The velocity cap throttles
  a burst *per artifact per window in one cell*; it cannot foreclose a slow, distributed,
  human-coordinated campaign. **Who governs, and for what, decides** (mirror Capa-2/1/3 ST5). Flagged,
  not coded away.
- **Substring over-refusal in the surveillance scan** (`ban` in `bandwidth`) is inherited from Capa
  1/2/3 ST1: the taxonomy is a shape heuristic **biased to over-refuse** — a false refusal is safe, a
  false admit is a surveillance leak. Kept verbatim.
- **Evaporation parameters are a governance choice.** `half_life`, `velocity_cap`, and `window` are
  supplied by the caller; the function enforces them deterministically but does not decide them.
  Bad parameters (a huge cap, an infinite half-life) weaken the breakers — that is a governance
  matter, flagged, not coded.

## Relationship to Capa 1, 2, 3, and 4 (reuse, not duplication)
- Reuses the **exact** `FORBIDDEN_KEY` taxonomy of Capa 1/2/3/4 (one anti-surveillance definition, not
  five). AC-X regression-checks that a Capa-1 surveillance-shaped payload fed as a Capa-5 trace is
  refused identically, and that `stigmergy.FORBIDDEN_KEYS` equals the set in every sibling module.
- Traces are **cell-scoped** exactly as a Capa-1 interaction, a Capa-2 vouch, a Capa-3 candidate, and a
  Capa-4 campaign are; local-bounded visibility (invariant 4) is one idea across the stack.
- Forgetting is native, as everywhere — but here it is the **evaporation mechanism itself**, not an
  `expires_at` stamp.

## Out of scope (explicitly NOT this component)
- **Any score/rank/reputation of a person** — none; `about` is an artifact, `effective_strength` is a
  trace property. Emitting a person-scalar is the whole antipattern.
- **A ban / distrust / condemnation of a person** — unrepresentable (signal whitelist + FORBIDDEN
  scan, invariant 3). A `flag` targets an artifact and needs context; it never marks a person.
- **Acting: amplifying, notifying, broadcasting, connecting, persisting** — `sense()` surfaces; humans
  act. No global feed, no timeline.
- **Cross-cell propagation / a global environment** — traces stay within the sensing cell (invariant
  4); there is no merge into one global trace-field.
- **Foreclosing a determined off-protocol mob (§6), or choosing the breaker parameters** — the breaker
  throttles per-artifact-per-window-per-cell and enforces caller parameters; whether the parameters
  and governance are sound is **flagged, not solved**.
