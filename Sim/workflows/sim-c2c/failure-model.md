# Sim-C2C — failure model (harness-specific defects the negative control must catch)

This lists defects **in the harness/SUT-copy** that are NOT actor-inducible — the negative control's
job (mirrors B2B's F1–F6 split: live adversaries stress invariants; numbered implementation defects
are the control's job). Each is a *silent* plant: the broken SUT copy must bypass its own guards, or
the test measures the SUT's self-defence rather than the harness oracle.

## H-1 — silent person-scalar (→ N-01, oracle T-A1)
A `legibility_query` copy that, alongside its normal `from_your_position` output, emits a per-node
`reachability` float (a god-view centrality scalar). It evades the real `FORBIDDEN_KEYS` scan because
`reachability` carries no forbidden substring — exactly the README's named trap (`fertility` /
`reachability` / `centrality` all pass the blacklist).
- **Caught by**: T-A1 structurally — the scalar cannot be represented in a `WelfareReport` (type
  wall) and the Track-A output-shape oracle flags any layer output whose shape grew a scalar keyed by
  a person token.
- **Control**: the real `legibility_query` never emits such a field (its output is paths/facts only).
- **Non-vacuity (ST6)**: a *naive* variant naming the field `trust_score` IS self-caught by the real
  `FORBIDDEN_KEYS` scan (`score`) — proving the gate isn't testing the blacklist but the structure.

## H-2 — silent market leak (→ N-02, oracle T-A2)
A `membrane` copy whose `MARKET_KEYS` scan in the `communal_gift`/`equality_matching` branch is
disabled, so it *admits* an interaction carrying `price`/`_cents` into a gift room and returns
`admitted: True` instead of raising `MembraneBreachError`. The kula/gimwali wall (inv. 1) is
silently down.
- **Caught by**: T-A2 — an admitted (returned) interaction in a non-market room carrying a
  `MARKET_KEYS` shape is a FAIL.
- **Control**: the real `membrane.admit` raises `MembraneBreachError` on the identical interaction.
- **Non-vacuity (ST6)**: a naive variant that also lets a `FORBIDDEN_KEYS` (`rating`) shape through
  is still self-caught by the untouched surveillance scan (step 2 runs before the membrane branch),
  so only the *surgical* market-scan removal produces a silent admit — proving T-A2, not the
  surveillance wall, is what catches N-02.

## Why these two
They cover the two structurally distinct C2C breach shapes: **(H-1)** the anti-goal that carries *no
forbidden substring* — the reason the type wall exists and the blacklist is insufficient; and
**(H-2)** a *bypassed raise* — the wall that normally arrives as an adapter exception, so the oracle
must catch the case where the exception never fired. A gate covering both proves Track A
independently re-derives integrity rather than trusting the SUT's self-reports.
