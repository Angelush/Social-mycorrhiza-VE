# Sim-C2C — social-protocol simulation (seam contract; since BUILT — see Status)

This began as a **stub with the seams marked**, per brief §7 sequencing: build Sim-B2B full first
(cleaner metrics, finished SUT), then instantiate the *same engine* (`../engine/spec.md`) over the C2C
SUT. The bundle now lives beside this file (`spec.md`, `failure-model.md`, `evals/`) and the build is
done — this README remains the record of the **one hard trap** that makes C2C fundamentally different
from B2B, and of the seams designed for it (all honoured; see Status).

## The SUT (the real code this will drive — do NOT reimplement)
`../../../C2C/src/`: `partition/membrane.py` (Capa 1, the rooms) · `legibility/legibility_query.py`
(Capa 2, asker-relative trust query) · `matcher/matcher.py` + `claude_matcher.py` (Capa 3, proposal-
only LLM) · `assurance/assurance_engine.py` (Capa 4, quorum) · `stigmergy/stigmergy.py` (Capa 5,
anti-cascade) · `governance/governance.py` (Capa 6, consent).

## The defining difference from Sim-B2B (why this is not "B2B sim for people")
**B2B is denominated; C2C is not.** There is no obligations graph to net and no clean welfare scalar.
The parent social brief is explicit (C2C inv. 2, §6.4): **there is no global scalar of the person, and the
"fertility" success metric resists quantification and Goodharts under any proxy.** Therefore:

- **Sim invariant 5 is load-bearing here:** Track-B measurement **cannot emit a per-person scalar.**
  The structural guarantee is the **output *type*** — a `WelfareReport` has *no agent-indexed
  dimension*, so a per-person score is **unrepresentable**, not merely un-named. The reused C2C
  `FORBIDDEN_KEYS` substring scan runs on top as **defense-in-depth lint** and is **insufficient
  alone**: it catches `trust_score` but not a scalar named `fertility`, `reachability`, or
  `centrality` — precisely the proxy sim brief §6.3 warns the researcher will Goodhart, which carries
  no forbidden substring. A sim that scores each person's trust to study "fertility" **rebuilds the exact
  god-view surveillance shape the C2C system exists to prevent.** Measuring it wrong is not a smaller
  win — it is the anti-goal, and a blacklist the researcher can rename around is not the wall.
- **Track B for C2C is position-relative and descriptive, never an objective the loop maximizes:**
  reachability of cooperation *from a sampled position* (did a newcomer find a match?), diversity of the
  vouch graph *seen from sampled positions*, cascade-damping ratio, bootstrapping cost. Every number
  ships with a **Goodhart flag**. When a proxy can't be measured honestly, the sim says so.

## Actors (each maps to a C2C invariant/failure mode — brief §2; verified against the real modules when built)
Reciprocator (good) · Newcomer (neutral, bootstrapping) · Lurker (neutral) · Surveillor (bad, C2C F1
surveillance-creep) · Sybil-voucher (bad, C2C F8) · Engagement-baiter (bad, C2C F7 / C2C inv. 8) ·
Mob-instigator (bad, C2C inv. 9 anti-cascade) · Room-leaker (bad, C2C inv. 1 kula/gimwali wall) ·
Bad-faith blocker (bad, C2C Capa-6 F8 consent capture / tyranny of the minority — flagged, not
solved; C2C brief §6.3). *As with B2B, these will be
checked against the shipping `membrane`/`legibility`/`matcher`/`assurance`/`stigmergy`/`governance`
modules when the full bundle is built — a mapping that assumes a mechanism the code lacks is a finding,
not a test.*

## Track A oracles (C2C-specific integrity)
No person-scalar emitted · market logic did not leak the gift/equality rooms · legibility answers
stayed asker-relative (the two-askers divergence property) · forgetting actually dropped expired
data · consent surfaced *reasons* not objector identities · anti-cascade breaker throttled the mob.

## Seams this stub reserves in the engine (so B2B doesn't foreclose them)
1. The **aggregate-only `WelfareReport` type** (no agent-indexed dimension) is in the **engine base
   class** (already specced), with `assert_no_person_scalar` as its secondary substring lint — so C2C
   inherits both the structural type-guard and the backstop for free, and neither is bolted on later.
2. `LLMPolicy` / cassette machinery is engine-level — C2C's matcher probes and fuzzy need-descriptions
   reuse it.
3. The `Researcher` is forbidden from optimizing a Track-B objective when the domain declares its
   welfare **descriptive-only** (a per-domain flag) — so the C2C fertility proxy can never become the
   loop's maximization target (brief §6.3).
4. Actor identity is engine-level so the same identity can later live in both worlds (integration).

## Status
- [x] Full bundle: `spec.md` + `failure-model.md` + `evals/acceptance.md` (M0, 2026-07-11).
- [x] Built and verified against the real C2C modules — `../../src/sim_c2c/` (M1–M6: adapter, world +
      9 archetypes, the 6 Track-A oracles, descriptive-only Track B, negative control N-01/N-02,
      researcher + campaign). Every seam above was honoured; note the descriptive-only researcher
      guard lives domain-side (`C2CResearcher.assert_descriptive_only`) because the engine carries
      no per-domain flag.
