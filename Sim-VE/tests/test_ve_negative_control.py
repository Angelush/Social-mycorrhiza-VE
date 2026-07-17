"""TS.3 — the negative-control gate for the four VE oracles (AC-s3.*).

Four deliberately-broken SUT copies under negative_control/, ONE surgical silent plant each.
Per plant, the four upstream gate patterns: (a) the broken op does NOT raise (the plant beats
every SUT self-guard — otherwise the gate tests the SUT's self-defence, not the oracle: ST6);
(b) the INDEPENDENT VE oracle catches it; (c) the real SUT, same scenario, rejects or never
emits, and the oracle PASSES; (d) the plant is surgical — the fixture's other guards still fire.
"""
from pathlib import Path

import pytest

from engine.measurement import Verdict
from engine.types import TraceEvent
from sim_b2b.adapter import B2BAdapter
from sim_b2b.track_a_ve import B2BTrackAVE
from sim_b2b.world import ScopedStatements, Rejected as B2BRejected
from sim_c2c.adapter import C2CAdapter
from sim_c2c.track_a_ve import C2CTrackAVE
from sim_c2c.world import ModuleCall, Rejected as C2CRejected

SIM_SRC = Path(__file__).resolve().parent.parent / "src"
B2B_ROOT = Path(__file__).resolve().parent.parent.parent / "B2B-VE"
C2C_ROOT = Path(__file__).resolve().parent.parent.parent / "C2C-VE"
VE_FX = SIM_SRC / "sim_b2b" / "negative_control" / "ve_fx_fixture"
VE_VIS = SIM_SRC / "sim_b2b" / "negative_control" / "ve_vis_fixture"
VE_GATE = SIM_SRC / "sim_b2b" / "negative_control" / "ve_gate_fixture"
VE_MONEDA = SIM_SRC / "sim_c2c" / "negative_control" / "ve_moneda_fixture"

CELL_PARAMS = {
    "moneda": "USD", "sal_seudonimo": "sim-ve-sal",
    "neg_line_bp": 1000, "pos_line_bp": 1000,
    "velocity_window_s": 3600, "velocity_max_cents": 10_000_000,
}


def _ev(result, tick=0):
    return TraceEvent(tick=tick, actor_id="x", proposal=None, result=result)


def _cell(root, members=("A", "B", "C")):
    a = B2BAdapter(root)
    a.create_cell("cell-1", dict(CELL_PARAMS), ratified_by="ops", ts=0)
    for m in members:
        a.add_member({"id": m, "turnover_cents": 10_000_000}, ratified_by="ops", ts=0)
    return a


def _cycle_and_clear(adapter):
    """A perfect 3-cycle, cleared and applied: the committed clearing_applied event."""
    for oid, d, c in (("o1", "A", "B"), ("o2", "B", "C"), ("o3", "C", "A")):
        adapter.record_obligation(
            {"id": oid, "debtor": d, "creditor": c, "amount_cents": 10_000}, ts=0)
    proposal = adapter.run_clearing()
    return adapter.apply_clearing(proposal, ratified_by="harness-scheduler", ts=1)


# ---- ve_fx: the engine writes an FX gap into its own committed log -------------------------
def test_fx_plant_is_silent():
    event = _cycle_and_clear(_cell(VE_FX))          # AC-s3.1.a: must NOT raise
    assert event["payload"]["tasa_referencia"], "fixture sanity: the plant must have fired"


def test_fx_plant_is_caught_by_the_oracle():
    event = _cycle_and_clear(_cell(VE_FX))
    r = B2BTrackAVE().measure([_ev(event)]).results
    assert r["fx_irrepresentable"].verdict is Verdict.FAIL          # AC-s3.1.b
    # the recursive scan reaches the inner 'bcv' key before the outer 'tasa_referencia' —
    # either names the same plant; both are in the oracle's own taxonomy
    assert r["fx_irrepresentable"].exploit_trace["key"] in ("tasa_referencia", "bcv", "paralelo")


def test_fx_control_real_ledger_never_writes_a_rate():
    event = _cycle_and_clear(_cell(B2B_ROOT))       # AC-s3.1.c
    assert "tasa_referencia" not in event["payload"]
    r = B2BTrackAVE().measure([_ev(event)]).results
    assert r["fx_irrepresentable"].verdict is Verdict.PASS


def test_fx_plant_is_surgical_proposal_moneda_gate_still_fires():
    # AC-s3.1.d: the fixture's proposal_moneda gate (TB.8b) is intact — the plant did not
    # have to disable it, which is exactly WHY it is silent (it guards the unit, not the log).
    adapter = _cell(VE_FX)
    proposal = adapter.run_clearing()
    bad = dict(proposal); bad["moneda"] = "VES"
    with pytest.raises(ValueError, match="proposal_moneda"):
        adapter.apply_clearing(bad, ratified_by="x", ts=1)


# ---- ve_vis: publico also returns the balance -----------------------------------------------
def _probe(adapter, member="A", foreign="B"):
    def scoped(scope, solicitante=None):
        try:
            return adapter.member_statement(member, scope, solicitante=solicitante)
        except ValueError as exc:
            return B2BRejected(reason=str(exc))
    return ScopedStatements(member_id=member, publico=scoped("publico"),
                            miembro=scoped("miembro", solicitante=member),
                            cruce_ajeno=scoped("miembro", solicitante=foreign))


