"""TS.4 — named descriptive VE campaign scenarios for the B2B side.

Populations buena / neutra / mala over USD and VES cells. Each scenario is a plain
RoundConfig factory: build with `sim_b2b.campaign.build_campaign(escenario_ve(name), root)`.
Track B stays DESCRIPTIVE (distributions; never the loop's objective — the search space
carries only the adversary knob) and Track A (composite, VE oracles included) is a hard stop.

The VES scenarios declare `expira_en_dias` because D1 makes it mandatory-iff-VES: a VES
balance without expiry is an inflationary liability the engine would be lying about. The
harness only DECLARES it (the engine has no clock; the comité executes it) and never
re-implements the biconditional — the real ledger rejects a confused config (AC-s4.5).
"""
from __future__ import annotations

from .config import RoundConfig

# population mixes: buena = all-cooperative; neutra = cooperative + passive/neutral archetypes,
# low adversity; mala = all four adversarial archetypes present, high adversity.
_MEZCLA_BUENA = {"circulator": 1.0}
_MEZCLA_NEUTRA = {"circulator": 0.6, "hoarder": 0.2, "wallflower": 0.2}
_MEZCLA_MALA = {"circulator": 0.4, "hoarder": 0.1,
                "defrauder": 0.15, "velocity_attacker": 0.15,
                "sybil_hopper": 0.1, "cell_leaker": 0.1}


def _base(seed: int, mezcla, intensidad: float, **overrides) -> RoundConfig:
    kw = dict(
        actor_mix=dict(mezcla), n_firms=16, T=24, clearing_cadence=5,
        base_turnover_cents=10_000_000, neg_line_bp=1000, pos_line_bp=1000,
        topology_params={"m": 2}, adversary_intensity=intensidad,
        velocity_window_s=1, ticks_per_second=10, velocity_max_cents=5_000_000,
        credit_crunch=False, seed=seed,
    )
    kw.update(overrides)
    return RoundConfig(**kw)


ESCENARIOS_VE = {
    "usd_buena": lambda seed=101: _base(seed, _MEZCLA_BUENA, 0.0),
    "usd_neutra": lambda seed=102: _base(seed, _MEZCLA_NEUTRA, 0.1),
    "usd_mala": lambda seed=103: _base(seed, _MEZCLA_MALA, 0.8),
    # the §3.1 scenario: a VES cell IS a separate cell with mandatory expiry — hyperinflation
    # is answered by expiry, never by a representable rate (N3).
    "ves_buena": lambda seed=104: _base(seed, _MEZCLA_BUENA, 0.0,
                                        moneda="VES", expira_en_dias=60),
    "ves_mala": lambda seed=105: _base(seed, _MEZCLA_MALA, 0.8,
                                       moneda="VES", expira_en_dias=60),
}
