# Failure Model + Stress Report — Capa 1 Relational-Mode Partition

> Produced by red-team. Hostile review of the Capa-1 firewall spec.

## Failure modes (F#)
- **F1 — Membrane leak by nesting.** A market instrument buried inside `payload.terms.deal.fee_cents`
  passes a top-level-only check → market logic enters the gift room. *Mitigation:* M1 recursive
  scan; AC2/B2; property P2 (leak at random depth always refuses).
- **F2 — Repair-instead-of-refuse.** Code "helpfully" strips the `price` field and admits the
  interaction → a corrupted communal interaction is admitted as clean, and the corruption is
  now invisible. *Mitigation:* M2/N5; AC2 asserts the field is never stripped-then-admitted;
  only admit-as-is or refuse.
- **F3 — Surveillance creep via the market room.** Someone assumes "the market room already has
  numbers, so a `trust_score` is fine there." → a person-scalar enters through the one room
  that allows denomination. *Mitigation:* M5 — the surveillance-shape scan runs in **all**
  rooms, orthogonal to the market membrane; AC5/E2.
- **F4 — The refusal becomes a dossier.** The firewall stores/returns `{"participant": "t1",
  "admitted": false, "reason": "..."}` → a persistent record of who tried to do what: a
  blacklist by another name (inverts invariant 3). *Mitigation:* N3/AC6 — a breach **raises**;
  there is no `admitted:false` return; the verdict echoes no payload content and no person.
- **F5 — Directionality inverted.** A symmetric wall also refuses gift-shaped content in the
  market room → the system nags sellers for "not pricing" a free sample, pushing everything
  toward pricing. *Mitigation:* M3/AC4 — the wall is market→gift/equality only.
- **F6 — Ledger over-block.** Banning all reciprocity in `equality_matching` breaks its core
  logic (balanced turns) → the equality room can't function. *Mitigation:* M4/AC3 — ledger ban
  is `communal_gift`-only; equality allows balanced-in-kind counters, bars only priced/denominated ones.
- **F7 — LLM/optimization creep.** "Let an agent *infer* the room, or nudge a gift toward a
  priced listing." → engagement/monetization optimization (violates invariants 1 & 8).
  *Mitigation:* N1 — the room is *declared* and type-checked, never inferred by a model here.
- **F8 — Taxonomy drift from Capa 4.** Capa 1 and Capa 4 keep separate forbidden-key lists that
  diverge → the two layers disagree on the membrane (AC-X breaks). *Mitigation:* P2 (constraints)
  — share the exact `FORBIDDEN_KEY` set; AC-X regression-checks agreement.

## Stress findings (ST#)
- **ST1 — Substring false positives.** `_cents` as a substring could catch an innocent key
  (e.g. `"accents"`, `"incentive"`). *Found gap:* `"accents"` contains `cents`, `"incentive"`
  contains no full MARKET token but `"scent"`⊄list; **decision:** match `_cents` (with the
  underscore) and whole tokens like `price`,`cost`,`fee`,`currency`,`valuation`,`denominat`;
  document that the taxonomy is a *shape heuristic* biased to over-refuse in non-market rooms
  (a false refusal is safe — caller re-tags the room — while a false admit is a membrane leak).
  Test with `"incentive_note"` (must NOT trip) and `"price"` (must trip).
- **ST2 — Empty payload / empty participants.** A gift with `payload={}` and `participants=[]`
  is valid (an offer with no structured content) → admit. *Verify:* AC1 tolerates empties.
- **ST3 — `market_price` with zero market fields.** Legitimately gift-shaped market interaction
  (free sample) → admit (AC4). Not a breach.
- **ST4 — Self-confirmation.** The firewall's own scanner agrees with its own bug. *Mitigation:*
  independent recursive key-walker oracle in tests (tests.md cross-check, AGD-045).
- **ST5 — Forgetting vs. auditability (open §6.6).** The verdict is auditable yet must not be a
  permanent record. *Partial mitigation:* `expires_at` carried through (M7); the firewall stores
  nothing. **Flagged:** enforcing expiry is the caller's/storage responsibility, outside this
  pure function — noted, not faked-resolved (mirrors Capa-4 ST5).

## Open (system-level, NOT this firewall) — do not fake-resolve (§6)
- **Who decides the room is honest?** The firewall type-checks a *declared* mode; it cannot tell
  that a genuinely commercial deal was mislabeled `communal_gift` to dodge the market room. That
  is a governance/social question (§6.1: "who governs decides"), not a code one — the firewall
  enforces the *shape* of the declared room, it does not adjudicate intent. *Stakes: a cage if
  mis-governed, not just a failure.*
- **Sybil / token↔person binding** (§6.2) — unsolved; the firewall treats `participants` as opaque
  tokens and never binds them to people.
- **Fertility metric is Goodhart-prone** (§6.4); federation as recentralizing bottleneck (§6.5);
  exit-vs-accountability (§6.6). All governance/relationship problems — flagged, not coded.
