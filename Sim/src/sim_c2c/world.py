"""C2CWorld — owns ALL accumulation (the six SUT modules are pure/stateless) and runs the two
clocks coherently. Each tick, every actor observes an asker-relative view, proposes, and the world
either accumulates into its graph/declarations/traces/pledges/dispositions or builds the exact
module envelope from accumulated state and forwards it to the real adapter.

The world NEVER re-implements adjudication: a module-call proposal's verdict is whatever the real
module returns (or a Rejected wrapping the real module's own raise). The world's only power is which
accumulated slice it hands in — and it hands in the WHOLE relevant set (all vouches/facts/etc.),
letting the real module do its own cell-scoping and expiry-forgetting, exactly as in production.
"""
from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from random import Random

from engine.types import Proposal
from engine.world import World

from .adapter import C2CAdapter
from .config import C2CView
from .proposals import (
    CastDisposition, DecideProposal, Declare, EmitTrace, Interact,
    LegibilityQuery, MatchRequest, Pledge, RecordFact, RecordVouch,
    ResolveCampaign, SenseRequest,
)


@dataclasses.dataclass(frozen=True)
class Rejected:
    reason: str


@dataclasses.dataclass(frozen=True)
class ModuleCall:
    # Carries BOTH the exact request the world built (from accumulated state) and the real module's
    # output, so Track A/B can independently verify input->output without trusting a single side --
    # the C2C analogue of B2B's ClearingOutcome(proposal, applied_event).
    method: str
    request: dict
    output: object  # module output dict, or Rejected


@dataclasses.dataclass(frozen=True)
class Accumulated:
    kind: str
    record: dict


def _iso(tick: int) -> str:
    # A synthetic but strictly monotone, fixed-width ISO-surrogate: the five string-clock modules
    # only ever compare timestamps lexicographically, so zero-padding gives correct ordering while
    # advancing in lockstep with the integer stigmergy clock (world.tick).
    return "T%08d" % tick


