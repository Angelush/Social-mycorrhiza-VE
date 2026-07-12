# Acceptance Criteria — Capa 5 Stigmergic Coordination + Anti-Cascade Breakers

> Produced by design-evals. Binary Done (AGD-028): verify the artifact, not a self-report.
> Every AC is machine-executable with zero human judgement. The component is **deterministic** (no
> LLM, no stub). The defining test is **AC4**: a mob/cascade input is structurally throttled to the
> velocity cap AND a blacklist/score trace is refused in every cell.

- **AC1 — A valid in-cell, unexpired (un-evaporated) trace is sensed.** Given a `contribution` trace
  `about="wiki:art-42"` in the sensing `cell_id`, `created_at` recent enough that
  `strength·0.5^(elapsed/half_life) >= min_strength`, `sense()` returns
  `verdict == "signals_sensed"` with exactly one sensed entry carrying `about`, `signal`, the
  `cell_id`, an `effective_strength` (a number), and `context`. Pass/fail: field equality.
  (Targets M1; invariants 4/5.)

- **AC2 — Senses, never acts / no person-scalar surface.** The module exposes **no** function that
  amplifies, notifies, broadcasts, connects, or persists (static: only `sense(request)` + helpers +
  `FORBIDDEN_KEYS`), and the output contains **no** action field and **no** field that scores/ranks a
  person (a recursive key scan finds zero `FORBIDDEN_KEYS`; `effective_strength` is an artifact-trace
  property). Pass/fail: static surface + output key scan. (Targets N1/N2, invariant 2.)

- **AC3 — No ban/distrust signal is representable (invariant 3, positive-sum).** (a) A trace with
  `signal="ban"` (or any signal outside `contribution|path|endorsement|presence|flag`) is **refused**
  (`StigmergyBreachError`). (b) A trace carrying a `blacklist`/`penalty`/`distrust` key at any depth
  is **refused**. Pass/fail: rejection. (Targets M3/N3, invariant 3, F3.)

- **AC4 — A mob/cascade is structurally throttled (invariant 9). THE defining test.** Given
  `velocity_cap = k` and `window = w`, and `n > k` traces about the **same** `about` all landing
  in-window, `sense()` senses **at most `k`** for that artifact and counts `damped_velocity >= n − k`.
  The kept `k` are the earliest by `(created_at, about, signal, strength)`. This is the case where
  "correct" = *throttling the stampede*. Pass/fail: per-artifact sensed count `<= k` + damp count.
  (Targets M5, invariant 9 walls a/c, F1.)

- **AC5 — No person-scalar out; surveillance shape refused (the razor at the breaker).** (a) For every
  sensed entry, a recursive key scan finds **zero** `FORBIDDEN_KEYS`
  (`score|rating|reputation|rank|blacklist|ban|penalty|global_id|dni`) and there is **no field that
  scores/ranks a person**. (b) A request carrying a `FORBIDDEN_KEY` at any depth (e.g. a trace with
  `"reputation": 88`) is **refused**. Pass/fail: key-scan + rejection. (Targets M2/N2/N5, invariant 2,
  F2.)

- **AC6 — Context before judgment (invariant 9, wall b).** A `flag` trace with `context` absent, `None`,
  or empty is **damped** (`damped_no_context >= 1`) and never sensed; the identical `flag` trace with a
  non-empty `context` is sensed. Pass/fail: damp count + verdict flip. (Targets M6, invariant 9, F4.)

- **AC7 — Zero global broadcast / cell scope (invariant 4).** A trace whose `cell_id` ≠ the sensing
  `cell_id` is **dropped** (`dropped_off_cell >= 1`) and never sensed, even though it is otherwise
  valid. Pass/fail: proposal absent + drop counted. (Targets M7/N7, invariant 4, wall d, F5.)

- **AC8 — Forgetting: evaporation drops faded traces; verdict flips on age alone.** (a) A trace old
  enough that `round(strength·0.5^(elapsed/half_life),6) < min_strength` is **not sensed**
  (`evaporated >= 1`); the identical trace with a recent `created_at` **is** sensed — the verdict flips
  on age alone. (b) `effective_strength` strictly decreases as `created_at` recedes from `now`.
  Pass/fail: verdict flip + monotonicity. (Targets M4/N9, invariant 5, F6.)

- **AC9 — Canonical order (not a people-ranking).** With several sensed traces, the emitted `sensed`
  list is sorted by `(about, signal, −effective_strength, str(context))`, byte-identical regardless of
  the input trace order. Pass/fail: `json.dumps` equality across a shuffled input. (Targets M9/P3.)

- **AC10 — Damping is drop-and-count, never a crash; raise is only for the envelope.** A request mixing,
  in one `traces` list: an off-cell trace, a future trace, a bare `flag`, an over-cap burst, and an
  evaporated trace, together with **one** valid trace → `sense()` returns normally (no raise) with the
  one valid trace sensed and each drop/damp category counted. A request with a `FORBIDDEN` key or a
  non-whitelisted signal/key **raises**. Pass/fail: no exception on content + counts; exception on
  shape. (Targets M11/N8, F7.)

- **AC11 — Determinism.** Running `sense()` twice on the same request yields byte-identical JSON
  (`json.dumps(out, sort_keys=True)`). Pass/fail: string equality. (Targets M9, F9.)

- **AC12 — Envelope validation.** Empty `cell_id`; `now` not int; `window`/`velocity_cap`/`half_life`
  not `int > 0`; `min_strength` negative or not a number; `traces` not a list; a trace not a dict; a
  trace with an unknown (non-whitelisted) key; `signal` not in the whitelist; `strength` not a number
  `> 0`; `created_at` not int; a `bool` where an int/number is required → each **refused** (not
  repaired). Pass/fail: exception raised. (Targets E2/E3/N8.)

- **AC13 — No LLM / no network / stdlib-only, importable offline.** Importing
  `src/stigmergy/stigmergy.py` succeeds with **no** `anthropic`/network dependency; a static check
  finds **no** import of `anthropic`, `requests`, `httpx`, `openai`, `urllib`, or `socket`, and **no**
  injected `propose`/model parameter on `sense`. Pass/fail: import + static scan. (Targets N4 — the
  whole difference from Capa 3.)

## Consistency with Capa 1, 2, 3, and 4
- **AC-X — Shared surveillance taxonomy is honored across all five layers.** Feeding a Capa-1
  surveillance-shaped payload (e.g. a trace `{"about":"x", ... , "reputation": 88}` or nested
  `{"seller":{"trust_score":88}}`) into `sense()` **refuses** it — the same verdict Capa 1's membrane,
  Capa 2's query, Capa 3's matcher, and Capa 4's engine reach independently on that shape.
  Additionally, `stigmergy.FORBIDDEN_KEYS == membrane.FORBIDDEN_KEYS == legibility.FORBIDDEN_KEYS ==
  matcher.FORBIDDEN_KEYS`. Pass/fail: all refuse + set equality. (Targets P2, F10.)
</content>
