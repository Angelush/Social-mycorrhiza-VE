# Sim-Integrated — failure model (seam-specific defects the negative control must catch)

The integration seam creates failure modes that neither single-system sim can express. Two are
SUT-enforced walls whose bypass must be caught (NI-01/NI-02, the negative control); one (F-VS2) is a
wall NO SUT can enforce, so the oracle itself is the only guard.

## HI-1 — silent debt→gift-room leak (→ NI-01, oracle F-VS1)
A broken C2C membrane copy (the Sim-C2C `n02_fixture`, market scan disabled) *admits* a communal_gift
interaction whose payload carries a `*_cents` value lifted from a real B2B obligation, instead of
raising. A denominated debt has entered a non-denominated room — the cross-system kula/gimwali wall is
down and silent.
- **Caught by**: F-VS1 — an admitted gift/equality interaction carrying a value key whose amount
  matches a live B2B obligation is a FAIL.
- **Control**: the real membrane raises `MembraneBreachError` on the identical interaction.
- **Non-vacuity**: the plant is surgical (surveillance scan intact), so a payload that also carries a
  forbidden key still self-catches — F-VS1, not the surveillance wall, is what catches NI-01.

## HI-2 — silent cross-cell contagion (→ NI-02, oracle F-CC)
A broken B2B ledger copy with the `debtor not in members` (and `creditor not in members`) guard
removed *accepts* an obligation in cell B whose debtor is a cell-A-only member — letting a cell-A
default draw value out of cell B. The single-cell contagion firewall (B2B inv. 6) is silently down.
- **Caught by**: F-CC — a committed cell-B obligation with a party absent from cell B's independently
  reconstructed roster is a FAIL.
- **Control**: the real ledger raises `ValueError("debtor")` on the identical op.
- **Non-vacuity (ST6)**: a naive plant that also drops the terminal `balance_sum == 0` guard is
  self-caught by the ledger's remaining conservation check — so only the surgical membership-guard
  removal produces a silent accept, proving F-CC (not the SUT's own conservation) is the gate.

## HI-3 — social score feeds a credit decision (F-VS2; the seam's native failure, no negative control)
This is NOT a broken-SUT plant: the real `mutual_credit_ledger.update_member` *accepts* a credit bound
derived from a C2C reachability answer, because a strict int carries no provenance. The failure is
intrinsic to the seam. The oracle enforces it by provenance: any successful B2B credit op tagged
`c2c_person_scalar` is a FAIL, while a `turnover`/`human_ratified` credit op passes. Demonstrated as a
first-class finding, not gated behind a broken copy — because there is no SUT wall to break.

## Why these
NI-01/NI-02 prove the harness independently re-derives the two SUT-enforced firewalls (value→social,
cell→cell) rather than trusting either SUT's self-report. F-VS2 proves the harness catches the one
firewall that exists *only* as a harness invariant — the automated social-score-to-credit denial that
both systems are built to prevent (C2C inv. 2 + B2B inv. 9).
