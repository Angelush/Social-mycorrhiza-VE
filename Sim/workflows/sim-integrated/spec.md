# Sim-Integrated — spec (the compact bundle)

Runs **both** SUTs over **one population** on the **shared engine** (`../engine/spec.md`), reusing the
proven `B2BAdapter` and `C2CAdapter` unchanged. This file states only what is *integration-specific*;
`sim-b2b/`, `sim-c2c/`, the capa/B2B bundles, and `engine/spec.md` carry everything else — do not
restate them. Built LAST, per brief §7.

## 0. The point (brief §5)
The integration exists to make the **cross-effects** observable and, above all, to **test the firewall
between the value path (B2B, denominated) and the social path (C2C, non-denominated)** — the seam is
exactly where a *new* failure mode lives. If the harness finds a leak, that is the highest-value
finding in the whole project.

## 1. The single seam: a shared identity
One `Identity` (`identity.py`) lives in both worlds: a **business** is simultaneously a B2B firm and a
C2C market-room org; a **person** is a C2C member who may also be a sole-trader firm. The engine's
actor identity is domain-agnostic precisely so one identity spans both SUTs. `IntegratedWorld`
(`world.py`) holds **two** `B2BAdapter` instances (cell-A, cell-B — two independent ledger states) and
**one** `C2CAdapter`, and steps all three per tick over the shared population. Two clocks: B2B integer
`ts` and the C2C string clock both derive from `world.tick`.

## 2. The three firewalls Track A must TEST (not assume)
Each is checked over recorded `BridgeAttempt(kind, request, output, provenance)` results — the analogue
of B2B's `ClearingOutcome`, carrying BOTH sides of a seam-crossing so the oracle re-derives
independently.

- **F-VS1 debt→gift-room (value into social)** — a denominated B2B debt must NOT enter a C2C
  gift/equality room (parent C2C inv. 1, now a *cross-system* kula/gimwali wall). **Enforced by the
  real C2C membrane**: a payload carrying a value key (`_cents`, `price`, `debt`, `owed`, `balance`)
  raises `MembraneBreachError` → the attempt is `Rejected`. The oracle FAILs only if such an admit
  *succeeded* (the wall was bypassed) AND the leaked amount matches a real B2B obligation (proving it
  is genuine cross-system value, not merely any market key).

- **F-VS2 person-scalar→credit (social into value)** — a C2C person-scalar (a legibility/reachability
  answer) must NOT become an input to a B2B credit decision (parent C2C inv. 2 + B2B inv. 9,
  human-in-loop). **This wall is NOT enforceable by either real SUT**: `mutual_credit_ledger.
  update_member` accepts any strict-int `credit_max_cents` and cannot see that the int was *derived
  from* a social scalar. So the oracle enforces it by **provenance**: any successful B2B credit op
  tagged `provenance="c2c_person_scalar"` is a FAIL. This is the seam's genuinely new failure mode —
  the oracle is the ONLY thing that can catch it, and a cooperative population (credit ops with
  `turnover`/`human_ratified` provenance) passes.

- **F-CC cell-to-cell contagion (B2B inv. 6)** — a default or bound-breach in B2B cell A must NOT move
  value into cell B. The shipping B2B SUT is single-cell, so *within* one Sim-B2B world the wall holds
  trivially by the input contract (an unknown member is rejected); the genuine oracle needs **two
  ledger instances** and lives here. **Enforced by the real B2B**: recording an obligation in cell B
  whose counterparty is not a cell-B member raises `ValueError("debtor"/"creditor")` → `Rejected`. The
  oracle FAILs if a cell-B obligation was accepted with a party absent from cell B's roster, or if
  cell B's independently-recomputed net value moved in lockstep with cell A's default.

## 3. The adversary: Bridge-exploiter (generalises the Cell-leaker)
`BridgeExploiter` (`policies.py`) exists only to smuggle value or a score across a seam: it emits
`LeakDebtToGiftRoom`, `ScoreToCredit`, and `CrossCellValueMove`. Against the real SUTs, F-VS1 and F-CC
are rejected (the walls hold); F-VS2 *succeeds against real B2B* and is caught only by the provenance
oracle — the headline finding, demonstrated in its own test, not folded into the green campaign.

## 4. The green campaign vs the finding
- The **clean campaign** (`campaign.py`) runs cooperative bridged actors + a Bridge-exploiter
  restricted to F-VS1/F-CC (both rejected by the real code): **zero violations**, byte-reproducible —
  proving the two SUT-enforced walls hold across the real stack.
- **F-VS2 is demonstrated separately** as the exploitable seam: the provenance oracle FAILs on a
  `ScoreToCredit` against the *real* B2B, and PASSes a legitimate credit op — the highest-value
  finding, reported honestly rather than hidden.

## 5. Negative control (the gate — MI-3)
- **NI-01 debt-leak** reuses the Sim-C2C `n02_fixture` membrane (market scan silently disabled): the
  debt→gift admit *succeeds*; F-VS1 catches it; the real membrane raises on the same interaction.
- **NI-02 cross-cell** plants a B2B ledger copy that silently accepts an unknown (cross-cell) debtor
  (the `debtor not in members` guard removed): the cell-B obligation *commits*; F-CC catches it via an
  independent roster/conservation recompute; the real ledger raises on the same op. Non-vacuity: a
  naive plant that also breaks the balance-sum guard is self-caught by the ledger's remaining
  `balance_sum` check.

## 6. Descriptive-only + one-way door carry over
Track B (if emitted) stays position-relative/descriptive; the researcher's search space contains no
Track-B objective and never patches either SUT (the one-way door stays shut across both worlds).
