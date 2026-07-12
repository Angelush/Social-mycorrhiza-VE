# Contributing to Micorriza

Thanks for your interest. This project values a few things strongly — please read before
opening a PR.

## Ground rules (non-negotiable design invariants)

1. **The agent proposes, the gate disposes.** Anything that moves real value must remain
   deterministic and human-gated. Do not automate the irreversible one-way door.
2. **Invariants halt, they don't average.** A violated invariant is a headline (a stopped
   run + an exploit trace), never a data point folded into a pass rate.
3. **The simulation drives the real code.** `Sim/` must never become a second copy of the
   mechanism. Test against the real systems under test, not mocks.
4. **Anti-surveillance first (social branch).** Do not add legibility/scoring features ahead
   of the parts that make scoring impossible to weaponize.

If a change tensions one of these, open an issue to discuss *before* writing code.

## Workflow

1. Fork and branch from `master` (`feature/short-name` or `fix/short-name`).
2. Set up the environment:
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install pytest hypothesis networkx
   ```
3. Make your change. Keep it scoped and match the surrounding style.
4. Run the relevant test suite(s) — all must stay green:
   ```bash
   (cd B2B && ../.venv/bin/python -m pytest tests -q)
   (cd C2C && ../.venv/bin/python -m pytest tests -q)
   (cd Sim && ../.venv/bin/python -m pytest tests -q)
   ```
5. Add tests for new behavior (acceptance / property / golden-set as appropriate).
6. Open a PR describing *what* changed and *which invariants you checked it against*.

## Commit messages

Short imperative subject; body explains the "why." Reference the relevant brief section or
spec AC where it helps (e.g. `brief §10 step 1`, `AC-L3`).

## Reporting issues

For bugs, include a minimal reproduction and which sub-project (`B2B` / `C2C` / `Sim`).
For a suspected invariant violation, include the exploit trace — that's the most valuable
kind of report here.

## Licensing of contributions

By submitting a contribution you agree it is licensed under this project's terms:
**GPLv3** for code and **CC BY-SA 4.0** for documentation (see [`LICENSE.md`](LICENSE.md)).
