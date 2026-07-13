"""IntegratedWorld — both SUTs, one population, one step loop.

Holds TWO B2BAdapter instances (cell-A, cell-B: independent ledger states) and ONE C2CAdapter, and
steps all three per tick over the shared `Identity` population. Both B2B integer clocks and the C2C
string clock derive from `world.tick`, so the whole system advances coherently. The world never
re-implements adjudication: a proposal's verdict is whatever the real module returns (or a Rejected
wrapping its own raise). Every seam-crossing is recorded as a BridgeAttempt(kind, request, output,
provenance) — both sides of the crossing — so Track A re-derives each firewall independently.
"""
from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from random import Random

from engine.world import World
from engine.types import Proposal, TraceEvent

from .proposals import (
    AdjustCredit, B2BTrade, C2CGift, CrossCellValueMove, LeakDebtToGiftRoom, ScoreToCredit,
)


@dataclasses.dataclass(frozen=True)
class Rejected:
    reason: str


@dataclasses.dataclass(frozen=True)
class WorldEvent:
    kind: str          # "member_added" | "obligation_recorded" | "gift_admitted"
    cell: str
    event: dict


@dataclasses.dataclass(frozen=True)
class BridgeAttempt:
    kind: str          # "debt_to_gift" | "score_to_credit" | "cross_cell"
    request: dict
    output: object     # module output dict, or Rejected
    provenance: str    # "b2b_obligation" | "c2c_person_scalar" | "cross_cell_default"


def _iso(tick: int) -> str:
    return "T%08d" % tick


@dataclasses.dataclass(frozen=True)
class IntegratedView:
    identity: object
    tick: int
    iso_now: str
    b2b_members: Mapping[str, tuple[str, ...]]
    c2c_members: Mapping[str, tuple[str, ...]]
    own_open_obligations: tuple[tuple[str, str, int], ...]  # (cell, obligation_id, amount)


