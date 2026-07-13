# Constraints — MUST / MUST-NOT / escalation (Sim-B2B)

> Produced by author-constraints. Each carries a because-clause. Species-scoped: `[HARNESS]`,
> `[SUT]`, `[ORACLE]`, `[RESEARCHER]`, `[LLM-PROBE]`.

## MUST
- **C1 `[SUT]`** Drive the real `clearing_solver` and `mutual_credit_ledger`; import them read-only and
  pin their commit hash for the campaign. *Because: a sim that reimplements the mechanism tests a
  fiction (inv. 1).*
- **C2 `[HARNESS]`** Keep money as integer cents on the value path; reject (never clamp/repair) a
  malformed amount. *Because: float drift silently breaks conservation (B2B inv. 1 / F1); clamping
  hides a breach (B2B inv. 4).*
- **C3 `[ORACLE]`** Re-derive each invariant *independently* of the SUT's own bookkeeping. *Because:
  the SUT's self-check would agree with its own bug (self-confirmation; parent AGD-045).*
- **C4 `[ORACLE]`** On any invariant violation, **halt the campaign and surface the minimal exploit
  trace**; do not average it into a rate. *Because: one real conservation break is a system-defining
  bug, not a data point (inv. 4).*
- **C5 `[HARNESS]`** Keep Track A and Track B as separate outputs end to end. *Because: "efficient but
  broken" and "safe but useless" are different verdicts (inv. 7).*
- **C6 `[HARNESS]`** Make a campaign byte-reproducible from `(scenario, seed, actor_mix, params, SUT
  commit, cassette)`; seed the RNG; cassette-back all LLM calls under replay. *Because: an auditable
  finding must be reconstructable (inv. 3), mirroring the SUT.*
- **C7 `[RESEARCHER]`** Confine every proposed diff to the declared `search_space` via
  `apply_within_gate`. *Because: unbounded autonomy wastes the budget in an uninteresting corner
  (brief §6.2).*
- **C8 `[HARNESS]`** Journal every round to a hash-chained, append-only log. *Because: the journal is
  the campaign's artifact and its audit trail (brief §3), same discipline as the ledger audit log.*
- **C9 `[HARNESS]`** Map each adversary policy to the invariant it stresses (B2B inv. 4/5/8/10), an
  input-contract rule (B2B F7), or a documented open problem — and cite the mapping. The implementation
  defects B2B F1–F6 are **not** actor-inducible; they belong to the negative control (C10), not to an
  archetype. *Because: coverage must be auditable against the red-team work already done, on the correct
  axis — a live actor filed under a planted-defect number mislabels what was tested (sim inv. 6;
  mitigates F8).*
- **C10 `[HARNESS]`** Pass the negative-control gate (spec §7) before the build is accepted. *Because:
  a harness that cannot catch a planted bug cannot be trusted to report a real one.*

## MUST-NOT
- **C11 `[SUT]`** Never reimplement any adjudication (netting, balance, bound check, sanction) inside
  the harness. *Because: inv. 1 — the driver is not a second copy of the mechanism.*
- **C12 `[RESEARCHER]`** Never patch, monkeypatch, or hot-reload the SUT source inside the loop; a
  "the code should change" finding is a **flagged journal recommendation** for a human between
  campaigns, never an applied change. *Because: the one-way door over value stays shut inside the loop
  (inv. 2), even under autonomous rounds.*
- **C13 `[LLM-PROBE]`** Never let an LLM adjudicate a value-path event; probes generate only fuzzy
  intentions/descriptions (input side). *Because: no stochastic process on the value path (engine inv.
  8 / B2B inv. 1).*
- **C14 `[HARNESS]`** Never emit a per-firm "trustworthiness/reputation score." The `WelfareReport` is
  aggregate-only **by type** (no agent-indexed slot), so an identity-keyed scalar is unrepresentable;
  `assert_no_person_scalar`'s substring scan is a secondary lint, not the guarantee (it would miss a
  neutrally-named one). Firm-level *economic* figures (net position, benefit) legitimately feed
  distributions — that is not the forbidden shape. *Because: a reputational scalar is the C2C anti-goal;
  do not smuggle it onto the value path (sim inv. 5, defensive; the C2C counterpart is C2C N2).*
- **C15 `[HARNESS]`** Never present a green campaign as proof of safety. Report **coverage over the
  explored space**, never "unbreakable." *Because: the sim can only falsify (brief §6.1).*
- **C16 `[LLM-PROBE / RESEARCHER]`** Never make a live model call on a *reproducible* campaign path
  without a cassette. *Because: it breaks byte-determinism (inv. 3 / E3).*

## Escalation (surface, do not auto-decide)
- **X1** A Track-A violation → **halt**, surface the exploit trace and the exact `RoundConfig` that
  produced it, and stop the campaign (C4). A human triages whether it is a SUT bug or a harness bug.
- **X2** A Track-B result that contradicts the calibration anchor by an order of magnitude (e.g. debt
  reduction ≈0% or ≈95% on a cooperative mix) → flag as a **probable harness/topology modelling error**
  (calibration ≠ validation, brief §6.5), not a system finding, and surface for review.
- **X3** The Sybil-hopper (A5) succeeding in minting extra credit lines → surface as a **membership-gate
  finding** (B2B inv. 10 lives in a human/policy layer the sim only stubs); flag the boundary of what
  the code alone can enforce.
- **X4** The researcher's search converging without ever crossing an integrity/welfare phase boundary →
  flag the `search_space` as probably too narrow (a human widens it between campaigns).
- **X5** The graduated-sanctions ladder (T1e) — the SUT has **no appeal mechanism** and the *decision*
  to sanction is external; surface both as **human-layer (Capa-0) boundaries the code does not enforce**,
  and surface the two SUT findings T1e-i (line-reduction raises against a drawn-down member) and T1e-ii
  (unrestricted downward rehabilitation) as **flagged findings for a human**, not oracle passes. *Because:
  asserting an appeal path the code lacks would be theatre; the honest output is the boundary (B2B inv. 5
  vs. shipped ledger).*
- **X6** T2d measuring the positive cap as **blocking, not redistributing** (strong→weak flow ≈0 beyond
  second-order rerouting) → surface as a **flagged gap between B2B inv. 4's redistribution *intent* and the
  shipped behaviour** (the ledger rejects the over-cap obligation but moves no value), a recommendation for
  humans between campaigns — never patched in-loop (C12). *Because: the sim's job is to find where the code
  may not fulfil the brief, not to assume it does (H3).*
- **X7** B2B inv. 8 promises **automatic pause on anomalies**; the shipped ledger has only a manual,
  human-ratified `pause_cell` and no anomaly detector. The harness breaker-policy that decides *when* to
  pause is therefore modelling a mechanism the code lacks → surface as a **brief-vs-code gap** (same
  species as X5 appeal and X6 redistribution): a flagged journal recommendation for humans, never an
  oracle assertion that "the auto-breaker held." *Because: asserting a breaker the code lacks would be
  theatre; the honest output is the boundary (audit V7).*
