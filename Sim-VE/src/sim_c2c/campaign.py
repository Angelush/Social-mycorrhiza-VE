"""Runnable Sim-C2C campaign: wires engine.campaign over the full real C2C stack.

Cooperative + adversarial population across a don_comunal cell and a precio_de_mercado cell, driven by
the six real Capa modules through C2CAdapter. Byte-reproducible; cassette-free because the injected
matcher `propose` is a deterministic rule closure (no LLM inside the loop).
"""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from random import Random

from engine.campaign import Budget, CampaignResult, campaign
from engine.types import RangeBound, SearchSpace

from .adapter import C2CAdapter
from .config import RoundConfig
from .policies_core import (
    Convener, Lurker, Matchmaker, Newcomer, Reciprocator, Sensor,
)
from .policies_adversarial import (
    BadFaithBlocker, EngagementBaiter, MobInstigator, RoomLeaker, Surveillor, SybilVoucher,
)
from .researcher import C2CResearcher
from .track_a import C2CTrackA
from .track_a_ve import C2CTrackAComposite
from .track_b import C2CTrackB
from .world import C2CWorld

GIFT_CELL, MARKET_CELL = "cell-gift", "cell-market"
CIRCLE, PROP, CAMP = "circle-1", "prop-1", "camp-1"

_DEFAULT_MIX = {
    "reciprocator": 0.35, "newcomer": 0.1, "lurker": 0.1, "surveillor": 0.08,
    "sybil_voucher": 0.07, "engagement_baiter": 0.08, "mob_instigator": 0.08,
    "room_leaker": 0.07, "bad_faith_blocker": 0.07,
}


def _make_actor(archetype: str, token: str):
    if archetype == "newcomer":
        return Newcomer(token)
    if archetype == "lurker":
        return Lurker(token)
    if archetype == "surveillor":
        return Surveillor(token)
    if archetype == "sybil_voucher":
        return SybilVoucher(token, CAMP)
    if archetype == "engagement_baiter":
        return EngagementBaiter(token)
    if archetype == "mob_instigator":
        return MobInstigator(token, target_artifact=f"artifact-{GIFT_CELL}")
    if archetype == "room_leaker":
        return RoomLeaker(token)
    if archetype == "bad_faith_blocker":
        return BadFaithBlocker(token, CIRCLE, PROP)
    return Reciprocator(token)


def _build_actors(cfg: RoundConfig, rng: Random):
    mix = dict(cfg.actor_mix) or dict(_DEFAULT_MIX)
    names = list(mix)
    weights = list(mix.values())
    total = sum(weights) or 1.0
    cumulative, running = [], 0.0
    for w in weights:
        running += w
        cumulative.append(running)

    def pick() -> str:
        r = rng.random() * total
        for name, c in zip(names, cumulative):
            if r <= c:
                return name
        return names[-1]

    # adversary_intensity biases the roster toward adversaries by re-rolling a cooperative pick.
    actors, cell_of = {}, {}
    askers = []
    for i in range(cfg.n_actors):
        token = f"t{i:02d}"
        arch = pick()
        if arch == "reciprocator" and rng.random() < cfg.adversary_intensity:
            arch = pick()
        actors[token] = _make_actor(arch, token)
        cell_of[token] = GIFT_CELL
        askers.append(token)

    # one cooperative anchor in the market cell (exercises a market_price room legitimately)
    actors["m0"] = Reciprocator("m0")
    cell_of["m0"] = MARKET_CELL

    actors["__matchmaker__"] = Matchmaker(askers=tuple(sorted(askers)), cell_id=GIFT_CELL)
    actors["__sensor__"] = Sensor(cell_id=GIFT_CELL, cfg=cfg)
    actors["__convener__"] = Convener(CIRCLE, PROP, CAMP, GIFT_CELL, threshold=2)
    return actors, cell_of


def default_config(seed: int = 7, n_actors: int = 12, T: int = 30) -> RoundConfig:
    return RoundConfig(
        actor_mix=dict(_DEFAULT_MIX), n_actors=n_actors, T=T,
        cells={GIFT_CELL: "don_comunal", MARKET_CELL: "precio_de_mercado"},
        adversary_intensity=0.3, window=5, velocity_cap=3, half_life=4,
        min_strength=0.1, seed=seed,
    )


def build_campaign(
    cfg: RoundConfig,
    c2c_root: str | Path,
    max_rounds: int = 5,
    search_space: SearchSpace | None = None,
) -> CampaignResult:
    adapter = C2CAdapter(c2c_root)
    mode_of = dict(cfg.cells)

    def build_world(round_cfg: Mapping[str, object], rng: Random) -> C2CWorld:
        merged = RoundConfig(**round_cfg)
        actors, cell_of = _build_actors(merged, rng)
        return C2CWorld(adapter, actors, merged, cell_of, mode_of, rng)

    def ticks_for(round_cfg: Mapping[str, object]) -> int:
        return int(round_cfg["T"])

    if search_space is None:
        # DESCRIPTIVE-ONLY: the only knob is the adversary intensity — no Track-B-derived objective.
        search_space = SearchSpace(bounds={"adversary_intensity": RangeBound(0.0, 1.0)})
    C2CResearcher.assert_descriptive_only(search_space)

    return campaign(
        initial_cfg=dict(vars(cfg)),
        search_space=search_space,
        budget=Budget(max_rounds=max_rounds),
        seed=cfg.seed,
        sut_adapter=adapter,
        researcher=C2CResearcher(),
        build_world=build_world,
        ticks_for=ticks_for,
        track_a=C2CTrackAComposite(C2CTrackA()),  # TS.2: VE oracle also halts
        track_b=C2CTrackB(),
    )
