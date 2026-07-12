# Constraint Architecture — Capa 5 Stigmergic Coordination + Anti-Cascade Breakers

> Produced by author-constraints. Each rule carries a "because" clause (AGD-029).
> Sibling of the Capa-4 / Capa-1 / Capa-2 / Capa-3 `constraints.md`; the anti-surveillance rules are
> deliberately identical. This layer is **DETERMINISTIC, not an LLM** — the constraints ARE the
> mechanism (friction, context, locality, forgetting), not a policy wrapped around a model.

## MUSTs
- **M1** Treat every trace as **environmental**: `about` is an artifact/path/contribution token, never
  a person aggregate — *because* stigmergy coordinates via traces in the *environment*, and a trace
  that aggregates a person is the surveillance scalar (invariants 2/3).
- **M2** Scan the exact Capa-1/2/3/4 `FORBIDDEN_KEY` taxonomy over the whole request and **refuse**
  (raise) any match at any depth — *because* a `score`/`rank`/`reputation`/`blacklist` trace must be
  refused, not stored (invariant 2). Same taxonomy, verbatim, across five layers.
- **M3** Whitelist the `signal` field to environmental/positive kinds
  (`contribution`/`path`/`endorsement`/`presence`/`flag`) and whitelist trace keys — *because* a
  `ban`/`distrust`/`condemn` signal, or a field carrying a scalar/engagement counter, must be
  **unrepresentable** (invariant 3, positive-sum). Any non-whitelisted signal or key → refuse.
- **M4** Make **evaporation** the forgetting mechanism: `effective = strength · 0.5^(elapsed/half_life)`;
  drop any trace whose evaporated strength `< min_strength` before sensing — *because* forgetting is
  native and load-bearing here, and an un-fading trace is both a permanent dossier (inverts inv. 5)
  and a runaway signal.
- **M5** Enforce the **velocity cap** (friction / velocity-limit): per `about`, at most `velocity_cap`
  in-window traces survive; the earliest `velocity_cap` are kept, the rest **damped** — *because* a
  signal must not amplify instantly; a burst is throttled deterministically (invariant 9, walls a/c).
- **M6** Enforce **context-before-judgment**: a `flag` (judgment-shaped signal, about an artifact) with
  no context is **damped**, never sensed bare — *because* a condemnation/pile-on with no attached
  context must not propagate (invariant 9, wall b).
- **M7** Enforce **cell scope**: drop any trace whose `cell_id` ≠ the sensing cell — *because*
  propagation is confined to the Dunbar neighborhood; there is **zero global broadcast** (invariants
  4/9, wall d).
- **M8** Be **pure over caller-supplied local state**: scan the trace-field, sense, and **discard**;
  persist nothing across calls — *because* there is no central holder of the trace graph (invariant 6)
  and no dossier (invariant 5).
- **M9** Be **byte-deterministic** for identical input (fixed taxonomy, integer-tick arithmetic,
  `round(...,6)`, canonical sort, deterministic throttle tie-breaks) — *because* an auditable sense
  that is non-reproducible cannot be audited (mirrors Capa-4/1/2/3 M9).
- **M10** Emit an auditable `audit_trace` (rule + every drop/damp/sense count + the breaker
  parameters) — *because* the breakers must be **inspectable**: a caller must be able to see that a
  burst was throttled and why.
- **M11** Distinguish **raise vs. damp**: envelope/type/whitelist/`FORBIDDEN` breaches **raise**;
  cascade-shaped content (off-cell, future, bare flag, over-cap, evaporated) is **dropped-and-counted**
  — *because* a malformed request is an integrity error, but throttling a stampede is the *normal,
  correct* runtime behavior and must never crash.

## MUST-NOTs
- **N1** No **acting**: no amplify, notify, broadcast, connect, or persist — *because* it is a
  protocol read of the environment; it **senses, humans act** (architecture.md: not an agent).
