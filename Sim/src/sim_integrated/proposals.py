"""Integrated proposals: baseline per-world activity + the three seam-crossing bridges.

Baseline proposals drive the real B2B ledger and real C2C membrane so the firewalls have genuine
value and genuine rooms to guard. The three bridge proposals are the whole reason this sim exists —
each attempts to move value or a score across the value/social or cell/cell seam.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Mapping

from engine.types import Proposal


# ---- baseline per-world activity -------------------------------------------------------------
@dataclass(frozen=True)
class B2BTrade(Proposal):
    cell: str
    obligation_id: str
    debtor: str
    creditor: str
    cents: int


@dataclass(frozen=True)
class C2CGift(Proposal):
    cell_id: str
    interaction_id: str
    participants: tuple[str, ...]
    payload: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class AdjustCredit(Proposal):
    # A LEGITIMATE credit change: provenance is turnover/human_ratified, never a social scalar.
    cell: str
    member_id: str
    new_credit_max_cents: int
    provenance: str = "human_ratified"


# ---- the three seam-crossing bridges (adversarial) -------------------------------------------
@dataclass(frozen=True)
class LeakDebtToGiftRoom(Proposal):
    # F-VS1: lift a live B2B obligation's amount and try to admit it into a C2C gift room.
    b2b_cell: str
    obligation_id: str
    c2c_cell_id: str
    interaction_id: str


@dataclass(frozen=True)
class ScoreToCredit(Proposal):
    # F-VS2: run a C2C legibility query and derive a B2B credit bound from the social answer.
    c2c_asker: str
    c2c_target: str
    c2c_cell_id: str
    b2b_cell: str
    b2b_member: str
    max_hops: int = 3


@dataclass(frozen=True)
class CrossCellValueMove(Proposal):
    # F-CC: record an obligation in cell B whose debtor is a member of cell A only.
    from_cell: str
    to_cell: str
    obligation_id: str
    foreign_debtor: str      # a member of from_cell, NOT of to_cell
    local_creditor: str      # a member of to_cell
    cents: int
