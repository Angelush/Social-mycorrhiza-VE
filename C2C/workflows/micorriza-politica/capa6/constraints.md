# Constraint Architecture — Capa 6 Sociocratic Governance (consent, not consensus)

> Produced by author-constraints. Each rule carries a "because" clause (AGD-029).
> Sibling of the Capa-4/1/2/3/5 `constraints.md`; the anti-surveillance rules are deliberately
> identical. This layer is **DETERMINISTIC, not an LLM**. Its defining move is invariant 7: voice
> independent of reputation, made structural.

## MUSTs
- **M1** Give each participant **exactly one voice**, deduped by **opaque token**; a token appearing on
  more than one disposition is **refused** (raise) — *because* one person, one voice; ballot-stuffing /
  weighted-voice-by-duplication is an attack on invariant 7.
- **M2** Make the **weight unrepresentable**: whitelist disposition keys **and** scan+refuse a
  `VOTE_WEIGHT_KEY` taxonomy (`weight|shares|voting_power|vote_count|tally|majority|percent|proxy|
  seats|quorum`) over the whole request — *because* the voice must be structurally independent of
  reputation (invariant 7); a high-"reputation" member gets the same single voice, and the god-view
  weighting cannot even be phrased.
- **M3** Scan the exact Capa-1/2/3/4/5 `FORBIDDEN_KEY` taxonomy over the whole request and **refuse**
  any match at any depth — *because* no global scalar of the person (invariant 2). Same taxonomy,
  verbatim, across six layers.
- **M4** Resolve by **consent**: `adopted` iff **no paramount objection** stands, else `revisit` —
  *because* the lineage is consent, not consensus, not majority (Haudenosaunee / Quaker / sociocracy);
  a single reasoned block is decisive.
- **M5** Emit a **categorical** verdict; compute **no percentage, no majority, no tally** that decides —
  *because* a majority tally is the tyranny-of-the-majority the brief forbids (invariant 7); no number
  is a verdict.
- **M6** Treat a paramount objection as a **whitelist-shaped pause** that surfaces the **reason** and
  opens revision; **never mark the objector** — *because* reputation opens doors, it cannot easily
  close them (invariant 3); an objection is a pause, not a blacklist.
- **M7** Scope the decision to the **circle**; drop out-of-circle dispositions; **do not** propagate to
  a parent/global authority — *because* circles are local and double-linked by humans, not merged into
  one central authority (invariants 4/6).
- **M8** Forget per round: drop expired dispositions (`expires_at <= now`); stamp the decision with
  `expires_at`; keep **no dossier of who objected** (surface reasons, never objector tokens); persist
  nothing across calls — *because* forgetting is native and there is no permanent record of dissent
  (invariants 5/6).
- **M9** Be **byte-deterministic** for identical input (fixed taxonomies, canonical reason sort,
  categorical verdict) — *because* the same proposal in the same circle must yield the same verdict
  regardless of reputation, and an unauditable decision cannot be trusted (mirrors Capa-4/1/2/3/5 M9).
- **M10** Emit an auditable `audit_trace` (rule + drop counts + objection/concern counts) as **process
  transparency**, never as a majority computation — *because* a caller must see how many voices were
  weighed and why the verdict fell, without a tally deciding.
- **M11** Distinguish **raise vs. drop**: envelope/type/whitelist/`FORBIDDEN`/`VOTE_WEIGHT`/duplicate-
  token breaches **raise**; out-of-circle and expired dispositions are **dropped-and-counted** —
  *because* a malformed or weighted ballot is an integrity error, but scoping and forgetting are normal
  runtime behavior and must not crash.

## MUST-NOTs
- **N1** No **weighted / reputation-bearing voice**: no `weight`/`shares`/`voting_power`/`proxy` field —
  *because* the anti-plutocracy firewall is structural (invariant 7). Not even a "seniority" multiplier.
