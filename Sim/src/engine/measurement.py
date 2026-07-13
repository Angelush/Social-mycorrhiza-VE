from __future__ import annotations

import abc
import dataclasses
import enum
from collections.abc import Mapping, Sequence

from .types import TraceEvent


class Verdict(enum.Enum):
    PASS = enum.auto()
    FAIL = enum.auto()


@dataclasses.dataclass(frozen=True)
class InvariantResult:
    verdict: Verdict
    exploit_trace: object | None = None


@dataclasses.dataclass(frozen=True)
class IntegrityReport:
    results: Mapping[str, InvariantResult]

    @property
    def violation(self) -> bool:
        return any(result.verdict is Verdict.FAIL for result in self.results.values())

    @property
    def failed_invariants(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                name
                for name, result in self.results.items()
                if result.verdict is Verdict.FAIL
            )
        )


@dataclasses.dataclass(frozen=True)
class Distribution:
    summary: Mapping[str, float]
    samples: tuple[float, ...] = ()

    def __post_init__(self) -> None:
        for key, value in self.summary.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError(
                    f"Distribution.summary[{key!r}] must be a non-bool int or float, "
                    f"got {type(value).__name__}"
                )
        for index, element in enumerate(self.samples):
            if not isinstance(element, (int, float)) or isinstance(element, bool):
                raise TypeError(
                    f"Distribution.samples[{index}] must be a non-bool int or float, "
                    f"got {type(element).__name__}"
                )


@dataclasses.dataclass(frozen=True)
class WelfareReport:
    metrics: Mapping[str, "Distribution | float | int"]

    def __post_init__(self) -> None:
        for key, value in self.metrics.items():
            # Python does NOT enforce dataclass field type hints at runtime: the closed
            # "Distribution | float | int" value type declared above is advisory only, seen
            # by static type-checkers and ignored by the interpreter. This runtime isinstance
            # check is therefore the thing that actually makes the "no per-identity slot"
            # guarantee real rather than aspirational -- without it, a mapping keyed by an
            # individual's identity could still be assigned as a value here despite the hint.
            if not (isinstance(value, (Distribution, int, float)) and not isinstance(value, bool)):
                raise TypeError(
                    f"WelfareReport.metrics[{key!r}] must be a Distribution or a non-bool "
                    f"int/float, got {type(value).__name__}"
                )


def assert_no_person_scalar(
    report: WelfareReport, forbidden_substrings: frozenset[str]
) -> None:
    # Necessary-but-insufficient defense-in-depth: an innocuously-named per-individual scalar would still pass this name scan, so it matters only because WelfareReport.__post_init__ already makes that per-identity shape structurally impossible.
    lowered = tuple(fragment.lower() for fragment in forbidden_substrings)
    for key in report.metrics:
        key_lower = key.lower()
        for fragment in lowered:
            if fragment in key_lower:
                raise ValueError(
                    f"metrics key {key!r} contains forbidden substring {fragment!r}"
                )


class TrackA(abc.ABC):
    @abc.abstractmethod
    def measure(self, trace: Sequence["TraceEvent"]) -> IntegrityReport: ...


class TrackB(abc.ABC):
    @abc.abstractmethod
    def measure(self, trace: Sequence["TraceEvent"]) -> WelfareReport: ...