class IntegratedWorld(World):
    def __init__(
        self,
        b2b_adapters: Mapping[str, object],
        c2c_adapter: object,
        actors: Mapping[str, object],
        identities: Mapping[str, "Identity"],
        b2b_rosters: Mapping[str, tuple[str, ...]],
        c2c_modes: Mapping[str, str],
        rng: Random,
    ) -> None:
        # sut_adapter is set to the c2c adapter for the engine's pin assertion; both B2B adapters are
        # pinned explicitly by the campaign. (The engine only calls assert_pinned on one handle.)
        super().__init__(c2c_adapter, actors, env=None, rng=rng)
        self.b2b = dict(b2b_adapters)
        self.c2c = c2c_adapter
        self.identities = dict(identities)
        self.b2b_rosters = {c: tuple(r) for c, r in b2b_rosters.items()}
        self.c2c_modes = dict(c2c_modes)

        # accumulation the modules do not hold
        self.open_obligations: dict[str, dict[str, tuple[str, str, int]]] = {c: {} for c in self.b2b}
        self.vouches: list[dict] = []
        self.facts: list[dict] = []

        # seed the trace with the initial rosters so Track A can reconstruct membership independently
        for cell, roster in self.b2b_rosters.items():
            for mid in roster:
                self.trace.append(TraceEvent(
                    tick=-1, actor_id="__setup__", proposal=None,
                    result=WorldEvent("member_added", cell, {"member_id": mid}),
                ))

    def add_vouch(self, frm: str, to: str, cell_id: str) -> None:
        self.vouches.append({"from": frm, "to": to, "cell_id": cell_id, "expires_at": None})

    def observe(self, actor_id: str) -> object:
        ident = self.identities.get(actor_id)
        own = tuple(
            (cell, oid, amt)
            for cell, obs in self.open_obligations.items()
            for oid, (debtor, _cred, amt) in obs.items()
            if debtor == actor_id
        )
        c2c_members = {}
        for cell, mode in self.c2c_modes.items():
            c2c_members[cell] = tuple(sorted(
                i.c2c_token for i in self.identities.values() if i.c2c_cell == cell
            ))
        return IntegratedView(
            identity=ident, tick=self.tick, iso_now=_iso(self.tick),
            b2b_members=self.b2b_rosters, c2c_members=c2c_members, own_open_obligations=own,
        )

    def adjudicate(self, actor_id: str, proposal: "Proposal") -> object:
        ts = self.tick

        if isinstance(proposal, B2BTrade):
            adapter = self.b2b[proposal.cell]
            try:
                event = adapter.record_obligation(
                    {"id": proposal.obligation_id, "debtor": proposal.debtor,
                     "creditor": proposal.creditor, "amount_cents": proposal.cents}, ts=ts)
            except ValueError as exc:
                return Rejected(reason=f"ValueError: {exc}")
            self.open_obligations[proposal.cell][proposal.obligation_id] = (
                proposal.debtor, proposal.creditor, proposal.cents)
            return WorldEvent("obligation_recorded", proposal.cell, event)

        if isinstance(proposal, C2CGift):
            try:
                out = self.c2c.admit({
                    "mode": self.c2c_modes.get(proposal.cell_id, "communal_gift"),
                    "cell_id": proposal.cell_id, "interaction_id": proposal.interaction_id,
                    "participants": list(proposal.participants), "payload": dict(proposal.payload)})
            except self.c2c.MembraneBreachError as exc:
                return Rejected(reason=f"MembraneBreachError: {exc}")
            return WorldEvent("gift_admitted", proposal.cell_id, out)

        if isinstance(proposal, AdjustCredit):
            adapter = self.b2b[proposal.cell]
            request = {"member_id": proposal.member_id,
                       "changes": {"credit_max_cents": proposal.new_credit_max_cents}}
            try:
                event = adapter.update_member(
                    proposal.member_id, {"credit_max_cents": proposal.new_credit_max_cents},
                    ratified_by="ops", ts=ts)
                output = event
            except ValueError as exc:
                output = Rejected(reason=f"ValueError: {exc}")
            return BridgeAttempt("score_to_credit", request, output, provenance=proposal.provenance)

        # ---- the three bridges ----
        if isinstance(proposal, LeakDebtToGiftRoom):
            triple = self.open_obligations.get(proposal.b2b_cell, {}).get(proposal.obligation_id)
            amount = triple[2] if triple else 0
            # lift the denominated B2B amount into a gift-room payload (a *_cents market key)
            request = {"mode": "communal_gift", "cell_id": proposal.c2c_cell_id,
                       "interaction_id": proposal.interaction_id, "participants": [actor_id],
                       "payload": {"settlement_amount_cents": amount, "ref": proposal.obligation_id}}
            try:
                output = self.c2c.admit(dict(request))
            except self.c2c.MembraneBreachError as exc:
                output = Rejected(reason=f"MembraneBreachError: {exc}")
            return BridgeAttempt("debt_to_gift", request, output, provenance="b2b_obligation")

        if isinstance(proposal, ScoreToCredit):
            query_req = {"asker": proposal.c2c_asker, "target": proposal.c2c_target,
                         "cell_id": proposal.c2c_cell_id, "now": _iso(self.tick),
                         "max_hops": proposal.max_hops,
                         "graph": {"vouches": [dict(v) for v in self.vouches],
                                   "facts": [dict(f) for f in self.facts]}}
            answer = self.c2c.query(query_req)
            # derive a B2B credit bound from the SOCIAL answer — the forbidden move
            reachable = answer["from_your_position"]["reachable"]
            derived_max = 5_000_000 if reachable else 100_000
            request = {"member_id": proposal.b2b_member, "derived_from": query_req,
                       "changes": {"credit_max_cents": derived_max}}
            adapter = self.b2b[proposal.b2b_cell]
            try:
                output = adapter.update_member(
                    proposal.b2b_member, {"credit_max_cents": derived_max},
                    ratified_by="bridge", ts=ts)
            except ValueError as exc:
                output = Rejected(reason=f"ValueError: {exc}")
            return BridgeAttempt("score_to_credit", request, output, provenance="c2c_person_scalar")

        if isinstance(proposal, CrossCellValueMove):
            adapter = self.b2b[proposal.to_cell]
            request = {"to_cell": proposal.to_cell, "from_cell": proposal.from_cell,
                       "obligation_id": proposal.obligation_id,
                       "debtor": proposal.foreign_debtor, "creditor": proposal.local_creditor,
                       "amount_cents": proposal.cents}
            try:
                output = adapter.record_obligation(
                    {"id": proposal.obligation_id, "debtor": proposal.foreign_debtor,
                     "creditor": proposal.local_creditor, "amount_cents": proposal.cents}, ts=ts)
            except ValueError as exc:
                output = Rejected(reason=f"ValueError: {exc}")
            return BridgeAttempt("cross_cell", request, output, provenance="cross_cell_default")

        raise TypeError(f"unhandled proposal type: {type(proposal).__name__}")

    def apply(self, actor_id: str, proposal: "Proposal", result: object) -> None:
        pass
