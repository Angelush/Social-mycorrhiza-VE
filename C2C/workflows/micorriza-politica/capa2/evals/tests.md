# Test Cases — Capa 2 Trust-Legibility Query

> Produced by design-evals. Each: input, expected verdict, verification rule.
> Tokens are opaque per-cell strings; `now`/`expires_at` are normalized-UTC ISO-8601 (`...Z`).

## Test A — Normal: reachable in-cell target (AC1)
- **A1 two-hop:** asker `a` vouches `t7`; `t7` vouches target `x`; all `cell_id="barrio-1"`,
  `expires_at="2027-01-01T00:00:00Z"`, `now="2026-07-06T00:00:00Z"`, `max_hops=3`.
  → `verdict="known_via_trust"`, `reachable=true`, `nearest_hops=2`,
  `["a","t7","x"] in vouch_paths`, `"t7" in vouched_by_people_you_trust`.
- **A2 with a fact:** add fact `{"about":"x","statement":"completed 12 exchanges","cell_id":"barrio-1","expires_at":null}`
  → the fact appears verbatim in `from_your_position.facts`.
- **A3 self-query:** asker `a` == target `a`, no self-vouch → `no_info_from_your_position` unless a
  fact about `a` exists (then `known_via_trust` via the fact, `reachable=false`).
- **Verify:** AC1, AC8.

## Test B — Contextual: out-of-cell items ignored (AC2)
- **B1:** same A1 chain but edges tagged `cell_id="otro-barrio"`, query `cell_id="barrio-1"`
  → `no_info_from_your_position`, `reachable=false`, empty paths.
- **Verify:** AC2 (reputation does not follow the person across cells).

## Test C — Forgetting: expired items dropped (AC3)
- **C1 expired:** A1 chain but `expires_at="2020-01-01T00:00:00Z"` (< `now`)
  → `no_info_from_your_position`.
- **C2 fresh:** identical chain, `expires_at="2027-01-01T00:00:00Z"` → `known_via_trust`.
- **Verify:** AC3 — the verdict flips on expiry alone.

## Test D — Absence is not a mark (AC4)
- **D1 empty graph:** `vouches=[]`, `facts=[]` → returns normally, `no_info_from_your_position`,
  `reachable=false`, no negative/blacklist field anywhere in the output.
- **D2 unreachable:** graph has edges but none path from asker to target → same neutral verdict.
- **Verify:** AC4 — normal return (no raise), neutral verdict, no negative field.

## Test E — Adversarial / the razor's edge: no scalar out, surveillance shape refused (AC5)
- **E1 (verdict scan):** for every admitted case (A1–A3, C2), a recursive key scan of the verdict
  finds **zero** forbidden keys, and no field ranks/scores the target.
- **E2 (graph node with a score):** graph fact `{"about":"x","reputation":0.9,"cell_id":"barrio-1"}`
  → **refused** (`LegibilityBreachError`) — a person-scalar smuggled through the graph.
- **E3 (nested in a vouch):** vouch edge `{"from":"a","to":"x","cell_id":"barrio-1","meta":{"trust_rank":1}}`
  → **refused** (forbidden shape at depth).
- **E4 (envelope):** top-level `blacklist=[...]` on the query → **refused**.
- **Verify:** AC5 (a,b). Correct behavior is to refuse the social-credit shape at any depth AND to
  emit no scalar of the person.

## Test F — No enumeration / no god-view entrypoint (AC6)
- **F1 (static surface):** the module exposes exactly one query entrypoint requiring an `asker` and
  a single `target`; assert there is no `standing_of`/`rank_all`/asker-less function.
- **F2 (wildcard/list target):** `target="*"`, `target=["x","y"]`, `target=None`, `target=""`
  → each **refused**.
- **Verify:** AC6 (no god-view, no enumeration).

## Test G — Position-relativity: the two-askers divergence proof (AC7)
- **G:** one graph — `A` vouches `t7`, `t7` vouches `x`; `B` vouches nobody toward `x`. Query the
  **same** `(target=x, cell, now)` once as `asker=A`, once as `asker=B`.
  → `result(A).verdict="known_via_trust"`, `result(B).verdict="no_info_from_your_position"`, and
  `result(A) != result(B)`.
- **Verify:** AC7 — the answer is a function of the asker; there is no god-view. This is the Capa-2
  analogue of Capa-1's "surveillance shape refused in every room" defining test.

## Test H — Determinism (AC8)
- **H:** run A1 (with several vouch-paths of equal length) twice; assert byte-identical
  `json.dumps(out, sort_keys=True)`; assert `vouch_paths` is deterministically ordered.
- **Verify:** AC8.

## Test I — Envelope validation (AC9)
- Missing/empty `asker`, `cell_id`, `now`; `max_hops=0`/`-1`/`"3"`/`True`; `graph=[]` (not dict);
  `vouches="x"` (not list); a malformed edge (missing `from`/`to`/`cell_id`); a malformed fact
  (missing `about`) → each **refused**.
- **Verify:** AC9.

## Test J — Cross-layer consistency (AC-X)
- Feed a Capa-1 surveillance-shaped payload as a Capa-2 graph fact node:
  `facts=[{"about":"x","cell_id":"barrio-1","seller":{"trust_score":88}}]` → **refused**
  (`trust_score` matches `score`/`rank`), matching Capa-1's and Capa-4's independent refusals.
- **Verify:** AC-X — the three layers agree on the forbidden-key taxonomy.

## Property tests (Test P — hypothesis)
- **P1 (no scalar out):** for any clean random graph that admits, the verdict scanned recursively
  contains zero FORBIDDEN keys and no target-ranking number.
- **P2 (forgetting):** adding only-expired vouches/facts (`expires_at <= now`) to any graph never
  changes the verdict vs. the graph without them.
- **P3 (contextual):** adding vouches/facts in a *different* cell never changes the verdict for the
  query cell.
- **P4 (surveillance refused at any depth):** a graph containing any FORBIDDEN key nested at random
  depth is always **refused**.
- **P5 (position-relativity, monotone whitelist):** adding a vouch edge can only *create or keep*
  reachability, never remove it — the graph opens doors, it cannot close them (positive-sum).

## Cross-check (independent oracle, AGD-045)
Re-derive reachable/unreachable with a hand-written BFS over the (independently) cell-filtered,
expiry-filtered edge set — separate from the module's traversal — and compare verdicts.
Disagreement = fail (catches self-confirmation).
