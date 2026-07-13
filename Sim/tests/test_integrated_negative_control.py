"""MI-3: the integration negative-control gate (spec §5, failure-model HI-1/HI-2) — ACI3.1–3.3.

Drives the REAL, unmodified adapters against deliberately-broken SUT copies; B2B/ and C2C/ themselves
are never touched. NI-01 reuses the Sim-C2C n02 broken membrane (silent market admit); NI-02 plants a
broken B2B ledger that silently auto-registers a cross-cell stranger. If either passes silently, the
harness has gone blind to a cross-system leak — the highest-value finding in the project.
"""
from pathlib import Path
from random import Random

import pytest

from engine.measurement import Verdict
from sim_b2b.adapter import B2BAdapter
from sim_c2c.adapter import C2CAdapter
from sim_integrated.identity import Identity
from sim_integrated.policies import BridgeExploiter
from sim_integrated.track_a import IntegratedTrackA
from sim_integrated.world import BridgeAttempt, IntegratedWorld, Rejected

from test_integrated_world_smoke import setup_b2b, CELL_PARAMS, B2B_ROOT, C2C_ROOT

SIM_SRC = Path(__file__).resolve().parent.parent / "src"
C2C_N02 = SIM_SRC / "sim_c2c" / "negative_control" / "n02_fixture"
B2B_XCELL = SIM_SRC / "sim_integrated" / "negative_control" / "b2b_xcell_fixture"


def _setup_root(root, cell, members):
    a = B2BAdapter(root)
    a.create_cell(cell, dict(CELL_PARAMS), ratified_by="ops", ts=0)
    for m in members:
        a.add_member({"id": m, "turnover_eur_cents": 10_000_000}, ratified_by="ops", ts=0)
    return a


def _attempts(world, kind):
    return [e.result for e in world.trace
            if isinstance(e.result, BridgeAttempt) and e.result.kind == kind]


# ---- NI-01: silent debt -> gift-room leak (broken membrane) ----------------------------------
def _debt_leak_world(c2c_root):
    ex = Identity("X", "business", b2b_cell="cell-A", c2c_cell="room-gift")
    actors = {"X": BridgeExploiter(ex, modes=frozenset({"debt_to_gift"}))}
    b2b = {"cell-A": setup_b2b("cell-A", ("X", "A2"))}
    world = IntegratedWorld(b2b, C2CAdapter(c2c_root), actors, {"X": ex},
                            b2b_rosters={"cell-A": ("X", "A2")},
                            c2c_modes={"room-gift": "communal_gift"}, rng=Random(3))
    for _ in range(6):
        world.step()
    return world


def test_ni01_silent_debt_leak_is_caught_by_the_oracle():
    world = _debt_leak_world(C2C_N02)
    admitted = [a for a in _attempts(world, "debt_to_gift") if not isinstance(a.output, Rejected)]
    assert admitted, "fixture sanity: the broken membrane must have silently admitted the debt"
    report = IntegratedTrackA().measure(world.trace)
    assert report.results["value_social_debt_leak"].verdict is Verdict.FAIL, (
        "ACI3.1: the oracle must catch a denominated debt silently admitted into a gift room"
    )


def test_ni01_control_real_membrane_rejects_the_same_interaction():
    world = _debt_leak_world(C2C_ROOT)
    attempts = _attempts(world, "debt_to_gift")
    assert attempts and all(isinstance(a.output, Rejected) for a in attempts)
    report = IntegratedTrackA().measure(world.trace)
    assert report.results["value_social_debt_leak"].verdict is Verdict.PASS


# ---- NI-02: silent cross-cell contagion (broken ledger) --------------------------------------
def _xcell_world(b2b_b_root):
    ex = Identity("X", "business", b2b_cell="cell-A", c2c_cell=None)
    actors = {"X": BridgeExploiter(ex, modes=frozenset({"cross_cell"}),
                                   from_cell="cell-A", to_cell="cell-B",
                                   foreign_debtor="A1", local_creditor="B1")}
    b2b = {"cell-A": setup_b2b("cell-A", ("X", "A1")),
           "cell-B": _setup_root(b2b_b_root, "cell-B", ("B1", "B2"))}
    world = IntegratedWorld(b2b, C2CAdapter(C2C_ROOT), actors, {"X": ex},
                            b2b_rosters={"cell-A": ("X", "A1"), "cell-B": ("B1", "B2")},
                            c2c_modes={"room-gift": "communal_gift"}, rng=Random(3))
    for _ in range(9):
        world.step()
    return world


def test_ni02_silent_cross_cell_contagion_is_caught_by_the_oracle():
    world = _xcell_world(B2B_XCELL)
    committed = [a for a in _attempts(world, "cross_cell") if not isinstance(a.output, Rejected)]
    assert committed, "fixture sanity: the broken ledger must have silently committed the obligation"
    report = IntegratedTrackA().measure(world.trace)
    assert report.results["cell_contagion"].verdict is Verdict.FAIL, (
        "ACI3.2: the oracle must catch a cell-A stranger committed as a cell-B obligation"
    )
    assert report.results["cell_contagion"].exploit_trace["stranger"] == "A1"


def test_ni02_control_real_ledger_rejects_the_foreign_debtor():
    world = _xcell_world(B2B_ROOT)
    attempts = _attempts(world, "cross_cell")
    assert attempts and all(isinstance(a.output, Rejected) for a in attempts)
    report = IntegratedTrackA().measure(world.trace)
    assert report.results["cell_contagion"].verdict is Verdict.PASS


def test_ni02_plant_is_surgical_remaining_guards_still_fire():
    # ST6 non-vacuity: the broken ledger's OTHER guards are intact — a settlement that would breach a
    # member's credit bound still raises, proving only the membership guard was removed and that F-CC
    # (not the ledger's own conservation) is the load-bearing gate.
    a = _setup_root(B2B_XCELL, "cell-B", ("B1", "B2"))
    with pytest.raises(ValueError):
        a.settle_obligation("does-not-exist", 100, ts=1)


def test_suts_are_byte_unchanged():
    # ACI3.3: plants live only under negative_control/.
    assert "NI-02 SILENT PLANT" not in (B2B_ROOT / "src" / "ledger" / "mutual_credit_ledger.py").read_text()
    assert "N-02 SILENT PLANT" not in (C2C_ROOT / "src" / "partition" / "membrane.py").read_text()
