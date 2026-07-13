# Acceptance criteria (Sim-B2B)

> Produced by design-evals. AC# = an acceptance criterion; each is checkable and traces to a spec/
> constraint id. "The build finished" ≠ "you trust it" — every red-team finding maps to an AC here.

## Harness-integrity acceptance (the harness tests itself first)
- **AC1 — Drives the real SUT.** The B2B adapter imports `clearing_solver` and `mutual_credit_ledger`
  and calls them for every value-path event; a static check confirms the harness contains **no**
  netting/balance/bound/sanction arithmetic of its own. *(spec M1, C1/C11; F1.)*
- **AC2 — SUT pinned & read-only.** A campaign records the SUT commit hash at start and aborts if it
  changes mid-run. *(spec M3/E4, C1; inv. 2.)*
- **AC3 — Negative control: catches a *silent* planted bug.** Against a broken **SUT copy** that drops
  one cent and disables **both** the solver's conservation assert **and** the ledger's apply-time batch
  re-verification (so the bad settlement *commits* silently — a plant that leaves either guard intact
  is self-caught by the SUT and does not test the oracle: ST6, audit V2), the campaign
  **halts on the first offending round** and surfaces the exploit trace via T1a's *independent*
  recompute; against a ledger patched to **silently clamp the effective amount** to the bound headroom
  (zero-sum preserved — audit V3), T1b fires the same way.
  *(spec §7, C10; B2B F2/F5; H2.)*
- **AC4 — Independent oracle.** Track A re-derives net positions from the raw obligation stream, not
  from the solver's output; a unit test feeds a known graph and confirms the oracle's numbers are
  computed without calling the solver's net-position method. *(spec T1a, C3; F2.)*
- **AC5 — Halt, don't average.** Given a scripted round that violates conservation, the campaign
  returns a **halted** journal with the exploit trace — not a pass-rate that includes it. *(spec R3,
  C4; F3.)*
- **AC6 — Two tracks separate.** `IntegrityReport` and `WelfareReport` are distinct objects in the
  journal; no code path produces a combined score. A test asserts no function consumes both to emit one
  number. *(spec T3, C5; F4.)*
- **AC7 — Byte-reproducible.** Two runs of the same campaign `(scenario, seed, actor_mix, params, SUT
  commit, cassette)` produce **byte-identical journals**. *(spec R4/C6; F6.)*
- **AC8 — No person-scalar.** `WelfareReport` passes `assert_no_person_scalar`; a test that injects a
  per-firm reputation field is rejected. *(spec T4/C14; F7.)*
- **AC9 — Researcher bounded & SUT-safe.** Every researcher diff passes `apply_within_gate`; a test
  that proposes a SUT-touching field or an out-of-space value is rejected. *(spec R2/C7/C12; F5.)*
- **AC10 — No live LLM on the reproducible path.** A reproducible campaign with a probe/researcher but
  no cassette raises; with a cassette it replays deterministically. *(spec E3/C16; F6.)*

## System-finding acceptance (what the harness must be able to show about the SUT)
- **AC11 — Conservation under load holds.** On a mixed cooperative+adversarial campaign, T1a reports
  PASS every round (net position pre==post every clearing). *(B2B inv. conservation.)*
- **AC12 — Credit bounds: solver flags, ledger rejects, neither clamps.** On a Hoarder/Defrauder-heavy
  mix, the solver's `credit_flags` equals the independent recompute of out-of-bounds nets, and every
  ledger op that would breach a bound is **rejected** (raises) in the trace — never a
  clamped-and-continued balance (T1b PASS). *(B2B inv. 4 / B2B F5.)*
- **AC13 — Firewall holds by the input contract (single-cell SUT).** The harness **never** assembles a
  `clear()`/ledger input mixing two cells, and the SUT **rejects** a foreign-member obligation and a
  clearing proposal whose `cell_id` mismatches the cell (T1c
  PASS). The genuine two-cell contagion firewall (B2B inv. 6) is a Sim-Integrated criterion, not a
  Sim-B2B one. *(B2B F7 — single-`cell_id` contract; C1/ST7.)*
- **AC14 — Velocity breaker rejects the burst.** Under a Velocity-attacker mix at rising intensity, T1d
  confirms no debtor exceeds `velocity_max_cents` within `velocity_window_s` and the over-cap
  `record_obligation` is **rejected**; the intensity at which bursts start being rejected is reported
  as the finding (not a crash, and **not** a cascade depth — the SUT has none). *(B2B inv. 8.)*
- **AC15 — Sanctions ladder-ordered; appeal is human-layer; two SUT findings surfaced.** A Defrauder's
  status transitions obey the ladder ordering (the SUT rejects rung-skips); T1e does **not** assert an
  appeal path (the code has none — flagged via X5), and surfaces T1e-i (a `line_reduced` step **raises**
  against a drawn-down member) and T1e-ii (unrestricted downward rehabilitation) as findings. *(B2B
  inv. 5; C3.)*
- **AC16 — Calibration anchor reported with sensitivity, not gated.** On a cooperative mix, T2a reports
  net-debt reduction in the **≈25% / ≈50%** ballpark **plus its sensitivity to `topology_params`**; a
  result off by an order of magnitude triggers X2 (probable modelling error). This is a sanity check,
  **not a build gate** — the gate is AC3 (calibration ≠ validation; H4/F9).
- **AC17 — Distribution, not just mean; cap effect stated honestly.** T2b reports a non-trivial Gini of
  clearing benefit (power-law inequality visible); T2d reports the measured strong→weak flow and, if the
  positive cap only **blocks** (flow ≈0 beyond rerouting) rather than **redistributes**, **escalates the
  gap vs. B2B inv. 4's intent** (X6) — a finding either way, not a presupposed redistribution. *(H3.)*
- **AC18 — Contracyclical signal.** T2e reports the system's relative advantage (T2a/T2c)
  **rising** under `credit_crunch=True` vs. off. *(brief §7.4.)*
- **AC19 — Frontier output.** A campaign returns the Pareto frontier of (integrity, welfare) over the
  explored space + the hash-chained journal; never a single scalar verdict. *(spec R5; ST5.)*
- **AC20 — Coverage honesty.** Every campaign report states the explored `search_space` and the
  caveat that green = "no explored adversary broke it," not "safe." *(C15; F10.)*
- **AC21 — Default mutualisation measured, not assumed.** On an A4-heavy mix, T2f reports the
  distribution of realised loss across the creditor side of a defrauder's persisted negative
  balance (identity-free by the `WelfareReport` type — audit V13; conservation still PASS via T1a);
  the report does **not** claim the loss is "bounded to the
  defrauder." *(spec T2f; ST3.)*
- **AC22 — Membership-gate finding surfaced (Sybil).** On an A5 mix, the campaign surfaces via X3 a
  membership-gate finding — `add_member` admits any non-empty `ratified_by` and derives credit lines
  from **self-declared** turnover, so the gate is a human/policy layer the SUT only stubs — flagged as
  the code-vs-human-enforceable boundary, never reported as a SUT break. *(spec A5; X3; ST2; audit
  V20/V21.)*
