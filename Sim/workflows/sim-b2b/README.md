# Sim-B2B — falsification harness + microeconomic microscope for the B2B system

spec bundle (upstream: what to build + how to know it's right) for the **B2B simulation**. It
drives the **real** B2B code (`../../../B2B/src/clearing/clearing_solver.py`,
`../../../B2B/src/ledger/mutual_credit_ledger.py`) with a population of good/neutral/bad actors inside
a Karpathy-style auto-research loop. Sibling of `../sim-c2c` (stub) and `../sim-integrated` (stub);
shares `../engine/spec.md`.

> **North star (brief §0):** the sim is a **driver and an oracle, never a second copy of the
> mechanism**, and it obeys the laws it tests — the agent proposes, the gate disposes, and the one-way
> door over value never opens inside the loop.

## The bundle
```
.specsmith.json     # route + species + which real modules are the SUT
intent.md           # the real objective + correctness contract
context.md          # data room: the SUT, terminology, anchor data, actor archetypes, generators
architecture.md     # components by nature: [SUT] [HARNESS] [ORACLE] [RESEARCHER] [LLM-PROBE]
spec.md             # self-contained build spec (M/A/T/R/E ids) + negative-control gate
constraints.md      # MUST / MUST-NOT / escalation, each with a because-clause
failure-model.md    # red-team of the HARNESS (a sim that lies) — F1–F10 + stress findings
audit.md            # audit-feedback-loop: findings → enforcement (M#/H# authoring pass; V# source-verification pass)
evals/acceptance.md # AC1–AC22: harness-integrity + system-finding criteria
evals/tests.md      # A/B/C + property + golden-set + negative-control tests
```

## The two tracks (never mixed — brief §1 sim inv. 7)
- **Track A — invariant integrity `[ORACLE]`:** conservation (independent recompute); credit-bound
  (*solver flags / ledger rejects — neither clamps*); cell firewall (*held by the single-`cell_id`
  input contract* — the true two-cell firewall is a Sim-Integrated oracle); velocity breaker
  (*over-cap obligation rejected* — a rate limit, not a cascade); sanction ladder (*ordering enforced;
  appeal is human-layer, not in the code*). Red/green + exploit trace. A violation **halts** the
  campaign (a headline, not a data point).
- **Track B — microeconomics `[STATISTICS]`:** net-debt reduced % (*reported with topology-sensitivity,
  not gated*), Gini of clearing benefit, credit-enabled liquidity, **positive-cap effect** (*does it
  redistribute or merely block?* — the honest open question), contracyclical delta, **default
  mutualisation** (*how a defrauder's persisted loss distributes across creditors*). Aggregate-only
  by type — never a per-firm reputation scalar.

## The seven actors (each stresses an invariant, verified against the real SUT — brief §2)
Circulator (good) · Hoarder (neutral, positive-cap effect) · Wallflower (neutral, thin cycles) ·
Defrauder (bad, B2B inv. 4/5 + mutualisation) · Sybil-hopper (bad, membership gate — human-layer stub) ·
Velocity attacker (bad, B2B inv. 8 velocity-cap rejection) · Cell-leaker (bad, single-cell → harness
partition + foreign-member rejection). *Live adversaries stress invariants; planted implementation
defects (B2B F1–F6) are the negative control's job, not an actor's (§2 two-axes note).*

## The defining build gate
**The negative control (spec §7 / N-01, N-02):** against a deliberately-broken copy of the SUT, the
harness must **halt on the first offending round and surface the exploit trace.** The plant must be
**silent**, and the SUT guards conservation at *three* points (solver self-assert; ledger apply-time
batch re-verification; global zero-sum assert — audit V2): the cent-drop plant must drop a cent *and*
disable the solver's conservation assert *and* the ledger's apply-time re-verification (silencing
only one leaves the plant self-caught by the SUT, testing its self-defence, not the oracle); the
clamp plant must **silently clamp the effective amount** to the bound headroom (a balance-clamp trips
the SUT's own zero-sum assert — V3). A harness that cannot catch a planted bug cannot be trusted to
report a real one. Golden test **G-04** freezes this: if a future change makes the broken-SUT runs
*pass*, the harness has gone blind — the loudest possible regression.

## Status
- [x] spec bundle (Deep route) — this document set
- [ ] Shared engine (`../engine/spec.md`) implementation
- [ ] Sim-B2B implementation (adapter, actors, two-track measurement, researcher, one campaign)
- [ ] Sim-C2C (after B2B proves the engine) · Sim-Integrated (last)

## Honesty boundaries (brief §6 — flagged, never coded away)
A green campaign proves **coverage, not safety** — the search space is finite, the real adversary is
not. Autonomous rounds trade oversight for throughput (mitigated structurally: SUT immutable, journal
hash-chained, halt-on-violation). Synthetic topologies are hypotheses; **calibration ≠ validation** —
reproducing Sardex's ≈25%/≈50% shows *not-obviously-wrong*, never *right*.
