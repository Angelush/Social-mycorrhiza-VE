from __future__ import annotations

import abc
from collections.abc import Mapping
from dataclasses import dataclass


class Proposal(abc.ABC):
    pass


@dataclass(frozen=True)
class TraceEvent:
    tick: int
    actor_id: str
    proposal: Proposal | None
    result: object


class Bound(abc.ABC):
    @abc.abstractmethod
    def contains(self, value: object) -> bool:
        pass


@dataclass(frozen=True)
class RangeBound(Bound):
    lo: float
    hi: float

    def contains(self, value: object) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool) and self.lo <= value <= self.hi


@dataclass(frozen=True)
class SetBound(Bound):
    values: frozenset

    def contains(self, value: object) -> bool:
        return value in self.values


@dataclass(frozen=True)
class SearchSpace:
    bounds: Mapping[str, Bound]

    def contains_diff(self, fields: Mapping[str, object]) -> bool:
        # Strict allow-list ensures that any field not declared in search space is rejected.
        for key, val in fields.items():
            bound = self.bounds.get(key)
            if bound is None or not bound.contains(val):
                return False
        return True


@dataclass(frozen=True)
class WorldDiff:
    fields: Mapping[str, object]
