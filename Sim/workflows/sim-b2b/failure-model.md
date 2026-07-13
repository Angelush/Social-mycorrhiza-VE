# Failure Model + Stress Report — Sim-B2B

> Produced by red-team. Hostile review of the **harness** spec (not the SUT — the SUT has its own
> failure model). The danger here is a simulation that lies: gives false confidence, or measures the
> wrong thing.

## Failure modes (F#)
- **F1 — The sim reimplements the SUT and tests a fiction.** Someone stubs the netting "to go faster"
  and now the campaign validates the stub, not the shipping solver. *Mitigation:* C1/C11; the SUT is
  imported read-only with a pinned commit; the negative-control gate (spec §7) only passes if the real
  code's bug is caught.
- **F2 — Self-confirmation oracle.** Track A asks the SUT for its own net positions, so a solver bug
  and its checker share the error and both say PASS. *Mitigation:* C3 — Track A re-derives every
  invariant from the *raw obligation stream*, independently (parent AGD-045).
- **F3 — Violation averaged into a pass rate.** A conservation break in 1 of 10,000 rounds is reported
  as "99.99% integrity," burying a system-defining bug. *Mitigation:* C4 — halt-and-surface on first
  violation; a violation is a headline, not a point (inv. 4).
- **F4 — The two tracks contaminate.** A high welfare number is used to wave away a red integrity
  result ("it's efficient, ship it"). *Mitigation:* C5 — separate objects end to end; no combined
  score (inv. 7).
- **F5 — Autonomy drift.** The autonomous researcher wanders into an uninteresting corner and spends
  the whole budget there, or silently mutates something it shouldn't. *Mitigation:* C7 bounded
  `search_space` + C12 SUT-untouchable + X4 too-narrow-space flag; the search space is a human design
  act (brief §6.2).
- **F6 — Non-reproducible finding.** An LLM probe made a live call; the exploit cannot be replayed and
  is dismissed as noise (or worse, believed without proof). *Mitigation:* C6/C16/E3 — cassette-backed,
  seeded, byte-reproducible; a live call on the reproducible path is an error.
- **F7 — The reputation-score smuggle.** Someone adds a per-firm "reliability score" to Track B for
  convenience, importing the exact god-view shape the C2C system forbids onto the value path.
  *Mitigation:* C14 + `assert_no_person_scalar` on `WelfareReport` (inv. 5, defensive).
- **F8 — Adversary theater.** Bad actors are hand-wavy "chaos" that don't map to a real threat, so
  coverage is illusory. *Mitigation:* C9 — every **live** adversary maps to an invariant it stresses
  (B2B inv. 4/5/8/10), an input-contract rule (B2B F7), or a documented open problem, with the mapping
  cited; the planted defects B2B F1–F6 belong to the negative control, not to an actor (the two axes,
  brief §2 — audit V16).
- **F9 — Calibration mistaken for validation.** The sim reproduces Sardex's ≈25%/≈50% and the team
  declares the design "empirically proven." *Mitigation:* X2 + brief §6.5 honesty flag — the synthetic
  topology is a hypothesis; matching an anchor shows *not-obviously-wrong*, never *right*.
- **F10 — Green-means-safe.** A clean campaign is presented as proof of security. *Mitigation:* C15 —
  report coverage over the explored space, never safety; the sim only falsifies (brief §6.1).

## Stress findings (ST#)
- **ST1 — Velocity-breaker timing.** The per-debtor velocity breaker keys on `velocity_window_s` and an
  integer `ts`; a mis-modelled tick↔window↔ts mapping could make the breaker look better or worse than
  reality. *Found gap:* `velocity_window_s` + `ticks_per_second` must be explicit, documented
  `RoundConfig` fields, swept in the search space. T1d measures the **rejection boundary vs. intensity**
  — there is no cascade depth in the SUT to measure (the breaker rejects; it does not throttle a
  propagation).
