# Acceptance Criteria — Capa 1 Relational-Mode Partition

> Produced by design-evals. Binary Done (AGD-028): verify the artifact, not a self-report.
> Every AC is machine-executable with zero human judgement.

- **AC1 — Well-typed interactions are admitted.** A `communal_gift` with only gift-shaped
  payload, an `equality_matching` with balanced-in-kind (turn/slot) payload, and a
  `market_price` with a price are each **admitted**; the verdict echoes `mode`, `cell_id`,
  `interaction_id`, carries `expires_at` through (or `null`), and sets `admitted: true`.
  Pass/fail: verdict equality.
- **AC2 — Market leak into a non-market room is refused (kula/gimwali wall).** A
  `communal_gift` or `equality_matching` whose payload carries a market instrument
  (`price`, `cost`, `fee`, `currency`, `*_cents`, `valuation`) — **at any nesting depth** —
  is **refused** (`MembraneBreachError`). The market instrument is never stripped and then
  admitted. Pass/fail: exception raised. (Targets invariant 1.)
- **AC3 — Reciprocity ledger is refused in the gift room, allowed in kind in the equality
  room.** A `communal_gift` carrying a `debt`/`owed`/`balance`/`reciprocity` key is
  **refused**; the same balanced-in-kind counter in an `equality_matching` interaction is
  **admitted** (balanced exchange is that room's logic). Pass/fail: refuse vs. admit.
  (Targets §4 Capa 1 "rastrear la reciprocidad la mata".)
- **AC4 — Directionality.** A `market_price` interaction whose payload is entirely
  gift-shaped (no price at all) is **admitted** — the wall is one-directional
  (market→gift/equality), never the reverse. Pass/fail: admitted. (Targets M3.)
- **AC5 — Anti-surveillance shape (all rooms, the C2C-defining tail case, AGD-016).**
  (a) No verdict field anywhere scores/ranks/rates/persists a person (recursive key scan
  rejects `score|rating|reputation|rank|blacklist|ban|penalty|global_id|dni`); the verdict
  echoes **no** payload content. (b) An interaction carrying any such forbidden key **at any
  depth, in any room** (including `market_price`) is **refused**, not admitted. Pass/fail:
  key-scan + rejection. This is the case where "correct" means *refusing to accept the
  surveillance-shaped artifact*.
- **AC6 — No stored refusal / whitelist-not-blacklist.** The API has no code path that
  returns `admitted: false` — a breach **raises**; there is no verdict object recording that
  a person or interaction was rejected. Pass/fail: static — the only success return sets
  `admitted: true`, and refusals are exceptions. (Targets invariant 3 / F4.)
- **AC7 — Determinism.** Running the firewall twice on the same input yields byte-identical
  JSON. Pass/fail: string equality.
- **AC8 — Envelope validation.** Unknown `mode`, empty `interaction_id`/`cell_id`,
  non-list `participants`, or non-dict `payload` are **refused** (not repaired). Pass/fail:
  exception raised.

## Consistency with Capa 4
- **AC-X — Capa-4 AC6 is subsumed.** Feeding a Capa-4 binary campaign's shape (an
  `equality_matching` interaction whose payload carries `amount_cents` or `sponsor_bonus_cents`)
  to this firewall **refuses** it — the same verdict Capa-4 reaches independently. The two
  layers must not disagree on the membrane. Pass/fail: both refuse.
