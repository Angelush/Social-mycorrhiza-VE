# Spec — Sim-B2B (self-contained build spec)

> Produced by engineer-spec. Buildable without re-reading the brief. IDs: **M#** module requirements,
> **A#** actor policies, **T#** track/measurement requirements, **R#** research-loop requirements,
> **E#** input/validation rules. **Invariant namespaces (always explicit — never bare where it could
> collide):** "sim inv. N" (= simulation-brief §1, 1–8); "B2B inv. N" (= parent B2B brief §1, 1–10);
> "C2C inv. N" (= social brief §1). A bare "inv. N" means the sim namespace only; a B2B/C2C invariant
> is *always* prefixed. The same rule applies to section refs: a bare "§N" means this bundle's brief;
> a parent section is always "B2B brief §N" / "C2C brief §N" (audit V10). (The old bundle wrote bare
> "inv. 6/8/10" for B2B invariants — that collided with the sim namespace and is corrected
> throughout — audit M2; see `audit.md` for the M#/H#/V# findings ledger.)

## 0. What is built
A Python package `sim_b2b` (under a future `src/`) that instantiates the shared engine
(`../engine/spec.md`) over the real B2B SUT, plus one runnable campaign entrypoint and a test suite.

## 1. Data structures

- **`Proposal`** (actor → world): each maps **one-to-one to a real SUT operation** (no invented
  verbs — engine adapter rule / H1):
  `Trade(debtor, creditor, cents)` → `record_obligation` ·
  `Settle(obligation_id, cents)` → `settle_obligation` ·
  `RequestClearing()` → `run_clearing` (solver proposal) then ratified `apply_clearing` ·
  `SanctionStep(member_id, changes)` → `update_member` (a **compliance-policy** actor only, modelling
  the human Capa-0 layer) · `PauseCell()` → `pause_cell` and `ResumeCell()` → `resume_cell` (a
  **breaker-policy** actor — a paused world must be resumable inside the round; audit V14).
  There is **no `Draw` and no `Exit` primitive** — the ledger has no such operation. "Draw credit to
  the negative cap" is the *composite behaviour* of recording obligations as debtor and settling them
  until `balance → credit_min`; "default/exit" is drawing down then ceasing activity — the negative
  balance **persists on the books** (there is no op that erases it; it stays mutualised across
  creditors). `NeedDescription(member, text)` is an optional LLM-probe output that is **inert in B2B**:
  no B2B SUT module parses free text (the matcher is C2C's Capa 3, out of scope here), so it never
  reaches the value path and at most colours which `Trade` an actor's own policy chooses (M3-note).
  All amounts **integer cents** (M1). A proposal is *adjudicated by the real module*, never trusted.
- **`FirmState`** (world view exposed to an actor): its own balance, credit-line bounds, its trade
  neighbours' identities (not their books), the last public settlement report. **No god-view** (M2).
- **`RoundConfig`**: `actor_mix` (ratios by archetype), `n_firms`, `T` ticks, `clearing_cadence`,
  `line_calibration` (neg/pos cap % of turnover), `topology_params`, `adversary_intensity`,
  `velocity_window_s` + `ticks_per_second` (the **explicit tick↔window mapping** the ledger's velocity
  breaker keys on — ST1), `velocity_max_cents`, `credit_crunch: bool`, `seed`.
- **`IntegrityReport`** (Track A): `{invariant: PASS|FAIL, exploit_trace?}` for the five B2B oracles.
- **`WelfareReport`** (Track B): the microeconomic statistics (T2). Aggregate-only by *type* (no
  agent-indexed dimension); `assert_no_person_scalar` runs as a secondary lint (T4 / C14).
- **`JournalEntry`**: `(round, config_hash, IntegrityReport, WelfareReport, hypothesis, diff,
  prev_hash)`; hash-chained (R4).

## 2. SUT adapter (M-block — the real code, driven not copied)

The adapter surface is **exactly the real modules' public operations**, one-to-one (H1 / engine
adapter rule): `add_member` · `record_obligation` · `settle_obligation` · `run_clearing` (=
`ledger.to_clearing_input` → `solver.clear`, returns a proposal, commits nothing) · `apply_clearing`
(ratified commit) · `update_member` · `pause_cell` · `resume_cell` — plus `create_cell` (**world
setup only**: bootstrapping the cell is a ratified real op, never an actor proposal) and the ledger's
**read-only** accessors (`member_statement`, `cell_metrics`) that power the bounded `FirmState`
views (M2) — observation, no adjudication (audit V4). **No `draw_credit`, no
`exit_member`** — those are not ledger operations; the actor composes draw/default from
`record_obligation` + `settle_obligation` (M1a).

- **M1** — All value-path adjudication delegates to the **imported real modules**
  (`clearing_solver`, `mutual_credit_ledger`). The adapter MUST NOT compute a netting, a balance, a
  bound check, or a sanction itself. *(sim inv. 1.)*
- **M1a** — Actor behaviours the SUT has no operation for (draw-to-cap, default/exit) are **sequences
  of the real ops above**, chosen by the actor policy — never adapter methods that fake the missing
  operation by computing balances. Sequencing real ops is acting; computing a value result is a second
  copy of the mechanism (sim inv. 1 / C11). *(Fixes the old `Draw`/`Exit` verbs that had no SUT
  counterpart — H1.)*
- **M2** — The adapter exposes only bounded views to actors (`FirmState`). It never hands an actor
  another firm's ledger state.
- **M3** — The adapter pins the SUT at campaign start (`assert_sut_pinned`) and imports it read-only;
  a mid-campaign change aborts the campaign. The pin is a **content hash** (SHA-256 over the SUT
  source bytes), with the git commit recorded additionally when available — a commit id alone misses
  uncommitted edits, and C2C currently has no repo (audit V5). "SUT commit" elsewhere in this bundle
  is shorthand for this pin. *(sim inv. 2.)*
- **M4** — `apply_clearing` goes through the ledger's own human-gated one-way door (it requires a
  non-empty `ratified_by` and independently re-verifies per-member conservation before committing —
  `mutual_credit_ledger.apply_clearing`); the harness models the "human dispose" as a policy that
  approves within stated bounds and **logs** each approval. It never bypasses the gate. *(B2B inv. 2 —
  el agente propone, el humano dispone; sim inv. 2.)*
