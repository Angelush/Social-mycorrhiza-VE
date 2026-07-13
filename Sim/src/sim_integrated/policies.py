"""Integrated actors: a cooperative identity that lives honestly in both worlds, and the
Bridge-exploiter (brief §5, generalising the Sim-B2B Cell-leaker) whose only strategy is to smuggle
value or a score across a seam.
"""
from __future__ import annotations

from random import Random

from engine.policy import RulePolicy
from engine.types import Proposal
from .identity import Identity
from .proposals import (
    B2BTrade, C2CGift, CrossCellValueMove, LeakDebtToGiftRoom, ScoreToCredit,
)


class CooperativeBridge(RulePolicy):
    """Acts in both worlds without ever crossing the value/social seam: B2B trades and C2C gifts.
    (It never adjusts credit; the legitimate human_ratified AdjustCredit path is exercised by the
    F-VS2 oracle tests directly, so the clean campaign contains no credit ops at all.)"""

    def __init__(self, identity: Identity, b2b_partner: str | None):
        self._id = identity
        self._partner = b2b_partner
        self._seq = 0

    def act(self, view, rng: Random) -> Proposal | None:
        self._seq += 1
        r = rng.random()
        if self._id.in_b2b and self._partner and r < 0.4:
            return B2BTrade(cell=self._id.b2b_cell, obligation_id=f"{self._id.actor_id}-o{self._seq}",
                            debtor=self._id.actor_id, creditor=self._partner, cents=40_000)
        if self._id.in_c2c and r < 0.7:
            return C2CGift(cell_id=self._id.c2c_cell,
                           interaction_id=f"{self._id.actor_id}-g{self._seq}",
                           participants=(self._id.actor_id,), payload={"gift": "help"})
        return None


class BridgeExploiter(RulePolicy):
    """Smuggles across a seam. `modes` selects which bridges it attempts — the clean campaign runs it
    with the SUT-enforced walls only (debt_to_gift, cross_cell, both rejected by the real code); the
    score_to_credit finding is exercised in its own test because it leaks against the REAL B2B."""

    def __init__(self, identity: Identity, *, modes: frozenset[str],
                 c2c_target: str = "victim", from_cell: str | None = None,
                 to_cell: str | None = None, foreign_debtor: str | None = None,
                 local_creditor: str | None = None):
        self._id = identity
        self._modes = frozenset(modes)
        self._target = c2c_target
        self._from = from_cell
        self._to = to_cell
        self._foreign = foreign_debtor
        self._local = local_creditor
        self._seq = 0
        self._leaked = False

    def act(self, view, rng: Random) -> Proposal | None:
        self._seq += 1
        # 1. First open a real B2B obligation so there is genuine value to try to leak.
        if self._id.in_b2b and self._seq == 1 and "debt_to_gift" in self._modes:
            return B2BTrade(cell=self._id.b2b_cell, obligation_id=f"{self._id.actor_id}-debt",
                            debtor=self._id.actor_id, creditor=self._partner_in_cell(view),
                            cents=70_000)
        # 2. Attempt to leak that denominated debt into a C2C gift room.
        if "debt_to_gift" in self._modes and self._id.in_c2c and view.own_open_obligations:
            cell, oid, _amt = view.own_open_obligations[0]
            return LeakDebtToGiftRoom(b2b_cell=cell, obligation_id=oid,
                                      c2c_cell_id=self._id.c2c_cell,
                                      interaction_id=f"{self._id.actor_id}-leak{self._seq}")
        # 3. Attempt to move value across two B2B cells.
        if "cross_cell" in self._modes and self._seq % 3 == 0 and self._to and self._foreign:
            return CrossCellValueMove(from_cell=self._from, to_cell=self._to,
                                      obligation_id=f"{self._id.actor_id}-xc{self._seq}",
                                      foreign_debtor=self._foreign, local_creditor=self._local,
                                      cents=30_000)
        # 4. Attempt to feed a C2C person-scalar into a B2B credit decision.
        if "score_to_credit" in self._modes and self._id.in_b2b:
            return ScoreToCredit(c2c_asker=self._id.actor_id, c2c_target=self._target,
                                 c2c_cell_id=self._id.c2c_cell or "room-gift",
                                 b2b_cell=self._id.b2b_cell, b2b_member=self._id.actor_id)
        return None

    def _partner_in_cell(self, view) -> str:
        roster = [m for m in view.b2b_members.get(self._id.b2b_cell, ()) if m != self._id.actor_id]
        return roster[0] if roster else self._id.actor_id
