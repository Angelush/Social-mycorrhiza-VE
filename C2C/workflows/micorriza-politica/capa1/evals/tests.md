# Test Cases — Capa 1 Relational-Mode Partition

> Produced by design-evals. Each: input, expected verdict, verification rule.

## Test A — Normal: one well-typed interaction per room (AC1)
- **A1 gift:** `mode=communal_gift`, payload `{"offer": "help moving", "note": "no strings"}` → **admitted**.
- **A2 equality:** `mode=equality_matching`, payload `{"turns_taken": 1, "turns_owed_in_kind": 1}` → **admitted** (balanced in kind, no price).
- **A3 market:** `mode=market_price`, payload `{"item": "bike", "amount_cents": 8000, "currency": "EUR"}` → **admitted**.
- **Verify:** AC1, AC7 (each admitted; `admitted:true`; `expires_at` carried through).

## Test B — Membrane breach: market leak into a non-market room (AC2)
- **B1:** `mode=communal_gift`, payload `{"offer": "childcare", "price": 500}` → **refused**.
- **B2 (nested):** `mode=equality_matching`, payload `{"swap": {"terms": {"fee_cents": 200}}}` → **refused** (leak one level down).
- **B3:** `mode=communal_gift`, payload `{"help": "ride", "currency": "USD"}` → **refused**.
- **Verify:** AC2 — `MembraneBreachError` each; the field is never stripped-then-admitted.

## Test C — Reciprocity ledger: refused in gift, allowed in kind in equality (AC3)
- **C1:** `mode=communal_gift`, payload `{"care": "meals", "balance_owed": 3}` → **refused** (tracking reciprocity kills the gift).
- **C2:** `mode=equality_matching`, payload `{"slot": 2, "counter_in_kind": 2}` → **admitted** (no ledger/market key; balanced in kind).
- **Verify:** AC3.

## Test D — Directionality: gift-shaped content in the market room admits (AC4)
- **D:** `mode=market_price`, payload `{"gift_note": "free with purchase", "description": "no charge sample"}` → **admitted** (no price present, market room is permissive).
- **Verify:** AC4 (wall is one-directional).

## Test E — Adversarial / tail (AGD-016): surveillance-shape refusal in every room (AC5)
- **E1 (gift):** `communal_gift` payload with `{"reputation": 0.9}` → **refused**.
- **E2 (market, nested):** `market_price` payload `{"seller": {"trust_score": 88}}` → **refused** (forbidden shape holds even in the market room).
- **E3 (envelope):** any room with a top-level `"blacklist": [...]` → **refused**.
- **E4 (verdict scan):** for every admitted case (A1–A3, C2, D), a recursive key scan of the
  verdict finds **zero** forbidden keys and no echoed payload content.
- **Verify:** AC5 (a,b). Correct behavior is to refuse the social-credit shape at any depth, in any room.

## Test F — No stored refusal (AC6)
- **F:** assert the module exposes no return value with `admitted == False`; every breach in
  Tests B/C1/E is an exception, not a returned verdict. `admit()`'s only non-raising return
  sets `admitted: true`.
- **Verify:** AC6 (whitelist-not-blacklist; a refusal is not a person-record).

## Test G — Envelope validation (AC8)
- Unknown `mode="gift"` (not one of the three literals), `interaction_id=""`, `cell_id=""`,
  `participants="t1"` (str not list), `payload=[]` (list not dict) → each **refused**.
- **Verify:** AC8.

## Test H — Cross-layer consistency (AC-X)
- Feed the shape of a Capa-4 binary campaign into the firewall as an `equality_matching`
  interaction: payload `{"threshold": 3, "sponsor_bonus_cents": 500}` → **refused**
  (`sponsor_bonus_cents` matches `_cents`). Matches Capa-4 AC6's independent refusal.
- **Verify:** AC-X — the two layers agree on the membrane.

## Property tests (Test P — hypothesis)
- **P1:** for any payload built only from gift-shaped keys (drawn to exclude every MARKET/LEDGER/FORBIDDEN
  token), `communal_gift` and `equality_matching` both admit; `market_price` admits any payload
  without a FORBIDDEN key.
- **P2:** for any payload containing at least one MARKET key nested at random depth,
  `communal_gift` and `equality_matching` always **refuse** (no market key ever survives).
- **P3:** for any interaction containing a FORBIDDEN key at random depth, **all three rooms** refuse.
- **P4:** every admitted verdict, scanned recursively, contains zero FORBIDDEN keys.

## Cross-check (independent oracle, AGD-045)
Re-detect leaks with a hand-written recursive key-walker (independent of the firewall's own
scan) and compare admit/refuse decisions. Disagreement = fail (catches self-confirmation).
