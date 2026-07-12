# Failure Model + Stress Report — Capa 2 Trust-Legibility Query

> Produced by red-team. Hostile review of the Capa-2 query spec. This is the razor's-edge
> layer (§6.1); the failure mode is not a dead network, it is a **surveillance cage**.

## Failure modes (F#)
- **F1 — The helpful scalar.** Code "summarizes" the paths into an overall `trust_score` /
  `trust_pct` / normalized voucher count → the exact social-credit shape reappears (inverts
  invariant 2). *Mitigation:* M3/N2; AC5 scans the verdict for any scalar/forbidden key; the
  output schema has **no** number that ranks the person (only per-path/per-fact specifics).
- **F2 — The god-view entrypoint.** A convenience `standing_of(target)` (no asker) or a
  `rank_all(cell)` is added → an absolute/global view returns. *Mitigation:* M1/N3; the only
  entrypoint requires an `asker` and a single concrete `target`; AC1/AC6/AC7 assert position-
  relativity; M10 refuses wildcard/list targets (no enumeration).
- **F3 — Absence read as a mark.** `no_info_from_your_position` is stored/treated as "distrusted"
  → an invisible blacklist by absence (inverts invariant 3). *Mitigation:* M5/N4; there is no
  negative verdict and no distrust edge; AC4 asserts unreachable returns the neutral verdict and
  still returns normally (never raises, never a `false`-flavored dossier record).
- **F4 — Stale dossier.** Expired vouches/facts still influence the answer → a permanent record
  that never forgets (inverts invariant 5). *Mitigation:* M4/AC3; expired items are dropped
  **before** traversal; property P-expire: adding only-expired items never changes the verdict.
- **F5 — Cross-cell leak.** An out-of-cell vouch counts toward the answer → reputation follows the
  person across contexts (inverts principle 1 / invariant 4). *Mitigation:* M2/AC2; only
  `cell_id`-matching items are considered; property: out-of-cell items never change the verdict.
- **F6 — Surveillance creep via the graph.** A caller smuggles `{"about":"t5","reputation":0.9}`
  as a "fact" node → a person-scalar enters through the data. *Mitigation:* M8/AC5b; the recursive
  forbidden-key scan runs over the **whole input including the graph**; such a node is refused.
- **F7 — Repair-instead-of-refuse.** Code strips a `reputation` key or coerces a wildcard target
  and answers anyway → answers over a dossier-shaped input as if clean. *Mitigation:* N6/AC5b/AC6;
  the only responses are answer-as-asked or refuse (raise); never strip-and-answer.
- **F8 — Asker-blind cache.** Results are memoized by `(target, cell)` ignoring the asker → a
  single canonical standing per person = a god-view rebuilt in the cache. *Mitigation:* N9/AC7;
  the two-askers divergence test proves the result is a function of the asker; a correct cache key
  must include the asker (and the graph), documented.
- **F9 — Taxonomy drift from Capa 1/4.** Capa 2 keeps a separate forbidden-key list that diverges
  → the three layers disagree on the surveillance shape (AC-X breaks). *Mitigation:* P2 (constraints)
  — share the exact `FORBIDDEN_KEY` set; AC-X regression-checks agreement across layers.
- **F10 — Unbounded / self-referential traversal.** A cyclic vouch graph loops forever, or
  `asker == target` self-vouches into legibility. *Mitigation:* M7 + visited-set (cycle guard);
  ST3 — a self-query yields no path (you don't vouch yourself legible); `max_hops` caps depth.

## Stress findings (ST#)
- **ST1 — Substring false positives in the scan.** A benign key like `"bankruptcy_note"` contains
  `ban`; `"scan_result"` contains `scan`⊄list. **Decision (inherited from Capa 1 ST1):** the
  taxonomy is a *shape heuristic biased to over-refuse* — a false refusal is safe (the caller
  re-labels a field), a false admit is a surveillance leak. Keep the exact shared token set;
  document the bias. Test `"ban"` (must trip) and a clean fact statement (must not trip).
- **ST2 — Empty graph / no edges.** `vouches=[]`, `facts=[]` → valid; every target is
  `no_info_from_your_position` (bootstrapping state). *Verify:* AC4 tolerates the empty graph and
  returns the neutral verdict, not an error.
- **ST3 — Self-query.** `asker == target` → no vouch-path (a self-vouch is not legibility); facts
  about the asker may still surface if present. *Verify:* documented; AC1 variant.
- **ST4 — Self-confirmation.** The query's own traversal agrees with its own bug. *Mitigation:*
  an **independent** reachability oracle (hand-written BFS, separate from the module) cross-checks
  reachable/unreachable in tests (tests.md cross-check, AGD-045).
- **ST5 — Auditability vs. forgetting / no-storage (open §6.6).** The verdict is auditable yet must
  not become a permanent record, and the graph must not be stored. *Partial mitigation:* the
  function is pure and stores nothing; `now`-based expiry drops stale items (M4). **Flagged:**
  enforcing that the *caller* does not persist and correlate verdicts is outside this pure function
  — noted, not faked-resolved (mirrors Capa-4/Capa-1 ST5).
- **ST6 — ISO-8601 lexicographic compare.** String compare of `expires_at` is only correct for
  normalized UTC ISO-8601 (`...Z`, same offset). **Decision:** document that `now`/`expires_at`
  must be normalized-UTC ISO-8601 strings (as elsewhere in the stack); mixed offsets are the
  caller's error, not silently mishandled. Test with `...Z` timestamps only.

## Open (system-level, NOT this query) — do not fake-resolve (§6)
- **The razor's edge is a governance question, not a code one (§6.1).** The API removes the throne
  *per call* (asker-relative, graph-supplied, nothing stored, no scalar). But a **malign governor**
  who stores every result, varies the asker, and correlates across calls can reconstruct a god-view
  *outside* the function. Protocol benign + hand malign = the nightmare. Structure makes it *hard*,
  not impossible; *who governs and for what* decides. **Stakes: a cage, not just a failure.** Flagged.
- **Sybil / token↔person binding (§6.2)** — unsolved. The graph is trusted as given; a Sybil can
  fabricate vouches from throwaway tokens to manufacture reachability. The query treats
  `participants`/tokens as opaque and never binds them to people; it cannot tell a real web of trust
  from a puppet one. Flagged, not solved.
- **Newcomer / bootstrapping exclusion.** A newcomer with no in-cell vouch-paths always receives
  `no_info_from_your_position`. Positive-sum (principle 5) protects them from being *marked*, but
  leaves them *invisible* — reachable to no one, so transacted-with by no one. Making a newcomer
  legible without building a dossier is genuinely unsolved (§6.2, bootstrapping/exclusion). Flagged,
  not faked — the query does **not** paper over it with a default/seed score (that would be F1).
- **Fertility metric is Goodhart-prone** (§6.4); federation/translation as recentralizing bottleneck
  (§6.5); exit-vs-accountability, where re-entry under a fresh token launders a bad history but a
  persistent token is a dossier (§6.6). All governance/relationship problems — flagged, not coded.
