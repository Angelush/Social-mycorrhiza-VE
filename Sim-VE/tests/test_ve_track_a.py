"""TS.2 — the four VE Track-A oracles (AC-s2.1..AC-s2.6).

Each oracle: clean real material PASSES; one hand-planted breach per property FAILS; and the
oracle is proven independent (AST: imports no SUT module, no adapter). Anti-vacuity (TS.1's M2
lesson): the real campaigns must PRODUCE the material the oracles judge — an oracle with no
material is green blind.
"""
import ast
from pathlib import Path

from engine.measurement import Verdict
from engine.types import TraceEvent
from sim_b2b.track_a_ve import B2BTrackAVE
from sim_b2b.world import ClearingOutcome, Rejected as B2BRejected, ScopedStatements
from sim_c2c.track_a_ve import C2CTrackAVE
from sim_c2c.world import ModuleCall, Rejected as C2CRejected


def _ev(result, tick=0, actor="x"):
    return TraceEvent(tick=tick, actor_id=actor, proposal=None, result=result)


def _b2b(trace):
    return B2BTrackAVE().measure(trace).results


def _c2c(trace):
    return C2CTrackAVE().measure(trace).results


# ---- AC-s2.1: independence, by AST --------------------------------------------------------
def _imported_names(mod):
    tree = ast.parse(Path(mod.__file__).read_text())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_ve_oracles_import_no_sut_and_no_adapter():
    import sim_b2b.track_a_ve as b
    import sim_c2c.track_a_ve as c
    forbidden = ("mutual_credit_ledger", "clearing_solver", "adapter",
                 "membrana", "legibilidad", "emparejador", "aseguramiento",
                 "estigmergia", "gobernanza")
    for mod in (b, c):
        names = _imported_names(mod)
        for bad in forbidden:
            assert not any(bad in n for n in names), f"{mod.__name__} imports {bad}"


# ---- AC-s2.2: fx_irrepresentable -----------------------------------------------------------
_CELL_CREATED = {"kind": "cell_created", "ts": 0,
                 "payload": {"cell_id": "c1", "ratified_by": "ops",
                             "params": {"moneda": "USD", "sal_seudonimo": "s"}}}


def test_fx_clean_event_passes():
    r = _b2b([_ev(dict(_CELL_CREATED))])
    assert r["fx_irrepresentable"].verdict is Verdict.PASS


def test_fx_tasa_key_in_event_fails():
    ev = {"kind": "member_updated", "ts": 1,
          "payload": {"member_id": "A", "ratified_by": "ops",
                      "changes": {"tasa_bcv": 725_74}}}
    r = _b2b([_ev(ev)])
    assert r["fx_irrepresentable"].verdict is Verdict.FAIL
    assert r["fx_irrepresentable"].exploit_trace["key"] == "tasa_bcv"


def test_fx_glued_variant_also_fails():
    # the taxonomy is not the exact word (TA.6's reviewer hardening, duplicated here)
    ev = {"kind": "member_updated", "ts": 1,
          "payload": {"member_id": "A", "ratified_by": "ops",
                      "changes": {"tasadecambio": 36}}}
    assert _b2b([_ev(ev)])["fx_irrepresentable"].verdict is Verdict.FAIL


def test_fx_obligation_with_moneda_fails():
    # a per-obligation moneda is the door to partitioned L1 + a rate (D1: mixing stays
    # UNREPRESENTABLE, not merely unused)
    ev = {"kind": "obligation_recorded", "ts": 1,
          "payload": {"obligation": {"id": "o1", "debtor": "A", "creditor": "B",
                                     "amount_cents": 500, "moneda": "VES"}}}
    r = _b2b([_ev(ev)])
    assert r["fx_irrepresentable"].verdict is Verdict.FAIL
    assert r["fx_irrepresentable"].exploit_trace["kind"] == "obligation_carries_moneda"


def test_fx_proposal_in_another_moneda_fails():
    out = ClearingOutcome(proposal={"cell_id": "c1", "moneda": "VES", "settlements": []},
                          applied_event=None)
    r = _b2b([_ev(dict(_CELL_CREATED)), _ev(out)])
    assert r["fx_irrepresentable"].verdict is Verdict.FAIL
    assert r["fx_irrepresentable"].exploit_trace["kind"] == "proposal_moneda_mismatch"


# ---- AC-s2.3: visibilidad_saldos -----------------------------------------------------------
def _probe(publico, member_id="A", cruce=B2BRejected(reason="solicitante")):
    return ScopedStatements(member_id=member_id, publico=publico,
                            miembro={"member_id": member_id, "balance_cents": 0},
                            cruce_ajeno=cruce)


def test_visibilidad_clean_probe_passes():
    r = _b2b([_ev(_probe({"seudonimo": "1a32980dd16a890b"}))])
    assert r["visibilidad_saldos"].verdict is Verdict.PASS