- **N2** No **majority / percentage / tally verdict** — *because* consent is the absence of a reasoned
  objection, never the presence of enough votes (invariant 7, anti-majority).
- **N3** No **blacklist / mark of the objector**; no per-objector token in the output; no "who-blocked"
  list — *because* an objection is a pause, not a sanction (invariant 3), and there is no dossier of
  dissent (invariant 5).
- **N4** No **LLM, no injected model, no network client, no stochastic core** — *because* Capa 6 is
  deterministic procedure enforcement; nothing stochastic decides about a person's voice.
- **N5** No **stripping** of a weighted/surveillance-shaped request (remove the `weight` key, decide
  anyway) — **refuse the whole request** — *because* answering over a silently-cleaned weighted ballot
  launders the plutocracy shape (mirrors Capa-1/2/3/5 N5).
- **N6** No stored round history, no cross-call state, no central tally, no global authority — *because*
  no central holder (invariant 6), no permanent dossier (invariant 5), no throne.
- **N7** No **auto-propagation** of the decision to a parent/global circle — *because* the decision is
  local; escalation is a human double-linking act, never an automatic merge (invariant 4).
- **N8** No **silent failure on the envelope**: on any validation, `FORBIDDEN`/`VOTE_WEIGHT`, or
  duplicate-token breach, **raise** and surface. (Out-of-circle / expired dispositions, by contrast,
  are dropped-and-counted — scoping and forgetting are normal, not errors.)
- **N9** No **manufacturing of consent**: the function never fabricates agreement, never coerces a
  disposition, never overrides an objection — *because* you cannot manufacture the will to cooperate
  (§6.3); the code enforces the procedure, not good faith.

## PREFERENCES
- **P1** Prefer **stdlib-only, no imports at all** for auditability; `hypothesis` only in tests.
- **P2** Share the exact `FORBIDDEN_KEY` taxonomy with Capa 1/2/3/4/5 (one anti-surveillance definition,
  not six).
- **P3** Prefer property-based tests: the verdict is invariant to any reputation the members carry;
  one-token-one-voice always holds (a duplicate token always refuses); a weighted-voice input is always
  refused; a single paramount objection always blocks regardless of how many consent; the output never
  carries an objector token or a tally.

## ESCALATION TRIGGERS (reject + surface)
- **E1** Request (any depth) contains a `FORBIDDEN` surveillance-shaped **or** a `VOTE_WEIGHT`-shaped
  key → **refuse** (invariants 2/6/7).
- **E2** `circle_id`/`proposal_id`/`now`/`expires_at` missing/empty; a disposition with a non-whitelisted
  key; `disposition` not in `{consent, object, abstain}`; an `object` without a `{paramount, reason}`
  objection, or a non-`object` carrying an objection; a duplicate token → **refuse** (M1/M2/M4).
- **E3** Malformed envelope (`dispositions` wrong type, a disposition not a dict) → reject, do not repair.

## Reversibility framing
- `decide()` is a **two-way door** (pure, no side effects, no persistence) → fully autonomous to
  *resolve one round's consent*. Executing the adopted proposal is the **humans'** step.

## Constraint × Execution-Mode matrix
| ID | Decide (Live) | Simulation/Backtest | Notes |
|----|---------------|---------------------|-------|
| M1 one token one voice | Enforce (raise on dup) | Enforce | invariant 7; never relax |
| M2 weight unrepresentable | Refuse | Refuse | anti-plutocracy firewall |
| M3 forbidden scan | Refuse | Refuse | the surveillance shape |
| M4/M5 consent, no tally | Enforce | Enforce | categorical; no majority |
| M6 objection = pause | Enforce | Enforce | surface reason, never mark person |
| M7 circle-local | Enforce (drop off-circle) | Enforce | no auto-propagation |
| M8 forgetting | Enforce (drop + stamp) | Enforce | no dossier of dissent |
| N4 no LLM | Enforce | Enforce | deterministic procedure |
</content>
