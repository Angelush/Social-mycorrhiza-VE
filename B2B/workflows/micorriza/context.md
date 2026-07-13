# Context — information environment

> Produced by build-context. Data room before the work (Axiom 5).

## Domain
B2B mutual-credit / multilateral-clearing network ("micorriza económica"). Proven analogues: **WIR** (CH, 90y), **Sardex** (IT), **RES** (BE). Members are SMEs in a dense sectoral/geographic cluster (a "cell"); they trade on internal credit denominated in EUR. Multilateral clearing nets out circular debt; mutual credit lines smooth liquidity from strong nodes to weak ones.

## Terminology (stable)
- **Cell (célula):** a legally-incorporated cooperative, 50–500 firms, permissioned membership. The unit of governance and credit firewall.
- **Obligation:** a directed debt edge `debtor → creditor` for an amount (EUR-denominated), with a cell tag.
- **Clearing / netting:** finding directed cycles and cancelling the minimum amount around each, reducing gross outstanding debt without changing anyone's net position.
- **Net position:** for member m, `sum(incoming) − sum(outgoing)`. **Invariant: unchanged by clearing.**
- **Credit line:** per-member bounds, ~−1% turnover (negative cap) / ~+10% (positive cap), calibrable per cell. Positive cap is mandatory (anti-hoarding / redistribution; invariant 4).
- **Solver:** the deterministic Layer-1 component. Min-cost-flow with cycle cancellation.
- **Matcher:** the stochastic Layer-2 LLM component (later). Proposes trades; never commits.

## Anchor data (do not over-promise)
- Real Sardex data: net internal debt reduced ≈25% by clearing alone, ≈50% combined with mutual credit (§3 Capa 1).
- Clearing benefit is **unequal** (power-law network structure → best-connected nodes net more) → always combine with mutual credit.

## Hard constraints from environment (stable)
- **MiCA:** Spanish transitional window closes **2026-06-30**. Strategy: EUR-denominated mutual credit, **no token** → sidesteps most of MiCA. (§5)
- **RGPD Art. 22:** automated credit *denial* needs a human. (Invariant 9)
- Revenue model: **subscription fees**, not per-transaction commissions (commissions penalize circulation; §8).

## Tools / stack (proposed, stable for this iteration)
- Language: **Python 3.11+** for the solver (clear, testable, exact arithmetic via `decimal`/integer cents). No floats for money.
- Graph: adjacency via dicts / `networkx` optional but prefer a self-contained implementation for auditability.
- Tests: `pytest`. Property-based via `hypothesis` for conservation invariants.
- No external services, no LLM, no chain in this component.

## Examples of good/bad
- **Good:** solver returns settlement instructions whose application leaves every member's net position bit-identical to before, with gross debt strictly reduced, plus an audit trace.
- **Bad:** solver "optimizes" by approximating, loses a cent to rounding, or changes a net position. Inadmissible (invariant 1).

## Honesty flags (heuristics, §9)
- "Micorriza" / wood-wide-web science is **disputed** (Karst et al. 2023). Use as design heuristic only, never as proof. The honest analogue for distributed matching is *Physarum* (Tero et al. 2010).