def test_visibilidad_balance_under_publico_fails():
    r = _b2b([_ev(_probe({"seudonimo": "x", "balance_cents": 500}))])
    assert r["visibilidad_saldos"].verdict is Verdict.FAIL


def test_visibilidad_unforeseen_numeric_field_fails_by_type():
    # the wall is the output TYPE, not a list of names (TB.4's AC-7 lesson): `salud` is on
    # no blacklist anywhere — it must fail anyway.
    r = _b2b([_ev(_probe({"seudonimo": "x", "salud": 7}))])
    assert r["visibilidad_saldos"].verdict is Verdict.FAIL


def test_visibilidad_seudonimo_equal_to_identity_fails():
    r = _b2b([_ev(_probe({"seudonimo": "A"}, member_id="A"))])
    assert r["visibilidad_saldos"].verdict is Verdict.FAIL
    assert r["visibilidad_saldos"].exploit_trace["kind"] == "seudonimo_is_identity"


def test_visibilidad_unstable_seudonimo_fails():
    r = _b2b([_ev(_probe({"seudonimo": "aaa"})), _ev(_probe({"seudonimo": "bbb"}))])
    assert r["visibilidad_saldos"].verdict is Verdict.FAIL
    assert r["visibilidad_saldos"].exploit_trace["kind"] == "seudonimo_unstable"


def test_visibilidad_foreign_miembro_scope_not_rejected_fails():
    r = _b2b([_ev(_probe({"seudonimo": "x"}, cruce={"member_id": "A", "balance_cents": 0}))])
    assert r["visibilidad_saldos"].verdict is Verdict.FAIL
    assert r["visibilidad_saldos"].exploit_trace["kind"] == "foreign_miembro_scope_not_rejected"


# ---- AC-s2.4: puerta_humana_ops_nuevas -----------------------------------------------------
def test_puerta_clean_gated_events_pass():
    evs = [_ev(dict(_CELL_CREATED)),
           _ev({"kind": "bridge_paused", "ts": 1, "payload": {"ratified_by": "comite"}}),
           _ev({"kind": "member_exited", "ts": 2,
                "payload": {"member_id": "A", "ratified_by": "comite",
                            "resolucion": {"tipo": "simple"}}})]
    assert _b2b(evs)["puerta_humana_ops_nuevas"].verdict is Verdict.PASS


def test_puerta_member_exited_without_ratification_fails():
    ev = {"kind": "member_exited", "ts": 2,
          "payload": {"member_id": "A", "resolucion": {"tipo": "simple"}}}
    r = _b2b([_ev(ev)])
    assert r["puerta_humana_ops_nuevas"].verdict is Verdict.FAIL
    assert r["puerta_humana_ops_nuevas"].exploit_trace["event_kind"] == "member_exited"


def test_puerta_bridge_paused_without_ratification_fails():
    ev = {"kind": "bridge_paused", "ts": 1, "payload": {}}
    assert _b2b([_ev(ev)])["puerta_humana_ops_nuevas"].verdict is Verdict.FAIL


def test_puerta_obligation_without_ratification_does_not_fail():
    # negative control: trading carries no human gate BY DESIGN (N-d68.4 in spirit) — an
    # oracle that demanded one would be inventing policy, not checking it.
    ev = {"kind": "obligation_recorded", "ts": 1,
          "payload": {"obligation": {"id": "o1", "debtor": "A", "creditor": "B",
                                     "amount_cents": 500}}}
    assert _b2b([_ev(ev)])["puerta_humana_ops_nuevas"].verdict is Verdict.PASS


# ---- AC-s2.5: moneda_unica_por_campana -----------------------------------------------------
def _resolve_call(request, output):
    return _ev(ModuleCall(method="resolver", request=request, output=output))


_CLEAN_REQ = {"campana_id": "c1", "celula_id": "cell", "tipo": "binario", "umbral": 2,
              "expira_en": "T9", "moneda": "USD", "compromisos": [], "modo": "paz"}
_CLEAN_OUT = {"campana_id": "c1", "celula_id": "cell", "estado": "reembolsa",
              "comprometidos_distintos": 0, "umbral": 2, "expira_en": "T9",
              "moneda": "USD", "resolucion": {"se_activa": False, "reembolsos": []},
              "traza_auditoria": {}}


def test_moneda_unica_clean_passes():
    assert _c2c([_resolve_call(dict(_CLEAN_REQ), dict(_CLEAN_OUT))])[
        "moneda_unica_por_campana"].verdict is Verdict.PASS


def test_moneda_unica_output_in_other_moneda_fails():
    out = dict(_CLEAN_OUT); out["moneda"] = "VES"
    r = _c2c([_resolve_call(dict(_CLEAN_REQ), out)])
    assert r["moneda_unica_por_campana"].verdict is Verdict.FAIL
    assert r["moneda_unica_por_campana"].exploit_trace["kind"] == "moneda_mezclada_en_campana"


