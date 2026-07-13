# Sim-Integrated — acceptance criteria (numbered, per milestone)

Real pytest against the ACTUAL B2B and C2C code (never mocked; the only stub allowed is the C2C
matcher `propose`, unused on the integration path). Every commit after MI-0 held against these.

## MI-0 — spec bundle
- **ACI0.1** spec.md, evals/acceptance.md, failure-model.md exist; spec restates neither the engine
  nor the sib bundles.
- **ACI0.2** all three firewalls defined with their enforcement locus (real SUT vs harness provenance).

## MI-1 — identity + world + proposals
- **ACI1.1** one `Identity` spans both worlds; `IntegratedWorld` holds two `B2BAdapter`s + one
  `C2CAdapter` and steps all three per tick.
- **ACI1.2** baseline B2B trade and C2C gift both drive the REAL modules; both B2B clocks and the C2C
  clock advance from `world.tick`.
- **ACI1.3** the three bridge proposals exist and record `BridgeAttempt(kind, request, output,
  provenance)`.

## MI-2 — Track A firewalls + Bridge-exploiter
- **ACI2.1** three oracles: value_social_debt_leak, value_social_score_to_credit, cell_contagion.
- **ACI2.2** F-VS1: a rejected debt→gift admit passes; a (fixture) admitted one fails.
- **ACI2.3** F-VS2: a `ScoreToCredit` against the REAL B2B is caught (FAIL) by provenance; a legitimate
  credit op passes.
- **ACI2.4** F-CC: a rejected cross-cell move passes; an accepted foreign-party obligation fails.
- **ACI2.5** Track A imports neither SUT's modules (AST).

## MI-3 — negative control (the gate)
- **ACI3.1** NI-01: F-VS1 catches the silent debt-into-gift admit (broken membrane); real membrane
  raises on the same interaction.
- **ACI3.2** NI-02: F-CC catches the silent cross-cell debtor (broken ledger); real ledger raises on
  the same op; naive over-broad plant self-caught (ST6).
- **ACI3.3** broken copies live only under `negative_control/`; B2B/ and C2C/ byte-unchanged.

## MI-4 — researcher / campaign
- **ACI4.1** clean campaign (cooperative + F-VS1/F-CC exploiter): zero violations, byte-reproducible.
- **ACI4.2** F-VS2 finding demonstrated in its own test against the real B2B.
- **ACI4.3** researcher never patches either SUT; search space carries no Track-B objective. Full Sim
  suite (B2B + C2C + Integrated) green.