class C2CWorld(World):
    def __init__(
        self,
        sut_adapter: "C2CAdapter",
        actors: Mapping[str, "Policy"],
        cfg: "RoundConfig",
        cell_of: Mapping[str, str],
        mode_of: Mapping[str, str],
        rng: "Random",
    ) -> None:
        super().__init__(sut_adapter, actors, env=None, rng=rng)
        self.cfg = cfg
        self.cell_of = dict(cell_of)
        self.mode_of = dict(mode_of)

        # Accumulated state (all caller-supplied-then-discarded from the modules' POV).
        self.vouches: list[dict] = []
        self.facts: list[dict] = []
        self.declarations: dict[str, dict] = {}
        self.traces: list[dict] = []
        self.pledges: dict[str, list[dict]] = {}
        self.dispositions: dict[tuple[str, str], list[dict]] = {}
        self._pledge_seq = 0

        self._members_by_cell: dict[str, list[str]] = {}
        for tok, cell in self.cell_of.items():
            self._members_by_cell.setdefault(cell, []).append(tok)
        for cell in self._members_by_cell:
            self._members_by_cell[cell].sort()

    # --- views -------------------------------------------------------------------------------
    def observe(self, actor_id: str) -> object:
        cell = self.cell_of.get(actor_id, "cell-gift")
        return C2CView(
            token=actor_id,
            cell_id=cell,
            cell_mode=self.mode_of.get(cell, "communal_gift"),
            tick=self.tick,
            iso_now=_iso(self.tick),
            cell_members=tuple(m for m in self._members_by_cell.get(cell, ()) if m != actor_id),
            is_harness_role=actor_id.startswith("__"),
        )

    # --- injected deterministic proposer for the matcher -------------------------------------
    def _make_propose(self, self_decl: dict, poison: str | None):
        def propose(context):
            needs = set(self_decl.get("needs", ()))
            goals = set(self_decl.get("goals", ()))
            out = []
            for cand in context["candidates"]:
                if set(cand.get("offers", ())) & needs:
                    out.append({"token": cand["token"], "kind": "offer_meets_need",
                                "reason": "a declared offer meets your declared need"})
                elif set(cand.get("goals", ())) & goals:
                    out.append({"token": cand["token"], "kind": "shared_goal",
                                "reason": "a shared declared goal"})
            if poison == "engagement":
                # Simulate a prompt-injected / engagement-optimizing model: attach a click signal.
                # The matcher must DROP the whole proposal (dropped_surveillance_shape), never strip.
                bait = {"token": (out[0]["token"] if out else "__bait__"),
                        "kind": "offer_meets_need", "reason": "you'll love this",
                        "click_through_rate": 0.9}
                out = [bait] + out
            elif poison == "surveillance":
                bait = {"token": (out[0]["token"] if out else "__bait__"),
                        "kind": "offer_meets_need", "reason": "trusted",
                        "reputation": 0.95}
                out = [bait] + out
            return out
        return propose

    # --- adjudication ------------------------------------------------------------------------
    def adjudicate(self, actor_id: str, proposal: "Proposal") -> object:
        a = self.sut_adapter
        breaches = (
            a.MembraneBreachError, a.LegibilityBreachError, a.MatcherBreachError,
            a.StigmergyBreachError, a.GovernanceBreachError, ValueError,
        )
        # AssuranceInvariantError is NOT in `breaches` (it is not a ValueError, by design): an
        # internal no-loss/conservation abort must propagate, never be softened into a Rejected.

        # ---- accumulation proposals ----
        if isinstance(proposal, RecordVouch):
            rec = {"from": proposal.frm, "to": proposal.to,
                   "cell_id": self.cell_of.get(actor_id, "cell-gift"),
                   "expires_at": _iso(self.tick + proposal.ttl)}
            self.vouches.append(rec)
            return Accumulated("vouch", rec)
        if isinstance(proposal, RecordFact):
            rec = {"about": proposal.about, "statement": proposal.statement,
                   "cell_id": self.cell_of.get(actor_id, "cell-gift"),
                   "expires_at": _iso(self.tick + proposal.ttl)}
            self.facts.append(rec)
            return Accumulated("fact", rec)
        if isinstance(proposal, Declare):
            rec = {"token": proposal.token, "cell_id": self.cell_of.get(actor_id, "cell-gift"),
                   "offers": list(proposal.offers), "needs": list(proposal.needs),
                   "goals": list(proposal.goals),
                   "consent": {"surfaceable": bool(proposal.surfaceable)},
                   "expires_at": _iso(self.tick + proposal.ttl)}
            self.declarations[proposal.token] = rec
            return Accumulated("declaration", rec)
        if isinstance(proposal, EmitTrace):
            rec = {"about": proposal.about, "signal": proposal.signal,
                   "strength": proposal.strength, "created_at": self.tick,
                   "cell_id": self.cell_of.get(actor_id, "cell-gift"),
                   "context": proposal.context}
            self.traces.append(rec)
            return Accumulated("trace", rec)
        if isinstance(proposal, Pledge):
            self._pledge_seq += 1
            rec = {"pledge_id": f"pl-{self._pledge_seq}",
                   "participant_token": proposal.participant_token}
            if proposal.kind == "monetary":
                rec["amount_cents"] = proposal.amount_cents
            self.pledges.setdefault(proposal.campaign_id, []).append(rec)
            return Accumulated("pledge", rec)
        if isinstance(proposal, CastDisposition):
            rec = {"token": proposal.token, "disposition": proposal.disposition,
                   "circle_id": proposal.circle_id,
                   "expires_at": _iso(self.tick + proposal.ttl)}
            if proposal.disposition == "object":
                rec["objection"] = {"paramount": bool(proposal.paramount),
                                    "reason": proposal.reason or "unspecified"}
            self.dispositions.setdefault((proposal.circle_id, proposal.proposal_id), []).append(rec)
            return Accumulated("disposition", rec)

        # ---- module-call proposals ----
        if isinstance(proposal, Interact):
            request = {
                "mode": proposal.mode, "cell_id": proposal.cell_id,
                "interaction_id": proposal.interaction_id,
                "participants": list(proposal.participants),
                "payload": dict(proposal.payload),
            }
            if proposal.ttl is not None:
                request["expires_at"] = _iso(self.tick + proposal.ttl)
            return self._call("admit", request, lambda: a.admit(request), breaches)

        if isinstance(proposal, LegibilityQuery):
            request = {
                "asker": proposal.asker, "target": proposal.target,
                "cell_id": proposal.cell_id, "now": _iso(self.tick),
                "max_hops": proposal.max_hops,
                "graph": {"vouches": [dict(v) for v in self.vouches],
                          "facts": [dict(f) for f in self.facts]},
            }
            return self._call("query", request, lambda: a.query(request), breaches)

        if isinstance(proposal, MatchRequest):
            self_decl = self.declarations.get(proposal.asker, {})
            candidates = [
                {k: c[k] for k in ("token", "cell_id", "offers", "needs", "goals",
                                   "consent", "expires_at") if k in c}
                for tok, c in sorted(self.declarations.items())
                if tok != proposal.asker
            ]
            request = {
                "asker": proposal.asker, "cell_ids": [proposal.cell_id],
                "now": _iso(self.tick), "expires_at": _iso(self.tick + proposal.ttl),
                "max_proposals": proposal.max_proposals,
                "self": {k: self_decl.get(k, []) for k in ("offers", "needs", "goals")},
                "candidates": candidates,
            }
            propose = self._make_propose(request["self"], proposal.poison)
            return self._call("match", request, lambda: a.match(request, propose), breaches)

        if isinstance(proposal, SenseRequest):
            request = {
                "cell_id": proposal.cell_id, "now": self.tick,
                "window": proposal.window, "velocity_cap": proposal.velocity_cap,
                "half_life": proposal.half_life, "min_strength": proposal.min_strength,
                "traces": [dict(t) for t in self.traces],
            }
            return self._call("sense", request, lambda: a.sense(request), breaches)

        if isinstance(proposal, ResolveCampaign):
            request = {
                "campaign_id": proposal.campaign_id, "cell_id": proposal.cell_id,
                "kind": proposal.kind, "threshold": proposal.threshold,
                "expires_at": _iso(self.tick + proposal.ttl),
                "pledges": [dict(p) for p in self.pledges.get(proposal.campaign_id, ())],
            }
            if proposal.sponsor_bonus_cents:
                request["sponsor_bonus_cents"] = proposal.sponsor_bonus_cents
            return self._call("resolve", request, lambda: a.resolve(request), breaches)

        if isinstance(proposal, DecideProposal):
            request = {
                "circle_id": proposal.circle_id, "proposal_id": proposal.proposal_id,
                "now": _iso(self.tick), "expires_at": _iso(self.tick + proposal.ttl),
                "dispositions": [dict(d) for d in
                                 self.dispositions.get((proposal.circle_id, proposal.proposal_id), ())],
            }
            return self._call("decide", request, lambda: a.decide(request), breaches)

        raise TypeError(f"unhandled proposal type: {type(proposal).__name__}")

    def _call(self, method: str, request: dict, thunk, breaches) -> ModuleCall:
        try:
            output = thunk()
        except breaches as exc:
            output = Rejected(reason=f"{type(exc).__name__}: {exc}")
        return ModuleCall(method=method, request=request, output=output)

    def apply(self, actor_id: str, proposal: "Proposal", result: object) -> None:
        # Accumulation already happened in adjudicate (state is the source of truth); module calls
        # persist nothing. Nothing to do here — mirrors B2BWorld.apply.
        pass
