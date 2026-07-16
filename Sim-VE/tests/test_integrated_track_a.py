"""MI-2: the three firewall oracles + Bridge-exploiter (ACI2.1–2.5), against the REAL B2B and C2C.

For the two SUT-enforced walls (F-VS1, F-CC) the real modules reject the exploit, so the clean run
passes and a hand-built *admitted* BridgeAttempt fails. F-VS2 has no SUT wall: a ScoreToCredit against
the REAL B2B succeeds and is caught only by the provenance oracle — the seam's headline finding.
"""
import ast
from pathlib import Path
from random import Random

from engine.measurement import Verdict
from engine.types import TraceEvent
from sim_c2c.adapter import C2CAdapter
from sim_integrated.identity import Identity
from sim_integrated.policies import BridgeExploiter, CooperativeBridge
from sim_integrated.track_a import IntegratedTrackA
from sim_integrated.world import BridgeAttempt, IntegratedWorld, Rejected, WorldEvent

from test_integrated_world_smoke import setup_b2b, C2C_ROOT


def _world(actors, ids, rosters, modes_note=""):
    b2b = {c: setup_b2b(c, r) for c, r in rosters.items()}
    c2c = C2CAdapter(C2C_ROOT)
    return IntegratedWorld(b2b, c2c, actors, ids, b2b_rosters=rosters,
                           c2c_modes={"room-gift": "don_comunal"}, rng=Random(3))


def _run(world, ticks=8):
    for _ in range(ticks):
        world.step()
    return IntegratedTrackA().measure(world.trace)


def _bridge_attempts(world, kind):
    return [e for e in world.trace if isinstance(e.result, BridgeAttempt) and e.result.kind == kind]


def _mc(kind, request, output, provenance):
    return TraceEvent(tick=0, actor_id="x", proposal=None,
                      result=BridgeAttempt(kind, request, output, provenance))


# ---- F-VS1 debt -> gift room -----------------------------------------------------------------
def test_fvs1_real_membrane_rejects_debt_leak_wall_holds():
    ex = Identity("X", "business", b2b_cell="cell-A", c2c_cell="room-gift")
    a2 = Identity("A2", "business", b2b_cell="cell-A")
    actors = {"X": BridgeExploiter(ex, modes=frozenset({"debt_to_gift"})),
              "A2": CooperativeBridge(a2, "X")}
    world = _world(actors, {"X": ex, "A2": a2}, {"cell-A": ("X", "A2")})
    report = _run(world)
    assert report.results["value_social_debt_leak"].verdict is Verdict.PASS
    # the exploiter DID attempt it, and the real membrane rejected every attempt
    leaks = _bridge_attempts(world, "debt_to_gift")
    assert leaks and all(isinstance(l.result.output, Rejected) for l in leaks)


def test_fvs1_admitted_leak_is_caught_by_the_oracle():
    trace = [
        TraceEvent(-1, "__setup__", None, WorldEvent("member_added", "cell-A", {"member_id": "X"})),
        TraceEvent(0, "X", None, WorldEvent("obligation_recorded", "cell-A",
                   {"payload": {"obligation": {"id": "o1", "amount_cents": 70_000}}})),
        _mc("debt_to_gift",
            {"carga": {"settlement_amount_cents": 70_000, "ref": "o1"}},
            {"admitido": True, "sala": "don_comunal"}, "b2b_obligation"),
    ]
    report = IntegratedTrackA().measure(trace)
    assert report.results["value_social_debt_leak"].verdict is Verdict.FAIL
    assert report.results["value_social_debt_leak"].exploit_trace["amount_cents"] == 70_000


# ---- F-VS2 person-scalar -> credit (no SUT wall; provenance oracle IS the wall) ---------------
def test_fvs2_score_to_credit_leaks_against_real_b2b_and_is_caught():
    ex = Identity("X", "business", b2b_cell="cell-A", c2c_cell="room-gift")
    actors = {"X": BridgeExploiter(ex, modes=frozenset({"score_to_credit"}), c2c_target="A2")}
    report = _run(_world(actors, {"X": ex}, {"cell-A": ("X", "A2")}))
    assert report.results["value_social_score_to_credit"].verdict is Verdict.FAIL, (
        "ACI2.3: the real B2B accepts a socially-derived credit bound (no provenance) — the oracle "
        "is the only thing that catches it; this is the seam's native failure mode"
    )


def test_fvs2_legitimate_credit_op_passes():
    # a human_ratified credit change is not a leak
    trace = [_mc("score_to_credit", {"member_id": "X", "changes": {"credit_max_cents": 200_000}},
                 {"kind": "member_updated"}, "human_ratified")]
    report = IntegratedTrackA().measure(trace)
    assert report.results["value_social_score_to_credit"].verdict is Verdict.PASS


# ---- F-CC cell -> cell contagion -------------------------------------------------------------
def test_fcc_real_b2b_rejects_foreign_debtor_wall_holds():
    ex = Identity("X", "business", b2b_cell="cell-A", c2c_cell=None)
    actors = {"X": BridgeExploiter(ex, modes=frozenset({"cross_cell"}),
                                   from_cell="cell-A", to_cell="cell-B",
                                   foreign_debtor="A1", local_creditor="B1")}
    ids = {"X": ex}
    world = _world(actors, ids, {"cell-A": ("X", "A1"), "cell-B": ("B1", "B2")})
    report = _run(world, ticks=9)
    assert report.results["cell_contagion"].verdict is Verdict.PASS
    xc = _bridge_attempts(world, "cross_cell")
    assert xc and all(isinstance(a.result.output, Rejected) for a in xc)


def test_fcc_accepted_foreign_obligation_is_caught_by_the_oracle():
    trace = [
        TraceEvent(-1, "__setup__", None, WorldEvent("member_added", "cell-B", {"member_id": "B1"})),
        TraceEvent(-1, "__setup__", None, WorldEvent("member_added", "cell-B", {"member_id": "B2"})),
        _mc("cross_cell", {"to_cell": "cell-B", "debtor": "A1", "creditor": "B1"},
            {"kind": "obligation_recorded"}, "cross_cell_default"),
    ]
    report = IntegratedTrackA().measure(trace)
    assert report.results["cell_contagion"].verdict is Verdict.FAIL
    assert report.results["cell_contagion"].exploit_trace["stranger"] == "A1"


def test_track_a_imports_neither_sut():
    import sim_integrated.track_a as mod
    tree = ast.parse(Path(mod.__file__).read_text())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    for banned in ("membrane", "legibility_query", "mutual_credit_ledger", "clearing_solver"):
        assert not any(banned in n for n in names)
