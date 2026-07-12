# Specification — Capa 1 Relational-Mode Partition ("las habitaciones")

> Produced by engineer-spec. Self-contained blueprint; an agent can build from this alone.
> Sibling of the Capa-4 `spec.md`. This is the **membrane primitive** the rest of the
> system routes through: Capa-4's AC6 (no bonus/price in a binary campaign) is a
> *special case* of the rule specified here.

## Purpose
Enforce, deterministically and by *shape*, the most important invariant of the social
system (brief §1.1, §4 Capa 1): **the separation of relational modes is sacred — market
logic never leaks into the gift or equality rooms.** The component is a **firewall /
type-system**: given a single *interaction* tagged with the room (relational mode) it
claims to belong to, it either **admits** it (returns a canonical admission verdict) or
**refuses** it (raises), because the interaction carries an instrument that does not
belong in that room. It classifies and gates; it never repairs, never prices, never
scores, never persists.

This is the `[INVARIANTE ARQUITECTÓNICA]` component (brief §4 Capa 1) — *"la capa más
importante y la más novedosa."* No LLM. Pure function. No state. Enabling by shape: it
refuses malformed **interactions**, never a **person** (a refusal is not a blacklist —
see Meaning layer).

## The three rooms (Fiske's relational models — brief §4 Capa 1)
| `mode` | Room (brief) | Logic | Market instruments (price/denomination/currency) | Reciprocity **ledger** (denominated debt) |
|---|---|---|---|---|
| `communal_gift` | Don comunal (mutual aid, care) | Diffuse, uncounted reciprocity | **FORBIDDEN** | **FORBIDDEN** — *tracking it kills the gift* (§4 Capa 1) |
| `equality_matching` | Emparejamiento por igualdad (turns, favors, time-banks, ROSCAs) | Symmetric, balanced, **in kind** | **FORBIDDEN** — balanced but *not priced* | Allowed **in kind only** (turn/slot counts); denominated/priced ledger forbidden |
| `market_price` | Precio de mercado (real C2C/C2B commerce, sale, gig) | Denomination, price, valuation | **Allowed** — this is their proper room | Allowed |

**The membrane is directional** (kula/gimwali wall): the forbidden direction is *market →
gift/equality*. The absence of a price is never a breach, so nothing gift-shaped is ever
refused for entering the market room. **The surveillance-shape ban is orthogonal and
holds in ALL three rooms** (invariants 2/3/6): no room may carry a person-scalar.

## Input (one interaction, JSON)
```json
{
  "mode": "communal_gift | equality_matching | market_price",
  "cell_id": "str (non-empty) — the local context; interactions are cell-scoped (invariant 4)",
  "interaction_id": "str (non-empty)",
  "expires_at": "str (ISO-8601) — optional; carried through if present (invariant 5, forgetting)",
  "participants": ["str — opaque, per-context token; NOT a cross-context identity"],
  "payload": { "... free-form room content ..." }
}
```
- `payload` is the room content whose *shape* is checked against `mode`. It is scanned
  **recursively, at any nesting depth** (a market field hidden a level down is still a leak).
- `participants` are opaque tokens (invariant 6/7); the firewall never binds a token to a
  person and never counts tokens toward anything.

## Output (an admission verdict, JSON) — on ADMIT
```json
{
  "mode": "...",
  "cell_id": "...",
  "interaction_id": "...",
  "expires_at": "... | null",
  "admitted": true,
  "audit_trace": {
    "rule": "no market instrument in a non-market room; no surveillance shape in any room",
    "checked_keys": "int (count of payload keys scanned, recursively)"
  }
}
```
- **The verdict contains NO field that scores, ranks, or persists a person, and echoes no
  payload content** — it reports *that* the interaction is well-typed for its room, not a
  judgement of anyone. On a breach the function **raises** (see below); it never returns
  `admitted: false` (a stored "refused" record of a person is itself a dossier — F4).

## Algorithm (deterministic)
1. **Validate envelope** (reject, do not repair): `mode` in the three literals; non-empty
   `interaction_id`/`cell_id`; `participants` a list of non-empty strings (may be empty);
   `expires_at`, if present, a non-empty str; `payload` a dict (may be empty).