- **ST2 — Sybil at the membership gate.** B2B inv. 10 lives in a human/policy layer the sim can only
  stub; A5's "success" is really a statement about the stub. *Mitigation:* X3 — surface as a gate
  finding, flag the boundary of code-enforceable vs. human-enforceable.
- **ST3 — Defrauder loss attribution (mutualisation, not "bounded to the defrauder").** The loss is
  *bounded in magnitude* by the negative cap, but it is **not** absorbed by the defrauder — the
  persisted negative balance is socialised onto the **creditors holding the offsetting positives**
  (that is what mutual credit *does*). Asserting "bounded to the defrauder's line and non-contagious"
  is wrong economics. *Verify:* T1a (conservation still holds) + **T2f default-mutualisation** (trace
  which creditors realise the loss) on an A4-heavy mix. "Non-contagious" is only meaningful *across
  cells* — and there is one cell, so it is trivially true (see ST6).
- **ST4 — Cassette staleness.** A cassette recorded against an old persona/model silently diverges from
  intended behaviour on replay. *Mitigation:* cassette carries a persona+model hash; a mismatch is an
  error (extends E3).
- **ST5 — Frontier, not scalar.** Teams will want "the number." *Mitigation:* R5 returns a Pareto
  frontier of (integrity, welfare); resist collapsing it — the collapse is where F4 re-enters.
- **ST6 — The negative control the SUT catches for you (false confidence in the oracle).** The solver
  already self-raises on a conservation break, so a naive "drop a cent" plant surfaces as an *exception*
  — the SUT caught it, not the independent oracle. A harness that treats that as "negative control
  passed" has verified the SUT's self-defence, not its own oracle, and will believe it can catch a
  *silent* breach it actually cannot. **And the same logic bites one guard deeper (audit V2):** the
  ledger's `apply_clearing` *re-verifies batch conservation* (per-member net delta = 0) and its global
  zero-sum assert runs after every op, so a solver-only plant is still self-caught at apply time — and
  a batch that passes that check cannot change committed net positions at all. *Mitigation:* spec §7 /
  N-01 — the plant is a broken **SUT**, not a broken solver: drop a cent **and** disable the solver's
  conservation assert **and** the ledger's apply-time re-verification, so the bad settlement *commits*
  silently; only then does T1a's independent recompute earn its keep. Golden G-04 freezes the *silent*
  variant.
- **ST7 — Firewall theatre on a single-cell SUT.** The shipped SUT has no cross-cell operation, so a
  "Cell-leaker" oracle that asserts "the solver refused to net across a boundary" tests a mechanism that
  does not exist — vacuously green, and mistaken for coverage (the sim's own F8, adversary theatre).
  *Mitigation:* T1c is retargeted to a harness-partition guard + foreign-member rejection; the genuine
  two-cell contagion firewall (B2B inv. 6) moves to Sim-Integrated over two instances (brief §5).
- **ST8 — The breaker the brief promised but the code lacks (auto-pause).** B2B inv. 8 calls for
  "automatic pause on anomalies"; the shipped `pause_cell` is manual and human-ratified, and no anomaly
  detector exists in the SUT. A harness whose breaker-policy quietly supplies that automation and then
  reports "breaker held" has tested its own policy, not the SUT. *Mitigation:* T1d labels the pause
  decision as harness-policy (a model of the missing human/automation layer); X7 surfaces the gap as a
  flagged recommendation, symmetric with X5 (appeal) and X6 (redistribution). (Audit V7.)

## Open (system-level, NOT the harness — do not fake-resolve; brief §6)
- A green campaign proves coverage, not safety (§6.1). Autonomous rounds trade oversight for throughput
  (§6.2). The C2C fertility proxy is Goodhart-prone by construction and must never become the loop's
  objective (§6.3, matters at integration). Calibration ≠ validation (§6.5). These are honesty
  boundaries of the method, flagged in every report — not coded away.
