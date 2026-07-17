"""TS.4 — descriptive VE campaign scenarios (AC-s4.1..AC-s4.5).

Every named scenario runs end-to-end against the REAL VE SUTs, byte-reproducibly; Track A
(composite, VE oracles included) stays green and complete; VES-ness is judged on the TRACE
(the cell_created event), never on the config; Track B stays descriptive.
"""
from pathlib import Path

import pytest

from engine.measurement import Distribution, Verdict

from sim_b2b.adapter import B2BAdapter
from sim_b2b.campaign import build_campaign as build_b2b, params_de_celula
from sim_b2b.campanas_ve import ESCENARIOS_VE as B2B_VE
from sim_c2c.campaign import build_campaign as build_c2c
from sim_c2c.campanas_ve import ESCENARIOS_VE as C2C_VE

B2B_ROOT = Path(__file__).resolve().parent.parent.parent / "B2B-VE"
C2C_ROOT = Path(__file__).resolve().parent.parent.parent / "C2C-VE"

_B2B_INVARIANTES = {"conservation", "credit_bound", "firewall", "velocity", "sanctions",
                    "fx_irrepresentable", "visibilidad_saldos", "puerta_humana_ops_nuevas"}
_C2C_INVARIANTES = {"no_person_scalar", "no_market_leak", "asker_relative", "forgetting",
                    "consent_privacy", "anti_cascade", "moneda_unica_por_campana"}


# ---- AC-s4.1 + AC-s4.2: byte-reproducible, unhalted, full oracle set ------------------------
@pytest.mark.parametrize("nombre", sorted(B2B_VE))
def test_b2b_escenario_reproducible_y_verde(nombre):
    a = build_b2b(B2B_VE[nombre](), B2B_ROOT, max_rounds=2)
    b = build_b2b(B2B_VE[nombre](), B2B_ROOT, max_rounds=2)
    assert not a.halted, f"{nombre}: Track A (VE incluido) detuvo la campaña"
    assert a.history == b.history                                    # AC-s4.1
    assert [e.entry_hash for e in a.journal.entries] == \
           [e.entry_hash for e in b.journal.entries]                 # the strong witness
    assert set(a.history[0].integrity_report.results) == _B2B_INVARIANTES  # AC-s4.2
    for r in a.history[0].integrity_report.results.values():
        assert r.verdict is Verdict.PASS


@pytest.mark.parametrize("nombre", sorted(C2C_VE))
def test_c2c_escenario_reproducible_y_verde(nombre):
    a = build_c2c(C2C_VE[nombre](), C2C_ROOT, max_rounds=2)
    b = build_c2c(C2C_VE[nombre](), C2C_ROOT, max_rounds=2)
    assert not a.halted, f"{nombre}: Track A (VE incluido) detuvo la campaña"
    assert a.history == b.history
    assert [e.entry_hash for e in a.journal.entries] == \
           [e.entry_hash for e in b.journal.entries]
    assert set(a.history[0].integrity_report.results) == _C2C_INVARIANTES
    for r in a.history[0].integrity_report.results.values():
        assert r.verdict is Verdict.PASS


# ---- AC-s4.3: VES-ness judged on the TRACE (the cell_created event), not the config ---------
@pytest.mark.parametrize("nombre,moneda", [("ves_buena", "VES"), ("ves_mala", "VES"),
                                           ("usd_buena", "USD")])
def test_b2b_celula_es_lo_que_su_evento_dice(nombre, moneda):
    cfg = B2B_VE[nombre]()
    event = B2BAdapter(B2B_ROOT).create_cell(
        "cell-1", params_de_celula(cfg), ratified_by="ops", ts=0)
    params = event["payload"]["params"]
    assert params["moneda"] == moneda
    if moneda == "VES":
        assert params["expira_en_dias"] == 60      # D1 biconditional, declared for real
    else:
        assert "expira_en_dias" not in params


def test_b2b_poblacion_mala_lleva_los_cuatro_adversarios():
    mix = B2B_VE["usd_mala"]().actor_mix
    assert {"defrauder", "velocity_attacker", "sybil_hopper", "cell_leaker"} <= set(mix)


def test_c2c_catastrofe_acotada_llega_al_cable():
    # the scenario's modo must reach the SUT envelopes, not just sit in the config
    from random import Random
    from sim_c2c.campaign import _build_actors
    from sim_c2c.adapter import C2CAdapter
    from sim_c2c.world import C2CWorld, ModuleCall
    cfg = C2C_VE["catastrofe_acotada"]()
    assert cfg.modo == "catastrofe_acotada"
    actors, cell_of = _build_actors(cfg, Random(3))
    world = C2CWorld(C2CAdapter(C2C_ROOT), actors, cfg, cell_of, dict(cfg.cells), Random(3))
    for _ in range(8):
        world.step()
    calls = [e.result for e in world.trace if isinstance(e.result, ModuleCall)]
    assert calls and all(mc.request.get("modo") == "catastrofe_acotada" for mc in calls)


def test_c2c_ves_campana_llega_al_cable():
    from random import Random
    from sim_c2c.campaign import _build_actors
    from sim_c2c.adapter import C2CAdapter
    from sim_c2c.world import C2CWorld, ModuleCall, Rejected
    cfg = C2C_VE["ves_campana"]()
    actors, cell_of = _build_actors(cfg, Random(3))
    world = C2CWorld(C2CAdapter(C2C_ROOT), actors, cfg, cell_of, dict(cfg.cells), Random(3))
    for _ in range(24):
        world.step()
    resolves = [e.result for e in world.trace
                if isinstance(e.result, ModuleCall) and e.result.method == "resolver"
                and not isinstance(e.result.output, Rejected)]
    assert resolves, "sin material: ninguna campaña de aseguramiento resolvió"
    assert all(mc.output["moneda"] == "VES" for mc in resolves)


# ---- AC-s4.4: Track B stays descriptive ------------------------------------------------------
def test_b2b_track_b_es_distribucional():
    result = build_b2b(B2B_VE["usd_mala"](), B2B_ROOT, max_rounds=1)
    metrics = result.history[0].welfare_report.metrics
    assert any(isinstance(v, Distribution) for v in metrics.values()), (
        "Track B sin una sola distribución: dejó de ser distribucional"
    )


def test_c2c_track_b_sin_dimension_por_agente():
    # the structural wall: WelfareReport has no agent-indexed dimension; sampled positions only
    result = build_c2c(C2C_VE["paz_mala"](), C2C_ROOT, max_rounds=1)
    metrics = result.history[0].welfare_report.metrics
    for name, v in metrics.items():
        assert not isinstance(v, dict), f"{name}: un mapa con clave de agente es el escalar prohibido"


# ---- AC-s4.5: a confused VES config does not start — the REAL ledger kills it ---------------
def test_ves_sin_expiracion_no_arranca():
    import dataclasses
    cfg = dataclasses.replace(B2B_VE["ves_buena"](), expira_en_dias=None)
    with pytest.raises(ValueError, match="expira_en_dias"):
        build_b2b(cfg, B2B_ROOT, max_rounds=1)


def test_usd_con_expiracion_tampoco():
    # the other half of the biconditional: a USD cell declaring expiry is confused about
    # what it is — the real ledger rejects it too (harness repairs nothing).
    import dataclasses
    cfg = dataclasses.replace(B2B_VE["usd_buena"](), expira_en_dias=30)
    with pytest.raises(ValueError, match="expira_en_dias"):
        build_b2b(cfg, B2B_ROOT, max_rounds=1)
