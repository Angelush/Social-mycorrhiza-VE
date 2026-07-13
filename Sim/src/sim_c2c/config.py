from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping


@dataclass(frozen=True)
class RoundConfig:
    actor_mix: Mapping[str, float]
    n_actors: int
    T: int
    # cell topology: cell_id -> mode. A single default two-cell layout (a gift room + a market
    # room) is enough to exercise the kula/gimwali wall; more can be declared per round.
    cells: Mapping[str, str]
    adversary_intensity: float
    # stigmergy clock knobs (integer ticks)
    window: int
    velocity_cap: int
    half_life: int
    min_strength: float
    seed: int


@dataclass(frozen=True)
class C2CView:
    """What an actor sees each tick. Read-only snapshot; the world owns the real accumulation.

    Deliberately thin: an actor gets its own identity + cell context + both clocks + the roster of
    tokens it could plausibly reference. It does NOT get a god-view of the whole graph — that would
    be exactly the surveillance shape the system forbids; legibility is asker-relative and an actor
    learns reachability only by ASKING (a LegibilityQuery)."""
    token: str
    cell_id: str
    cell_mode: str
    tick: int
    iso_now: str
    cell_members: tuple[str, ...]      # tokens in the same cell (for choosing a counterparty)
    is_harness_role: bool = False
