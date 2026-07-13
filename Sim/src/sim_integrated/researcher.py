from __future__ import annotations

from collections.abc import Sequence

from engine.researcher import Researcher, RoundRecord
from engine.types import SearchSpace, WorldDiff

from .track_b import IntegratedTrackB


class IntegratedResearcher(Researcher):
    """Monotonic adversary_intensity nudge. The one-way door stays shut across BOTH worlds: this
    researcher only ever emits a diff on the declared adversary knob, never a patch to either SUT, and
    (descriptive-only) its search space must name no Track-B welfare metric."""

    def __init__(self, step: float = 0.1) -> None:
        self._step = step

    @staticmethod
    def assert_descriptive_only(search_space: SearchSpace) -> None:
        offending = {k for k in search_space.bounds if k in IntegratedTrackB.GOODHART_FLAGS}
        if offending:
            raise ValueError(
                f"descriptive-only violation: search space names Track-B metric(s) {sorted(offending)}")

    def next(self, history: Sequence[RoundRecord], search_space: SearchSpace):
        self.assert_descriptive_only(search_space)
        if not history:
            return ("initial round: no history yet", WorldDiff(fields={}))
        bound = search_space.bounds.get("adversary_intensity")
        if bound is None:
            return ("no adversary_intensity knob declared", WorldDiff(fields={}))
        last = history[-1].config.get("adversary_intensity", 0.0)
        proposed = last + self._step
        if not bound.contains(proposed):
            return (f"round {len(history)}: holding adversary_intensity at {last}",
                    WorldDiff(fields={}))
        return (f"round {len(history)}: nudging adversary_intensity to {proposed:.3f}",
                WorldDiff(fields={"adversary_intensity": proposed}))
