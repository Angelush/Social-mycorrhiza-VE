# Audit — every finding → an enforceable requirement (Sim-B2B)

> Produced by audit-feedback-loop (the judge), in two passes. **Pass 1** is the authoring audit whose
> findings (M#/H#) the bundle cites throughout; this file was omitted when the bundle was first
> written (finding V1), so pass 1 is re-recorded here from its surviving citations. **Pass 2** (V#) is
> a source-verification audit of the whole bundle against the **shipping SUT code**
> (`B2B/src/clearing/clearing_solver.py`, `B2B/src/ledger/mutual_credit_ledger.py`, the C2C `src/`
> modules) and against the parent briefs' actual numbering. Same discipline as the parent audits:
> every finding becomes a constraint, an AC, or a test — never just a report line.

## Pass 1 — authoring audit (M# mislabelled references · H# hardening findings)

| Finding | What it was | Became enforceable as | Enforced? |
|---|---|---|---|
| M2 — namespace collision | Bare "inv. 6/8/10" meant B2B invariants but read as sim invariants | spec header namespace rule (sim inv. / B2B inv. / C2C inv. always explicit) | ✅ |
| H1 — invented verbs | `Draw`/`Exit` adapter primitives had no SUT counterpart; faking them means computing balances = a second mechanism | M1a + engine adapter rule (composite behaviours, never new primitives); spec §1/§2; architecture SUT layer | ✅ |
| H2 — self-caught plant | A naive cent-drop negative control is caught by the SUT itself, proving nothing about the oracle | spec §7 N-01 *silent* requirement; ST6; AC3; G-04 — **deepened by V2** | ✅ |
| H3 — presupposed mechanism | "The positive cap redistributes strong→weak" is B2B inv. 4's *claim*, not the code's behaviour (the ledger rejects and moves nothing) | T2d honest open question; X6 escalation; AC17 | ✅ |
| H4 — anchor as gate | Gating the build on the Sardex ≈25%/≈50% band rewards tuning the generator to the anchor (calibration ≠ validation) | T2a reported-with-sensitivity-not-gated; X2; AC16; A-01 | ✅ |

*(Pass 1 findings with no surviving citation were editorial and are not reconstructed.)*

## Pass 2 — source-verification audit (V#), 2026-07-08

### Corrections applied to the bundle

| Finding | What was wrong | Fixed in |
|---|---|---|
| **V1 — this file was missing** | H1–H4 and "audit M2" were cited in 9 places but defined nowhere; `.specsmith.json` claims `audit-feedback-loop` ran | audit.md created; README bundle listing |
| **V2 — N-01 was not silent (critical)** | The SUT self-checks conservation at **three** points, not one: solver `post_net == pre_net` raise; ledger `apply_clearing` re-verifies the batch (per-member net delta = 0) and **rejects**; ledger global zero-sum assert after every op. Disabling only the solver assert leaves the plant self-caught at apply time — ST6's own error, one guard deeper. A batch that passes the ledger's check *cannot* change committed net positions, so a committed silent breach **requires a ledger-side plant** | spec §7 N-01; ST6; AC3; tests N-01/G-04; both READMEs |
| **V3 — N-02's naive clamp is also self-caught** | Clamping a *balance* to its bound breaks zero-sum (one side moves more than the other) and trips the ledger's own balance-sum assert. The silent clamp shrinks the **effective amount** to the headroom (zero-sum preserved) | spec §7 N-02; tests N-02 |
| **V4 — adapter surface incomplete** | The declared surface ("…and nothing else") omitted `create_cell` — the only way to bootstrap a cell — and the read-only accessors (`member_statement`, `cell_metrics`) that power `FirmState` views | engine spec; architecture; spec §2 |
| **V5 — "SUT commit hash" under-defined** | C2C has no git repo (B2B does); and a commit id misses uncommitted edits — fatal for a discipline whose negative control runs *modified copies*. Pin = **content hash** of SUT source bytes; commit recorded additionally when available | spec M3; engine adapter + reproducibility contract |
| **V6 — two bound quantities conflated** | Solver `credit_flags` fire on the **obligation-net**; the ledger enforces **balance** (settle) and **projected position** = balance + obligation-net (record). A flag is informational, not per se a ledger-bound breach; the oracle must recompute each by its own definition and never equate the lists | spec T1b note; architecture Track A |
| **V7 — auto-pause gap unflagged** | B2B inv. 8 promises "**automatic** pause on anomalies"; the shipped `pause_cell` is manual + human-ratified, and no anomaly detector exists in the SUT. Same species as the appeal gap (X5) and the redistribution gap (X6), but the bundle didn't flag it | spec T1d; constraints X7; failure-model ST8; architecture |
| **V8 — dangling/wrong cross-references** | C9 cited "M4" (the apply-gate requirement) for the adversary-mapping rule; C14/T4/architecture cited a nonexistent "C4" for the person-scalar lint (sim's is C14; the C2C counterpart is **N2**); tests A-03 pointed at "AC8-adjacent" (AC8 is the person-scalar criterion); C-04/P-05 pointed at "AC-context" (no such id); README said AC1–AC20 (file had 21) | constraints C9/C14; spec T4; architecture; tests A-03/C-04/P-05; README |
| **V9 — Bad-faith blocker mis-cited** | "§6.3 tyranny of the minority" — C2C brief §6.3 is *"no se puede fabricar la voluntad de cooperar"*; the veto-capture finding lives in **C2C Capa-6 F8** (which itself ties to §6.3's "who participates and why decides") | simulation-brief §2; sim-c2c README |
| **V10 — unprefixed cross-document § refs** | Bare "§7.1 cold-start" (= B2B brief), "§6.2 bootstrapping" (= C2C brief) read as sim-brief sections; the namespace rule covered invariants only | simulation-brief §2 tables; spec A3; spec header rule extended to § refs |
| **V11 — terminology contradicted the code** | context.md said obligations are "cell-tagged" (they carry no cell tag), listed "draws, exits" as proposals (removed by H1), and said sanctions come "with appeal" (appeal is brief-only, X5) | context.md terminology + SUT section |
| **V12 — engine loop pseudocode bugs** | `history` appended the *next* round's cfg with *this* round's reports (off-by-one that would mis-train the researcher); journal entries could never contain the hypothesis/diff (computed after append); `researcher`/`sut_adapter` unbound; "engine inv. N" never declared ≡ sim inv. N | engine spec loop + Journal + numbering note |
| **V13 — Track B wording vs. its own type guard** | "Trace **which creditors** absorb the loss" implies an agent-indexed output the `WelfareReport` type forbids. Track B reports the **distribution** (quantiles/concentration); per-event identities stay in the raw trace for offline forensics | spec T2f; brief §4; architecture; tests C-01; README |
| **V14 — no `ResumeCell` proposal** | The breaker-policy could pause the world but nothing could resume it (`resume_cell` exists in the SUT and adapter) | spec §1 |
| **V15 — anti-cascade oracle missing from brief §4** | The Mob-instigator maps to C2C inv. 9, but the brief's C2C Track-A list had no anti-cascade oracle (the sim-c2c stub does) | simulation-brief §4 |
| **V16 — F8's mitigation contradicted the two-axes rule** | "Every adversary maps to a numbered failure mode (B2B F1–F7)" is the exact conflation C9/sim inv. 6 corrects (live actors ↦ invariants; F1–F6 ↦ negative control) | failure-model F8 |
| **V17 — researcher not in the reproducibility tuple** | The campaign-level function must pin the researcher strategy+config (a Grid vs. Bandit researcher diverges under the same seed); round-level replay from the journal does not need it, campaign re-run does | engine reproducibility contract + loop signature |
| **V18 — apply-time cell check unused** | `apply_clearing` rejects a proposal whose `cell_id` differs — a real SUT fact strengthening the firewall-by-input-contract oracle, uncited | spec T1c; AC13 |
| **V19 — status-gating of record ops undocumented** | `record_obligation` requires debtor *and* creditor status ∈ {active, warned, line_reduced}; `settle_obligation` has no status gate (a suspended defaulter's obligations can still be settled down) — load-bearing for A4/T1e dynamics | context.md SUT section |
| **V20 — Sybil finding understated** | `add_member` not only accepts any non-empty `ratified_by` — it derives credit lines from **self-declared** `turnover_eur_cents` (fake turnover ⇒ real lines) | spec A5; AC22 |
| **V21 — ST2 had no acceptance criterion** | The bundle's own rule is "every red-team finding maps to an AC"; the Sybil membership-gate finding (ST2/X3) mapped to none | AC22 added; tests C-04 |

### Verified true against the source (the load-bearing claims that held)

- **Solver:** single entrypoint `clear({cell_id, members, obligations}) -> dict`; obligations carry no
  cell tag; `_validate` rejects self-loop / unknown member / non-int / ≤0 / duplicates; conservation
  self-raise (`post_net != pre_net`); `credit_flags` = post-net out of bounds, **flags never clamps**;
  sorted traversal; proposal-only; `render_report` exists.
- **Ledger:** ops exactly `create_cell` / `add_member` / `update_member` / `record_obligation` /
  `settle_obligation` / `apply_clearing` / `pause_cell` / `resume_cell` (+ read-only
  `to_clearing_input` / `member_statement` / `render_statement` / `cell_metrics` / `replay` /
  `verify_chain`); integer `ts`, monotone, no clock/RNG; hash-chained events with byte-exact
  replay/verify; **rejects-never-clamps** at record (projected), settle (balance), plus a global
  bounds + zero-sum re-check after every op; velocity = per-debtor **sliding** sum over
  `velocity_window_s` capped at `velocity_max_cents`, **rejected** on breach, `record_obligation`
  only; ladder `active→warned→line_reduced→suspended→expelled`, upward rung-skips rejected,
  **downward unrestricted** (T1e-ii confirmed); `update_member` refuses a line change stranding the
  balance (`new_min ≤ balance ≤ new_max` — T1e-i confirmed); `ratified_by` = any non-empty string on
  the six ratified kinds; **no `draw`, no `exit`**; `pause_cell` blocks everything except resume.
- **Parent briefs:** B2B inv. 1–10 and F1–F7 numbering match the bundle's usage (inv. 4 redistribution
  *claim*, inv. 5 "siempre con derecho de apelación", inv. 8 "pausa automática", inv. 9 human-in-loop,
  inv. 10 permissioned); §7.1 cold-start, §7.4 contracyclical, §7.5 "lo irreducible"; Sardex
  ≈25%/≈50% anchor is real (brief §3 Capa 1). C2C inv. 1/2/6/8/9 and F1/F5/F7/F8 match; Capa
  numbering (membrane 1 · legibility 2 · matcher 3 · assurance 4 · stigmergy 5 · governance 6)
  matches; `FORBIDDEN_KEYS` substring scans exist in membrane/legibility/governance/matcher;
  `claude_matcher.py` is lazily imported and stubbable exactly as the engine spec claims; the
  two-askers divergence property is capa2 AC7/Test G; forgetting (`expires_at`) is real; AGD-045
  exists in the parent audits; the repo-root `.venv` exists.

**Verdict:** with V1–V21 applied, every claim the bundle makes about the SUT surface is now true of
the shipping code, every cited id resolves, and the negative-control gate actually tests the oracle
rather than the SUT's self-defence. The bundle is ready to build.
