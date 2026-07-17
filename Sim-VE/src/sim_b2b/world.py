from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from random import Random

from engine.types import Proposal
from engine.world import World

from .adapter import B2BAdapter
from .config import CellView, FirmState
from .proposals import (
    NeedDescription,
    PauseCell,
    PuentePausar,
    PuenteReanudar,
    RegisterMember,
    RequestClearing,
    ResumeCell,
    SanctionStep,
    Settle,
    StatementProbe,
    Trade,
)


@dataclasses.dataclass(frozen=True)
class Rejected:
    reason: str


@dataclasses.dataclass(frozen=True)
class ScopedStatements:
    # TS.2: the REAL member_statement's outputs under the three scopes, recorded verbatim
    # (or a Rejected wrapping the real raise). `cruce_ajeno` is the `miembro`-scope attempt
    # with a FOREIGN solicitante — the D3 contract says the real ledger must reject it.
    member_id: str
    publico: object
    miembro: object
    cruce_ajeno: object


@dataclasses.dataclass(frozen=True)
class ClearingOutcome:
    # Always carries the raw run_clearing() proposal (with its credit_flags) even when
    # settlements is empty or apply_clearing wasn't called, so Track A can independently
    # cross-check credit_flags without that information being lost once apply_clearing's
    # own event is the only thing recorded.
    proposal: dict
    applied_event: dict | None


class B2BWorld(World):
    def __init__(
        self,
        sut_adapter: "B2BAdapter",
        actors: Mapping[str, "Policy"],
        cfg: "RoundConfig",
        neighbors: Mapping[str, tuple[str, ...]],
        rng: "Random",
    ) -> None:
        super().__init__(sut_adapter, actors, env=None, rng=rng)
        self.cfg = cfg
        self.neighbors = neighbors

    def ts(self) -> int:
        return self.tick // self.cfg.ticks_per_second

    def observe(self, actor_id: str) -> object:
        if actor_id in {
            "__clearing_scheduler__",
            "__compliance_officer__",
            "__circuit_breaker__",
            "__auditor__",
        }:
            return CellView(
                member_ids=tuple(self.neighbors),
                statements={
                    fid: self.sut_adapter.member_statement(fid, "comite_credito")
                    for fid in self.neighbors
                },
                metrics=self.sut_adapter.cell_metrics(),
                tick=self.tick,
            )
        return FirmState(
            # a firm observes ITSELF: scope "miembro" with solicitante=itself (D3, faithful)
            **self.sut_adapter.member_statement(actor_id, "miembro", solicitante=actor_id),
            neighbor_ids=self.neighbors.get(actor_id, ()),
        )

    def adjudicate(self, actor_id: str, proposal: "Proposal") -> object:
        if isinstance(proposal, Trade):
            def call():
                return self.sut_adapter.record_obligation(
                    {
                        "id": proposal.obligation_id,
                        "debtor": proposal.debtor,
                        "creditor": proposal.creditor,
                        "amount_cents": proposal.cents,
                    },
                    ts=self.ts(),
                )
        elif isinstance(proposal, Settle):
            def call():
                return self.sut_adapter.settle_obligation(
                    proposal.obligation_id, proposal.cents, ts=self.ts()
                )
        elif isinstance(proposal, RequestClearing):
            def call():
                clearing_proposal = self.sut_adapter.run_clearing()
                if clearing_proposal["settlements"]:
                    applied_event = self.sut_adapter.apply_clearing(
                        clearing_proposal, ratified_by="harness-scheduler", ts=self.ts()
                    )
                    return ClearingOutcome(proposal=clearing_proposal, applied_event=applied_event)
                return ClearingOutcome(proposal=clearing_proposal, applied_event=None)
        elif isinstance(proposal, SanctionStep):
            def call():
                return self.sut_adapter.update_member(
                    proposal.member_id,
                    dict(proposal.changes),
                    ratified_by="harness-compliance",
                    ts=self.ts(),
                )
        elif isinstance(proposal, PauseCell):
            def call():
                return self.sut_adapter.pause_cell(ratified_by="harness-breaker", ts=self.ts())
        elif isinstance(proposal, ResumeCell):
            def call():
                return self.sut_adapter.resume_cell(ratified_by="harness-breaker", ts=self.ts())
        elif isinstance(proposal, RegisterMember):
            def call():
                # RegisterMember forwards the proposal's own ratified_by rather than a
                # harness-fixed string: the real add_member accepts any non-empty string
                # with no real gate behind it, and this archetype exists to demonstrate
                # that the code does not stop a self-declared registration — routing a
                # harness string here would quietly hide that finding.
                return self.sut_adapter.add_member(
                    {
                        "id": proposal.candidate_id,
                        "turnover_cents": proposal.turnover_cents,
                    },
                    ratified_by=proposal.ratified_by,
                    ts=self.ts(),
                )
        elif isinstance(proposal, StatementProbe):
            # NOT wrapped in `call()`: each scope's outcome is recorded separately, verbatim.
            def probe(scope, solicitante=None):
                try:
                    return self.sut_adapter.member_statement(
                        proposal.member_id, scope, solicitante=solicitante)
                except ValueError as exc:
                    return Rejected(reason=str(exc))
            return ScopedStatements(
                member_id=proposal.member_id,
                publico=probe("publico"),
                miembro=probe("miembro", solicitante=proposal.member_id),
                cruce_ajeno=probe("miembro", solicitante=proposal.foreign_id),
            )
        elif isinstance(proposal, PuentePausar):
            def call():
                return self.sut_adapter.puente_pausar(ratified_by="harness-comite", ts=self.ts())
        elif isinstance(proposal, PuenteReanudar):
            def call():
                return self.sut_adapter.puente_reanudar(ratified_by="harness-comite", ts=self.ts())
        elif isinstance(proposal, NeedDescription):
            return None
        else:
            raise TypeError(f"unhandled proposal type: {type(proposal).__name__}")

        try:
            return call()
        except ValueError as exc:
            return Rejected(reason=str(exc))

    def apply(self, actor_id: str, proposal: "Proposal", result: object) -> None:
        # Intentionally empty: every view in this domain is rebuilt fresh from the
        # adapter's own read-only accessors each tick, so there is no local env here to
        # update — the adapter/real-ledger state is the source of truth for what
        # happened, not this method.
        pass
