# Intent — the real objective + correctness contract (Sim-B2B)

> Produced by engineer-intent.

## The real objective (frame audit)
The stated task is "simulate the B2B system with good/bad/neutral actors." The frame underneath: a
**falsification harness + microeconomic microscope** that drives the *real* clearing solver and
mutual-credit ledger under adversarial and mixed populations, inside an auto-research loop that
compounds what each round teaches. The wrong-frame version to reject: a pretty agent-based *demo* that
reimplements a clearing algorithm to show it "working" — that tests a fiction and flatters the design.
The value is in **what breaks** (Track A) and **who gains/loses** (Track B), driven against the code
that will actually ship.

## Mini-Me check
Do not encode "a market simulator, but with our vocabulary." Build a purpose-built harness whose SUT
is the imported real module and whose adversaries are the numbered failure modes. The engineering
challenge: drive the real solver/ledger hard enough to expose their edges **without** reimplementing
one line of their logic (engine inv. 1).

## Scope of THIS build (sequencing per brief §7)
1. **Shared engine** (`../engine/spec.md`) — loop, world, actor protocol, researcher, journal,
   two-track measurement base.
2. **Sim-B2B instantiation** (this deliverable): the B2B SUT adapter, the seven B2B archetypes
   (rule-based core; LLM probe optional + stubbable), the B2B Track-A oracles and Track-B statistics,
   and one runnable campaign.

Out of scope now: Sim-C2C (stub + seams only), Sim-Integrated (stub + seams only), any GUI, any live
deployment, any LLM on the value path.

## Correctness contract — for the harness
- **Truthfulness:** The trace is the single source of truth; Track-A oracles re-derive every invariant
  independently and never trust the SUT's own bookkeeping.
- **Completeness:** Every adjudicated value-path event in a round is measured under both tracks; none
  is silently dropped.
- **Determinism:** A campaign is byte-reproducible from `(scenario, seed, actor_mix, params, SUT
  commit, cassette)` — the harness inherits the SUT's own byte-determinism (engine inv. 3).
- **Policy compliance:** The SUT source is imported read-only for the whole campaign; the researcher
  mutates only the world, within the declared search space (engine inv. 2). No LLM on the value path
  (engine inv. 8 / parent B2B inv. 1).
- **Failure handling:** A caught invariant violation **halts and surfaces** the minimal exploit trace;
  it is never averaged into a success rate (engine inv. 4).
- **Auditability:** Every round is an entry in a hash-chained journal; a finding is reconstructable by
  replaying the journal.

## Flashlight beam (scope edges)
- **Bright center:** drive the real solver + ledger with mixed/adversarial B2B populations across an
  auto-research loop; report invariant integrity (Track A) and microeconomic distribution (Track B),
  separately, per round.
- **Edges (NOT this):** no reimplementation of clearing/ledger logic; no social/C2C actors here; no
  value adjudication by an LLM; no claim that a green campaign proves safety (it proves *no explored
  adversary broke it* — brief §6.1).
