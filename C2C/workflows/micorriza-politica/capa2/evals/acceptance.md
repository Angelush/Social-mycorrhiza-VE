# Acceptance Criteria — Capa 2 Trust-Legibility Query

> Produced by design-evals. Binary Done (AGD-028): verify the artifact, not a self-report.
> Every AC is machine-executable with zero human judgement.

- **AC1 — A reachable, in-cell, unexpired target is known via trust.** Given a graph where the
  asker vouches for `t7` and `t7` vouches for the target (all in `cell_id`, unexpired at `now`),
  the query returns `verdict == "known_via_trust"`, `from_your_position.reachable == true`,
  `nearest_hops == 2`, at least the path `[asker, "t7", target]` in `vouch_paths`, and `"t7"` in
  `vouched_by_people_you_trust`. Pass/fail: field equality. (Targets principles 1/2, invariant 2.)
- **AC2 — Out-of-cell edges/facts are ignored (contextual, not global).** The same vouch chain
  tagged with a *different* `cell_id` yields `verdict == "no_info_from_your_position"`,
  `reachable == false`, empty paths. Pass/fail: verdict + emptiness. (Targets principle 1 / invariant 4 / F5.)
- **AC3 — Expired edges/facts are forgotten (dropped before traversal).** A vouch chain whose edges
  have `expires_at <= now` yields `no_info_from_your_position`; the identical chain with
  `expires_at > now` yields `known_via_trust`. Pass/fail: verdict flips on expiry only.
  (Targets principle 4 / invariant 5 / F4.)
- **AC4 — Absence is not a mark; empty/unreachable returns the neutral verdict, never raises.** An
  empty graph, and a target reachable by no path with no facts, both **return normally** with
  `verdict == "no_info_from_your_position"`, `reachable == false`, and **no** negative/blacklist
  field anywhere. Pass/fail: normal return + verdict + absence of any negative field.
  (Targets principle 5 / invariant 3 / F3.)
- **AC5 — No person-scalar in the output; surveillance shape refused in the input (the razor's edge).**
  (a) For every admitted case, a recursive key scan of the verdict finds **zero** forbidden keys
  (`score|rating|reputation|rank|blacklist|ban|penalty|global_id|dni`) and there is **no numeric
  field that ranks/scores the target** (the only numbers are `nearest_hops`, `considered_*` counts,
  and fact statements — none is a person-rating). (b) An input carrying any forbidden key **at any
  depth, anywhere including a graph node/fact**, is **refused** (`LegibilityBreachError`), not
  answered. Pass/fail: key-scan + rejection. This is the case where "correct" means *refusing to
  emit or accept the surveillance-shaped artifact*. (Targets invariant 2 / F1 / F6.)
- **AC6 — No enumeration / no god-view entrypoint.** (a) The module exposes **no** function that
  answers about a target without an `asker`, and **no** function that ranks/lists multiple targets
  (static: only `query(...)` with a required `asker` + single `target`). (b) A `target` that is a
  wildcard (`"*"`), a list, a dict, `None`, or empty is **refused**. Pass/fail: static surface + rejection.
  (Targets principle 2/6 / N3 / F2.)
- **AC7 — Position-relativity (the divergence proof).** For a **single** graph and a **single**
  `(target, cell, now)`, two different askers `A` and `B` — positioned so that only `A` has a
  vouch-path to the target — return **different** verdicts (`A: known_via_trust`, `B:
  no_info_from_your_position`). Pass/fail: `result(A) != result(B)`. This is the structural proof
  that there is no god-view: the answer is a function of the asker. (Targets principle 2 / F8.)
- **AC8 — Determinism.** Running the query twice on the same input yields byte-identical JSON
  (sorted path/fact enumeration). Pass/fail: string equality. (Targets M9.)
- **AC9 — Envelope validation.** Missing/empty `asker`/`cell_id`/`now`, `max_hops` not `int > 0`,
  `graph`/`vouches`/`facts` of the wrong type, or a malformed edge/fact are **refused** (not
  repaired). Pass/fail: exception raised. (Targets E3 / N6.)

## Consistency with Capa 1 and Capa 4
- **AC-X — Shared surveillance taxonomy is honored.** Feeding a Capa-1 surveillance-shaped payload
  (e.g. `{"seller": {"trust_score": 88}}`) as a Capa-2 graph fact node **refuses** it — the same
  verdict Capa 1's membrane and Capa 4's engine reach independently on that shape. The three layers
  must not disagree on the forbidden-key taxonomy. Pass/fail: all refuse. (Targets P2 / F9.)
