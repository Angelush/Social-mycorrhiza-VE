"""The negative-control gate (spec.md §7, N-01/N-02) — the build's defining acceptance test.

Drives the REAL B2BAdapter (unmodified, production code) against deliberately-broken SUT
*copies* living under sim_b2b/negative_control/ -- B2B/ itself is never touched. If these
tests ever fail (or worse, silently pass because the harness stopped noticing), the harness's
own oracle has gone blind (G-04): it would be trusting a broken SUT's self-reports instead of
independently re-deriving conservation.
"""
from pathlib import Path

import pytest

from engine.measurement import Verdict
from engine.types import TraceEvent
from sim_b2b.adapter import B2BAdapter
from sim_b2b.proposals import Trade
from sim_b2b.track_a import B2BTrackA
from sim_b2b.world import ClearingOutcome

NEG_CONTROL_ROOT = Path(__file__).resolve().parent.parent / "src" / "sim_b2b" / "negative_control"
N01_ROOT = NEG_CONTROL_ROOT / "n01_fixture"
N02_ROOT = NEG_CONTROL_ROOT / "n02_fixture"
B2B_ROOT = Path(__file__).resolve().parent.parent.parent / "B2B-VE"

CELL_PARAMS = {
    "moneda": "USD", "sal_seudonimo": "sim-ve-sal",
    "neg_line_bp": 1000, "pos_line_bp": 1000,
    "velocity_window_s": 3600, "velocity_max_cents": 10_000_000,
}


def _setup_event(mid: str, stmt: dict) -> TraceEvent:
    return TraceEvent(
        tick=-1, actor_id="__setup__", proposal=None,
        result={
            "kind": "member_added",
            "payload": {
                "member": {
                    "id": mid, "turnover_cents": 10_000_000,
                    "credit_min_cents": stmt["credit_min_cents"], "credit_max_cents": stmt["credit_max_cents"],
                },
                "ratified_by": "ops",
            },
        },
    )


def _record_event(adapter: B2BAdapter, oid: str, debtor: str, creditor: str, amount: int, tick: int, ts: int) -> TraceEvent:
    event = adapter.record_obligation({"id": oid, "debtor": debtor, "creditor": creditor, "amount_cents": amount}, ts=ts)
    return TraceEvent(tick=tick, actor_id=debtor, proposal=None, result=event)


def _drive_three_cycle(adapter: B2BAdapter) -> list[TraceEvent]:
    """A, B, C each owe the next 10,000 cents in a perfect cycle: a true clearing must cancel
    all three edges identically and change no one's net position."""
    adapter.create_cell("cell-1", dict(CELL_PARAMS), ratified_by="ops", ts=0)
    setup = []
    for mid in ("A", "B", "C"):
        adapter.add_member({"id": mid, "turnover_cents": 10_000_000}, ratified_by="ops", ts=0)
        setup.append(_setup_event(mid, adapter.member_statement(mid, "comite_credito")))

    records = [
        _record_event(adapter, "o1", "A", "B", 10_000, tick=0, ts=0),
        _record_event(adapter, "o2", "B", "C", 10_000, tick=0, ts=0),
        _record_event(adapter, "o3", "C", "A", 10_000, tick=0, ts=0),
    ]
    return setup + records


def test_n01_silent_conservation_breach_is_caught_by_the_independent_oracle():
    adapter = B2BAdapter(N01_ROOT)
    trace = _drive_three_cycle(adapter)

    proposal = adapter.run_clearing()
    # The plant is silent by construction: this must NOT raise, unlike a naive one-guard plant
    # would (ST6) -- both the solver's own assert and the ledger's apply-time re-verification
    # are disabled in this fixture, so the corrupted proposal commits without incident.
    applied_event = adapter.apply_clearing(proposal, ratified_by="harness-scheduler", ts=1)
    trace.append(
        TraceEvent(
            tick=1, actor_id="__clearing_scheduler__", proposal=None,
            result=ClearingOutcome(proposal=proposal, applied_event=applied_event),
        )
    )

    track_a = B2BTrackA(velocity_window_s=3600, velocity_max_cents=10_000_000)
    report = track_a.measure(trace)

    assert report.results["conservation"].verdict is Verdict.FAIL, (
        "AC3/G-04: the harness's independent oracle must catch a silent conservation breach "
        "that bypasses BOTH of the SUT's own guards -- if this ever passes, the oracle has "
        "gone blind and cannot be trusted to report a real one"
    )
    assert report.violation is True
    exploit = report.results["conservation"].exploit_trace
    assert exploit is not None and "firm" in exploit


def test_n01_control_the_same_scenario_passes_against_the_real_sut():
    # Same exact scenario, against the REAL (unmodified) B2B code: must PASS. This proves the
    # FAIL above is caused by the plant, not by some artifact of the test scenario itself.
    adapter = B2BAdapter(B2B_ROOT)
    trace = _drive_three_cycle(adapter)
    proposal = adapter.run_clearing()
    applied_event = adapter.apply_clearing(proposal, ratified_by="harness-scheduler", ts=1)
    trace.append(
        TraceEvent(
            tick=1, actor_id="__clearing_scheduler__", proposal=None,
            result=ClearingOutcome(proposal=proposal, applied_event=applied_event),
        )
    )

    track_a = B2BTrackA(velocity_window_s=3600, velocity_max_cents=10_000_000)
    report = track_a.measure(trace)

    assert report.results["conservation"].verdict is Verdict.PASS
    assert report.violation is False


