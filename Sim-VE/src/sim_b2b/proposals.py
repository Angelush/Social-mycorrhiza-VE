from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
from engine.types import Proposal


@dataclass(frozen=True)
class Trade(Proposal):
    obligation_id: str
    debtor: str
    creditor: str
    cents: int


@dataclass(frozen=True)
class Settle(Proposal):
    obligation_id: str
    cents: int


@dataclass(frozen=True)
class RequestClearing(Proposal):
    pass


@dataclass(frozen=True)
class SanctionStep(Proposal):
    # Restricted by convention to the harness-level compliance-officer role.
    member_id: str
    changes: Mapping[str, object]


@dataclass(frozen=True)
class PauseCell(Proposal):
    pass


@dataclass(frozen=True)
class ResumeCell(Proposal):
    pass


@dataclass(frozen=True)
class RegisterMember(Proposal):
    # Added to resolve spec gaps, allowing the Sybil-hopper archetype to implement this action.
    candidate_id: str
    turnover_cents: int
    ratified_by: str


@dataclass(frozen=True)
class NeedDescription(Proposal):
    member_id: str
    text: str


# ---- TS.2: VE observability proposals (harness auditor role) ----
@dataclass(frozen=True)
class StatementProbe(Proposal):
    """Ask the world to call the REAL member_statement under the three scopes and record
    the outputs verbatim (ScopedStatements) — material for the visibilidad_saldos oracle."""
    member_id: str
    foreign_id: str      # a DIFFERENT member: the cross `miembro` attempt that must be rejected


@dataclass(frozen=True)
class PuentePausar(Proposal):
    # -> puente_pausar (D8): a gated VE op, material for puerta_humana_ops_nuevas
    pass


@dataclass(frozen=True)
class PuenteReanudar(Proposal):
    # -> puente_reanudar (D8)
    pass
