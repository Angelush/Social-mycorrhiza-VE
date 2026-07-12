# Failure Model + Stress Report

> Produced by red-team. Hostile review of the Capa-4 engine spec.

## Failure modes (F#)
- **F1 — Surveillance creep (the defining failure).** Someone adds a "committer reliability" field, or persists who failed to follow through, turning the engine into a reputation source. *Mitigation:* N2/N3/N4; AC5 recursive key scan + forbidden-field rejection (E1). The architecture must make the bad shape unrepresentable.
- **F2 — Cross-campaign join.** `participant_token` reused as a stable identity across campaigns → a dossier emerges by correlation. *Mitigation:* N4 (opaque, per-campaign tokens); AC5c; documented that tokens must be rotated per campaign by the caller.
- **F3 — No-loss broken by bonus arithmetic.** Float split or bad remainder leaves a committer short. *Mitigation:* M1 int cents, M3 deterministic remainder; AC2 + AC3 independent recompute.
- **F4 — Bonus paid when action fires.** Mis-wired branch pays the dominant bonus even though the threshold was met. *Mitigation:* spec step 4 (no bonus on fire); AC3 (all-zero bonus when firing).
- **F5 — Membrane leak.** A binary/equality campaign carries prices → market logic in the gift room. *Mitigation:* N5; AC6 rejection.
- **F6 — Double-count of a re-pledger.** Same person pledging twice counts as two toward threshold → action fires falsely. *Mitigation:* M4 dedup by token; AC1 (Test B re-pledge).
- **F7 — LLM/optimization creep.** "Let an agent tune the threshold / nudge people to pledge" → engagement optimization. *Mitigation:* N1; invariant 8 (optimize cooperation-initiated, never engagement); architecture caps the LLM at Capa 3 proposal-only.
- **F8 — Bonus-extraction Sybil.** A dominant-assurance bonus on a *binary* (zero-stake) campaign that fails pays every distinct token a share for pledging nothing → an attacker mints throwaway tokens and drains the sponsor's bonus at no cost. (Even for monetary campaigns the stake is refunded make-whole, so the bonus is still free money, merely capital-locked.) *Root:* dedup is one-*token*-one-weight; token↔person binding is unsolved (§6.2). *Mitigation (partial):* N5/AC6 reject `binary` + `sponsor_bonus_cents>0`, closing the free case; the capital-locked monetary case and Sybil in general remain caller/identity concerns — flagged, not faked-resolved.

## Stress findings (ST#)
- **ST1 — Remainder bias.** Bonus not divisible by committer count: who gets the extra cent must be deterministic and not a covert ranking. *Found gap:* fixed to ascending `participant_token` (lexicographic, content-free), documented as arbitrary-but-deterministic, **not** a merit order. Test B covers.
- **ST2 — Empty / zero-bonus campaigns.** `sponsor_bonus_cents=0` (plain assurance contract) → all bonus 0, refunds still full. *Verify:* AC2/AC3 with zero bonus.
- **ST3 — threshold exactly met / off-by-one.** `distinct == threshold` must fire (>=, not >). *Mitigation:* spec step 3; Test A is `4>=3`; add boundary test `3>=3`.
- **ST4 — Self-confirmation.** Engine's own dedup/split agrees with its own bug. *Mitigation:* independent `Counter`-based oracle (tests.md), AGD-045.
- **ST5 — Forgetting vs. auditability tension (open problem §6.6).** The artifact must be auditable yet not a permanent dossier. *Partial mitigation:* `expires_at` carried through (M7); the engine emits no store. **Flagged:** enforcing expiry is the *caller's/storage* responsibility, outside this pure function — noted, not faked-resolved.

## Open (system-level, NOT this engine) — do not fake-resolve (§6)
- The razor's edge: any legibility layer can slide to surveillance; "who governs decides" (§6.1) — governance, not code. *Stakes: a cage, not just a failure.*
- Sybil resistance without identity totalization (§6.2) — unsolved; this engine assumes the caller supplies committer tokens and does **not** attempt identity verification.
- Cannot manufacture the will to cooperate (§6.3); fertility metric is Goodhart-prone (§6.4); federation as recentralizing bottleneck (§6.5); exit-vs-accountability (§6.6). All governance/relationship problems — flagged, not coded.
