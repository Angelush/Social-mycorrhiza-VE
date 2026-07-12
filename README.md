# Micorriza 🍄

**Coordination-and-distribution infrastructure for an era of cheap creation.**

When creating things becomes cheap (because AI does the making), the scarce and valuable
work moves elsewhere: *coordination, ownership, trust, and governance*. Micorriza is a set
of designs and reference implementations for that layer. The discipline throughout is a
single separation of concerns:

> The AI does the **solver / matching** work.
> The human-cooperative layer holds **ownership, trust, and governance**.
> The agent *proposes*; a human *disposes*. The one-way door over value never opens
> inside the loop.

This is not "a more powerful AI" and not "a blockchain." It is the institution that
distributes what cheap creation produces.

---

## The three parts

| Directory | What it is | Status |
|-----------|-----------|--------|
| [`B2B/`](B2B/) | **Mutual-credit clearing** between businesses — net obligations in EUR with no bank, no token, no chain. Deterministic solver *proposes*; a human-gated ledger *disposes*. | ✅ Built · 128/128 tests |
| [`C2C/`](C2C/) | **Social protocol** for a society to cooperate *across its differences*. Built so the parts that *cannot become a surveillance score* come first; legibility comes last, with care (an inversion of social-credit scoring). | ✅ Core layers built |
| [`Sim/`](Sim/) | **Simulation harness** that drives the **real** B2B and C2C code with populations of good / neutral / bad actors in a Karpathy-style auto-research loop — a driver and oracle, never a second copy of the mechanism. | ✅ Built · 120/120 tests |

Each part has its own detailed `README.md` and a source design brief.

---

## Design principles

- **Proposer / disposer split.** The AI proposes; deterministic, human-gated code decides.
  The irreversible "one-way door" over real value is never automated.
- **Invariants are headlines, not averages.** A violated invariant halts a run; it is never
  averaged into a pass rate.
- **Fertility over efficiency (social branch).** The goal is conditions under which trust and
  cooperation reproduce themselves — gardener, not engineer.
- **Anti-surveillance by construction.** Build what *can't* become a score first; add
  legibility last.
- **Test against reality.** Simulations drive the real systems under test — never mocks.

---

## Quick start

Each sub-project is a self-contained Python package sharing one virtualenv at the repo root.

```bash
# one-time setup
python3 -m venv .venv
.venv/bin/pip install pytest hypothesis networkx

# run each suite
(cd B2B && ../.venv/bin/python -m pytest tests -q)   # 128 tests
(cd C2C && ../.venv/bin/python -m pytest tests -q)
(cd Sim && ../.venv/bin/python -m pytest tests -q)   # 120 tests
```

See each sub-directory's `README.md` for architecture and run details.

---

## Repository layout

```
B2B/   mutual-credit clearing system (brief + SpecSmith bundle + src + tests)
C2C/   social C2C/B2C/C2B protocol (layered: partition, legibility, matcher, assurance, stigmergy)
Sim/   simulation harness driving the real B2B + C2C code, with an auto-research loop
```

All three were built with the same method: a **SpecSmith** spec-engineering bundle
(intent / context / architecture / spec / constraints / failure-model / evals) plus
multi-model orchestration, then verified against acceptance, property, and golden-set tests.

---

## License

Dual-licensed — see [`LICENSE.md`](LICENSE.md):

- **Code** → [GNU GPL v3.0](LICENSE-GPLv3)
- **Content & docs** → [CC BY-SA 4.0](LICENSE-CC-BY-SA-4.0)

Both are copyleft with share-alike terms.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). By contributing you agree your code is licensed
under GPLv3 and your documentation under CC BY-SA 4.0.
