# Specification — Capa 6 Sociocratic Governance (consent, not consensus)

> Produced by engineer-spec. Self-contained blueprint; an agent can build from this alone.
> Sibling of the Capa-4/1/2/3/5 `spec.md`. This is the `[HUMANO → CONSENT-NOT-CONSENSUS]` layer
> (brief §4 Capa 6, invariant 7, architecture.md: *Not an agent. Consent-not-consensus; voice
> independent of reputation*). It is **DETERMINISTIC, NOT an LLM** — no stochastic core, no injected
> model, no network client. It enforces the **procedure** of consent; it cannot manufacture the will
> to cooperate. It routes through the Capa-1 membrane's `FORBIDDEN_KEY` taxonomy verbatim so the six
> layers cannot disagree on the surveillance shape.

## Purpose
Resolve one proposal in one **local circle** by **consent — the absence of a paramount (reasoned)
objection — not by consensus, and not by majority** (brief §4 Capa 6; lineage: Haudenosaunee Great
Law of Peace, Quaker meeting, sociocracy). Each participant contributes **exactly one disposition**;
the proposal is `adopted` iff **no paramount objection** stands, else it goes to `revisit` with the
objection's **reason surfaced** — a whitelist-shaped pause that opens the door to revision, never a
blacklist of the objector.

The defining design problem (brief §4 Capa 6, invariant 7, §6.3): **voice must be structurally
independent of reputation, or you rebuild social credit by the back door** (reputation → power →
discipline). The move is the Capa-6 analogue of Capa-2's unrepresentable god-view: **one person, one
voice**, and the weighting cannot even be *phrased*.

## The design move — the god-view weighting is unrepresentable
Five structural walls, each an analogue of a wall in the sibling layers:

1. **VOICE INDEPENDENT OF REPUTATION, made structural (invariant 7, the defining move).** One person,
   one voice: each participant contributes **exactly one** disposition, deduped by **opaque token**.
   There is **no representable `weight`/`score`/`shares`/`voting_power`/`tally` field** — the
   `VOTE_WEIGHT_KEY` taxonomy *and* the Capa-1/2/3/4/5 `FORBIDDEN_KEY` taxonomy are scanned over the
   whole request and **refuse** any such shape; disposition keys are **whitelisted**. A
   high-"reputation" member has exactly the same single voice; **the weighting cannot be phrased.**
   This is the anti-plutocracy / anti-social-credit firewall.

2. **Consent, not consensus, not majority.** A proposal is `adopted` iff **no paramount objection**
   stands; else `revisit`. The verdict is **categorical and relative** — **never a percentage, never a
   majority, never a tally**. The function does **not** compute "X% approve" or "N for, M against";
   there is no number that decides. Consent is the *absence of a blocking reasoned objection*, not the
   presence of enough votes.

3. **A paramount objection is a whitelist-shaped PAUSE (invariant 3).** It opens the door to revision
   and surfaces the objection's **reason**; it **never marks the objector**. The output carries the
   **reasons**, never a per-objector identity or a "who-blocked" list — no blacklist of the person.

4. **Circles are LOCAL and do not auto-propagate (invariants 4/6).** A circle's decision is scoped to
   that `circle_id`; it does **not** escalate to a parent/global authority. There is no central holder;
   dispositions tagged to a different circle are dropped. Double-linking between circles is a *human*
   structure the protocol scopes for, never a merge into one global authority.

5. **Forgetting: per-round, no dossier of who objected (invariant 5).** The decision carries an
   `expires_at`; expired dispositions are dropped before tallying consent; nothing is persisted across
   calls. There is **no permanent record of who objected** — the surfaced reasons carry no objector
   token.

## Enforces the procedure, not good faith (protocol, not an agent)
`decide()` enforces the **procedure** of consent. It cannot manufacture the will to cooperate (a
low-trust circle may not bootstrap), and consent is capturable by a bad-faith blocker (the
tyranny-of-the-minority tension). **The code enforces the procedure, not good faith** — who
participates and why decides. Flagged (§6.3), not coded.

