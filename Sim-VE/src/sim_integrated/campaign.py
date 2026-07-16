"""Runnable Sim-Integrated campaign: both real SUTs, one population, over engine.campaign.

The clean campaign runs cooperative bridged actors + a Bridge-exploiter restricted to the two
SUT-enforced walls (debt_to_gift, cross_cell) — both rejected by the real code — so it produces ZERO
integrity violations and is byte-reproducible, proving the value/social and cell/cell firewalls hold
across the real stack. The F-VS2 finding (which leaks against real B2B) is exercised separately.
"""
from __future__ import annotations

from collections.abc import Mapping
from random import Random

from engine.campaign import Budget, CampaignResult, campaign
from engine.types import RangeBound, SearchSpace

from sim_b2b.adapter import B2BAdapter
from sim_c2c.adapter import C2CAdapter
from .config import IntegratedConfig
from .identity import Identity
from .policies import BridgeExploiter, CooperativeBridge
from .researcher import IntegratedResearcher
from .track_a import IntegratedTrackA
from .track_b import IntegratedTrackB
from .world import IntegratedWorld

CELL_A, CELL_B, ROOM = "cell-A", "cell-B", "room-gift"
CELL_PARAMS = {"moneda": "USD", "sal_seudonimo": "sim-ve-sal",
               "neg_line_bp": 1000, "pos_line_bp": 1000,
               "velocity_window_s": 3600, "velocity_max_cents": 10_000_000}
ROSTERS = {CELL_A: ("X", "c0", "c1"), CELL_B: ("d0", "d1")}

_IDENTITIES = {
    "X": Identity("X", "business", b2b_cell=CELL_A, c2c_cell=ROOM),
    "c0": Identity("c0", "business", b2b_cell=CELL_A, c2c_cell=ROOM),
    "c1": Identity("c1", "business", b2b_cell=CELL_A, c2c_cell=None),
    "d0": Identity("d0", "person", b2b_cell=CELL_B, c2c_cell=ROOM),
    "d1": Identity("d1", "person", b2b_cell=CELL_B, c2c_cell=None),
}


def default_config(seed: int = 5, T: int = 24) -> IntegratedConfig:
    return IntegratedConfig(T=T, adversary_intensity=0.3, seed=seed)


def _setup_b2b(root, cell, members):
    a = B2BAdapter(root)
    a.create_cell(cell, dict(CELL_PARAMS), ratified_by="ops", ts=0)
    for m in members:
        a.add_member({"id": m, "turnover_cents": 10_000_000}, ratified_by="ops", ts=0)
    return a


def _build_actors(rng: Random):
    return {
        "X": BridgeExploiter(_IDENTITIES["X"], modes=frozenset({"debt_to_gift", "cross_cell"}),
                             from_cell=CELL_A, to_cell=CELL_B, foreign_debtor="c0",
                             local_creditor="d0"),
        "c0": CooperativeBridge(_IDENTITIES["c0"], "c1"),
        "c1": CooperativeBridge(_IDENTITIES["c1"], "c0"),
        "d0": CooperativeBridge(_IDENTITIES["d0"], "d1"),
        "d1": CooperativeBridge(_IDENTITIES["d1"], "d0"),
    }


def build_campaign(cfg: IntegratedConfig, b2b_root, c2c_root,
                   max_rounds: int = 4, search_space: SearchSpace | None = None) -> CampaignResult:
    pin_adapter = C2CAdapter(c2c_root)  # a stable handle for the engine's pin assertion

    def build_world(round_cfg: Mapping[str, object], rng: Random) -> IntegratedWorld:
        b2b = {CELL_A: _setup_b2b(b2b_root, CELL_A, ROSTERS[CELL_A]),
               CELL_B: _setup_b2b(b2b_root, CELL_B, ROSTERS[CELL_B])}
        return IntegratedWorld(b2b, C2CAdapter(c2c_root), _build_actors(rng), _IDENTITIES,
                               b2b_rosters=ROSTERS, c2c_modes={ROOM: "don_comunal"}, rng=rng)

    def ticks_for(round_cfg: Mapping[str, object]) -> int:
        return int(round_cfg["T"])

    if search_space is None:
        search_space = SearchSpace(bounds={"adversary_intensity": RangeBound(0.0, 1.0)})
    IntegratedResearcher.assert_descriptive_only(search_space)

    return campaign(
        initial_cfg=dict(vars(cfg)),
        search_space=search_space,
        budget=Budget(max_rounds=max_rounds),
        seed=cfg.seed,
        sut_adapter=pin_adapter,
        researcher=IntegratedResearcher(),
        build_world=build_world,
        ticks_for=ticks_for,
        track_a=IntegratedTrackA(),
        track_b=IntegratedTrackB(),
    )
