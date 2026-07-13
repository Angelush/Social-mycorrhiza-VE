import dataclasses

import pytest

from engine.campaign import Budget, campaign
from engine.journal import Journal
from engine.measurement import (
    Distribution,
    IntegrityReport,
    InvariantResult,
    TrackA,
    TrackB,
    Verdict,
    WelfareReport,
    assert_no_person_scalar,
)
from engine.policy import RulePolicy
from engine.researcher import GateViolation, Researcher, apply_within_gate
from engine.sut_adapter import SUTAdapter, SUTIntegrityError
from engine.types import Proposal, RangeBound, SearchSpace, SetBound, WorldDiff
from engine.world import World


def test_search_space_allow_list():
    ss = SearchSpace(bounds={"x": RangeBound(0.0, 1.0), "mix": SetBound(frozenset({"a", "b"}))})
    assert ss.contains_diff({"x": 0.5}) is True
    assert ss.contains_diff({"x": 1.5}) is False
    assert ss.contains_diff({"nonexistent": 1}) is False


def test_apply_within_gate_accepts_and_merges():
    ss = SearchSpace(bounds={"x": RangeBound(0.0, 1.0)})
    cfg = {"x": 0.1, "y": "unchanged"}
    diff = WorldDiff(fields={"x": 0.9})
    new_cfg = apply_within_gate(cfg, diff, ss)
    assert new_cfg == {"x": 0.9, "y": "unchanged"}
    assert cfg == {"x": 0.1, "y": "unchanged"}


def test_apply_within_gate_rejects_undeclared_field():
    ss = SearchSpace(bounds={"x": RangeBound(0.0, 1.0)})
    cfg = {"x": 0.1}
    diff = WorldDiff(fields={"sut_source_path": "/tmp/evil.py"})
    with pytest.raises(GateViolation):
        apply_within_gate(cfg, diff, ss)


def test_welfare_report_rejects_agent_indexed_mapping():
    with pytest.raises(TypeError):
        WelfareReport(metrics={"suspicious": {"agent_1": 0.9, "agent_2": 0.1}})


def test_welfare_report_accepts_honest_aggregate():
    report = WelfareReport(metrics={"gini": 0.42, "benefit": Distribution(summary={"mean": 10.0})})
    assert report.metrics["gini"] == 0.42


def test_assert_no_person_scalar_lint():
    report = WelfareReport(metrics={"trust_score": 0.5})
    with pytest.raises(ValueError):
        assert_no_person_scalar(report, frozenset({"trust_score"}))


def test_journal_hash_chain_verifies():
    j = Journal()
    ir = IntegrityReport(results={"conservation": InvariantResult(verdict=Verdict.PASS)})
    wr = WelfareReport(metrics={"reduction_pct": 25.0})
    j.append(0, "cfg0hash", ir, wr, "try higher intensity", WorldDiff(fields={}))
    j.append(1, "cfg1hash", ir, wr, None, None)
    assert j.verify_chain() is True
    assert j.entries[1].prev_hash == j.entries[0].entry_hash


def test_journal_hash_chain_detects_tamper():
    j = Journal()
    ir = IntegrityReport(results={"conservation": InvariantResult(verdict=Verdict.PASS)})
    wr = WelfareReport(metrics={})
    j.append(0, "cfg0hash", ir, wr, None, None)
    j.entries[0] = dataclasses.replace(j.entries[0], config_hash="TAMPERED")
    assert j.verify_chain() is False


def test_sut_adapter_pin_detects_drift(tmp_path):
    src = tmp_path / "fake_sut.py"
    src.write_text("VALUE = 1\n")
    adapter = SUTAdapter([str(src)])
    adapter.assert_pinned()
    src.write_text("VALUE = 2\n")
    with pytest.raises(SUTIntegrityError):
        adapter.assert_pinned()


class _Trade(Proposal):
    def __init__(self, amount: int):
        self.amount = amount


class _AlwaysProposePolicy(RulePolicy):
    def act(self, view, rng):
        return _Trade(amount=1)


class _FakeWorld(World):
    def observe(self, actor_id):
        return None

    def adjudicate(self, actor_id, proposal):
        return "accepted"

    def apply(self, actor_id, proposal, result):
        pass


class _AlwaysPassTrackA(TrackA):
    def measure(self, trace):
        return IntegrityReport(results={"dummy": InvariantResult(verdict=Verdict.PASS)})


class _AlwaysFailTrackA(TrackA):
    def measure(self, trace):
        return IntegrityReport(
            results={"conservation": InvariantResult(verdict=Verdict.FAIL, exploit_trace="drop 1 cent")}
        )


