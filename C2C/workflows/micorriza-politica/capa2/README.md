# Capa 2 — Trust-Legibility Query ("legibilidad de la confianza")

spec sub-bundle for **the razor's-edge layer** (brief §4 Capa 2, §6.1): the layer that
most easily slides into a surveillance score, built **last and with maximum care** (§7 Etapa 2).
It answers only the question that stays on the right side of the razor — **"do the people I
trust vouch for X, here, now?"** — as a web-of-trust query evaluated **from the asker's
position** over a **caller-supplied local graph**. It emits **no score, no rank, no reputation
number, no god-view**.

Shares the system-wide `../intent.md`, `../context.md`, and `../architecture.md` with the
Capa-4 and Capa-1 builds. Capa-2-specific docs live here:

```
spec.md            # the buildable blueprint (asker-relative query, six principles, algorithm)
constraints.md     # MUST/MUST-NOT with because-clauses
evals/acceptance.md  evals/tests.md   # AC1–AC9 + AC-X, machine-checkable
failure-model.md   # red-team: F1–F10, ST1–ST6, open (governance) problems
```

## The six principles that keep it off the razor (brief §4 Capa 2)
1. **Contextual, not global** — legible only within one `cell_id`, never a number that follows a person.
2. **Relational, not absolute** — answers "do the people I trust trust X?" from the **asker's** position (no god-view).
3. **Specific, not totalizing** — surfaces vouch-paths and facts ("completed 12 exchanges", "vouched by t7"), never a scalar or a moral verdict.
4. **Forgetting built in** — expired edges/facts are **dropped before traversal** (`expires_at`, native).
5. **Positive-sum** — only `vouches` (whitelist) edges; absence of a path is `no_info_from_your_position`, never a mark. You cannot lower anyone.
6. **No central holder** — the graph is a caller-supplied argument, scanned and discarded; no throne, no stored global graph.

## The defining design move — the god-view is *unrepresentable*, not merely disallowed
The same structural move that made the surveillance shape unrepresentable in Capa 1, applied to
Capa 2: **asker required** (no absolute-view entrypoint), **graph caller-supplied and never
stored**, **hop-bounded**, **output = paths/facts not a scalar**, **absence = "no info" not a
mark**, and **no enumeration** (single concrete target only). Proven by the **two-askers
divergence test** (AC7): the same `(target, cell)` returns different results for different
askers — the structural proof that there is no god-view.

## Relationship to Capa 1 and Capa 4
Reuses the **exact** `FORBIDDEN_KEY` taxonomy of the Capa-1 membrane and Capa-4 engine (one
anti-surveillance definition, not three). AC-X regression-checks that a surveillance-shaped
payload fed as a Capa-2 graph node is refused identically — the three layers cannot disagree.

## Flagged, NOT fake-resolved (brief §6)
- **Sybil / token-binding (§6.2):** the graph is trusted as given; fabricated vouches from
  throwaway tokens are not detected. Tokens are opaque; never bound to people.
- **The razor's edge is a governance question, not a code one (§6.1):** the API removes the
  throne *per call*, but a malign governor who stores and correlates results across askers
  rebuilds a god-view externally. Structure makes it hard, not impossible.
- **Newcomer / bootstrapping exclusion:** a token with no in-cell vouch-paths is always
  `no_info_from_your_position` — protected from being *marked*, but left *invisible*. Unsolved;
  the query does **not** paper over it with a seed/default score (that would be the antipattern).

## Implementation
`src/legibility/legibility_query.py` — pure, stdlib-only, deterministic, proposal-only query.
Tests: `tests/test_legibility.py` (AC1–AC9, AC-X) + `tests/test_legibility_properties.py` (P1–P5).