- **M5** — Integer cents everywhere on the value path; no float touches money. *(B2B inv. 1 / B2B F1.)*

## 3. Actor policies (A-block — the seven archetypes; each maps to a probed invariant)

- **A1 Circulator (good):** trades within lines with trade-neighbours, settles, keeps net near zero.
  Deterministic given seed. *Baseline/calibration.*
- **A2 Hoarder (neutral):** biases toward being paid, accumulates toward the positive cap. *Stresses
  B2B inv. 4 — the open question T2d answers: does the cap **redistribute** value strong→weak, or does
  the ledger simply **reject** the over-cap obligation and move nothing?*
- **A3 Wallflower (neutral):** low trade rate, few neighbours. *Probes B2B brief §7.1 cold-start /
  thin cycles.*
- **A4 Defrauder (bad):** draws the negative line to its cap (records obligations as debtor + settles
  them until `balance → credit_min`), then ceases activity — **there is no `Exit` op; the negative
  balance persists on the books.** *Stresses B2B inv. 4/5: the loss is bounded in magnitude by the
  negative cap, and the graduated-sanctions ladder should apply. Track A checks ladder ordering; **Track
  B (T2f) measures the mutualisation** — which creditors absorb the persisted negative balance — because
  "bounded to the defrauder" is false economics: mutual credit socialises the loss onto the counterparties
  holding the offsetting positives.*
- **A5 Sybil-hopper (bad):** attempts to have the membership layer admit multiple throwaway firm
  identities (`add_member`) to multiply credit lines. *B2B inv. 10 permissioned membership lives in a
  human/policy layer the SUT only stubs — `add_member` accepts any non-empty `ratified_by` string
  **and derives credit lines from self-declared `turnover_eur_cents`** (fake turnover ⇒ real lines;
  audit V20). If the sim
  admits lines freely, that is a **finding about the boundary of code-enforceable vs. human-enforceable**
  (X3), not a SUT break.*
