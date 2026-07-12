# Capa 3 — Prosocial-Affordance Matcher ("el emparejador")

SpecSmith sub-bundle for **the first LLM in the stack** (brief §4 Capa 3, invariant 8,
architecture.md: *Species 2 / Tool-assistant, NOT Dark Factory, capped at proposal level per
FWK-030*). It surfaces, for an asker and within that asker's own declared cells, a **bounded list
of candidate matches**, each with a **human-readable reason** — "who near you needs what you
offer", "who shares this goal", or a **translation of a need across two of your contexts". The
**stochastic model proposes; a deterministic wrapper validates, bounds, and shapes; a human
disposes.** It emits **no score, no rank, no reputation, no engagement signal, no god-view**.

Shares the system-wide `../intent.md`, `../context.md`, and `../architecture.md` with the Capa-4,
Capa-1, and Capa-2 builds. Capa-3-specific docs live here:

```
spec.md            # the buildable blueprint (boxed LLM, five structural walls, algorithm)
constraints.md     # MUST/MUST-NOT with because-clauses
evals/acceptance.md  evals/tests.md   # AC1–AC13 + AC-X, machine-checkable, offline stub LLM
failure-model.md   # red-team: F1–F11, ST1–ST7, open (governance) problems
```

## The whole design problem — this is the FIRST LLM
The gravity of every recommender is **engagement optimization**, and the shortest path to
engagement is outrage (invariant 8, the platform original sin). The answer is **structural, not a
policy line**: the engagement signal is made **unrepresentable** — no click/dwell/outcome input, no
feedback loop — so the objective *is* cooperation initiated because the system cannot see anything
else. The LLM is **boxed**: a deterministic wrapper is the guardrail; the model is never trusted.

## The five structural walls (each an analogue of a deterministic-layer wall)
1. **Engagement unrepresentable** — declaration keys whitelisted; an `ENGAGEMENT_KEY` taxonomy
   refused; only declared offers/needs/goals are inputs; no feedback loop (invariant 8).
2. **No person-scalar** — the exact Capa-1/2/4 `FORBIDDEN_KEY` scan over both the LLM's input and
   its output; a surveillance-shaped proposal is **dropped, not stripped**; may **cite** a Capa-2
   fact, never **synthesize** a rating (invariant 2).
3. **The LLM cannot rank people** — the wrapper discards the model's order and imposes a canonical
   `(kind, token, reason)` sort; engagement-bait ordering is destroyed by construction (invariants 2/8).
4. **Cell-scoped, thin translation bridge** — matches only within the asker's own declared cells;
   `translation` bridges only two of the asker's own cells, human-gated; no global-graph merge
   (invariant 4; §6.5 recentralizing bottleneck flagged).
5. **Forgetting + no dossier** — pure over supplied inputs; expired declarations dropped; every
   proposal carries `expires_at`; nothing persisted across calls (invariants 5/6).

## Proposes, never imposes
The output **surfaces**; it never connects, notifies, auto-introduces, or persists. The
Tool-assistant has **no tool** that acts (FWK-030). Acting on a proposal is the human's step.

## The correctness under test is the WRAPPER's (the LLM is boxed)
Because Capa 3 is stochastic, the whole test suite injects a **deterministic / adversarial stub**
`propose` and never touches the network. Given hallucinated/adversarial model output — an off-cell
match, a person-scalar, an engagement-bait ordering, a non-consenting or unknown token, or an
off-schema entry — the deterministic wrapper must **refuse/drop it and never crash** (AC10, the
defining test; ST6 prompt-injection is the same test).

## Relationship to Capa 1, 2, and 4
Reuses the **exact** `FORBIDDEN_KEY` taxonomy of the Capa-1 membrane, Capa-2 query, and Capa-4
engine (one anti-surveillance definition, not four). AC-X regression-checks that a surveillance-
shaped payload fed as a Capa-3 candidate declaration is refused identically — the four layers cannot
disagree.

## Flagged, NOT fake-resolved (brief §6)
- **Engagement optimization is the gravitational pull (§6, invariant 8):** removed *per call*
  (nothing to maximize), but a malign governor who adds an outcome feedback loop rebuilds the
  engagement machine outside the function. Structure makes it hard, not impossible.
- **Translation as a recentralizing bottleneck (§6.5):** the bridge is kept thin, cell-local, and
  human-gated; whether it centralizes is governance, not code.
- **Filter-bubble / homophily (§6.1/§6.4):** no feedback loop means it cannot *learn* to narrow, but
  the model's proposals can still skew; breadth/serendipity is a curation matter.
- **Sybil / token-binding (§6.2):** tokens opaque, trusted as given.

## Implementation
`src/matcher/matcher.py` — pure, stdlib-only, deterministic wrapper; the LLM is **injected** via a
`propose` callable (never imported at module top). `src/matcher/claude_matcher.py` — the real
Claude-backed `propose` (imported lazily; not needed to import or test the core).
Tests: `tests/test_matcher.py` (AC1–AC13, AC-X) + `tests/test_matcher_properties.py` (P1–P6), all
with a stubbed/adversarial fake matcher — deterministic and offline.
</content>
