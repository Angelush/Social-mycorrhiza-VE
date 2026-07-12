# Test Cases — Capa 4 Assurance-Contract Engine

> Produced by design-evals. Each: input, expected output, verification rule. Golden pairs live in `golden-set/`.

## Test A — Normal: binary campaign that fires
- **Input:** `kind=binary`, `threshold=3`, `sponsor_bonus_cents=0`. Pledges from tokens `t1, t2, t3, t4` (4 distinct, binary, no amounts).
- **Expected:** `status=fires`, `distinct_committers=4`, `resolution.fires.total_pledged_cents=0`, no refunds. `deduped_from_pledges=4`.
- **Verify:** AC1 (4>=3 → fires), AC2 (empty refunds), AC4.

## Test B — Edge: monetary campaign that refunds, with dominant bonus + duplicate pledger
- **Input:** `kind=monetary`, `threshold=5`, `sponsor_bonus_cents=1000`. Pledges: `t1` 2000, `t2` 3000, `t1` 500 (re-pledge), `t3` 1500. → distinct committers = {t1,t2,t3} = 3 < 5.
- **Expected:** `status=refunds`. Refunds: `t1` refund 2500 (2000+500), `t2` 3000, `t3` 1500 — full make-whole (AC2). Bonus 1000 / 3 = base 333, rem 1 → ascending token: `t1` 334, `t2` 333, `t3` 333; sum 1000 (AC3). `deduped_from_pledges=4`.
- **Verify:** AC1 (3<5 → refunds), AC2 (full refunds incl. re-pledge summed under one token), AC3 (bonus conserved, remainder to first ascending token), AC4.

## Test C — Adversarial / tail (AGD-016): the surveillance-shape refusal + membrane breach
- **Input C1 (forbidden field):** an otherwise-valid monetary campaign with an extra `"global_score": {...}` field, or a pledge carrying `"reputation": 0.9`.
- **Input C2 (membrane breach):** `kind=binary` campaign whose pledges carry positive `amount_cents` (market pricing leaking into an equality room), or a `kind=binary` campaign carrying `sponsor_bonus_cents > 0` (a monetary failure-bonus in an equality room — also a zero-stake Sybil faucet).
- **Input C3 (cross-campaign):** two separate campaigns that both include `participant_token="t1"`.
- **Expected:** C1 → **rejected** (ValueError), the engine refuses the surveillance shape (AC5b). C2 → **rejected** (AC6, kula/gimwali wall — priced pledge *or* sponsor bonus on a binary campaign). C3 → two independent outputs, neither containing any cross-campaign aggregate or person-score (AC5a, AC5c). A recursive key scan of every output finds zero forbidden keys.
- **Verify:** AC5 (a,b,c), AC6. This is the tail case where the *correct* behavior is to refuse to produce or accept the social-credit-shaped artifact — the inversion of China at the level of a single function.

## Cross-check (independent oracle, AGD-045)
For Tests A/B, recompute `distinct_committers`, refunds, and the bonus split with a hand-written independent routine (plain `collections.Counter` + integer division) and compare to the engine output. Disagreement = fail (catches implementation self-confirmation).

## Golden set
Serialize A, B, and C3's two campaigns as input→expected JSON pairs in `golden-set/`. Re-run on any engine change (DVH-007/008).
