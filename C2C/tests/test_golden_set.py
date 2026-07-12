"""Golden-set regression gate for the assurance engine.

The spec bundle (tests.md, README, audit.md) promises "re-run golden-set on any
change (DVH-007/008)" — but nothing loaded the fixtures, so they could drift from
the engine silently. This wires workflows/.../evals/golden-set/*.json into pytest
so a change that alters engine output fails here.

Drafted by Mistral via multi-model-orchestration; reviewed by Claude (repo-root
path anchoring fixed to match the sibling tests' idiom). stdlib + pytest only.
"""
import importlib.util
import json
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_ENGINE = _ROOT / "src" / "assurance" / "assurance_engine.py"
_spec = importlib.util.spec_from_file_location("assurance_engine_golden", _ENGINE)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
resolve = _mod.resolve

_GOLDEN = _ROOT / "workflows" / "micorriza-politica" / "evals" / "golden-set"


def _load(name):
    return json.loads((_GOLDEN / name).read_text())


@pytest.mark.parametrize("name", ["test_A.json", "test_B.json"])
def test_golden_full_equality(name):
    data = _load(name)
    assert resolve(data["input"]) == data["expected"]


@pytest.mark.parametrize("campaign_key", ["campaign_1", "campaign_2"])
def test_golden_status_check(campaign_key):
    entry = _load("test_C_crosscampaign.json")[campaign_key]
    assert resolve(entry["input"])["status"] == entry["expected_status"]


@pytest.mark.parametrize("reject_key", list(_load("test_C_crosscampaign.json")["rejected_inputs"]))
def test_golden_rejected_inputs(reject_key):
    bad = _load("test_C_crosscampaign.json")["rejected_inputs"][reject_key]
    with pytest.raises(ValueError):
        resolve(bad)
