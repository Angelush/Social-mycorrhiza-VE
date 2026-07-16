"""The six adversarial archetypes (brief §2). Each maps to a C2C invariant / failure mode and emits
only shapes the real modules actually accept — the point is to show the module's own wall firing
(a Rejected / dropped_ / damped_ count), never to assume a mechanism the code lacks.
"""
from __future__ import annotations

from random import Random

from engine.policy import RulePolicy
from engine.types import Proposal
from .config import C2CView
from .proposals import (
    CastDisposition, Declare, EmitTrace, Interact, MatchRequest, Pledge, RecordVouch,
)


class Surveillor(RulePolicy):
    """Bad (F1, surveillance-creep): tries a FORBIDDEN-shaped payload AND steers the matcher model
    toward a reputation scalar. The membrane raises; the matcher drops the shaped proposal."""

    def __init__(self, token: str):
        self._t = token
        self._seq = 0
        self._declared = False

    def act(self, view: C2CView, rng: Random) -> Proposal | None:
        if not self._declared:
            self._declared = True
            return Declare(token=self._t, offers=("bread",), surfaceable=True, ttl=200)
        self._seq += 1
        if self._seq % 2 == 1:
            # a surveillance shape in a payload -> membrane raises (rejected)
            return Interact(mode=view.cell_mode, cell_id=view.cell_id,
                            interaction_id=f"{self._t}-s{self._seq}",
                            participants=(self._t,),
                            payload={"note": "dossier", "reputation_score": 0.2})
        # steer the matcher's model toward a reputation scalar -> dropped_surveillance_shape
        return MatchRequest(asker=self._t, cell_id=view.cell_id, poison="surveillance")


class SybilVoucher(RulePolicy):
    """Bad (F8): fabricates throwaway tokens vouching in a ring and pads an assurance head-count.
    One person, many sock-puppet tokens — assurance dedupes by participant_token, so the padding
    that repeats a token collapses to one voice (the wall we observe)."""

    def __init__(self, token: str, campaign_id: str, ring: int = 4):
        self._t = token
        self._camp = campaign_id
        self._ring = ring
        self._seq = 0

    def act(self, view: C2CView, rng: Random) -> Proposal | None:
        self._seq += 1
        if self._seq % 2 == 1:
            i = self._seq % self._ring
            j = (self._seq + 1) % self._ring
            return RecordVouch(frm=f"{self._t}~sock{i}", to=f"{self._t}~sock{j}", ttl=150)
        # pad the campaign, but repeat the SAME sock token -> dedup collapses it (invariant 7)
        return Pledge(campaign_id=self._camp, participant_token=f"{self._t}~sock0", kind="binario")


class EngagementBaiter(RulePolicy):
    """Bad (F7 / invariant 8): steers the injected matcher model to emit an engagement signal.
    The matcher makes engagement UNREPRESENTABLE — the shaped proposal is dropped, never surfaced."""

    def __init__(self, token: str):
        self._t = token
        self._declared = False

    def act(self, view: C2CView, rng: Random) -> Proposal | None:
        if not self._declared:
            self._declared = True
            return Declare(token=self._t, needs=("bread",), surfaceable=True, ttl=200)
        return MatchRequest(asker=self._t, cell_id=view.cell_id, poison="engagement")


class MobInstigator(RulePolicy):
    """Bad (invariant 9, anti-cascade): a burst of `flag` traces on one artifact within a window.
    The stigmergy velocity cap throttles the stampede (damped_velocity), so a mob cannot manufacture
    a cascade — the traces carry context so this exercises the velocity breaker, not the no-context
    damper."""

    def __init__(self, token: str, target_artifact: str = "artifact-cell-gift"):
        self._t = token
        self._target = target_artifact

    def act(self, view: C2CView, rng: Random) -> Proposal | None:
        return EmitTrace(about=self._target, signal="bandera", strength=1.0,
                         context="pile-on")


class RoomLeaker(RulePolicy):
    """Bad (invariant 1, kula/gimwali wall): pushes a market instrument into a non-market room.
    The membrane raises MembraneBreachError -> the world records a Rejected: the wall fires."""

    def __init__(self, token: str):
        self._t = token
        self._seq = 0

    def act(self, view: C2CView, rng: Random) -> Proposal | None:
        self._seq += 1
        # always claim the gift room: a priced payload in communal_gift mode is the leak the
        # membrane must refuse, whichever cell the leaker itself lives in
        return Interact(mode="don_comunal", cell_id=view.cell_id,
                        interaction_id=f"{self._t}-leak{self._seq}",
                        participants=(self._t,),
                        payload={"item": "favour", "price_cents": 999})


class BadFaithBlocker(RulePolicy):
    """Bad (Capa-6, consent capture / tyranny of the minority — FLAGGED, not solved): casts a
    paramount objection with a bad-faith reason to block a circle's proposal. The system surfaces the
    reason (not the objector); that one reasoned block is decisive is by design — this archetype
    exists to make the residual risk visible, per the brief."""

    def __init__(self, token: str, circle_id: str, proposal_id: str):
        self._t = token
        self._circle = circle_id
        self._prop = proposal_id
        self._cast = False

    def act(self, view: C2CView, rng: Random) -> Proposal | None:
        if self._cast:
            return None
        self._cast = True
        return CastDisposition(circle_id=self._circle, proposal_id=self._prop, token=self._t,
                               disposition="objetar", paramount=True,
                               reason="I object on principle (bad-faith block)", ttl=200)