2. **Surveillance-shape scan (all rooms):** recurse the *whole* interaction; if any key
   (case-insensitive substring) matches a `FORBIDDEN_KEY` (`score`, `rating`, `reputation`,
   `rank`, `blacklist`, `ban`, `penalty`, `global_id`, `dni`) → **refuse** (`MembraneBreachError`).
   Refuse the *shape* of a dossier at any depth (invariants 2/3).
3. **Membrane scan (room-specific), recursive over `payload`:**
   - `market_price`: no market-field check (price is proper here).
   - `communal_gift`: if any key matches a `MARKET_KEY` (`price`, `cost`, `fee`, `amount_cents`,
     `_cents`, `currency`, `valuation`, `denominat`) **or** a `RECIPROCITY_LEDGER_KEY`
     (`debt`, `owed`, `balance`, `credit`, `reciprocity`, `iou`, `favor_balance`) → **refuse**.
   - `equality_matching`: if any key matches a `MARKET_KEY` → **refuse**. Reciprocity-in-kind
     is *allowed* here (balanced exchange is the room's logic); only *denominated/priced*
     instruments are barred, which the `MARKET_KEY` set already captures.
4. **Admit:** return the verdict with `expires_at` carried through (or `null`), `checked_keys`
   = count of payload keys visited. Commit nothing.

## Determinism
Pure classification over a fixed key taxonomy; no iteration order affects the yes/no
verdict. Same input → byte-identical JSON output.

## Termination & cost
Single recursive pass over the interaction. O(K) in total key/element count K. No unbounded loops.

## Meaning layer (Axiom 6 — what the agent cannot infer)
- **The membrane is the whole point (invariant 1, category error §2.2).** Introducing market
  logic into a communal relationship does not optimize it — it *corrupts* it, often
  *irreversibly* (Gneezy–Rustichini daycare: removing the fine did not restore the norm;
  Titmuss on blood; Tetlock taboo tradeoffs). So the correct behavior on a market leak is
  to **refuse, never to convert or strip** the field — stripping would silently admit a
  corrupted interaction.
- **Directionality (kula/gimwali wall).** The forbidden direction is market → gift/equality
  only. A gift entering the market room is not a breach. Do not build a symmetric wall.
- **Tracking reciprocity kills the gift (§4 Capa 1).** In `communal_gift`, a *ledger* of who
  owes whom is as corrosive as a price — hence the reciprocity-ledger ban there but not in
  `equality_matching`, where balanced-in-kind reciprocity *is* the logic.
- **A refusal is not a blacklist (invariant 3, whitelist-not-blacklist).** The firewall gates
  an **interaction's shape**, never a **person**. It can only *admit* (enable); it has no
  ban/penalty/exclusion of anyone. It emits no `admitted:false` record — refusal is an
  exception the caller handles, not a stored verdict about a person (that record would be a
  dossier; F4).
- **No person-scalar, anywhere (invariants 2/6).** The surveillance-shape scan runs in every
  room, recursively; the verdict carries no score/rank and no cross-context join key.
- **Forgetting is native (invariant 5).** The function is pure and stateless — it holds no
  interaction after returning; `expires_at` is carried through for the caller's storage, not
  enforced here (a pure function cannot police storage — mirrors Capa-4 ST5).
- **Reversibility:** the firewall is a **two-way door** (pure classification, no side effects)
  → may run autonomously. Acting on a refusal (dropping/routing the interaction) is the
  caller's step; the firewall only proposes the verdict.

## Relationship to Capa 4 (reuse, not duplication)
Capa-4's AC6 — reject a `binary`/equality campaign that carries per-pledge prices or a
`sponsor_bonus_cents > 0` — is exactly this membrane applied to a campaign: a binary campaign
is an `equality_matching` interaction, and price/bonus are `MARKET_KEY`s. Capa 1 generalizes
that one-off check into the reusable primitive every layer routes through. The shared
`FORBIDDEN_KEY` taxonomy is intentionally identical to the engine's, so the anti-surveillance
posture is one definition, not two.

## Out of scope (explicitly NOT this component)
Trust-legibility (Capa 2), LLM matching (Capa 3), quorum/assurance (Capa 4 — already built),
governance (Capa 6), persistence/database, identity verification / Sybil resistance
(§6.2 — flagged, not solved here), and any *judgement of a person* (there is none — this
gates interaction shape only).
