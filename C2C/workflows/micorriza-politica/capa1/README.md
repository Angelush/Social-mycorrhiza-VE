# Capa 1 — Relational-Mode Partition ("las habitaciones")

SpecSmith sub-bundle for the **most important layer** (brief §4 Capa 1): the
architectural membrane that keeps market logic out of the gift and equality rooms
(invariant 1, the kula/gimwali wall). It is the `[INVARIANTE ARQUITECTÓNICA]` firewall /
type-system every other layer routes through.

Shares the system-wide `../intent.md`, `../context.md`, and `../architecture.md` with the
Capa-4 build. Capa-1-specific docs live here:

```
spec.md            # the buildable blueprint (rooms, membrane rules, algorithm)
constraints.md     # MUST/MUST-NOT with because-clauses
evals/acceptance.md  evals/tests.md   # AC1–AC8 + AC-X, machine-checkable
failure-model.md   # red-team: F1–F8, ST1–ST5, open (governance) problems
```

## The three rooms (Fiske)
- **`communal_gift`** — mutual aid / care. No price, no denomination, **no reciprocity ledger** (tracking it kills the gift).
- **`equality_matching`** — turns, favors, time-banks, ROSCAs. Balanced **in kind**, never priced.
- **`market_price`** — real C2C/C2B commerce. Price and denomination belong here.

The membrane is **directional** (market → gift/equality is forbidden; the reverse is fine).
The **surveillance-shape ban holds in all three rooms** and reuses the exact `FORBIDDEN_KEY`
taxonomy of the Capa-4 engine — one anti-surveillance definition, not two.

## Relationship to Capa 4
Capa-4's AC6 (no price/bonus in a binary campaign) is a *special case* of this membrane:
a binary campaign is an `equality_matching` interaction. Capa 1 generalizes that one-off
check into the reusable primitive (AC-X regression-checks that the two layers agree).

## Implementation
`src/partition/membrane.py` — pure, stdlib-only, deterministic, proposal-only firewall.
Tests: `tests/test_membrane.py` (AC1–AC8, AC-X) + `tests/test_membrane_properties.py` (P1–P4).
