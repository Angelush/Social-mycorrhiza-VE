# Micorriza — Simulation harness (Sim)

A simulation to test **both** Micorriza approaches — the B2B mutual-credit clearing system (`../B2B`)
and the C2C social protocol (`../C2C`) — by driving the **real** code with populations of
good / neutral / bad actors inside a **Karpathy-style auto-research loop**: a fixed-budget round
produces measurements to study, an auto-researcher reads them and mutates the next round, and the loop
compounds. Two sibling simulations share one engine and are built to later **integrate** so both run at
once and cross-effects on microeconomics become observable.

Built with the same method as its siblings (a spec bundle plus a review-gated build). **Status
(2026-07-11): BUILT.** The shared engine and all three harnesses (Sim-B2B, Sim-C2C, Sim-Integrated)
are implemented under `src/` and verified against the real SUTs — 120/120 tests green, one commit per
milestone (`git log --oneline` tells the build story). Run the suite from `Sim/` with
`../.venv/bin/python -m pytest tests -q`.

> **North star:** the sim is a **driver and an oracle, never a second copy of the mechanism**, and it
> obeys the laws it tests — the agent proposes, the gate disposes, and the one-way door over value
> never opens inside the loop.

## Two things it measures, kept separate (never mixed)
- **Track A — invariant integrity `[ORACLE]`:** does the real code hold when live actors attack it?
  Red/green per invariant + the exploit trace. A violation **halts** the campaign (a headline, not a
  data point averaged into a pass rate).
- **Track B — microeconomics `[STATISTICS]`:** how do surplus, liquidity, and trust distribute across
  a population that isn't all well-behaved? Distributions, never a per-person scalar.

## Layout
```
simulation-brief.md              # the design synthesis (sibling of ../B2B and ../C2C briefs)
workflows/engine/spec.md         # the shared ABM + auto-research core (spec'd once)
workflows/sim-b2b/               # FULL bundle — drives the real solver + ledger
  intent/context/architecture/spec/constraints/failure-model/audit + evals/{acceptance,tests}
workflows/sim-c2c/               # seam README + spec + failure-model + evals ("no person-scalar" trap)
workflows/sim-integrated/        # seam README + spec + failure-model + evals (cross-system firewalls)
src/engine/                      # shared core: types, world, policy/cassette, measurement,
                                 #   researcher (one-way door), journal (hash chain), campaign
src/sim_b2b/                     # B2BAdapter, world, archetypes, Track A/B, negative control N-01/N-02
src/sim_c2c/                     # C2CAdapter, world, 9 archetypes, 6 oracles, descriptive-only Track B
src/sim_integrated/              # both SUTs, one population: Identity, bridges, firewall Track A
tests/                           # 120 tests, all driven against the REAL SUTs (never mocked)
```

## The design in one screen
1. **The SUT is the real code, imported read-only.** The harness drives `clearing_solver`,
   `mutual_credit_ledger`, and the C2C modules — it never reimplements them, so findings transfer.
2. **Bad actors map to invariants; planted defects map to the negative control (two axes).** Live
   adversaries stress the *invariants* (B2B inv. 4/5/8/10) and the input contract (B2B F7); the
   implementation defects B2B F1–F6 (float/determinism/termination/clamp/scope-creep) are *not*
   actor-inducible — they are the **negative control's** job. A sim that files a live actor under "F1
   float drift" mislabels what it tested (brief §2 two-axes note).
3. **Agents are hybrid:** a rule-based, seeded, reproducible core (the bulk + all adversaries) plus
   injected, cassette-backed LLM probes for fuzzy need-descriptions. **No LLM ever on the value path.**
4. **The researcher runs autonomously within a declared search space** but can **never patch the SUT**
   — a "the code should change" finding is a flagged journal recommendation for a human between
   campaigns. Autonomy over the world; the one-way door over the mechanism stays shut.
5. **The C2C trap:** measuring "fertility" naively rebuilds the surveillance god-view the C2C system
   exists to prevent. Track-B for C2C is **structurally forbidden from emitting a per-person scalar by
   its output *type*** (no agent-indexed dimension — a per-person score is unrepresentable), with the
   `FORBIDDEN_KEYS` substring scan as a *secondary lint* (necessary but insufficient — a scalar named
   `fertility` would pass it). Descriptive only, never the loop's objective.
6. **The defining build gate is a negative control — with a *silent* plant:** against a deliberately
   broken copy of the SUT, the harness must halt and surface the exploit. The plant must bypass **all**
   the SUT's own guards (the solver self-raises on a conservation break **and** the ledger re-verifies
   batch conservation at apply, plus a global zero-sum assert — silencing only one leaves the plant
   self-caught), or the gate tests the
   SUT's self-defence, not the harness's oracle. A harness that can't catch a *silent* planted bug
   can't be trusted to report a real one.

## Sequencing (mirrors how ../B2B and ../C2C were built — all three stages done)
1. ✅ Shared engine + **Sim-B2B full**. Gate of done: **catches a
   *silent* injected conservation bug** (negative control). The Sardex ≈25%/≈50% band is *reported with
   its topology-sensitivity as a sanity check, not a gate* — the number is a property of the synthetic
   generator, so gating on it rewards curve-fitting (calibration ≠ validation).
2. ✅ **Sim-C2C full** — same engine over the C2C SUT; the hard part was the person-scalar-free Track B
   (structural: the `WelfareReport` type has no agent-indexed dimension; the researcher's
   descriptive-only guard lives domain-side).
3. ✅ **Sim-Integrated** — one population across both SUTs; the value/social and cell/cell firewalls as
   tested invariants (F-VS1/F-CC are SUT-enforced; F-VS2 has NO SUT wall — the provenance oracle IS
   the wall, and that finding is proven against the real B2B). The cross-effect microeconomic study
   over integrated campaigns remains open future work.

## Honesty boundaries (flagged, never coded away)
A green campaign proves **coverage, not safety**. Autonomous rounds trade oversight for throughput
(mitigated structurally). **Calibration ≠ validation** — synthetic topologies are hypotheses. The C2C
fertility proxy is Goodhart-prone by construction and must never become the loop's maximization target.
