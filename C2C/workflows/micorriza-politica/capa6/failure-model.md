# Failure Model + Stress Report — Capa 6 Sociocratic Governance

> Produced by red-team. Hostile review of the Capa-6 spec. The failure mode here is not a dead
> network — it is **social credit rebuilt through the governance door**: reputation weighting the
> voice → power → discipline (brief §4 Capa 6, invariant 7, §6.3). Consent decays into a majority
> tally, or an objection becomes a mark against the objector.

## Failure modes (F#)
- **F1 — The weighted voice (invariant 7, the gravitational pull).** A disposition carries a `weight`,
  `voting_power`, or `shares`, or the reputation of Capa 2 is used to scale a vote → reputation → power
  → discipline, and the surveillance cage is rebuilt from inside governance. *Mitigation:* M1/M2/N1;
  the `VOTE_WEIGHT_KEY` taxonomy is refused, disposition keys are whitelisted, and one token = one
  voice. AC1 (the defining test) proves the verdict is invariant to any reputation the members carry.
  **This is the gravity, not a solved problem — flagged: a governor who tallies off-protocol reopens
  it.**
- **F2 — The majority tally.** The verdict becomes "68% approve" or "N for, M against" → the
  tyranny-of-the-majority the brief forbids (inverts invariant 7). *Mitigation:* M4/M5/N2; the verdict
  is **categorical** (`adopted`/`revisit`); a single paramount objection blocks regardless of how many
  consent; **no number decides**. AC2/AC4 assert no tally is a verdict.
- **F3 — The synthesized person-scalar.** A `score`/`reputation` field rides in on a disposition → the
  social-credit scalar reappears at governance (inverts invariant 2). *Mitigation:* M3/N5; the
  `FORBIDDEN_KEY` scan refuses it. AC3.
- **F4 — The marked objector (inverts invariant 3).** The output records **who** objected, building a
  dossier of dissent that becomes a blacklist. *Mitigation:* M6/M8/N3; the output surfaces objection
  **reasons only** — no objector token, no "who-blocked" list. AC5 scans the output for any objector
  identity.
- **F5 — Auto-propagation to a central authority (inverts invariants 4/6).** A circle's decision flows
  up automatically to a parent/global circle → the throne that aggregates all circles reappears.
  *Mitigation:* M7/N7; the decision is scoped to `circle_id`, out-of-circle dispositions are dropped,
  and there is **no escalation field**. AC6.
- **F6 — The permanent dossier (inverts invariants 5/6).** Expired dispositions still count, or the
  function stores round history → a permanent record of every vote and objection. *Mitigation:* M8;
  expired dispositions are dropped before resolving, the decision carries `expires_at`, and the
  function persists nothing. AC7 flips on expiry.
- **F7 — The duplicated voice.** One token submits several dispositions to out-shout the circle → a
  weighted voice by duplication (inverts invariant 7). *Mitigation:* M1; a repeated token is
  **refused** (raise). AC8.
- **F8 — The bad-faith blocker / tyranny of the minority (§6.3).** A single actor issues a spurious
  "paramount" objection on every proposal, stalling the circle forever. *Mitigation (partial):* the
  function enforces that an objection carries a **reason** and opens **revision** (it does not mark
  anyone); whether the objection is in good faith is a **human/governance** judgement the pure function
  cannot make. **Flagged, NOT solved:** consent is capturable by a bad-faith blocker; who participates
  and why decides (§6.3, mirror Capa-2/1/3/5 ST5).
- **F9 — Manufacturing consent.** The code "helps" a low-trust circle by overriding an objection, or
  fabricating agreement to reach adoption → the protocol pretending to make cooperation it cannot make.
  *Mitigation:* N9; the function never overrides an objection and never invents a disposition. **You
  cannot manufacture the will to cooperate (§6.3)** — flagged, not coded.
- **F10 — Repair-instead-of-refuse; strip-instead-of-drop.** Code strips a `weight` key from a
  disposition and decides anyway. *Mitigation:* N5/N8; the request is **refused** (raise) on any
  `VOTE_WEIGHT`/`FORBIDDEN`/whitelist/duplicate breach.
