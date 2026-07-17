from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from random import Random

from engine.campaign import Budget, CampaignResult, campaign
from engine.types import RangeBound, SearchSpace, TraceEvent

from .adapter import B2BAdapter
from .config import RoundConfig
from .policies_adversarial import CellLeaker, Defrauder, SybilHopper, VelocityAttacker
from .policies_core import (Auditor, Circulator, CircuitBreaker, ClearingScheduler,
                            ComplianceOfficer, Hoarder, Wallflower)
from .researcher import B2BResearcher
from .topology import generate_trade_graph
from .track_a import B2BTrackA
from .track_a_ve import B2BTrackAComposite
from .track_b import B2BTrackB
from .world import B2BWorld


def _build_actors(
    actor_mix: Mapping[str, float],
    firm_ids: list[str],
    neighbors: Mapping[str, tuple[str, ...]],
    cfg: RoundConfig,
    rng: Random,
) -> dict[str, object]:
    names = list(actor_mix.keys())
    weights = list(actor_mix.values())
    total = sum(weights)
    cumulative = []
    running = 0.0
    for w in weights:
        running += w
        cumulative.append(running)

    def pick_archetype() -> str:
        if not names or total <= 0:
            return "circulator"
        r = rng.random() * total
        for name, c in zip(names, cumulative):
            if r <= c:
                return name
        return names[-1]

    actors: dict[str, object] = {}
    for fid in sorted(firm_ids):
        archetype = pick_archetype()
        if archetype == "hoarder":
            actors[fid] = Hoarder(fid)
        elif archetype == "wallflower":
            actors[fid] = Wallflower(fid)
        elif archetype == "defrauder":
            actors[fid] = Defrauder(fid)
        elif archetype == "sybil_hopper":
            actors[fid] = SybilHopper(fid)
        elif archetype == "velocity_attacker":
            own_neighbors = neighbors.get(fid, ())
            target = own_neighbors[0] if own_neighbors else fid
            burst = int(cfg.velocity_max_cents * (0.5 + cfg.adversary_intensity))
            actors[fid] = VelocityAttacker(fid, burst_cents=burst, target_neighbor=target)
        elif archetype == "cell_leaker":
            actors[fid] = CellLeaker(fid)
        else:  # "circulator" and any unrecognised name both fall back to the baseline archetype
            actors[fid] = Circulator(fid)

    typical_credit_min = -(cfg.base_turnover_cents * cfg.neg_line_bp) // 10000
    actors["__clearing_scheduler__"] = ClearingScheduler(cadence_ticks=cfg.clearing_cadence)
    actors["__compliance_officer__"] = ComplianceOfficer(warn_threshold_cents=int(typical_credit_min * 0.8))
    actors["__circuit_breaker__"] = CircuitBreaker(velocity_max_cents=cfg.velocity_max_cents)
    actors["__auditor__"] = Auditor(member_ids=tuple(neighbors))
    return actors


def params_de_celula(cfg: "RoundConfig") -> dict:
    """The create_cell params a campaign declares — single source (campaign AND tests).

    D1 biconditional: `expira_en_dias` only forwarded when declared. The REAL ledger enforces
    mandatory-iff-VES; the harness neither repairs nor completes a confused config (AC-s4.5).
    """
    return {
        "moneda": cfg.moneda,           # D1: mono-moneda por célula, sin default
        "sal_seudonimo": "sim-ve-sal",  # D3: sal obligatoria en toda célula
        **({"expira_en_dias": cfg.expira_en_dias} if cfg.expira_en_dias is not None else {}),
        "neg_line_bp": cfg.neg_line_bp,
        "pos_line_bp": cfg.pos_line_bp,
        "velocity_window_s": cfg.velocity_window_s,
        "velocity_max_cents": cfg.velocity_max_cents,
    }


def build_campaign(
    cfg: RoundConfig,
    b2b_root: str | Path,
    max_rounds: int = 10,
    search_space: SearchSpace | None = None,
) -> CampaignResult:
    adapter = B2BAdapter(b2b_root)
    cell_event = adapter.create_cell("cell-1", params_de_celula(cfg), ratified_by="ops", ts=0)
    neighbors = generate_trade_graph(cfg.n_firms, seed=cfg.seed)

    setup_events: list[TraceEvent] = [
        # TS.4: cell_created leads the trace — the fx oracle reads the cell's moneda from the
        # TRACE, so its proposal-moneda cross-check is armed inside campaigns (and AC-s4.3
        # judges the trace, not the config).
        TraceEvent(tick=-1, actor_id="__setup__", proposal=None, result=cell_event)
    ]
    known_bounds: dict[str, dict[str, int]] = {}
    for fid in neighbors:
        adapter.add_member(
            {"id": fid, "turnover_cents": cfg.base_turnover_cents}, ratified_by="ops", ts=0
        )
        stmt = adapter.member_statement(fid, "comite_credito")
        known_bounds[fid] = {
            "credit_min_cents": stmt["credit_min_cents"],
            "credit_max_cents": stmt["credit_max_cents"],
        }
        setup_events.append(
            TraceEvent(
                tick=-1,
                actor_id="__setup__",
                proposal=None,
                result={
                    "kind": "member_added",
                    "payload": {
                        "member": {
                            "id": fid,
                            "turnover_cents": cfg.base_turnover_cents,
                            "credit_min_cents": known_bounds[fid]["credit_min_cents"],
                            "credit_max_cents": known_bounds[fid]["credit_max_cents"],
                        },
                        "ratified_by": "ops",
                    },
                },
            )
        )

    def build_world(round_cfg: Mapping[str, object], rng: Random) -> B2BWorld:
        merged_cfg = RoundConfig(**round_cfg)
        actors = _build_actors(merged_cfg.actor_mix, list(neighbors), neighbors, merged_cfg, rng)
        world = B2BWorld(adapter, actors, merged_cfg, neighbors, rng)
        # Every round's trace must start with the initial roster's registration events, or
        # Track A/B have no way to know who the legitimate members are or what their credit
        # bounds are (see track_a.py's module docstring on this exact convention).
        world.trace.extend(setup_events)
        return world

    def ticks_for(round_cfg: Mapping[str, object]) -> int:
        return int(round_cfg["T"])

    # TS.2: composite = inherited oracles + the VE ones; a VE violation also halts.
    track_a = B2BTrackAComposite(B2BTrackA(
        velocity_window_s=cfg.velocity_window_s, velocity_max_cents=cfg.velocity_max_cents))
    track_b = B2BTrackB(known_bounds=known_bounds)
    researcher = B2BResearcher()
    budget = Budget(max_rounds=max_rounds)

    if search_space is None:
        search_space = SearchSpace(bounds={"adversary_intensity": RangeBound(0.0, 1.0)})

    initial_cfg = dict(vars(cfg))

    return campaign(
        initial_cfg=initial_cfg,
        search_space=search_space,
        budget=budget,
        seed=cfg.seed,
        sut_adapter=adapter,
        researcher=researcher,
        build_world=build_world,
        ticks_for=ticks_for,
        track_a=track_a,
        track_b=track_b,
    )