- **A6 Velocity attacker (bad):** emits a machine-speed burst of `record_obligation` from one debtor
  within a `velocity_window_s` aiming to exceed `velocity_max_cents`. Intensity is a search-space knob.
  *Stresses B2B inv. 8 — the ledger's real breaker is a **per-debtor velocity cap that rejects** the
  over-cap obligation (raises), plus a manual `pause_cell`. There is **no cascade dynamic and no
  depth-cap D** in the SUT; clearing preserves net positions, so the "flash-loan" value-extraction
  surface does not exist. T1d measures the **rejection boundary**, not a cascade depth.*
- **A7 Cell-leaker (bad):** tries to move value between cells — by naming a foreign member in an
  obligation, or by inducing the harness to batch two cells into one `clear()`. *The SUT is single-cell:
  `clear()` takes one `cell_id`, obligations carry no cell tag, and a foreign member is **rejected** as
  "unknown member" (`clearing_solver._validate`); `record_obligation` likewise rejects a non-member. So
  the firewall (B2B inv. 6) holds by the **input contract**, not by "the solver refusing to net across a
  boundary" (it has no such logic). In Sim-B2B this reduces to T1c's **harness-partition guard** + the
  foreign-member rejection check; the true two-cell contagion firewall is a **Sim-Integrated** oracle
  (brief §5). Maps to B2B F7 (cross-cell leakage), whose own mitigation is "input is a single `cell_id`".*
- **A8 (probe overlay) LLMProbe — optional, inert in B2B:** wraps any archetype to generate a
  `NeedDescription` via an injected, cassette-backed model. **No B2B SUT module consumes free text**
  (the matcher is C2C Capa 3, out of scope), so in B2B the probe never touches the value path and at most
  biases which concrete `Trade` the actor's own rule policy emits. Off by default; its live consumer is
  Sim-C2C. **Proposal-only, never a value decision** (sim inv. 8). Suite runs offline with the stub.

## 4. Measurement (T-block — two tracks, never mixed — inv. 7)

