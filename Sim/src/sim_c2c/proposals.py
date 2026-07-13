"""C2C proposal types — each maps to exactly one real-module input shape or one world-state
accumulation. The harness owns all accumulation (the six SUT modules are pure/stateless), so a
proposal is either:
  (a) an ACCUMULATION into C2CWorld's graph/declarations/traces/pledges/dispositions, or
  (b) a MODULE CALL whose envelope C2CWorld builds from accumulated state and forwards to the
      adapter (admit/query/match/resolve/sense/decide).

Every shape conforms EXACTLY to the module's closed whitelist (memory fact #3): an actor cannot
smuggle an extra metadata key through a proposal, because the world only ever writes the fields
named here into the envelope it hands the real module.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Mapping

from engine.types import Proposal


# ---- (a) accumulation proposals -------------------------------------------------------------
@dataclass(frozen=True)
class RecordVouch(Proposal):
    frm: str
    to: str
    ttl: int  # ticks until expiry; world stamps expires_at


@dataclass(frozen=True)
class RecordFact(Proposal):
    about: str
    statement: str
    ttl: int


@dataclass(frozen=True)
class Declare(Proposal):
    token: str
    offers: tuple[str, ...] = ()
    needs: tuple[str, ...] = ()
    goals: tuple[str, ...] = ()
    surfaceable: bool = True
    ttl: int = 100


@dataclass(frozen=True)
class EmitTrace(Proposal):
    about: str
    signal: str            # one of ALLOWED_SIGNALS
    strength: float
    context: str | None = None


@dataclass(frozen=True)
class Pledge(Proposal):
    campaign_id: str
    participant_token: str
    kind: str              # "binary" | "monetary"
    amount_cents: int = 0


@dataclass(frozen=True)
class CastDisposition(Proposal):
    circle_id: str
    proposal_id: str
    token: str
    disposition: str       # "consent" | "object" | "abstain"
    paramount: bool = False
    reason: str | None = None
    ttl: int = 100


# ---- (b) module-call proposals --------------------------------------------------------------
@dataclass(frozen=True)
class Interact(Proposal):
    # -> membrane.admit
    mode: str
    cell_id: str
    interaction_id: str
    participants: tuple[str, ...]
    payload: Mapping[str, object] = field(default_factory=dict)
    ttl: int | None = None


@dataclass(frozen=True)
class LegibilityQuery(Proposal):
    # -> legibility_query.query (reads the world vouch/fact graph)
    asker: str
    target: str
    cell_id: str
    max_hops: int = 3


@dataclass(frozen=True)
class MatchRequest(Proposal):
    # -> matcher.match (reads world declarations; world injects a deterministic `propose`)
    asker: str
    cell_id: str
    max_proposals: int = 5
    ttl: int = 50
    poison: str | None = None  # None | "engagement" | "surveillance" — steers the injected model


@dataclass(frozen=True)
class SenseRequest(Proposal):
    # -> stigmergy.sense (reads world traces; integer-tick clock)
    cell_id: str
    window: int = 5
    velocity_cap: int = 3
    half_life: int = 4
    min_strength: float = 0.1


@dataclass(frozen=True)
class ResolveCampaign(Proposal):
    # -> assurance_engine.resolve (reads world pledges)
    campaign_id: str
    cell_id: str
    kind: str
    threshold: int
    ttl: int = 100
    sponsor_bonus_cents: int = 0


@dataclass(frozen=True)
class DecideProposal(Proposal):
    # -> governance.decide (reads world dispositions)
    circle_id: str
    proposal_id: str
    ttl: int = 100
