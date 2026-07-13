"""The single seam that makes the integration possible (brief §5): ONE identity in both worlds.

A `business` is simultaneously a B2B firm and a C2C market-room org; a `person` is a C2C member who
may also be a sole-trader firm. The engine's actor identity is domain-agnostic precisely so one
identity can span both SUTs — this dataclass is that identity, carrying the per-world handles an actor
uses to act in each world. `actor_id` is the engine-level key; `b2b_firm_id` and `c2c_token` default
to it so a single string names the same party everywhere (which is exactly what a bridge exploits).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Identity:
    actor_id: str
    kind: str                       # "business" | "person"
    b2b_cell: str | None = None     # which B2B ledger this identity is a member of (None = C2C-only)
    c2c_cell: str | None = None     # which C2C room this identity acts in (None = B2B-only)

    @property
    def b2b_firm_id(self) -> str:
        return self.actor_id

    @property
    def c2c_token(self) -> str:
        return self.actor_id

    @property
    def in_b2b(self) -> bool:
        return self.b2b_cell is not None

    @property
    def in_c2c(self) -> bool:
        return self.c2c_cell is not None
