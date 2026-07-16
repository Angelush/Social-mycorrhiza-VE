from __future__ import annotations

from collections.abc import Sequence

from engine.researcher import Researcher, RoundRecord
from engine.types import SearchSpace, WorldDiff

from .track_b import C2CTrackB


class C2CResearcher(Researcher):
    """Monotonic adversary_intensity nudge (deliberately simple; not a real bandit) — searches
    toward the phase boundary where the adversarial walls are most stressed.

    DESCRIPTIVE-ONLY SEAM (engine seam #3, implemented domain-side — the one stub the engine does
    NOT carry). This researcher's search space MUST contain no Track-B-derived objective, so the C2C
    "fertility" welfare can never become the thing the loop maximizes (brief §6.3: measuring it wrong
    is the anti-goal, not a smaller win). The guard is enforced two ways: (1) `next` reads ONLY
    integrity history and the adversary knob — it never inspects `welfare_report`; (2) `assert_
    descriptive_only` rejects any search space whose knobs collide with a C2CTrackB metric name.
    """

    def __init__(self, step: float = 0.1) -> None:
        self._step = step

    @staticmethod
    def assert_descriptive_only(search_space: SearchSpace) -> None:
        welfare_names = set(C2CTrackB.GOODHART_FLAGS)
        offending = {k for k in search_space.bounds if k in welfare_names}
        if offending:
            raise ValueError(
                "descriptive-only violation: the C2C researcher's search space must not contain a "
                f"Track-B-derived objective; offending knob(s): {sorted(offending)}"
            )

    def next(
        self, history: Sequence[RoundRecord], search_space: SearchSpace
    ) -> tuple[str | None, WorldDiff]:
        self.assert_descriptive_only(search_space)
        if not history:
            return ("initial round: no history yet", WorldDiff(fields={}))

        bound = search_space.bounds.get("adversary_intensity")
        if bound is None:
            return ("no adversary_intensity knob declared in search space", WorldDiff(fields={}))

        # Reads integrity/config history only — deliberately NOT welfare_report (descriptive-only).
        last = history[-1].config.get("adversary_intensity", 0.0)
        proposed = last + self._step
        if not bound.contains(proposed):
            return (
                f"round {len(history)}: adversary_intensity at the edge of the search space, "
                f"holding at {last}",
                WorldDiff(fields={}),
            )
        return (
            f"round {len(history)}: nudging adversary_intensity to {proposed:.3f}",
            WorldDiff(fields={"adversary_intensity": proposed}),
        )
