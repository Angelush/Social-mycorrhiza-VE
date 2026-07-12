# Test Cases — Capa 5 Stigmergic Coordination + Anti-Cascade Breakers

> Produced by design-evals. Each: input, expected result, verification rule. The component is
> **deterministic** — no stub model, no network. `now`/`created_at`/`window`/`half_life` are integer
> logical ticks; `strength`/`min_strength` are numbers. Tokens (`about`, `cell_id`) are opaque strings.

## Builders
- `_trace(about, signal="contribution", strength=8, created_at=NOW, cell="barrio-1", context=None)`.
- `_req(traces, cell="barrio-1", now=NOW, window=100, velocity_cap=3, half_life=50, min_strength=0.5)`.
- `NOW = 1000`. A trace at `created_at = NOW` has `elapsed 0` → `effective == strength`.

## Test A — Normal: a valid trace is sensed (AC1)
- **A1:** one `contribution` about `wiki:art-42`, `created_at=NOW`, `strength=8` → `verdict=
  "signals_sensed"`, one sensed entry, `about="wiki:art-42"`, `cell_id="barrio-1"`,
  `effective_strength==8.0` (elapsed 0), `context` echoed.
- **A2 quiet:** `traces=[]` → `verdict="quiet_from_your_cell"`, `sensed==[]` (bootstrapping/quiet
  state, not an error).
- **Verify:** AC1, AC5a, AC11, ST2.

## Test B — Senses, never acts / no scalar (AC2)
- **B1 (static surface):** the module exposes exactly `sense` (+ helpers/`FORBIDDEN_KEYS`); assert no
  `amplify`/`notify`/`broadcast`/`connect`/`persist`/`rank` public function.
- **B2 (output scan):** scan every key of the output — no action field, no `FORBIDDEN_KEYS`.
- **Verify:** AC2.

## Test C — No ban/distrust signal (AC3, invariant 3)
- **C1 (ban signal):** a trace `signal="ban"` → **refused**.
- **C2 (unknown signal):** `signal="condemn"` → **refused** (not in whitelist).
- **C3 (blacklist key):** a trace with a `blacklist` key at depth → **refused**.
- **Verify:** AC3 — the exclusion shape is unrepresentable.

## Test D — THE mob/cascade throttle (AC4, invariant 9) — the defining test
- **D1:** `velocity_cap=3`, `window=100`; **seven** traces all `about="hot-thread"`, all in-window
  (`created_at` in `[NOW-100, NOW]`), each `strength` high enough to survive evaporation → **exactly 3
  sensed** for `hot-thread`, `damped_velocity == 4`. The 3 kept are the earliest by
  `(created_at, about, signal, strength)`.
- **D2 (two artifacts):** a burst of 5 about `A` and 2 about `B`, `cap=3` → 3 sensed for `A`
  (`damped_velocity==2`), 2 sensed for `B` (no damp). The cap is **per artifact**.
- **D3 (spread across time, not a burst):** 5 traces about `A` but spread so only 3 fall in-window →
  the 2 older-than-window are not velocity-throttled (they face only evaporation).
- **Verify:** AC4 — a stampede is throttled to the cap, deterministically, per artifact.

## Test E — No scalar out; surveillance refused (AC5)
- **E1 (verdict scan):** for A1, recursive key scan of every sensed entry finds **zero** `FORBIDDEN`
  keys and no person-scoring number.
- **E2 (request-level surveillance):** a trace with `"reputation": 88` → **refused**.
- **E3 (nested):** a trace with `context` a string but a sibling `{"meta":{"trust_score":1}}` … (note:
  non-whitelisted key `meta` also trips the whitelist) → **refused**.
- **Verify:** AC5 (a,b).

## Test F — Context before judgment (AC6, invariant 9 wall b)
- **F1 (bare flag):** a `flag` about `art-9` with `context=None` → **damped**, not sensed,
  `damped_no_context>=1`, `verdict="quiet_from_your_cell"` (if it was the only trace).
- **F2 (flag with context):** identical `flag` with `context="duplicate of art-3, see talk page"` →
  **sensed**. Verdict flips on context alone.
- **F3 (empty string context):** `context=""` on a flag → **damped**.
- **Verify:** AC6.

## Test G — Zero global broadcast / cell scope (AC7, invariant 4)
- **G1:** a trace `cell_id="otro-barrio"`, sensing `cell_id="barrio-1"` → **dropped**,
  `dropped_off_cell>=1`, not sensed.
- **G2:** two traces, one in-cell one off-cell → only the in-cell one sensed.
- **Verify:** AC7 — no cross-cell propagation.

## Test H — Forgetting / evaporation (AC8, invariant 5)
- **H1 (evaporated):** `half_life=50`, `min_strength=0.5`, `strength=8`, `created_at=NOW-300`
  → `effective = 8·0.5^6 = 0.125 < 0.5` → **not sensed**, `evaporated>=1`.