def test_moneda_unica_mixed_pledge_that_succeeded_fails():
    # if the SUT stopped rejecting a per-pledge mismatch, only the oracle sees it
    req = dict(_CLEAN_REQ)
    req["compromisos"] = [{"compromiso_id": "p1", "ficha_participante": "a", "moneda": "VES"}]
    r = _c2c([_resolve_call(req, dict(_CLEAN_OUT))])
    assert r["moneda_unica_por_campana"].verdict is Verdict.FAIL


def test_moneda_unica_rejected_calls_are_skipped():
    # the SUT's own wall fired: nothing was emitted; the oracle judges successful calls only
    req = dict(_CLEAN_REQ); req["moneda"] = "EUR"
    r = _c2c([_resolve_call(req, C2CRejected(reason="moneda"))])
    assert r["moneda_unica_por_campana"].verdict is Verdict.PASS


# ---- AC-s2.6: anti-vacuity — the real campaigns produce the material -----------------------
def test_b2b_campaign_produces_probes_and_puente_cycle_and_stays_green():
    from sim_b2b.campaign import build_campaign
    from sim_b2b.config import RoundConfig
    cfg = RoundConfig(
        actor_mix={"circulator": 1.0}, n_firms=8, T=16, clearing_cadence=5,
        base_turnover_cents=10_000_000, neg_line_bp=1000, pos_line_bp=1000,
        topology_params={"m": 2}, adversary_intensity=0.0, velocity_window_s=1,
        ticks_per_second=10, velocity_max_cents=5_000_000, credit_crunch=False, seed=11,
    )
    root = Path(__file__).resolve().parent.parent.parent / "B2B-VE"
    result = build_campaign(cfg, root, max_rounds=1)
    assert not result.halted
    report = result.history[0].integrity_report
    for name in ("fx_irrepresentable", "visibilidad_saldos", "puerta_humana_ops_nuevas"):
        assert report.results[name].verdict is Verdict.PASS, name


def test_b2b_world_trace_carries_the_ve_material():
    # the material itself, not just the verdicts: probes AND the puente pair must exist —
    # an auditor that stopped probing would leave the oracles green and blind (M2 lesson).
    from random import Random
    from sim_b2b.adapter import B2BAdapter
    from sim_b2b.config import RoundConfig
    from sim_b2b.policies_core import Auditor, Circulator
    from sim_b2b.world import B2BWorld
    root = Path(__file__).resolve().parent.parent.parent / "B2B-VE"
    adapter = B2BAdapter(root)
    adapter.create_cell("cell-1", {
        "moneda": "USD", "sal_seudonimo": "sim-ve-sal",
        "neg_line_bp": 1000, "pos_line_bp": 1000,
        "velocity_window_s": 3600, "velocity_max_cents": 10_000_000,
    }, ratified_by="ops", ts=0)
    for fid in ("A", "B"):
        adapter.add_member({"id": fid, "turnover_cents": 10_000_000}, ratified_by="ops", ts=0)
    cfg = RoundConfig(
        actor_mix={}, n_firms=2, T=12, clearing_cadence=5,
        base_turnover_cents=10_000_000, neg_line_bp=1000, pos_line_bp=1000,
        topology_params={}, adversary_intensity=0.0, velocity_window_s=3600,
        ticks_per_second=10, velocity_max_cents=10_000_000, credit_crunch=False, seed=5,
    )
    actors = {"A": Circulator("A"), "B": Circulator("B"),
              "__auditor__": Auditor(member_ids=("A", "B"))}
    world = B2BWorld(adapter, actors, cfg, {"A": ("B",), "B": ("A",)}, Random(5))
    for _ in range(12):
        world.step()
    probes = [e for e in world.trace if isinstance(e.result, ScopedStatements)]
    kinds = {e.result.get("kind") for e in world.trace if isinstance(e.result, dict)}
    assert probes, "no ScopedStatements in the trace — visibilidad_saldos had no material"
    assert {"bridge_paused", "bridge_resumed"} <= kinds, (
        "no puente cycle in the trace — puerta_humana_ops_nuevas never saw the ops nuevas"
    )
    # and the real material judged by the real oracle stays green
    report = B2BTrackAVE().measure(world.trace)
    for name in ("fx_irrepresentable", "visibilidad_saldos", "puerta_humana_ops_nuevas"):
        assert report.results[name].verdict is Verdict.PASS, name


def test_c2c_campaign_resolver_material_and_green():
    from test_c2c_world_actors import _run
    world = _run(7)
    resolves = [e for e in world.trace
                if isinstance(e.result, ModuleCall) and e.result.method == "resolver"
                and not isinstance(e.result.output, C2CRejected)]
    assert resolves, "no successful resolver call — moneda_unica had no material"
    report = C2CTrackAVE().measure(world.trace)
    assert report.results["moneda_unica_por_campana"].verdict is Verdict.PASS
