from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntegratedConfig:
    T: int
    adversary_intensity: float
    seed: int