- **H2 (fresh):** identical trace `created_at=NOW-50` → `effective = 8·0.5^1 = 4.0 >= 0.5` → **sensed**.
  Verdict flips on age alone.
- **H3 (monotone decay):** for `created_at ∈ {NOW, NOW-50, NOW-100}`, `effective_strength` is strictly
  decreasing (`8.0 > 4.0 > 2.0`).
- **Verify:** AC8.

## Test I — Canonical order (AC9)
- **I:** three sensed traces about `c`,`a`,`b` in shuffled input order → emitted `sensed` sorted by
  `(about, signal, −effective_strength, str(context))`; byte-identical across two shuffles.
- **Verify:** AC9 — a deterministic environmental read, not a people-ranking.

## Test J — Adversarial mixed damping, never a crash (AC10) — the wrapper-correctness analogue
- **J:** one valid trace `good` (in-cell, recent, strong) plus: an off-cell trace, a future trace
  (`created_at=NOW+10`), a bare `flag`, a 5-deep burst about one artifact with `cap=2`, and a fully
  evaporated trace → `sense()` returns normally (no raise); **only** the valid ones sensed; each of
  `dropped_off_cell`, `dropped_future`, `damped_no_context`, `damped_velocity`, `evaporated` counted
  `>= 1`. Then a request with a `FORBIDDEN` key / a `signal="ban"` **raises**.
- **Verify:** AC10 — cascade-shaped content is damped-and-counted; only the envelope raises.

## Test K — Determinism (AC11)
- **K:** run D1 twice → byte-identical `json.dumps(out, sort_keys=True)`. Floats via `round(...,6)`.
- **Verify:** AC11.

## Test L — Envelope validation (AC12)
- Empty `cell_id`; `now="1000"`/`now=True`; `window=0`/`-1`/`True`; `velocity_cap=0`; `half_life=0`;
  `min_strength=-1`/`min_strength="x"`; `traces="x"`; a trace not a dict; a trace missing `about`; a
  trace with a non-whitelisted key (`priority`); `signal="nope"`; `strength=0`/`strength=-1`/
  `strength=True`; `created_at="t"` → each **refused**.
- **Verify:** AC12.

## Test M — No LLM, importable offline, stdlib-only (AC13)
- **M1:** import `src/stigmergy/stigmergy.py` with no `anthropic` installed → succeeds.
- **M2 (static):** source has no `import anthropic|requests|httpx|openai|urllib|socket`, and `sense`
  takes only `request` (no injected model/`propose`).
- **Verify:** AC13 — deterministic, the whole difference from Capa 3.

## Test N — Cross-layer consistency (AC-X)
- **N1:** feed a Capa-1 surveillance-shaped payload as a Capa-5 trace node
  (`{"about":"x", ... , "seller":{"trust_score":88}}`) → **refused** (also a whitelist violation on
  `seller`; and `trust_score` matches `score`).
- **N2 (taxonomy identity):** `stigmergy.FORBIDDEN_KEYS == membrane.FORBIDDEN_KEYS ==
  legibility.FORBIDDEN_KEYS == matcher.FORBIDDEN_KEYS`.
- **Verify:** AC-X — the five layers agree on the forbidden-key taxonomy.

## Property tests (Test P — hypothesis)
- **P1 (no scalar out):** for any clean random trace set, the output scanned recursively contains zero
  `FORBIDDEN` keys and no person-scoring number.
- **P2 (mob always throttled):** for any `about`, any `velocity_cap=k`, and any number `n` of in-window
  traces about it, the sensed count for that artifact is `<= k` (the stampede is always capped).
- **P3 (evaporated never surfaces):** any trace with `round(strength·0.5^(elapsed/half_life),6) <
  min_strength` never appears in `sensed`.
- **P4 (off-cell never surfaces):** any trace with `cell_id ≠` the sensing cell never appears.
- **P5 (surveillance refused at any depth):** a request with any `FORBIDDEN` key nested at random depth
  is always **refused**.
- **P6 (never crashes on content):** for any random mix of off-cell/future/bare-flag/over-cap/evaporated
  traces (no envelope breach), `sense()` returns normally; it only raises on a malformed **envelope**.
- **P7 (order canonical):** permuting the input trace order never changes the emitted `sensed` order.

## Cross-check (independent oracle, AGD-045)
Re-derive the sensed survivor set with a **hand-written** filter (cell scope → future drop → flag/context
gate → per-artifact in-window velocity cap keeping the earliest `k` → evaporation floor) + key-scanner,
**separate from the module**, and assert the module's `sensed` equals the independently-derived set.
Disagreement = fail (catches self-confirmation, ST4).
</content>