def test_n01_naive_single_guard_plant_is_self_caught_not_a_valid_gate():
    # ST6's own warning, verified directly: disabling ONLY the solver's assert (guard i) while
    # leaving the ledger's apply-time re-verification (guard ii) intact must still raise --
    # from the SUT itself, not from the harness. A negative control that stopped here would be
    # testing the SUT's self-defence, not the independent oracle, which is exactly the mistake
    # spec.md §7 warns against.
    import importlib.util

    solver_path = N01_ROOT / "src" / "clearing" / "clearing_solver.py"
    real_ledger_path = B2B_ROOT / "src" / "ledger" / "mutual_credit_ledger.py"

    def _load(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    broken_solver = _load("partial_plant_solver", solver_path)
    real_ledger = _load("partial_plant_ledger", real_ledger_path)

    state, _ = real_ledger.create_cell("cell-1", dict(CELL_PARAMS), ratified_by="ops", ts=0)
    for mid in ("A", "B", "C"):
        state, _ = real_ledger.add_member(state, {"id": mid, "turnover_cents": 10_000_000}, ratified_by="ops", ts=0)
    for oid, debtor, creditor in [("o1", "A", "B"), ("o2", "B", "C"), ("o3", "C", "A")]:
        state, _ = real_ledger.record_obligation(state, {"id": oid, "debtor": debtor, "creditor": creditor, "amount_cents": 10_000}, ts=0)

    proposal = broken_solver.clear(real_ledger.to_clearing_input(state))  # the corrupted proposal, no raise (guard i disabled)
    with pytest.raises(ValueError):
        real_ledger.apply_clearing(state, proposal, ratified_by="harness-scheduler", ts=1)  # guard ii still catches it


def test_n02_silent_clamp_is_caught_by_credit_bound_oracle():
    adapter = B2BAdapter(N02_ROOT)
    adapter.create_cell("cell-1", dict(CELL_PARAMS), ratified_by="ops", ts=0)
    trace = []
    for mid in ("A", "B"):
        adapter.add_member({"id": mid, "turnover_cents": 10_000_000}, ratified_by="ops", ts=0)
        trace.append(_setup_event(mid, adapter.member_statement(mid, "comite_credito")))

    # A's negative cap is -1,000,000; request an obligation for 1,200,000 -- the real ledger
    # would reject this outright. The N-02 fixture instead silently clamps to 1,000,000 and
    # reports success, with the event echoing the clamped (not requested) amount.
    event = adapter.record_obligation({"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 1_200_000}, ts=0)
    assert event["payload"]["obligation"]["amount_cents"] == 1_000_000, "fixture sanity: the clamp itself must have fired"

    trace.append(
        TraceEvent(
            tick=0, actor_id="A",
            proposal=Trade(obligation_id="o1", debtor="A", creditor="B", cents=1_200_000),
            result=event,
        )
    )

    track_a = B2BTrackA(velocity_window_s=3600, velocity_max_cents=10_000_000)
    report = track_a.measure(trace)

    assert report.results["credit_bound"].verdict is Verdict.FAIL, (
        "AC3: an op accepted for X cents whose committed effect is Y < X must be caught"
    )
    assert report.results["credit_bound"].exploit_trace["kind"] == "silent_clamp_trade"
    assert report.results["credit_bound"].exploit_trace["requested"] == 1_200_000
    assert report.results["credit_bound"].exploit_trace["committed"] == 1_000_000


def test_n02_control_the_same_request_is_rejected_outright_by_the_real_sut():
    adapter = B2BAdapter(B2B_ROOT)
    adapter.create_cell("cell-1", dict(CELL_PARAMS), ratified_by="ops", ts=0)
    for mid in ("A", "B"):
        adapter.add_member({"id": mid, "turnover_cents": 10_000_000}, ratified_by="ops", ts=0)

    with pytest.raises(ValueError):
        adapter.record_obligation({"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 1_200_000}, ts=0)


def test_n03_conservation_oracle_never_imports_the_sut_it_is_checking():
    # Static self-confirmation guard (AC4/N-03): Track A must recompute independently of the
    # SUT's own modules, never call into them. Checks actual import statements via ast, not a
    # raw substring scan -- track_a.py's own comments legitimately mention clearing_solver.py
    # by name when explaining WHY its recompute uses a different code path, and that mention
    # must not itself trip this guard.
    import ast

    import sim_b2b.track_a as track_a_module

    source = Path(track_a_module.__file__).read_text()
    tree = ast.parse(source)
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)

    assert not any("clearing_solver" in m for m in imported_modules)
    assert not any("mutual_credit_ledger" in m for m in imported_modules)
    assert "networkx" in imported_modules
