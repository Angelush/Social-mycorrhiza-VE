from __future__ import annotations

import abc
import dataclasses
from collections.abc import Mapping, Sequence

from .measurement import IntegrityReport, WelfareReport
from .types import SearchSpace, WorldDiff


class GateViolation(Exception):
    pass


@dataclasses.dataclass(frozen=True)
class RoundRecord:
    config: Mapping[str, object]
    integrity_report: IntegrityReport
    welfare_report: WelfareReport


class Researcher(abc.ABC):
    @abc.abstractmethod
    def next(
        self, history: Sequence[RoundRecord], search_space: SearchSpace
    ) -> tuple[str | None, WorldDiff]: ...


def apply_within_gate(
    cfg: Mapping[str, object], diff: WorldDiff, search_space: SearchSpace
) -> Mapping[str, object]:
    # All-or-nothing: raise before merging anything so a bad diff is never partly applied with only its bad keys silently dropped -- a partial merge could slip an undeclared, SUT-shaped field past the one-way door that confines the researcher to declared world knobs.
    if not search_space.contains_diff(diff.fields):
        offending = sorted(
            key
            for key, value in diff.fields.items()
            if key not in search_space.bounds
            or not search_space.bounds[key].contains(value)
        )
        raise GateViolation(
            "diff rejected by gate; offending key(s): "
            + ", ".join(repr(key) for key in offending)
        )
    return {**cfg, **diff.fields}