## Time model
Capa 6 needs no elapsed-time arithmetic, so it keeps the **family's ISO-8601 string convention** (as
Capa 1/2/3): `now` and `expires_at` are non-empty strings compared **lexicographically** (normalized
UTC, `…Z`). A disposition with `expires_at <= now` is dropped (forgetting). (Capa 5, which needs
evaporation arithmetic, is the one layer using integer ticks.)

## Input (one governance round, JSON)
```json
{
  "circle_id": "str (non-empty) — the local circle deciding (invariant 4); decision is scoped here",
  "proposal_id": "str (non-empty) — the proposal under consent",
  "now": "str (ISO-8601 UTC) — evaluation time; dispositions with expires_at <= now are dropped",
  "expires_at": "str (ISO-8601 UTC, non-empty) — the expiry STAMPED on the decision (forgetting)",
  "dispositions": [
    {
      "token": "str (non-empty) — opaque per-circle participant token; ONE voice each (deduped)",
      "disposition": "one of consent | object | abstain (whitelist)",
      "objection": {                         // REQUIRED iff disposition == object; else absent
        "paramount": "bool — true = a blocking reasoned objection; false = a non-blocking concern",
        "reason": "str (non-empty) — the reason, surfaced; never a mark against the person"
      },
      "circle_id": "str (non-empty) — MUST equal the request circle_id (else dropped; local scope)",
      "expires_at": "str | null — the disposition's own expiry; <= now => dropped (forgetting)"
    }
  ]
}
```
- **Disposition keys are whitelisted** (`token`/`disposition`/`objection`/`circle_id`/`expires_at`).
  Any other key — a `weight`, a `score`, a `voting_power`, a `share` — is **refused** (raise). There is
  no field through which reputation could weight a voice.
- `disposition` must be one of the **three whitelisted values**. An `object` **must** carry
  `objection.reason` (non-empty) and `objection.paramount` (bool); a `consent`/`abstain` must **not**
  carry an objection.
- **One token, one voice:** a token appearing on more than one **surviving in-circle** disposition is a
  ballot-integrity breach → **refused** (raise). It is a *per-circle* invariant (D-03): a duplicate token
  on an off-circle or expired disposition is dropped, not fatal, so a straggler scoped to another circle
  cannot veto this round. (Contrast Capa 3, which dedupes silently; here a double voice is an attack on
  invariant 7 and is surfaced.)

## Output (a categorical consent verdict, JSON) — always returns
```json
{
  "circle_id": "consejo-barrio",
  "proposal_id": "prop-42",
  "verdict": "revisit",                        // or "adopted"
  "paramount_objections": [
    {"reason": "we have no budget line for this until Q3"}
  ],
  "concerns": [
    {"reason": "prefer a 3-month trial first"}
  ],
  "note": "Consent is the absence of a paramount objection, never a majority. An objection is a reasoned pause that opens revision, never a mark against anyone. Scoped to this circle; it does not propagate.",
  "expires_at": "2026-08-01T00:00:00Z",
  "audit_trace": {
    "rule": "adopted iff no paramount objection; one token one voice; voice independent of reputation; no tally, no majority; circle-local; per-round forgetting",
    "considered_dispositions": 7,
    "dropped_off_circle": 0,
    "dropped_expired": 0,
    "paramount_objections": 1,
    "concerns": 1
  }
}
```
- `verdict` is **categorical**: `adopted` (no paramount objection stands) or `revisit` (≥1 paramount
  objection — its reason surfaced). **Never a number, never a percentage, never a majority.** There is
  no "X% consent," no "N for / M against" that decides.
- `paramount_objections` is a list of **reasons only** — no objector token, no per-person mark (a pause,
  not a blacklist; invariant 3). `concerns` are non-blocking objection reasons (also token-free).
- The output is **scoped to `circle_id`**; there is **no** field that escalates to a parent/global
  authority (invariants 4/6). It carries `expires_at` (per-round forgetting; invariant 5).
