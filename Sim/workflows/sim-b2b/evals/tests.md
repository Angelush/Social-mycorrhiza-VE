# Tests — A/B/C + golden set + property tests (Sim-B2B)

> Produced by design-evals. Concrete test designs the build must satisfy. Grouped by the classic
> A (happy) / B (edge) / C (adversarial) split, plus property-based and golden-set tests. Each cites
> the AC it discharges.

## Test A — happy path (cooperative mix)
- **A-01** A 100-firm cooperative (all-Circulator) campaign runs T ticks; T1a PASS every round;
  T2a reports debt reduction in the ≈25%/≈50% ballpark **with its sensitivity to `topology_params`**
  (reported, not gated — the gate is N-01). → AC11, AC16.
- **A-02** Two independent runs of A-01 with the same seed produce byte-identical journals. → AC7.
- **A-03** The journal is a valid hash chain (each entry's `prev_hash` matches). → C8 (journal
  discipline; supports AC7/AC19).

## Test B — edges
- **B-01** Hoarder-heavy mix drives several firms to the positive cap; T1b shows the ledger **rejects**
  the over-cap obligation (raises) and the solver **flags** any pre-existing out-of-bounds net — neither
  clamps; T2d reports whether the cap **redistributed** value strong→weak or merely **blocked** it (and
  escalates the gap vs. B2B inv. 4 if it only blocked, X6). → AC12, AC17.
- **B-02** Wallflower-heavy (sparse) mix yields few cycles; T2a reduction is low but T1a still PASS
  (thin-cycle cold-start does not break conservation). → AC11.
- **B-03** `credit_crunch=True` vs `False` on the same base mix; T2e advantage rises under crunch. → AC18.
- **B-04** Boundary: a single 2-firm A→B, B→A pair nets exactly to zero net-change (drive the solver's
  parallel-edge/back-allocation path through the adapter). → AC11.

## Test C — adversarial (each maps to a failure mode)
- **C-01 Defrauder (stresses B2B inv. 4/5):** an A4-heavy mix (draw to `credit_min` via record+settle,
  then cease activity — no `exit` op); T1a PASS (no conservation break), T1e confirms the status
  transitions obeyed ladder ordering (appeal is **not** asserted — human-layer, X5) and surfaces T1e-i
  (line-reduction **raises** against the drawn-down defrauder) and T1e-ii (downward rehab allowed);
  **T2f** reports how the persisted negative balance distributes across creditors (mutualisation —
  *not* "bounded to the defrauder"; identity-free by type). → AC15, AC11, AC21, ST3.
- **C-02 Cell-leaker (B2B F7, single-cell SUT):** A7 tries a foreign-member obligation and tries to make
  the harness batch two cells; the SUT **rejects** the foreign member and the **harness-partition guard**
  holds (T1c PASS). No cross-cell op exists to "refuse"; the true two-cell firewall is a Sim-Integrated
  test. → AC13, ST7.
- **C-03 Velocity attacker (B2B inv. 8):** A6 sweeps `adversary_intensity` (obligations/window) at a
  documented `velocity_window_s`/`ticks_per_second` mapping; T1d confirms the over-cap
  `record_obligation` is **rejected** and no debtor exceeds `velocity_max_cents` in a window; the
  intensity at which bursts start being rejected is reported (finding, not crash — **no cascade depth**).
  → AC14, ST1.
- **C-04 Sybil-hopper (B2B inv. 10):** A5 attempts multi-identity registration; the outcome is surfaced via
  X3 as a membership-gate finding (the gate is a stubbed human/policy layer; lines derive from
  self-declared turnover), flagging code-vs-human
  enforceability. → AC22, X3.
- **C-05 Reputation-smuggle (F7 harness):** a test that adds a per-firm reputation field to a
  `WelfareReport` is rejected by `assert_no_person_scalar`. → AC8.

## Negative-control tests (the harness's self-confirmation guard)
- **N-01 Silent cent-drop SUT:** run a campaign against a broken **SUT copy** that drops one cent from
  one cycle **and disables both the solver's `post_net == pre_net` assert and the ledger's apply-time
  batch re-verification (`member_net == 0`)**, so the bad settlement **commits** (a plant that leaves
  either guard intact is self-caught by the SUT, not the oracle — ST6, audit V2; run those partial
  variants as *supplementary* controls asserting the SUT's own rejection surfaces in the trace, never
  as the gate); the
  campaign **halts on the first offending round** with T1a's *independent* exploit trace. → AC3, AC5.
- **N-02 Silent-clamp ledger:** run against a copy of `mutual_credit_ledger` patched to **silently
  clamp the effective amount** of `record_obligation`/`settle_obligation` to the bound headroom
  (zero-sum preserved — a naive *balance* clamp trips the ledger's own balance-sum assert, audit V3);
  T1b catches the accepted-X-committed-Y divergence and the campaign halts. → AC3.
- **N-03 Self-confirmation guard:** confirm Track A's net-position numbers are computed without calling
  the solver's own net-position method (static/behavioural check). → AC4.

## Property-based tests (hypothesis — the harness's own invariants)
- **P-01 Conservation is oracle-independent:** for random valid obligation graphs, the Track-A oracle's
  net positions equal a second, differently-implemented recompute (e.g. `networkx`), never the solver's.
  → AC4.
- **P-02 Reproducibility:** for random `(seed, actor_mix within space)`, two runs give identical journal
  hashes. → AC7.
- **P-03 Gate soundness:** for random researcher diffs, `apply_within_gate` accepts iff the diff is
  inside `search_space` and touches no SUT field. → AC9.
- **P-04 Track separation:** for random traces, `IntegrityReport` and `WelfareReport` are independent —
  perturbing a welfare stat never changes an integrity verdict and vice versa. → AC6.
- **P-05 Integer-cents invariant:** no float ever appears on a value-path amount across a random
  campaign (type assertion). → C2 (the property test is the enforcement; no separate AC).

## Golden set (frozen reference campaigns)
- **G-01** A fixed cooperative campaign → frozen journal hash + frozen T2a/T2b band. Guards against
  silent regressions in the harness or the measurement.
- **G-02** A fixed Defrauder campaign → frozen T1e ladder-ordering trace (incl. the T1e-i line-reduction
  rejection) + frozen T2f mutualisation distribution.
- **G-03** A fixed Velocity campaign at pinned intensity → frozen T1d **rejection boundary** (the
  intensity at which the breaker starts rejecting). Regression guard on the breaker.
- **G-04** The two negative-control runs (N-01 *silent* cent-drop, N-02 *silent* amount-clamp) → frozen
  "halted-with-trace" outcomes. If a future harness change makes these *pass*, the harness has gone
  blind — the loudest possible regression. (N-01 specifically guards against ST6: the plant must remain
  *silent* so the independent oracle — not the solver's self-assert **nor** the ledger's apply-time
  re-verification or zero-sum assert — is what catches it. Audit V2/V3.)

## Cross-cutting
- **X-01 Coverage caveat present:** every generated campaign report contains the explored-space
  statement and the "green = coverage, not safety" caveat. → AC20.
