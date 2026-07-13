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
    out = {"asker": "A", "target": "T", "cell_id": "c1",
           "from_your_position": {"reachable": True, "nearest_hops": 1, "vouch_paths": [],
                                  "vouched_by_people_you_trust": [], "facts": [],
                                  "reachability": {"A": 0.9, "B": 0.3}},  # the silent proxy
           "verdict": "known_via_trust", "note": "", "audit_trace": {}}
    report = C2CTrackA().measure([_mc("query", {"cell_id": "c1"}, out)])
    assert report.results["no_person_scalar"].verdict is Verdict.FAIL
    assert report.results["no_person_scalar"].exploit_trace["kind"] == "person_scalar_leak"


def test_t_a1_forbidden_named_scalar_also_caught():
    out = {"cell_id": "c1", "now": 1, "sensed": [], "verdict": "quiet_from_your_cell",
           "note": "", "audit_trace": {"damped_velocity": 0}, "trust_score": 0.5}
    report = C2CTrackA().measure([_mc("sense", {"cell_id": "c1"}, out)])
    assert report.results["no_person_scalar"].verdict is Verdict.FAIL


def test_t_a2_market_leak_admitted_is_caught():
    request = {"mode": "communal_gift", "cell_id": "c1", "interaction_id": "i1",
               "payload": {"item": "x", "price_cents": 500}}
    out = {"mode": "communal_gift", "cell_id": "c1", "interaction_id": "i1", "expires_at": None,
           "admitted": True, "audit_trace": {}}
    report = C2CTrackA().measure([_mc("admit", request, out)])
    assert report.results["no_market_leak"].verdict is Verdict.FAIL
    assert report.results["no_market_leak"].exploit_trace["key"] == "price_cents"


def test_t_a3_position_independent_path_is_caught():
    out = {"asker": "A", "target": "T", "cell_id": "c1",
           "from_your_position": {"reachable": True, "nearest_hops": 2,
                                  "vouch_paths": [["X", "B", "T"]],  # does not start at asker A
                                  "vouched_by_people_you_trust": [], "facts": []},
           "verdict": "known_via_trust", "note": "", "audit_trace": {}}
    report = C2CTrackA().measure([_mc("query", {"cell_id": "c1"}, out)])
    assert report.results["asker_relative"].verdict is Verdict.FAIL


def test_t_a4_expired_edge_surfaced_is_caught():
    request = {"cell_id": "c1", "now": "T00000010",
               "graph": {"vouches": [{"from": "A", "to": "T", "cell_id": "c1",
                                      "expires_at": "T00000005"}],  # expired at now
                         "facts": []}}
    out = {"asker": "A", "target": "T", "cell_id": "c1",
           "from_your_position": {"reachable": True, "nearest_hops": 1,
                                  "vouch_paths": [["A", "T"]],
                                  "vouched_by_people_you_trust": ["A"], "facts": []},
           "verdict": "known_via_trust", "note": "", "audit_trace": {}}
    report = C2CTrackA().measure([_mc("query", request, out)])
    assert report.results["forgetting"].verdict is Verdict.FAIL


def test_t_a5_objector_token_leak_is_caught():
    request = {"circle_id": "c1", "proposal_id": "p1",
               "dispositions": [{"token": "bb1", "disposition": "object", "circle_id": "c1",
                                 "objection": {"paramount": True, "reason": "no"}}]}
    out = {"circle_id": "c1", "proposal_id": "p1", "verdict": "revisit",
           "paramount_objections": [{"reason": "no", "objector": "bb1"}],  # token leaked
           "concerns": [], "note": "", "expires_at": None, "audit_trace": {}}
    report = C2CTrackA().measure([_mc("decide", request, out)])
    assert report.results["consent_privacy"].verdict is Verdict.FAIL
    assert report.results["consent_privacy"].exploit_trace["token"] == "bb1"


def test_t_a6_unthrottled_burst_is_caught():
    traces = [{"about": "art", "signal": "contribution", "strength": 1.0,
               "created_at": 10, "cell_id": "c1", "context": None} for _ in range(5)]
    request = {"cell_id": "c1", "now": 10, "window": 5, "velocity_cap": 3, "traces": traces}
    out = {"cell_id": "c1", "now": 10, "sensed": [], "verdict": "quiet_from_your_cell",
           "note": "", "audit_trace": {"damped_velocity": 0}}  # throttle silently disabled
    report = C2CTrackA().measure([_mc("sense", request, out)])
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
    for capa in ("membrane", "legibility_query", "matcher", "assurance_engine",
                 "stigmergy", "governance"):
        assert not any(capa in n for n in names), f"Track A must not import {capa}"