- **No consent/vote tally** appears as the verdict. `considered_dispositions` in the audit trace is
  process transparency (how many voices were weighed), *not* a majority computation — no verdict is
  derived from a count.

## Algorithm (deterministic)
1. **Validate envelope** (reject, do not repair): `circle_id`/`proposal_id` non-empty str; `now`
   non-empty str; `expires_at` non-empty str; `dispositions` a list of well-formed dicts with
   **whitelisted keys only** (unknown key → refuse), `token` non-empty str, `disposition` in
   `{consent, object, abstain}`, `circle_id` non-empty str, `expires_at` str/null. If
   `disposition == object`: `objection` must be a dict with `paramount` (bool) and non-empty `reason`;
   else `objection` must be absent.
2. **One token, one voice:** after circle-scope + expiry filtering, if any `token` appears on more than
   one **surviving in-circle** disposition → **refuse** (raise). Off-circle/expired duplicates are
   dropped, not fatal (per-circle invariant; D-03). (Ballot-stuffing / weighted-voice-by-duplication is
   an attack on invariant 7.)
3. **Surveillance + vote-weight scan (whole request, recursive):** any key (case-insensitive substring)
   matching a `FORBIDDEN_KEY` (`score|rating|reputation|rank|blacklist|ban|penalty|global_id|dni`)
   **or** a `VOTE_WEIGHT_KEY` (`weight|shares|voting_power|vote_count|tally|majority|percent|proxy|
   seats|quorum`) at any depth → **refuse** (`GovernanceBreachError`). The `FORBIDDEN_KEY` set is the
   exact Capa-1/2/3/4/5 taxonomy, verbatim.
4. **Circle scope + forgetting (drop-and-count, never raise):** drop a disposition whose
   `circle_id ≠` the request `circle_id` (`dropped_off_circle`) — the decision is local, no
   cross-circle vote. Drop a disposition with `expires_at <= now` (`dropped_expired`) — per-round
   forgetting.
5. **Resolve consent (categorical, no tally):** among surviving dispositions, collect the **reasons**
   of every `object` with `paramount == True` (the `paramount_objections`) and of every `object` with
   `paramount == False` (the `concerns`). `verdict = adopted` iff `paramount_objections` is empty, else
   `verdict = revisit`. **No count decides** — a single paramount objection blocks; a thousand consents
   do not out-vote it.
6. **Surface reasons, never people.** Sort `paramount_objections` and `concerns` by `reason` (canonical,
   deterministic); each entry is `{reason}` — **no token**. No per-objector record.
7. **Assemble output.** Attach `expires_at` (per-round forgetting) and the audit trace. Scope to
   `circle_id`; **do not** propagate to any parent. **Persist nothing.**

## Determinism
Pure and deterministic: given the same request it produces **byte-identical** JSON (fixed taxonomies +
canonical reason sort + categorical verdict). No clock, no randomness, no I/O. The same proposal in the
same circle yields the **same verdict regardless of any reputation the members carry** — because
reputation is unrepresentable (AC1, the defining test).

## Termination & cost
Bounded: O(dispositions) validation and scope/forgetting filters, O(objections·log) reason sort. No
unbounded loops.

## Meaning layer (Axiom 6 — what the agent cannot infer)
- **Reputation must not weight the voice, or the whole stack becomes social credit (invariant 7,
  §6.3).** If the reputation of Capa 2 could tilt a governance vote, then reputation → power →
  discipline, and the surveillance cage is rebuilt from the inside. The correct move is not a "don't
  weight votes" policy line — it is to make the weight **unrepresentable**: no `weight`/`shares`/
  `voting_power` field exists, disposition keys are whitelisted, and one token = one voice. **The
  god-view weighting cannot be phrased**, exactly as Capa-2's absolute trust-view cannot be phrased.
