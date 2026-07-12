# Specification — Capa 4 Assurance-Contract / Quorum Engine

> Produced by engineer-spec. Self-contained blueprint; an agent can build from this alone.

## Purpose
Resolve a **single collective-action campaign** deterministically: did enough distinct people commit to fire the action? If not, make every committer whole (refund) and, for a *dominant* assurance contract, distribute the sponsor's bonus exactly. The engine **proposes** a resolution; executing it (firing the action, moving refunds) is a separate, human/protocol-gated step. It is a pure function: no side effects, no persistence, no reputation, no cross-campaign state.

This is the `[DETERMINISTA]` component of the social system (brief §4 Capa 4). No LLM, no float money, no global scalar of a person.

## Input (one campaign, JSON)
```json
{
  "campaign_id": "str (non-empty)",
  "cell_id": "str (non-empty) — the local context; campaign is scoped to one cell",
  "kind": "binary | monetary",
  "threshold": "int > 0 — minimum number of DISTINCT committers to fire",
  "sponsor_bonus_cents": "int >= 0 — dominant-assurance bonus, paid to committers ONLY if threshold NOT met (0 = plain assurance contract). MUST be 0 when kind==binary: a bonus is a market instrument, barred from an equality room (membrane + anti-Sybil)",
  "expires_at": "str (ISO-8601) — when this resolution artifact ceases to be valid (invariant 5, forgetting)",
  "pledges": [
    {
      "pledge_id": "str (unique within campaign)",
      "participant_token": "str — opaque, per-campaign; NOT a cross-context identity",
      "amount_cents": "int >= 0 — required iff kind == 'monetary'; the amount escrowed/pledged"
    }
  ]
}
```
- A person may appear in multiple pledges (e.g. re-pledge); **distinct-committer count dedups by `participant_token`** (one *token*, one weight — invariant 7; token↔person binding / Sybil resistance is out of scope, §6.2).
- `amount_cents` is ignored for `kind == "binary"` (a binary campaign counts heads only, e.g. "20 people show up to the cleanup").

## Output (a resolution proposal, JSON)
```json
{
  "campaign_id": "...",
  "cell_id": "...",
  "status": "fires | refunds",
  "distinct_committers": "int",
  "threshold": "int",
  "expires_at": "...",
  "resolution": {
    "fires": {
      "total_pledged_cents": "int (0 for binary)"
    },
    "refunds": [
      {"participant_token": "...", "refund_cents": "int", "bonus_cents": "int"}
    ]
  },
  "audit_trace": {
    "rule": "distinct_committers >= threshold",
    "deduped_from_pledges": "int (raw pledge count)"
  }
}
```
- Exactly one of `resolution.fires` / `resolution.refunds` is populated, matching `status`.
- **The output schema deliberately contains NO field that scores, ranks, or persists a person across campaigns.** (See Meaning Layer M-shape.)

## Algorithm (deterministic)
1. **Validate** (reject, do not repair — see hazards): non-empty `campaign_id`/`cell_id`; `threshold > 0`; `sponsor_bonus_cents >= 0` int, and `== 0` when `kind == "binary"` (no market instrument in an equality room; anti-Sybil); unique `pledge_id`s; for `monetary`, every pledge has an int `amount_cents >= 0`; reject any forbidden field at any nesting depth (recursive scan — see M-shape). `binary` pledges must NOT carry positive amounts that imply pricing in a non-market room.
2. **Dedup committers:** `committers = sorted(set(p.participant_token))`. `distinct = len(committers)`.
3. **Decide:** `status = "fires" if distinct >= threshold else "refunds"`.
4. **If fires:** `total_pledged_cents = sum(amount_cents)` (0 for binary). No bonus paid. (Refund list empty.)
5. **If refunds:** for each distinct committer, `refund_cents =` sum of their pledged amounts (full make-whole; 0 for binary). Then distribute `sponsor_bonus_cents` across the distinct committers:
   - `base = sponsor_bonus_cents // distinct`; `rem = sponsor_bonus_cents % distinct`.
   - Sort committers by `participant_token` ascending; the first `rem` committers get `base + 1`, the rest get `base`. (Deterministic remainder allocation — invariant: exact, no float.)
6. **Assert conservation:** `sum(bonus_cents) == sponsor_bonus_cents` (refunds) or `== 0` (fires), and refunds sum to total pledged (no-loss). On failure, raise `AssuranceInvariantError` (a distinct type, NOT `ValueError`, so a caller validating input cannot swallow it) and abort — never emit a bad resolution.
7. **Emit** the resolution proposal with `expires_at` carried through. Commit nothing.

## Determinism
All iteration is over sorted keys (`participant_token`, `pledge_id`). Same input → byte-identical JSON output.

## Termination & cost
Single pass + one sort. O(P log P) in pledge count P. No loops that can fail to terminate.

## Meaning layer (Axiom 6 — what the agent cannot infer)
- **Invariant no-loss:** a committer is NEVER worse off for committing. If the action does not fire, full refund; for a dominant contract, refund **plus** a positive share of the bonus. This is the whole reason the mechanism works (Tabarrok). Violating it reproduces the free-rider trap the engine exists to dissolve.
- **Invariant conservation:** the sponsor bonus is neither created nor lost; it is split to the cent.
- **M-shape (the irreplaceable hazard, brief §1/§3/§6):** *within a single resolution* the engine must be **structurally incapable** of becoming a surveillance score (across campaigns this is a caller/storage convention — per-campaign token rotation + `expires_at` — not enforced by this pure function; see Reversibility + failure-model ST5). Concretely:
  - No output field ranks, scores, or rates a person.
  - No state persists across campaigns; `participant_token` is opaque and per-campaign (no cross-context join key).
  - The artifact carries `expires_at` (forgetting is native, invariant 5).
  - The engine can only **enable** (fire an action). It has **no** mechanism to exclude, ban, or penalize a person (whitelist-not-blacklist, invariant 3).
  - Input validation **rejects** (recursively, at any nesting depth) any field named like `score`, `rating`, `reputation`, `blacklist`, `ban`, `penalty`, `global_id`, or `dni` — a refusal to even accept the surveillance shape.
- **Unstated domain constraint (the membrane, invariant 1):** a `binary`/equality campaign must not smuggle a market instrument. A binary campaign carrying per-pledge prices **or a `sponsor_bonus_cents > 0`** is rejected — neither a priced pledge nor a monetary failure-bonus may leak into the equality room (kula/gimwali wall). The bonus ban is also anti-Sybil: with no stake, a binary failure-bonus is a zero-cost faucet — throwaway tokens drain it (§6.2).
- **Reversibility:** the engine is a **two-way door** (pure computation) → may run autonomously. The downstream *fire / move-refunds* step is a **one-way door** → draft + escalate; humans/protocol execute (agent proposes, human disposes).

## Out of scope (explicitly NOT this component)
Reputation, trust-legibility (Capa 2), LLM matching (Capa 3), governance voting (Capa 6), cross-cell federation, persistence/database, identity verification / Sybil resistance (open problem §6.2 — flagged, not solved here).
