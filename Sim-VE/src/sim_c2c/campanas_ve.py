"""TS.4 — named descriptive VE campaign scenarios for the C2C side.

buena / mala under modo `paz`, one scenario under `catastrofe_acotada` (the TA.4 surface
under real load: the modo's caps actually bite), and one VES assurance-campaign scenario
(TA.6: campañas mono-moneda, `moneda` in every Capa-4 envelope). Track B remains structurally
person-scalar-free (the WelfareReport TYPE is the wall) and descriptive-only.
"""
from __future__ import annotations

from .campaign import _DEFAULT_MIX, GIFT_CELL, MARKET_CELL
from .config import RoundConfig

_MEZCLA_BUENA = {"reciprocator": 0.7, "newcomer": 0.15, "lurker": 0.15}


def _base(seed: int, mezcla, intensidad: float, **overrides) -> RoundConfig:
    kw = dict(
        actor_mix=dict(mezcla), n_actors=12, T=24,
        cells={GIFT_CELL: "don_comunal", MARKET_CELL: "precio_de_mercado"},
        adversary_intensity=intensidad, window=5, velocity_cap=3, half_life=4,
        min_strength=0.1, seed=seed,
    )
    kw.update(overrides)
    return RoundConfig(**kw)


ESCENARIOS_VE = {
    "paz_buena": lambda seed=201: _base(seed, _MEZCLA_BUENA, 0.0),
    "paz_mala": lambda seed=202: _base(seed, dict(_DEFAULT_MIX), 0.8),
    # TA.4 under load: every envelope carries modo='catastrofe_acotada' and the modo's own
    # caps (payload/retention/velocity) are live in the REAL capas.
    "catastrofe_acotada": lambda seed=203: _base(seed, _MEZCLA_BUENA, 0.2,
                                                 modo="catastrofe_acotada"),
    # TA.6: mono-moneda VES assurance campaigns (the envelope's moneda; never per-pledge mixing)
    "ves_campana": lambda seed=204: _base(seed, _MEZCLA_BUENA, 0.0, moneda="VES"),
}