- **Consent is the absence of a reasoned objection, not the presence of a majority.** A majority tally
  is a small tyranny (the brief's "sin tiranía de la mayoría"); consent asks only whether anyone has a
  **paramount, reasoned** objection. So the function computes **no percentage** — the verdict is
  categorical, and one reasoned block is enough. This is the Ostrom-social / Quaker / sociocratic move.
- **An objection is a pause, not a mark (invariant 3).** The objector is never blacklisted; the *reason*
  is surfaced so the proposal can be revised. There is no dossier of who objected (invariant 5) — the
  output carries reasons, never objector tokens.
- **Local and non-propagating (invariants 4/6).** The decision is the circle's; it does not flow up to
  a central authority. There is no throne that aggregates all circles' decisions.
- **Enforces the procedure, not good faith.** The code cannot make a low-trust circle cooperate, and a
  bad-faith blocker can capture consent (tyranny of the minority). **Flagged, not fake-resolved (§6.3):**
  the protocol enforces one-token-one-voice and consent; *who participates and why* decides the
  outcome's legitimacy.
- **Reversibility:** `decide()` is a **two-way door** (pure, no side effects, no persistence) → it may
  run autonomously to *resolve one round's consent*. Executing the adopted proposal is the humans' step.

## Flagged, NOT fake-resolved (brief §6.3)
- **You cannot manufacture the will to cooperate (§6.3).** A low-trust circle may not bootstrap consent
  at all; the protocol scaffolds the procedure, it does not create the good faith. Flagged, not coded.
- **Consent is capturable by a bad-faith blocker (tyranny of the minority).** A single actor issuing a
  spurious "paramount" objection can stall every proposal. The function enforces the *procedure* (an
  objection must carry a reason; it opens revision, it does not mark anyone); whether an objection is
  in good faith is a **human/governance** judgement the pure function cannot make. Flagged.
- **Token↔person binding / Sybil (§6.2).** One token = one voice enforces one-token-one-voice, not
  one-*person*-one-voice; a Sybil with many tokens is a many-voiced actor. Tokens are opaque and
  trusted as given (as in Capa 2/3/4/5). Flagged, not solved.

## Relationship to Capa 1, 2, 3, 4, and 5 (reuse, not duplication)
- Reuses the **exact** `FORBIDDEN_KEY` taxonomy of all five siblings (one anti-surveillance definition,
  not six). AC-X regression-checks that a Capa-1 surveillance-shaped payload fed as a Capa-6 disposition
  is refused identically, and that `governance.FORBIDDEN_KEYS` equals the set in every sibling module.
- Dispositions are **circle-scoped** exactly as a Capa-1 interaction, a Capa-2 vouch, a Capa-3
  candidate, a Capa-4 campaign, and a Capa-5 trace are cell-scoped; local-bounded, never global
  (invariant 4).
- Forgetting is native (per-round `expires_at`), as everywhere.
- Adds one gate the others do not need: the `VOTE_WEIGHT_KEY` taxonomy — the Capa-6-specific
  anti-plutocracy firewall (invariant 7), the analogue of Capa-3's `ENGAGEMENT_KEY` and Capa-5's signal
  whitelist.

## Out of scope (explicitly NOT this component)
- **Any weighted / reputation-bearing voice** — unrepresentable (VOTE_WEIGHT + FORBIDDEN scan +
  whitelist; invariant 7). No `weight`, no `shares`, no `voting_power`, no proxy.
- **A majority / percentage / tally verdict** — the verdict is categorical (`adopted`/`revisit`); no
  number decides (invariant 7, anti-majority).
- **A blacklist / mark of the objector** — the output surfaces reasons, never objector identities
  (invariant 3); no dossier of who objected (invariant 5).
- **Auto-propagation to a parent/global authority** — the decision is circle-local; no escalation field,
  no central holder (invariants 4/6).
- **Manufacturing cooperation, or judging an objection's good faith (§6.3)** — the function enforces the
  procedure; who participates and whether they act in good faith decides. Flagged, not coded.
- **Sybil / one-person-one-voice (§6.2)** — one *token* one voice; token↔person binding is out of scope.
</content>
