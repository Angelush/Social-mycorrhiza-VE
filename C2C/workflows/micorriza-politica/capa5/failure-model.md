# Failure Model + Stress Report — Capa 5 Stigmergic Coordination + Anti-Cascade Breakers

> Produced by red-team. Hostile review of the Capa-5 spec. The failure mode here is not a dead
> network — it is the **ant mill**: the coordinating mechanism running away into a death spiral, an
> information cascade, or a mob (brief §4 Capa 5, §5 "molino de hormigas", invariant 9). The same
> traces that build the nest march the colony off the cliff.

## Failure modes (F#)
- **F1 — The stampede / ant mill (invariant 9, the gravitational pull).** A trace amplifies instantly:
  one signal about an artifact triggers a burst of copies, which triggers more, a runaway cascade —
  the death spiral. *Mitigation:* M5; the **velocity cap** throttles in-window traces per artifact to
  `velocity_cap` (friction/velocity-limit), and **evaporation** (M4) prevents unbounded accumulation.
  AC4 feeds a mob (many rapid traces for one artifact) and asserts it is throttled to the cap. **This
  is the gravity, not a solved problem — flagged: a determined off-protocol mob across many cells/ticks
  still can (§6); who governs decides.**
- **F2 — The person-scalar trace.** A trace arrives shaped as `{"about":"t7","reputation":88}` or the
  output "summarizes" traces into a person rating → the social-credit scalar reappears at Capa 5
  (inverts invariant 2). *Mitigation:* M2/N2; the `FORBIDDEN_KEY` scan refuses such a request, and the
  output has **no** field that scores a person (`effective_strength` is an artifact-trace property).
  AC2/AC5 scan for it.
- **F3 — The ban / distrust trace (inverts invariant 3).** A trace tries to encode "this person is
  bad" — a `signal: "ban"`, a `distrust` field. *Mitigation:* M3/N3; the `signal` is **whitelisted**
  to positive/environmental kinds and the `FORBIDDEN_KEY` scan refuses `ban`/`blacklist`/`penalty`
  keys. There is **no representable distrust signal**. AC3.
- **F4 — Bare condemnation / context-free pile-on (invariant 9, wall b).** A `flag` about an artifact
  arrives with no reasons, ready to be amplified into a mob. *Mitigation:* M6; a `flag` with no
  `context` is **damped** (`damped_no_context`), never sensed bare — context before judgment. AC6.
- **F5 — Global broadcast / cross-cell leak (inverts invariant 4).** A trace from another cell is
  sensed, so a signal propagates globally → the flock becomes a stampede (the platform original sin).
  *Mitigation:* M7/N7; a trace whose `cell_id` ≠ the sensing cell is **dropped** (`dropped_off_cell`).
  Propagation is confined to the Dunbar neighborhood. AC7.
- **F6 — The un-fading trace / permanent dossier (inverts invariants 5/6).** A trace never decays, so
  the environment accumulates a permanent record and old signals compound forever. *Mitigation:* M4/N9;
  **evaporation always applies** and traces below `min_strength` are dropped before sensing. AC8 flips
  the verdict on age/evaporation alone.
- **F7 — Repair-instead-of-refuse on input; strip-instead-of-drop.** Code strips a `reputation` key
  from a trace and senses anyway. *Mitigation:* N5/N8; the request is **refused** (raise) on any
  `FORBIDDEN`/whitelist/envelope breach. (Cascade-shaped content is *damped whole*, never
  stripped-and-kept.)
- **F8 — Velocity cap starves legitimate coordination.** The cap throttles a real, healthy burst of
  contributions (a wiki article getting justified attention) as if it were a mob. *Decision:* this is
  the **deliberate trade** — friction is the point; a false throttle is safe (the trace re-lands next
  window / older traces still sense), a false pass is a cascade leak. The cap/window/half_life are
  **caller-supplied governance parameters** (flagged), tuned per cell, not decided by the function.
- **F9 — Determinism drift via floats.** `0.5^(elapsed/half_life)` differs across runs/platforms.
  *Mitigation:* M9; identical integer inputs → identical floats in CPython, and `effective` is
  `round(...,6)` before compare/emit, so the output is byte-identical. AC11.
- **F10 — Taxonomy drift from Capa 1/2/3/4.** Capa 5 keeps a separate forbidden-key list that diverges
  → the five layers disagree on the surveillance shape (AC-X breaks). *Mitigation:* P2; share the exact
  `FORBIDDEN_KEY` set; AC-X regression-checks agreement across all five layers.
