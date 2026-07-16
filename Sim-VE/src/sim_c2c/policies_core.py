"""Cooperative + neutral archetypes and harness driver roles.

Each actor_id IS its token. Actors never get a god-view: they learn reachability only by ASKING
(a LegibilityQuery), exactly as the real system intends. Every proposal shape conforms to the
module whitelist — an actor cannot smuggle an extra key, because the world writes only named fields.
"""
from __future__ import annotations

from random import Random

from engine.policy import RulePolicy
from engine.types import Proposal
from .config import C2CView
from .proposals import (
    DecideProposal, Declare, EmitTrace, Interact,
    LegibilityQuery, MatchRequest, RecordVouch, ResolveCampaign, SenseRequest,
)


def _payload_for(mode: str, tag: str) -> dict:
    if mode == "precio_de_mercado":
        return {"item": tag, "price_cents": 500}
    if mode == "igualdad":
        return {"item": tag, "in_kind": "an equal favour"}
    return {"gift": tag}  # don_comunal


class Reciprocator(RulePolicy):
    """Good: declares consentingly, vouches for cell peers, interacts in-mode (positive-sum)."""

    def __init__(self, token: str):
        self._t = token
        self._seq = 0
        self._declared = False

    def act(self, view: C2CView, rng: Random) -> Proposal | None:
        if not self._declared:
            self._declared = True
            return Declare(token=self._t, offers=("bread", "repair"), needs=("childcare",),
                           goals=("mutual-aid",), surfaceable=True, ttl=200)
        r = rng.random()
        if r < 0.3 and view.cell_members:
            return RecordVouch(frm=self._t, to=rng.choice(view.cell_members), ttl=150)
        if r < 0.6 and view.cell_members:
            self._seq += 1
            return Interact(mode=view.cell_mode, cell_id=view.cell_id,
                            interaction_id=f"{self._t}-i{self._seq}",
                            participants=(self._t, rng.choice(view.cell_members)),
                            payload=_payload_for(view.cell_mode, "loaf"))
        return None


class Newcomer(RulePolicy):
    """Neutral bootstrapping: declares a need, then queries from a position with no vouch-path."""

    def __init__(self, token: str):
        self._t = token
        self._declared = False

    def act(self, view: C2CView, rng: Random) -> Proposal | None:
        if not self._declared:
            self._declared = True
            return Declare(token=self._t, needs=("childcare", "bread"), surfaceable=True, ttl=200)
        if view.cell_members:
            # ask about a peer: from a newcomer's empty position this is usually 'no_info'
            return LegibilityQuery(asker=self._t, target=rng.choice(view.cell_members),
                                   cell_id=view.cell_id, max_hops=3)
        return None


class Lurker(RulePolicy):
    """Neutral: mostly quiet; occasionally leaves a low-strength environmental trace."""

    def __init__(self, token: str):
        self._t = token
        self._seq = 0

    def act(self, view: C2CView, rng: Random) -> Proposal | None:
        if rng.random() >= 0.2:
            return None
        self._seq += 1
        signal = "presencia" if rng.random() < 0.5 else "ruta"
        return EmitTrace(about=f"artifact-{view.cell_id}", signal=signal,
                         strength=0.4, context="passing through")


# ---- harness driver roles: keep the read-side module calls flowing so oracles have outputs ----
class Matchmaker(RulePolicy):
    """Harness role: periodically asks the matcher to surface matches for a rotating asker."""

    def __init__(self, askers: tuple[str, ...], cell_id: str, cadence: int = 3):
        self._askers = askers
        self._cell = cell_id
        self._cadence = cadence

    def act(self, view: C2CView, rng: Random) -> Proposal | None:
        if not self._askers or view.tick % self._cadence != 0:
            return None
        asker = self._askers[view.tick % len(self._askers)]
        return MatchRequest(asker=asker, cell_id=self._cell, max_proposals=5)


class Sensor(RulePolicy):
    """Harness role: periodically senses the environmental traces of a cell (anti-cascade throttle)."""

    def __init__(self, cell_id: str, cfg, cadence: int = 2):
        self._cell = cell_id
        self._cfg = cfg
        self._cadence = cadence

    def act(self, view: C2CView, rng: Random) -> Proposal | None:
        if view.tick % self._cadence != 0:
            return None
        return SenseRequest(cell_id=self._cell, window=self._cfg.window,
                            velocity_cap=self._cfg.velocity_cap, half_life=self._cfg.half_life,
                            min_strength=self._cfg.min_strength)


class Convener(RulePolicy):
    """Harness role: resolves one governance proposal and one assurance campaign on a cadence."""

    def __init__(self, circle_id: str, proposal_id: str, campaign_id: str, cell_id: str,
                 threshold: int = 2, cadence: int = 5):
        self._circle = circle_id
        self._prop = proposal_id
        self._camp = campaign_id
        self._cell = cell_id
        self._threshold = threshold
        self._cadence = cadence

    def act(self, view: C2CView, rng: Random) -> Proposal | None:
        if view.tick == 0 or view.tick % self._cadence != 0:
            return None
        if (view.tick // self._cadence) % 2 == 1:
            return DecideProposal(circle_id=self._circle, proposal_id=self._prop)
        return ResolveCampaign(campaign_id=self._camp, cell_id=self._cell,
                               kind="binario", threshold=self._threshold)
