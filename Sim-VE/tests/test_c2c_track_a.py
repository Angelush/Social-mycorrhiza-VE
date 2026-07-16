"""M3: Track A integrity oracles (AC3.1–AC3.3).

Clean pass: the real mixed-population trace shows zero violations (adversaries are caught by the
modules' own walls, which the oracles correctly skip). Then one hand-planted breach per oracle is
independently caught, and Track A is proven to import no C2C module (AST).
"""
import ast
from pathlib import Path

from engine.measurement import Verdict
from engine.types import TraceEvent
from sim_c2c.track_a import C2CTrackA
from sim_c2c.world import ModuleCall

from test_c2c_world_actors import _run  # reuse the mixed-population driver


def _mc(method, request, output):
    return TraceEvent(tick=0, actor_id="x", proposal=None,
                      result=ModuleCall(method=method, request=request, output=output))


def test_clean_mixed_population_has_no_violations():
    world = _run(7)
    report = C2CTrackA().measure(world.trace)
    assert not report.violation, f"clean run should pass; failed: {report.failed_invariants}"
    assert all(r.verdict is Verdict.PASS for r in report.results.values())


def test_t_a1_out_of_schema_person_scalar_is_caught():
    out = {"consultante": "A", "objetivo": "T", "celula_id": "c1",
           "desde_tu_posicion": {"alcanzable": True, "saltos_minimos": 1, "rutas_de_aval": [],
                                 "avalado_por_gente_de_tu_confianza": [], "hechos": [],
                                 "reachability": {"A": 0.9, "B": 0.3}},  # the silent proxy
           "veredicto": "conocido_via_confianza", "nota": "", "traza_auditoria": {}}
    report = C2CTrackA().measure([_mc("consultar", {"celula_id": "c1"}, out)])
    assert report.results["no_person_scalar"].verdict is Verdict.FAIL
    assert report.results["no_person_scalar"].exploit_trace["kind"] == "person_scalar_leak"


def test_t_a1_forbidden_named_scalar_also_caught():
    out = {"celula_id": "c1", "ahora": 1, "sentidas": [], "veredicto": "silencio_desde_tu_celula",
           "nota": "", "traza_auditoria": {"amortiguadas_velocidad": 0}, "trust_score": 0.5}
    report = C2CTrackA().measure([_mc("sentir", {"celula_id": "c1"}, out)])
    assert report.results["no_person_scalar"].verdict is Verdict.FAIL


def test_t_a2_market_leak_admitted_is_caught():
    request = {"sala": "don_comunal", "celula_id": "c1", "interaccion_id": "i1",
               "carga": {"item": "x", "price_cents": 500}}
    out = {"sala": "don_comunal", "celula_id": "c1", "interaccion_id": "i1", "expira_en": None,
           "admitido": True, "traza_auditoria": {}}
    report = C2CTrackA().measure([_mc("admitir", request, out)])
    assert report.results["no_market_leak"].verdict is Verdict.FAIL
    assert report.results["no_market_leak"].exploit_trace["key"] == "price_cents"


def test_t_a3_position_independent_path_is_caught():
    out = {"consultante": "A", "objetivo": "T", "celula_id": "c1",
           "desde_tu_posicion": {"alcanzable": True, "saltos_minimos": 2,
                                 "rutas_de_aval": [["X", "B", "T"]],  # does not start at asker A
                                 "avalado_por_gente_de_tu_confianza": [], "hechos": []},
           "veredicto": "conocido_via_confianza", "nota": "", "traza_auditoria": {}}
    report = C2CTrackA().measure([_mc("consultar", {"celula_id": "c1"}, out)])
    assert report.results["asker_relative"].verdict is Verdict.FAIL


def test_t_a4_expired_edge_surfaced_is_caught():
    request = {"celula_id": "c1", "ahora": "T00000010",
               "grafo": {"avales": [{"de": "A", "a": "T", "celula_id": "c1",
                                     "expira_en": "T00000005"}],  # expired at now
                         "hechos": []}}
    out = {"consultante": "A", "objetivo": "T", "celula_id": "c1",
           "desde_tu_posicion": {"alcanzable": True, "saltos_minimos": 1,
                                 "rutas_de_aval": [["A", "T"]],
                                 "avalado_por_gente_de_tu_confianza": ["A"], "hechos": []},
           "veredicto": "conocido_via_confianza", "nota": "", "traza_auditoria": {}}
    report = C2CTrackA().measure([_mc("consultar", request, out)])
    assert report.results["forgetting"].verdict is Verdict.FAIL


def test_t_a5_objector_token_leak_is_caught():
    request = {"circulo_id": "c1", "propuesta_id": "p1",
               "posturas": [{"ficha": "bb1", "postura": "objetar", "circulo_id": "c1",
                             "objecion": {"primordial": True, "razon": "no"}}]}
    out = {"circulo_id": "c1", "propuesta_id": "p1", "veredicto": "revisar",
           "objeciones_primordiales": [{"razon": "no", "objector": "bb1"}],  # token leaked
           "inquietudes": [], "nota": "", "expira_en": None, "traza_auditoria": {}}
    report = C2CTrackA().measure([_mc("decidir", request, out)])
    assert report.results["consent_privacy"].verdict is Verdict.FAIL
    assert report.results["consent_privacy"].exploit_trace["ficha"] == "bb1"


def test_t_a6_unthrottled_burst_is_caught():
    traces = [{"about": "art", "senal": "contribucion", "fuerza": 1.0,
               "creado_en": 10, "celula_id": "c1", "contexto": None} for _ in range(5)]
    request = {"celula_id": "c1", "ahora": 10, "ventana": 5, "tope_velocidad": 3, "trazas": traces}
    out = {"celula_id": "c1", "ahora": 10, "sentidas": [], "veredicto": "silencio_desde_tu_celula",
           "nota": "", "traza_auditoria": {"amortiguadas_velocidad": 0}}  # throttle silently disabled
    report = C2CTrackA().measure([_mc("sentir", request, out)])
    assert report.results["anti_cascade"].verdict is Verdict.FAIL


def test_track_a_imports_no_c2c_module():
    import sim_c2c.track_a as mod
    tree = ast.parse(Path(mod.__file__).read_text())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    for capa in ("membrana", "legibilidad", "emparejador", "aseguramiento",
                 "estigmergia", "gobernanza"):
        assert not any(capa in n for n in names), f"Track A must not import {capa}"