- **T1 Track A (integrity oracles)** — for each round, independently re-derive and report PASS/FAIL +
  minimal exploit trace:
  - **T1a Conservation:** recompute each firm's net position from the raw obligation stream with a
    **second, differently-implemented oracle** (e.g. `networkx`), *not* the solver's own figure; assert
    pre==post across every clearing. The strongest, best-grounded oracle. *(solver conservation under
    load; B2B F2.)*
  - **T1b Credit-bound integrity (flag vs. reject — never clamp):** two distinct SUT behaviours, both
    checked. (i) The **solver** emits `credit_flags` for members whose *post-clearing* net is
    out-of-bounds — assert this list equals the independent recompute of out-of-bounds nets, and note
    clearing preserves net position so it can only surface a *pre-existing* breach, never create or
    clamp one. (ii) The **ledger rejects** (raises) any `record_obligation`/`settle_obligation`/
    `apply_clearing` that would breach a bound — assert the trace shows a **rejection**, never a
    clamped-and-continued balance. **Two different bound quantities — do not conflate them (audit
    V6):** the solver's flag quantity is the *obligation-net* (incoming − outgoing over the fed
    obligations); the ledger enforces the *balance* (at settle) and the *projected position* =
    balance + obligation-net (at record). A `credit_flag` is therefore informational, not per se a
    ledger-bound breach; the oracle recomputes each quantity by that SUT part's own definition and
    never asserts the flag list equals the ledger-breach list. *(B2B inv. 4; B2B F5 silent-clamp.)*
  - **T1c Firewall (single-cell SUT — harness-partition guard):** the SUT has no cross-cell operation
    (one `cell_id` per `clear()`; obligations carry no cell tag; a foreign member is rejected). So this
    oracle asserts (i) the harness **never assembles a `clear()`/ledger input mixing two cells** (a
    guard on the *harness's* own correctness) and (ii) the SUT **rejects** an obligation naming a
    non-member, and `apply_clearing` rejects a proposal whose `cell_id` differs from the cell's
    (audit V18). The genuine two-cell contagion firewall (B2B inv. 6) is a **Sim-Integrated** oracle
    over two instances (brief §5). *(B2B F7 — mitigation is the single-`cell_id` input contract.)*
  - **T1d Velocity breaker (rejection boundary — not cascade depth):** under A6, assert that within any
    `velocity_window_s` the committed obligations for a debtor never exceed `velocity_max_cents`
    (the ledger's window is **sliding**: records with `ts > now − velocity_window_s` count), and
    that the first over-cap `record_obligation` was **rejected** (raised); confirm `pause_cell` halts
    further mutation — noting `pause_cell` is **manual and human-ratified**: B2B inv. 8's "automatic
    pause on anomalies" has **no code counterpart**, so the pause *decision* is a harness
    breaker-policy modelling the missing automation, flagged via X7 the way appeal is via X5 (audit
    V7). Sweep `adversary_intensity` and **report the intensity at which bursts start
    being rejected** — the finding is the boundary, not a crash, and not a fictional "depth ≤ D."
    *(B2B inv. 8; there is no cascade in the SUT — clearing preserves net positions.)*
  - **T1e Sanctions (ladder ordering + two real findings; appeal is human-only):** assert every member
    status transition in the trace obeyed the ledger's ladder ordering (the SUT **rejects** a rung-skip
    upward — `update_member`); the *decision* to sanction comes from the harness compliance-policy actor
    modelling the human Capa-0 layer (flagged, not a SUT behaviour). **Appeal is not in the code** — do
    not assert an appeal path; flag it as human-layer (X5). Two findings the real SUT forces, surfaced
    not smoothed: **(T1e-i)** a `line_reduced` sanction on a *drawn-down* member **raises** (the ledger
    refuses a line change that would strand the current balance — `update_member` checks
    `new_min ≤ balance ≤ new_max`), so the ladder's most-relevant rung can be unenforceable exactly
    when needed; **(T1e-ii)** the ladder permits **unrestricted downward** moves (e.g. `expelled →
    active` in one step) — silent rehabilitation without appeal. *(B2B inv. 5.)*
- **T2 Track B (microeconomics)** — per round, report **aggregate distributions** (the `WelfareReport`
  type has no agent-indexed dimension; per-firm *economic* figures feed distributions but no
  identity-keyed reputation scalar is representable — T4):
  - **T2a** net internal debt reduced % (clearing-only and clearing+credit) — **reported with its
    sensitivity to `topology_params`, not gated.** The Sardex ≈25%/≈50% band is a sanity check (a value
    off by an order of magnitude trips X2, a probable modelling error); it is *not* a build gate,
    because `reduction_pct` is a property of the synthetic graph, not of the exact solver (H4 / §6.5).
  - **T2b** Gini of clearing benefit across firms (power-law-unequal expected) — a distribution over a
    per-firm *economic* benefit, legitimately aggregated.
  - **T2c** credit-enabled liquidity: volume of trade that cleared only because a credit line absorbed
    it.
  - **T2d** positive-cap effect (**honest open question, not a presupposed mechanism**): does the cap
    move value strong→weak (B2B inv. 4's *claim*), or does the ledger merely **reject** the over-cap
    obligation and transfer nothing (what the code *does*)? Report the measured strong→weak flow and,
    if it is ~0 beyond second-order rerouting, **escalate the gap between B2B inv. 4's redistribution intent
    and the shipped behaviour** as a flagged journal recommendation (X6) — a real finding either way.
  - **T2e** contracyclical delta: T2a/T2c with `credit_crunch=True` minus without.
  - **T2f** default mutualisation: when A4 defaults, report **how the persisted negative balance
    distributes across the creditor side** (distribution of realised loss: quantiles, concentration,
    top-decile share) — the true distributional cost, since no op erases the balance. Identity-free
    by the `WelfareReport` type (T4); the raw trace retains per-event identities for offline
    forensics — Track B never emits them (audit V13).
- **T3** Track A and Track B are returned and journaled as **separate** objects; no code path combines
  them into one score. *(sim inv. 7.)*
- **T4** `WelfareReport` is aggregate-only **by type** (no agent-indexed slot); `assert_no_person_scalar`
  runs the `FORBIDDEN_KEYS` substring scan as a **secondary lint** (symmetry with C2C N2 — insufficient
  alone, since a neutrally-named per-firm scalar would pass it; the type is the real guard). *(sim
  inv. 5, defensive; C14.)*

## 5. Research loop (R-block — autonomous within bounds)

- **R1** `B2BResearcher.next(history, search_space)` proposes the next `RoundConfig` **within the
  declared `search_space`** only. Default strategy: bandit/evolutionary over `actor_mix` +
  `adversary_intensity`, sweeping toward phase boundaries; an `LLMResearcher` option writes a natural-
  language hypothesis per round (cassette-backed). *(brief §3.)*
- **R2** The diff passes `apply_within_gate`, which **rejects any field that would touch the SUT
  source or step outside `search_space`**. *(inv. 2.)*
- **R3** The loop halts on: budget exhausted, convergence (no knob improves the (integrity, welfare)
  frontier over K rounds), or **any Track-A violation** (halt + surface, do not average). *(inv. 4.)*
- **R4** Every round is appended to a **hash-chained `Journal`**; the campaign replays byte-identically
  from `(scenario, seed, actor_mix, params, SUT commit, cassette)`. *(inv. 3.)*
- **R5** The campaign returns the journal + the Pareto frontier of `(integrity, welfare)` over the
  explored space. A single "score" is never the output. *(brief §3.)*

## 6. Input validation (E-block)
- **E1** A `RoundConfig` outside `search_space` is rejected before any round runs (fail fast).
- **E2** A non-integer or negative `cents` in a `Proposal` is rejected by the adapter (defence in
  depth; the SUT also rejects it — never repaired/clamped by the harness). *(B2B inv. 1.)*
- **E3** An LLM probe/researcher call without a cassette under a *reproducible* campaign is an error
  (no silent live call that would break determinism). *(inv. 3.)*
- **E4** A campaign whose SUT commit does not match the pinned hash aborts. *(inv. 2 / M3.)*

## 7. Negative control (build-acceptance gate — the real gate, per brief §7.1)
The build is not accepted until, against a **deliberately-broken copy** of the SUT, the harness
**halts on the first offending round and surfaces the exploit trace**. The plant must be **silent**,
or it proves nothing about the *independent* oracle:

- **N-01 must bypass ALL the SUT's own guards — there are three, not one (audit V2).** The SUT
  self-checks conservation at three points: (i) `clearing_solver.clear` raises on a changed net
  (`if post_net != pre_net: raise`); (ii) `mutual_credit_ledger.apply_clearing` independently
  re-verifies the settlement batch (per-member net delta must be 0) and **rejects** a non-conserving
  proposal; (iii) the ledger re-asserts global zero-sum balances after **every** op. A naive
  "drop a cent" copy is caught by (i); a copy with only (i) disabled is still caught by (ii) at apply
  time — in both cases an ordinary exception the SUT raised itself, **not** the silent breach the
  independent oracle exists to catch. And since a batch that passes (ii) cannot change committed net
  positions, a committed silent breach *requires* a ledger-side plant. So the negative-control copy is
  a **broken SUT, not just a broken solver**: drop a cent *and* disable the solver's conservation
  assert *and* the ledger's apply-time re-verification, so the bad settlement **commits** silently.
  Only then does T1a's independent recompute have something to catch that the SUT missed. (Variants
  that leave a guard intact are *supplementary* controls — they document the SUT's defence-in-depth
  and must surface as the SUT's own rejection in the trace — but none of them is the gate.)
- **N-02 silent-clamp ledger — the clamp must itself be silent (audit V3).** A copy that clamps a
  *balance* to its bound at settle moves one side more than the other, breaks zero-sum, and is caught
  by the ledger's own global balance-sum assert — the SUT again. The silent plant clamps the
  **effective amount** instead: `record_obligation`/`settle_obligation` silently shrink the requested
  cents to the bound headroom (both sides move equally; nothing raises) and report success. T1b must
  catch the divergence — an op accepted for X cents whose committed effect is Y < X, a
  clamped-and-continued balance — and halt.

A harness that cannot catch a planted bug cannot be trusted to report a real one — and a "planted bug"
the SUT catches for you tests the SUT's self-defence, not the oracle. *(The harness's own
self-confirmation guard; parent AGD-045.)*