- **F11 — Off-protocol coordinated mob (§6, the real limit).** A determined attacker coordinates a
  pile-on across many real cells and many real ticks, each within-cap, so the per-artifact-per-window
  breaker never trips. *Mitigation (partial):* the breaker throttles a *burst in one cell*; it cannot
  foreclose a slow distributed human campaign. **Flagged, NOT solved:** who governs and for what
  decides (mirror Capa-2/1/3 ST5). Structure makes it hard, not impossible.

## Stress findings (ST#)
- **ST1 — Substring false positives in the scan.** `"bandwidth"` contains `ban`; `"scoreboard-path"`
  contains `score`. **Decision (inherited from Capa 1/2/3 ST1):** the taxonomy is a shape heuristic
  **biased to over-refuse** — a false refusal is safe (the caller re-labels a field), a false admit is
  a surveillance leak. Keep the shared `FORBIDDEN_KEY` set verbatim. Test `ban`/`score` (must trip) and
  a clean trace (must not trip).
- **ST2 — Empty / all-damped trace list.** `traces=[]`, or all dropped/evaporated → valid;
  `quiet_from_your_cell` (the quiet state), never an error. AC tolerates it.
- **ST3 — In-window boundary.** A trace at exactly `created_at == now − window` is in-window; at
  `created_at == now` it is in-window (elapsed 0, evaporation factor 1.0). Document the closed interval
  `[now − window, now]`. Test the boundary.
- **ST4 — Self-confirmation.** The module's own damping agrees with its own bug. *Mitigation:* an
  **independent** hand-written oracle (separate from the module) re-derives the throttled/evaporated
  survivor set in tests (tests.md cross-check, AGD-045).
- **ST5 — Auditability vs. forgetting / no-storage (open §6).** The sensed set is auditable yet must
  not become a permanent record. *Partial mitigation:* the function is pure and stores nothing;
  evaporation fades traces natively. **Flagged:** enforcing that the *caller* does not persist and
  correlate sensed sets is outside this pure function (mirrors Capa-4/1/2/3 ST5).
- **ST6 — Velocity tie-breaks.** Two in-window traces for one artifact with the same `created_at` — the
  throttle must be deterministic. *Decision:* sort the group by `(created_at, about, signal, strength)`
  and keep the first `velocity_cap`; ties broken by `(signal, strength)`. Documented and tested.
- **ST7 — Future / negative time.** `created_at > now` (future trace) → dropped (`dropped_future`), not
  a negative-elapsed evaporation. `now`/`created_at` are integer ticks (ST-inherited from Capa 2/3's
  time normalization, but numeric here for arithmetic). Test a future trace.
- **ST8 — `flag` about a person.** A caller could put a person token in a `flag`'s `about`. *Decision:*
  the function cannot know a token is "a person" vs "an artifact" — `about` is opaque. The structural
  guards are: `flag` needs context (M6), no person-scalar can attach (M2), no ban signal exists (M3),
  and it is cell-local (M7). Whether a caller misuses `about` semantically is a **governance/curation**
  matter, flagged — the same opaque-token stance as Capa 2/3/4.

## Open (system-level, NOT this breaker) — do not fake-resolve (§6)
- **The ant-mill/cascade is the obligatory dark side of stigmergy (§6, invariant 9).** The breaker
  makes a stampede **hard, not impossible.** A coordinated mob acting *outside* the function — across
  many cells, many ticks, each within-cap — still can. Structure makes it hard; *who governs and for
  what* decides. **Stakes: a mob/death-spiral, not just a failure.** Flagged (F1/F11).
- **The breaker parameters are a governance choice.** `half_life`, `velocity_cap`, `window`,
  `min_strength` are caller-supplied. A malign or careless governor who sets an infinite half-life or a
  huge cap weakens the breakers. The function enforces the parameters deterministically; it does not
  choose them. Flagged (F8).
- **Sybil / token↔person binding (§6.2).** `about` tokens are opaque and trusted as given; a Sybil can
  deposit traces from throwaway artifact tokens. Not detected here (as in Capa 2/3/4). Flagged.
- **Semantic misuse of `about` (a person token in an artifact field).** The function guards the shape,
  not the semantics; whether `about` names a genuine artifact is curation/governance. Flagged (ST8).
</content>
