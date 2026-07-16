from __future__ import annotations

from random import Random
from collections.abc import Callable

from engine.policy import Cassette, LLMPolicy, RulePolicy
from engine.types import Proposal
from .config import FirmState
from .proposals import NeedDescription, RegisterMember, Settle, Trade


class Defrauder(RulePolicy):
    def __init__(self, member_id: str, bite_size_cents: int = 100_000):
        self._member_id = member_id
        self._bite_size = bite_size_cents
        self._seq = 0
        self._pending: tuple[str, int] | None = None
        self._done = False

    def act(self, view: FirmState, rng: Random) -> Proposal | None:
        # Once headroom is exhausted this goes quiet permanently and stays quiet: there is no exit
        # op in the real ledger, so the negative balance left behind simply persists uncorrected.
        if self._done:
            return None
        if self._pending is not None:
            obligation_id, amount = self._pending
            self._pending = None
            return Settle(obligation_id=obligation_id, cents=amount)
        headroom = view.balance_cents - view.credit_min_cents
        if headroom <= 0 or not view.neighbor_ids:
            self._done = True
            return None
        neighbor = rng.choice(view.neighbor_ids)
        amount = min(self._bite_size, headroom)
        obligation_id = f"{self._member_id}-fraud{self._seq}"
        self._seq += 1
        self._pending = (obligation_id, amount)
        return Trade(obligation_id=obligation_id, debtor=self._member_id, creditor=neighbor, cents=amount)


class SybilHopper(RulePolicy):
    def __init__(self, member_id: str, max_attempts: int = 5, fake_turnover_cents: int = 1_000_000_000):
        self._member_id = member_id
        self._max_attempts = max_attempts
        self._fake_turnover = fake_turnover_cents
        self._attempts = 0

    def act(self, view: FirmState, rng: Random) -> Proposal | None:
        if self._attempts >= self._max_attempts:
            return None
        candidate_id = f"sybil-{self._member_id}-{self._attempts}"
        self._attempts += 1
        # ratified_by accepts any non-empty string with no real gate behind it in add_member;
        # the finding is that this works at all, not that the string is convincing.
        return RegisterMember(
            candidate_id=candidate_id,
            turnover_cents=self._fake_turnover,
            ratified_by=f"self-ratified-by-{self._member_id}",
        )


class VelocityAttacker(RulePolicy):
    def __init__(self, member_id: str, burst_cents: int, target_neighbor: str):
        self._member_id = member_id
        self._burst = burst_cents
        self._target = target_neighbor
        self._seq = 0

    def act(self, view: FirmState, rng: Random) -> Proposal | None:
        # Fixed target concentrates the whole burst on one creditor so the velocity-cap breach is
        # unambiguous, rather than diffusing it across many small trades to different neighbours.
        obligation_id = f"{self._member_id}-burst{self._seq}"
        self._seq += 1
        return Trade(obligation_id=obligation_id, debtor=self._member_id, creditor=self._target, cents=self._burst)


class CellLeaker(RulePolicy):
    def __init__(self, member_id: str, foreign_id: str = "foreign-cell-member"):
        self._member_id = member_id
        self._foreign_id = foreign_id
        self._seq = 0

    def act(self, view: FirmState, rng: Random) -> Proposal | None:
        obligation_id = f"{self._member_id}-leak{self._seq}"
        self._seq += 1
        return Trade(obligation_id=obligation_id, debtor=self._member_id, creditor=self._foreign_id, cents=10_000)


class _NeedProbe(LLMPolicy):
    def build_prompt(self, view: FirmState) -> str:
        return (
            f"firm {view.member_id} balance {view.balance_cents} neighbors "
            f"{len(view.neighbor_ids)}: describe a plausible trade need in one sentence."
        )

    def parse_response(self, response: object, view: FirmState) -> NeedDescription:
        return NeedDescription(member_id=view.member_id, text=str(response))


class LLMProbeWrapper(RulePolicy):
    def __init__(
        self,
        inner: RulePolicy,
        member_id: str,
        enabled: bool = False,
        call_model: Callable[[str], object] | None = None,
        cassette: Cassette | None = None,
        reproducible: bool = True,
    ) -> None:
        self._inner = inner
        self._enabled = enabled
        self.last_description: NeedDescription | None = None
        if enabled:
            self._probe = _NeedProbe(
                persona=f"firm:{member_id}",
                model_id="need-probe-v1",
                call_model=call_model,
                cassette=cassette,
                reproducible=reproducible,
            )
        else:
            self._probe = None

    def act(self, view: FirmState, rng: Random) -> Proposal | None:
        if self._enabled and self._probe is not None:
            # Generated to prove the LLM-probe machinery is genuinely wired and cassette-backed
            # end to end, then deliberately discarded: no B2B module parses free text.
            self.last_description = self._probe.act(view, rng)
        return self._inner.act(view, rng)