- **F11 — Taxonomy drift from Capa 1/2/3/4/5.** Capa 6 keeps a separate forbidden-key list that
  diverges → the six layers disagree on the surveillance shape (AC-X breaks). *Mitigation:* P2; share
  the exact `FORBIDDEN_KEY` set; AC-X regression-checks agreement across all six layers.

## Stress findings (ST#)
- **ST1 — Substring false positives.** `"percentage_note"` contains `percent`; `"proxy_server"`
  contains `proxy`; `"bandwidth"` contains `ban`. **Decision (inherited from Capa 1/2/3/5 ST1):** the
  taxonomy is a shape heuristic **biased to over-refuse** — a false refusal is safe (re-label a field),
  a false admit is a plutocracy/surveillance leak. Keep the shared `FORBIDDEN_KEY` set verbatim;
  document the `VOTE_WEIGHT_KEY` bias. Test `weight`/`majority` (must trip) and a clean disposition
  (must not trip).
- **ST2 — Empty / all-dropped disposition list.** `dispositions=[]`, or all out-of-circle/expired → a
  valid round: **no paramount objection ⇒ `adopted`** (vacuous consent). *Decision:* this is correct
  and intentional — an empty circle raising no objection adopts; it is not an error. Documented; a
  governor who wants a quorum enforces it outside (there is deliberately no `quorum` field — it is in
  the `VOTE_WEIGHT` refuse-list, since a quorum is a count-gate that reintroduces tally logic). AC
  tolerates the empty case.
- **ST3 — ISO-8601 lexicographic compare.** As in Capa 2/3: `expires_at`/`now` must be normalized-UTC
  (`…Z`) for the lexicographic expiry compare to be correct. Document it; test with `…Z` only.
- **ST4 — Self-confirmation.** The function's own resolution agrees with its own bug. *Mitigation:* an
  **independent** hand-written oracle (separate from the module) re-derives the surviving-disposition
  set and the verdict in tests (tests.md cross-check, AGD-045).
- **ST5 — Auditability vs. forgetting / no-storage (open §6).** The decision is auditable yet must not
  become a permanent voting record. *Partial mitigation:* the function is pure and stores nothing;
  `expires_at` stamps the round; no objector token is emitted. **Flagged:** enforcing that the *caller*
  does not persist and correlate rounds is outside this pure function (mirrors Capa-4/1/2/3/5 ST5).
- **ST6 — `stand_aside` vs `abstain` vs non-paramount object.** The model uses three dispositions:
  `consent`, `object` (with `paramount` true/false), `abstain`. A non-paramount `object` is a
  **concern** — surfaced (reason) but non-blocking; an `abstain` is silent. A "stand aside" (I consent
  though I have a concern) maps to `object` with `paramount=false`. Documented so the caller has no
  ambiguity.
- **ST7 — One token ≠ one person (Sybil, §6.2).** One token, one voice enforces one-*token*-one-voice,
  not one-*person*-one-voice; a Sybil with many tokens is a many-voiced actor. *Decision:* tokens are
  opaque and trusted as given (as in Capa 2/3/4/5). Flagged, not solved.

## Open (system-level, NOT this function) — do not fake-resolve (§6.3)
- **You cannot manufacture the will to cooperate (§6.3).** A low-trust circle may not bootstrap consent
  at all; the protocol scaffolds the procedure, it does not create good faith. **Stakes: a cage or a
  dead circle, not just a failure.** Flagged (F9).
- **Consent is capturable by a bad-faith blocker (tyranny of the minority).** A spurious "paramount"
  objection stalls everything; the function enforces the procedure (a reason, a revision door), not the
  good faith. Who participates and why decides. Flagged (F8).
- **Reputation weighting rebuilt off-protocol (invariant 7, §6.3).** The API removes the weight *per
  round* (unrepresentable). But a malign governor who tallies reputation-weighted votes *outside* the
  function rebuilds the plutocracy. Structure makes it hard, not impossible; who governs decides.
  Flagged (F1).
- **Sybil / token↔person binding (§6.2).** One token, one voice ≠ one person, one voice. Tokens opaque,
  trusted as given. Flagged (F7/ST7).
</content>
