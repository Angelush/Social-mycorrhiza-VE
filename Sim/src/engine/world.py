from __future__ import annotations

from collections.abc import Mapping
from random import Random

from .policy import Policy
from .sut_adapter import SUTAdapter
from .types import Proposal, TraceEvent


class World:

    def __init__(
        self, sut_adapter: SUTAdapter, actors: Mapping[str, Policy], env: object, rng: Random
    ) -> None:
        self.sut_adapter = sut_adapter
        self.actors = actors
        self.env = env
        self.rng = rng
        self.tick: int = 0
        self.trace: list[TraceEvent] = []

    def observe(self, actor_id: str) -> object:
        raise NotImplementedError

    def adjudicate(self, actor_id: str, proposal: Proposal) -> object:
        raise NotImplementedError

    def apply(self, actor_id: str, proposal: Proposal, result: object) -> None:
        raise NotImplementedError

    def step(self) -> None:
        for actor_id in sorted(self.actors):
            policy = self.actors[actor_id]
            view = self.observe(actor_id)
            proposal = policy.act(view, self.rng)
            if proposal is None:
                continue
            # Let exceptions propagate because exception-to-rejection mapping is domain knowledge handled by the subclass.
            result = self.adjudicate(actor_id, proposal)
            self.apply(actor_id, proposal, result)
            self.trace.append(
                TraceEvent(
                    tick=self.tick, actor_id=actor_id, proposal=proposal, result=result
                )
            )
        self.tick += 1
