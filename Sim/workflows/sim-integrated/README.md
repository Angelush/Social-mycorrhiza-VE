# Sim-Integrated — B2B + C2C running at once (seam + threat contract; BUILT last, as designed)

Per brief §5 and §7, the integration is designed-for-now, built-last. It runs **both** SUTs over **one
population** so the cross-effects on microeconomics become observable — the question the user is really
after: *how does one context change the other?*

## The questions only the integrated sim can ask
- Does C2C **trust legibility** change who defaults in the B2B cell? (A firm's owner is also a C2C
  member; does their social standing predict — or fail to predict — B2B credit behaviour?)
- Does B2B **liquidity stress** (a credit crunch) change C2C **cooperation** (do people fall back to
  the gift/equality rooms, or does trust erode)?
- Does an adversary who is blocked in one system **route around it via the other**?

## The single seam that enables it (brief §5)
**A shared actor identity that lives in both worlds.** A "business" is simultaneously a firm in a B2B
cell and an org in a C2C market room; a "person" is a C2C member who may also be a sole-trader firm.
The engine's actor identity is domain-agnostic precisely so one identity can span both SUTs. The
integrated `World` holds both adapters and steps both per tick over the shared population.

## The invariant the integration must TEST (not assume)
The firewall between the **value path** (B2B, denominated) and the **social path** (C2C, non-
denominated) is itself an invariant. The integration seam is exactly where a **new failure mode lives**:
- a denominated B2B debt must **not** leak into a C2C gift/equality room (parent C2C inv. 1, the
  kula/gimwali wall — now a cross-system wall);
- a C2C **person-scalar** must **not** become an input to a B2B credit decision (parent C2C inv. 2 +
  B2B inv. 9 human-in-loop; a social score feeding an automated credit denial is the nightmare both
  systems are built to prevent).

There is also a **second firewall that only a multi-instance sim can test: the B2B cell-to-cell
contagion firewall (B2B inv. 6).** The shipping B2B SUT is single-cell (`clear()` takes one `cell_id`;
no obligation carries a cell tag; a foreign member is rejected as "unknown member"), so *within* a
single Sim-B2B world there is nothing to attack — the firewall holds trivially by the input contract
(B2B F7's own mitigation). A real default-contagion test needs **two B2B ledger/solver instances** and
an actor trying to make a default or a bound-breach in cell A move value into cell B. That is the same
multi-instance shape as the value/social wall, which is why the "Cell-leaker" degrades to a
harness-partition guard in Sim-B2B (brief §5) and the genuine oracle lives **here**.

So the integrated sim gets a **Track A of its own** for both firewalls (value/social *and* cell-to-cell),
plus a bad actor (**Bridge-exploiter**, generalising the Cell-leaker) whose whole strategy is to smuggle
value or a score across a seam. If the harness finds a leak, that is the highest-value finding in the
whole project.

## Status
- [x] Full bundle: `spec.md` + `failure-model.md` + `evals/` (M0, 2026-07-11).
- [x] Built and verified against BOTH real SUTs — `../../src/sim_integrated/` (M1–M4: Identity,
      IntegratedWorld over two B2B ledger instances + the C2C modules, Bridge-exploiter, the three
      firewall oracles, negative control, researcher + campaign). Headline finding, exactly as
      predicted above: **F-VS2 has no SUT-enforceable wall** — a person-scalar-derived credit change
      succeeds against the real B2B and is caught only by the harness's provenance oracle.
- [ ] The cross-effect microeconomic study (the questions above) over integrated campaigns — open
      future work; the firewalls it needs are now tested infrastructure.
