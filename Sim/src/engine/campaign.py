from __future__ import annotations

from dataclasses import dataclass
from random import Random
from collections.abc import Callable, Mapping, Sequence

from .types import SearchSpace
from .sut_adapter import SUTAdapter
from .world import World
from .measurement import TrackA, TrackB, IntegrityReport
from .researcher import Researcher, RoundRecord, apply_within_gate
from .journal import Journal, canonical_hash


class Budget:
    def __init__(self, max_rounds: int) -> None:
        self.max_rounds = max_rounds
        self.rounds_spent = 0

    def remaining(self) -> bool:
        return self.rounds_spent < self.max_rounds

    def spend(self) -> None:
        self.rounds_spent += 1


@dataclass(frozen=True)
class CampaignResult:
    journal: Journal
    history: tuple[RoundRecord, ...]
    halted: bool
    halting_report: IntegrityReport | None


# CampaignResult.history intentionally exposes the raw per-round configs and reports
# rather than a computed Pareto frontier: which welfare axes trade off against which
# is domain-specific knowledge this engine-level function does not have.
def campaign(
    *,
    initial_cfg: Mapping[str, object],
    search_space: SearchSpace,
    budget: Budget,
    seed: int,
    sut_adapter: SUTAdapter,
    researcher: Researcher,
    build_world: Callable[[Mapping[str, object], Random], World],
    ticks_for: Callable[[Mapping[str, object]], int],
    track_a: TrackA,
    track_b: TrackB,
    converged: Callable[[Sequence[RoundRecord]], bool] | None = None,
) -> CampaignResult:
    sut_adapter.assert_pinned()
    journal = Journal()
    history: list[RoundRecord] = []
    cfg: Mapping[str, object] = dict(initial_cfg)
    round_number = 0

    while budget.remaining() and not (converged is not None and converged(history)):
        sut_adapter.assert_pinned()
        # Deterministic per-round seed via plain integer arithmetic, never Python's built-in hash()
        # on strings/tuples-of-strings: str/bytes hashing is randomized per process (PYTHONHASHSEED)
        # by default, which would silently break cross-process byte-reproducibility.
        round_seed = seed * 1_000_003 + round_number
        rng = Random(round_seed)
        world = build_world(cfg, rng)
        ticks = ticks_for(cfg)
        for _ in range(ticks):
            world.step()

        integrity_report = track_a.measure(world.trace)
        welfare_report = track_b.measure(world.trace)
        config_hash = canonical_hash(cfg)

        if integrity_report.violation:
            journal.append(round_number, config_hash, integrity_report, welfare_report, None, None)
            return CampaignResult(journal=journal, history=tuple(history), halted=True, halting_report=integrity_report)

        record = RoundRecord(config=dict(cfg), integrity_report=integrity_report, welfare_report=welfare_report)
        hypothesis, diff = researcher.next(tuple(history) + (record,), search_space)
        journal.append(round_number, config_hash, integrity_report, welfare_report, hypothesis, diff)
        history.append(record)
        budget.spend()
        cfg = dict(apply_within_gate(cfg, diff, search_space))
        round_number += 1

    return CampaignResult(journal=journal, history=tuple(history), halted=False, halting_report=None)
