# Audit — every finding → an enforceable requirement

> Produced by audit-feedback-loop (the judge). Proves each F#/ST# became a constraint, AC, or task — not just a report line.

| Finding | Became enforceable as | Enforced? |
|---|---|---|
| F1 surveillance creep | N2/N3/N4 + E1 + AC5 (key scan + forbidden-field rejection) | ✅ |
| F2 cross-campaign join | N4 (opaque per-campaign tokens) + AC5c | ✅ (caller must rotate tokens — documented) |
| F3 no-loss broken by arithmetic | M1 (int cents) + M3 (deterministic remainder) + AC2 + AC3 | ✅ |
| F4 bonus paid on fire | spec step 4 + AC3 (zero bonus when firing) | ✅ |
| F5 membrane leak | N5 + AC6 (reject priced binary campaign) | ✅ |
| F6 double-count re-pledger | M4 (dedup by token) + AC1 (Test B) | ✅ |
| F7 LLM/engagement creep | N1 + architecture (LLM capped at Capa 3 proposal-only) | ✅ |
| F8 bonus-extraction Sybil (binary failure-bonus drained by throwaway tokens) | N5 (binary carries no bonus) + AC6 (reject `binary` + `sponsor_bonus_cents>0`) | ✅ free case closed; Sybil identity itself still §6.2-open |
| ST1 remainder bias | M3 (ascending-token, content-free) + Test B | ✅ |
| ST2 zero-bonus campaign | AC2/AC3 with zero bonus | ✅ |
| ST3 threshold boundary | spec step 3 (`>=`) + boundary test | ✅ |
| ST4 self-confirmation | independent Counter oracle (tests.md, AGD-045) | ✅ |
| ST5 forgetting vs audit | M7 (`expires_at` carried) | ⚠️ partial — expiry *enforcement* is storage's job, outside this pure function; flagged, not faked |

**Verdict:** All correctness/safety/shape findings are enforced by a constraint AND covered by an acceptance criterion. ST5 (expiry enforcement) and F8's residue (Sybil identity itself) are explicitly deferred to the storage/caller/governance layer with tracked notes (§6.2/§6.6), not silently dropped — dedup is one-*token*-one-weight, not one-*person*-one-weight, and cross-campaign forgetting is a caller/storage convention. The defining hazard (surveillance shape, F1/F2) is enforced both by refusing to emit and by refusing to accept the shape (now scanned recursively). Bundle is ready to build.

---

## Round 2 — post-build security & correctness audit (2026-07-07)

> Six findings surfaced by a live-repro audit across all six layers; each became a code fix **and** an
> acceptance test — the same finding→enforceable discipline. 293/293 tests pass; every finding was
> reproduced against the real module before and after the fix.

| Finding | Layer | Became enforceable as | Enforced? |
|---|---|---|---|
| D-01 — a market key on the *envelope* was admitted in a gift room (the market scan is payload-scoped; envelope keys weren't whitelisted) | Capa 1 | `_ENVELOPE_KEYS` whitelist in `admit()`: any unknown top-level key is refused (whitelist-not-blacklist, matching Capa 3/5/6) + `test_d01_*` | ✅ |
| D-02 — all-shortest-paths enumeration was exponential in a dense caller-supplied graph (resource-exhaustion) | Capa 2 | a reverse BFS computes `reachable`/`nearest_hops`/`vouched_by` EXACT in O(V+E); the concrete paths are a deterministic sample capped at `_MAX_VOUCH_PATHS`, with `audit_trace.paths_truncated` + `test_d02_*` | ✅ |
| D-03 — one-token-one-voice was checked before circle/expiry filtering, so an off-circle or expired duplicate vetoed the whole round | Capa 6 | uniqueness enforced only among the **surviving in-circle, unexpired** voices (it is a per-circle invariant) + `test_d03_*` | ✅ |
| D-04 — the velocity cap applied only in-window, so a burst backdated just past the window escaped it | Capa 5 | the cap applies per artifact **per window-bucket** (a burst is a burst whatever tick it is dated to); sustained cross-window coordination still passes + `test_d04_*` | ✅ |
| D-05 — duplicate vouch edges yielded duplicate identical paths | Capa 2 | adjacency de-duplicated (`sorted(set(...))`) + `test_d05_*` | ✅ |
| D-06 — binary `amount_cents` accepted `False`/`0.0` via Python's `==` coercion | Capa 4 | strict check: accept only absent / `None` / int `0`, reject bool/float/nonzero (matches the monetary path) + `test_d06_*` | ✅ |
| F-01 (crash) — a non-list `cite_facts` from the model crashed the matcher wrapper, violating its "never crash" guarantee (F7) | Capa 3 | a non-list `cite_facts` is coerced to `[]` (every cite dropped, proposal survives) + `test_ac10_non_list_cite_facts_*` | ✅ (prior pass) |

**Flagged, still open (governance, not code):** the underlying Sybil / token↔person binding (§6.2) and the off-protocol *distributed* mob (Capa-5 F11) remain governance questions — the D-04 breaker throttles a *burst*, not a slow campaign spread across many buckets by many tokens. The fixes make each attack harder, not impossible — the project's own idiom (structure makes it hard; who governs decides).
