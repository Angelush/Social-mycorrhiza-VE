from __future__ import annotations
from dataclasses import dataclass
from collections.abc import Mapping

@dataclass(frozen=True)
class RoundConfig:
    actor_mix: Mapping[str, float]
    n_firms: int
    T: int
    clearing_cadence: int
    base_turnover_cents: int
    neg_line_bp: int
    pos_line_bp: int
    topology_params: Mapping[str, object]
    adversary_intensity: float
    velocity_window_s: int
    ticks_per_second: int
    velocity_max_cents: int
    credit_crunch: bool
    seed: int

@dataclass(frozen=True)
class FirmState:
    member_id: str
    status: str
    balance_cents: int
    credit_min_cents: int
    credit_max_cents: int
    owed_by_cents: int
    owed_to_cents: int
    projected_cents: int
    neighbor_ids: tuple[str, ...]

@dataclass(frozen=True)
class CellView:
    member_ids: tuple[str, ...]
    statements: Mapping[str, Mapping[str, object]]
    metrics: Mapping[str, object]
    tick: int
