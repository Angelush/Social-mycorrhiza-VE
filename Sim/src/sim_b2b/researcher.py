from __future__ import annotations

from collections.abc import Sequence

from engine.researcher import Researcher, RoundRecord
from engine.types import SearchSpace, WorldDiff


class B2BResearcher(Researcher):
    # Default strategy, deliberately simple (a monotonic nudge, not a real bandit/evolutionary
    # search): each round, push adversary_intensity up by a fixed step within whatever bound
    # search_space declares, searching toward the phase boundary the brief calls out as the
    # interesting region. history only ever contains non-violating rounds (campaign() halts
    # before appending a violating one), so there's no "back off" signal available from
    # history alone; a more sophisticated strategy is future work, not required by this build.
    def __init__(self, step: float = 0.1) -> None:
        self._step = step

    def next(
        self, history: Sequence[RoundRecord], search_space: SearchSpace
    ) -> tuple[str | None, WorldDiff]:
        if not history:
            return ("initial round: no history yet", WorldDiff(fields={}))

        bound = search_space.bounds.get("adversary_intensity")
        if bound is None:
            return ("no adversary_intensity knob declared in search space", WorldDiff(fields={}))

        last_intensity = history[-1].config.get("adversary_intensity", 0.0)
        proposed = last_intensity + self._step
        if not bound.contains(proposed):
            return (
                f"round {len(history)}: adversary_intensity at the edge of the declared "
                f"search space, holding at {last_intensity}",
                WorldDiff(fields={}),
            )
        return (
            f"round {len(history)}: nudging adversary_intensity to {proposed:.3f}",
            WorldDiff(fields={"adversary_intensity": proposed}),
        )