def test_vis_plant_is_silent():
    probe = _probe(_cell(VE_VIS))                   # AC-s3.2.a: no raise
    assert probe.publico.get("balance_cents") == 0, "fixture sanity: the plant must have fired"


def test_vis_plant_is_caught_by_the_oracle():
    probe = _probe(_cell(VE_VIS))
    r = B2BTrackAVE().measure([_ev(probe)]).results
    assert r["visibilidad_saldos"].verdict is Verdict.FAIL          # AC-s3.2.b
    assert r["visibilidad_saldos"].exploit_trace["kind"] == "publico_beyond_seudonimo"


def test_vis_control_real_publico_is_seudonimo_only():
    probe = _probe(_cell(B2B_ROOT))                 # AC-s3.2.c
    assert set(probe.publico) == {"seudonimo"}
    r = B2BTrackAVE().measure([_ev(probe)]).results
    assert r["visibilidad_saldos"].verdict is Verdict.PASS


def test_vis_plant_is_surgical_foreign_miembro_still_rejected():
    # AC-s3.2.d: only publico was widened; the miembro-scope solicitante check still fires.
    probe = _probe(_cell(VE_VIS))
    assert isinstance(probe.cruce_ajeno, B2BRejected)


# ---- ve_gate: bridge_paused loses its human gate --------------------------------------------
def test_gate_plant_is_silent():
    adapter = _cell(VE_GATE)
    event = adapter.puente_pausar(ratified_by="ignored-by-the-plant", ts=1)  # AC-s3.3.a
    assert event["kind"] == "bridge_paused"
    assert "ratified_by" not in event["payload"], "fixture sanity: the plant must have fired"


def test_gate_plant_is_caught_by_the_oracle():
    adapter = _cell(VE_GATE)
    event = adapter.puente_pausar(ratified_by="ignored", ts=1)
    r = B2BTrackAVE().measure([_ev(event)]).results
    assert r["puerta_humana_ops_nuevas"].verdict is Verdict.FAIL    # AC-s3.3.b
    assert r["puerta_humana_ops_nuevas"].exploit_trace["event_kind"] == "bridge_paused"


def test_gate_control_real_ledger_records_the_ratification():
    adapter = _cell(B2B_ROOT)                       # AC-s3.3.c
    event = adapter.puente_pausar(ratified_by="comite", ts=1)
    assert event["payload"]["ratified_by"] == "comite"
    r = B2BTrackAVE().measure([_ev(event)]).results
    assert r["puerta_humana_ops_nuevas"].verdict is Verdict.PASS


def test_gate_plant_is_surgical_other_gates_still_fire():
    # AC-s3.3.d: only the bridge door was opened — member_updated without ratified_by still
    # raises in the SAME broken copy (this is what makes the plant a plant, not a demolition).
    adapter = _cell(VE_GATE)
    with pytest.raises(ValueError, match="ratified_by"):
        adapter.update_member("A", {"credit_max_cents": 1}, ratified_by="", ts=1)


# ---- ve_moneda: the per-pledge moneda match is disabled --------------------------------------
_MIXED_REQ = {
    "campana_id": "c1", "celula_id": "cell", "tipo": "monetario", "umbral": 1,
    "expira_en": "T00000009", "moneda": "USD", "modo": "paz",
    "compromisos": [{"compromiso_id": "p1", "ficha_participante": "a",
                     "monto_centavos": 500, "moneda": "VES"}],
}


def test_moneda_plant_is_silent():
    out = C2CAdapter(VE_MONEDA).resolver(dict(_MIXED_REQ))          # AC-s3.4.a: no raise
    assert out["moneda"] == "USD", "output indistinguishable from a legal one — that's the point"


def test_moneda_plant_is_caught_by_the_oracle():
    out = C2CAdapter(VE_MONEDA).resolver(dict(_MIXED_REQ))
    r = C2CTrackAVE().measure(
        [_ev(ModuleCall(method="resolver", request=dict(_MIXED_REQ), output=out))]).results
    assert r["moneda_unica_por_campana"].verdict is Verdict.FAIL    # AC-s3.4.b
    assert r["moneda_unica_por_campana"].exploit_trace["kind"] == "moneda_mezclada_en_campana"


def test_moneda_control_real_sut_rejects_the_mixture():
    adapter = C2CAdapter(C2C_ROOT)                  # AC-s3.4.c
    with pytest.raises(ValueError, match="mono-moneda"):
        adapter.resolver(dict(_MIXED_REQ))


def test_moneda_plant_is_surgical_envelope_moneda_still_required():
    # AC-s3.4.d: only the per-pledge match was disabled — an invalid envelope moneda still raises.
    adapter = C2CAdapter(VE_MONEDA)
    bad = dict(_MIXED_REQ); bad["moneda"] = "EUR"
    with pytest.raises(ValueError, match="moneda"):
        adapter.resolver(bad)


# ---- AC-s3.5: the real SUTs are byte-untouched ----------------------------------------------
def test_real_suts_carry_no_ts3_plant():
    for f in (B2B_ROOT / "src" / "ledger" / "mutual_credit_ledger.py",
              C2C_ROOT / "src" / "assurance" / "aseguramiento.py"):
        assert "TS3 SILENT PLANT" not in f.read_text(), f