class _CountingTrackB(TrackB):
    def measure(self, trace):
        return WelfareReport(metrics={"events": float(len(trace))})


class _OneShotResearcher(Researcher):
    def __init__(self):
        self.calls = 0

    def next(self, history, search_space):
        self.calls += 1
        return (f"round {self.calls}", WorldDiff(fields={}))


def test_campaign_end_to_end_runs_and_journals(tmp_path):
    src = tmp_path / "fake_sut.py"
    src.write_text("VALUE = 1\n")
    adapter = SUTAdapter([str(src)])

    def build_world(cfg, rng):
        return _FakeWorld(sut_adapter=adapter, actors={"a1": _AlwaysProposePolicy()}, env=None, rng=rng)

    result = campaign(
        initial_cfg={},
        search_space=SearchSpace(bounds={}),
        budget=Budget(max_rounds=3),
        seed=42,
        sut_adapter=adapter,
        researcher=_OneShotResearcher(),
        build_world=build_world,
        ticks_for=lambda cfg: 2,
        track_a=_AlwaysPassTrackA(),
        track_b=_CountingTrackB(),
    )

    assert result.halted is False
    assert len(result.history) == 3
    assert len(result.journal.entries) == 3
    assert result.journal.verify_chain() is True


def test_campaign_halts_on_violation(tmp_path):
    src = tmp_path / "fake_sut.py"
    src.write_text("VALUE = 1\n")
    adapter = SUTAdapter([str(src)])

    def build_world(cfg, rng):
        return _FakeWorld(sut_adapter=adapter, actors={"a1": _AlwaysProposePolicy()}, env=None, rng=rng)

    result = campaign(
        initial_cfg={},
        search_space=SearchSpace(bounds={}),
        budget=Budget(max_rounds=5),
        seed=1,
        sut_adapter=adapter,
        researcher=_OneShotResearcher(),
        build_world=build_world,
        ticks_for=lambda cfg: 1,
        track_a=_AlwaysFailTrackA(),
        track_b=_CountingTrackB(),
    )

    assert result.halted is True
    assert result.halting_report.violation is True
    assert len(result.history) == 0
    assert len(result.journal.entries) == 1


def test_campaign_reproducible_across_processes(tmp_path):
    import subprocess
    import sys as _sys

    src = tmp_path / "fake_sut.py"
    src.write_text("VALUE = 1\n")
    runner = tmp_path / "run_campaign.py"
    runner.write_text(
        f"""
import sys
sys.path.insert(0, {str((__import__('pathlib').Path(__file__).resolve().parent.parent / 'src'))!r})
from engine.campaign import Budget, campaign
from engine.measurement import IntegrityReport, InvariantResult, TrackA, TrackB, Verdict, WelfareReport
from engine.researcher import Researcher
from engine.sut_adapter import SUTAdapter
from engine.types import SearchSpace, WorldDiff
from engine.policy import RulePolicy
from engine.world import World

class _Trade:
    pass

class _P(RulePolicy):
    def act(self, view, rng):
        return None

class _W(World):
    def observe(self, actor_id): return None
    def adjudicate(self, actor_id, proposal): return None
    def apply(self, actor_id, proposal, result): pass

class _TA(TrackA):
    def measure(self, trace):
        return IntegrityReport(results={{"d": InvariantResult(verdict=Verdict.PASS)}})

class _TB(TrackB):
    def measure(self, trace):
        return WelfareReport(metrics={{"n": float(len(trace))}})

class _R(Researcher):
    def next(self, history, search_space):
        return (None, WorldDiff(fields={{}}))

adapter = SUTAdapter([{str(src)!r}])
result = campaign(
    initial_cfg={{}}, search_space=SearchSpace(bounds={{}}), budget=Budget(max_rounds=2),
    seed=7, sut_adapter=adapter, researcher=_R(),
    build_world=lambda cfg, rng: _W(sut_adapter=adapter, actors={{"a1": _P()}}, env=None, rng=rng),
    ticks_for=lambda cfg: 1, track_a=_TA(), track_b=_TB(),
)
print(result.journal.entries[-1].entry_hash)
"""
    )
    out1 = subprocess.run([_sys.executable, str(runner)], capture_output=True, text=True, check=True)
    out2 = subprocess.run([_sys.executable, str(runner)], capture_output=True, text=True, check=True)
    assert out1.stdout.strip() == out2.stdout.strip()
    assert len(out1.stdout.strip()) == 64