- **N2** No score/rating/ranking/reputation of a **person** in the output — *because* no global scalar
  (invariant 2). `effective_strength` is an artifact-trace property, never a person aggregate.
- **N3** No `ban`/`distrust`/`condemn` **signal**, and no blacklist/penalty key — *because* reputation
  opens doors, it cannot easily close them (invariant 3); the exclusion shape is unrepresentable.
- **N4** No **LLM, no injected model, no network client, no stochastic core** — *because* Capa 5 is
  `[PROTOCOLO + CIRCUIT BREAKERS]`, deterministic by nature; this is the whole difference from Capa 3.
- **N5** No **stripping** of a surveillance-shaped request (remove the key, answer anyway) — **refuse
  the whole request** — *because* answering over a silently-cleaned dossier-shaped input launders it
  (mirrors Capa-1/2/3 N5).
- **N6** No stored trace history, no cross-call state, no central trace-field, no global environment —
  *because* no central holder (invariant 6), no permanent dossier (invariant 5), no throne.
- **N7** No **global broadcast / cross-cell propagation**; traces stay within the sensing cell —
  *because* local-bounded visibility, never global (invariant 4; the platform's global-timeline
  original sin is what turns a flock into a stampede).
- **N8** No **silent failure on the envelope**: on any validation error or `FORBIDDEN` breach in the
  request, **raise** and surface. (Cascade-shaped *content*, by contrast, is damped-and-counted — the
  breaker must not be crashable by a mob.)
- **N9** No **un-fading trace**: a trace with no evaporation (infinite half-life is a caller
  parameter, but the mechanism must always apply decay) — *because* the death spiral and the dossier
  are the same failure of never-forgetting.

## PREFERENCES
- **P1** Prefer **stdlib-only, no imports at all** for auditability; `hypothesis` only in tests.
- **P2** Share the exact `FORBIDDEN_KEY` taxonomy with Capa 1/2/3/4 (one anti-surveillance definition,
  not five).
- **P3** Prefer property-based tests: no forbidden key ever survives into output; a cascade/mob input
  is always throttled below `velocity_cap` per artifact; an evaporated trace never surfaces; an
  off-cell trace never surfaces; the sensed order is canonical (never a people-ranking).

## ESCALATION TRIGGERS (reject + surface)
- **E1** Request (any depth) contains a `FORBIDDEN` surveillance-shaped key → **refuse** (invariants
  2/6).
- **E2** `cell_id` empty; `now` not int; `window`/`velocity_cap`/`half_life` not int>0; `min_strength`
  negative/not-number; a trace with an unknown (non-whitelisted) key; a `signal` not in the whitelist;
  `strength` not a number>0; `created_at` not int → **refuse** (M1/M3/M11).
- **E3** Malformed envelope (`traces` wrong type, a trace not a dict, `about`/`cell_id` empty) →
  reject, do not repair.

## Reversibility framing
- `sense()` is a **two-way door** (pure, no side effects, no persistence) → fully autonomous to
  *surface* the throttled environment. Acting on what is sensed is the **human's** step.

## Constraint × Execution-Mode matrix
| ID | Sense (Live) | Simulation/Backtest | Notes |
|----|--------------|---------------------|-------|
| M2 forbidden scan | Refuse | Refuse | the surveillance shape; never relax |
| M3 signal whitelist | Refuse | Refuse | no ban/distrust signal; positive-sum |
| M4 evaporation | Enforce (drop) | Enforce | forgetting is the mechanism |
| M5 velocity cap | Enforce (damp) | Enforce | friction/velocity breaker; the stampede throttle |
| M6 context-before-judgment | Enforce (damp) | Enforce | no bare condemnation |
| M7 cell scope | Enforce (drop) | Enforce | zero global broadcast |
| N1 no acting | Enforce | Enforce | senses, humans act |
| N4 no LLM | Enforce | Enforce | deterministic; the difference from Capa 3 |
</content>
