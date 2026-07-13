"""M1: C2CAdapter — thin 1:1 wrapper over the real six Capa modules (AC1.1–AC1.4).

Drives the REAL C2C code (never mocked; the only stub allowed anywhere in Sim-C2C is the
injected matcher `propose`). Confirms each method forwards verbatim: real returns come
back unchanged, and the real modules' own raises propagate untouched through the adapter.
"""
from pathlib import Path

import pytest

from engine.sut_adapter import SUTIntegrityError, compute_pin
from sim_c2c.adapter import C2CAdapter

C2C_ROOT = Path(__file__).resolve().parent.parent.parent / "C2C"


@pytest.fixture
def adapter():
    return C2CAdapter(C2C_ROOT)


def test_pin_in_fork_monorepo(adapter):
    # AC1.1: content_hash is the real pin. In this fork the C2C tree lives inside
    # the fork's monorepo, so the supplementary git_commit resolves to its HEAD.
    assert isinstance(adapter.pin.content_hash, str) and len(adapter.pin.content_hash) == 64
    assert len(adapter.pin.source_paths) == 6
    assert adapter.pin.git_commit is not None and len(adapter.pin.git_commit) == 40


def test_pin_git_commit_none_outside_any_repo(tmp_path):
    # The graceful-None property the original (pre-fork) test pinned: with no
    # enclosing repo, git_commit is None — never an error. content_hash still computes.
    src = tmp_path / "module.py"
    src.write_text("X = 1\n")
    pin = compute_pin([src], repo_dir=tmp_path)
    assert pin.git_commit is None
    assert len(pin.content_hash) == 64


def test_assert_pinned_passes_when_unchanged(adapter):
    adapter.assert_pinned()  # must not raise


def test_assert_pinned_fails_if_a_source_byte_changes(adapter, tmp_path):
    # AC1.3: copy the real tree, pin, mutate one byte, expect SUTIntegrityError.
    import shutil

    dst = tmp_path / "C2C"
    shutil.copytree(C2C_ROOT, dst)
    a = C2CAdapter(dst)
    a.assert_pinned()
    membrane = dst / "src" / "partition" / "membrane.py"
    membrane.write_text(membrane.read_text() + "\n# mutated\n")
    with pytest.raises(SUTIntegrityError):
        a.assert_pinned()


def test_admit_passthrough_and_raise(adapter):
    # AC1.2/AC1.4: a clean gift interaction returns admitted=True; a market key raises verbatim.
    ok = adapter.admit({
        "mode": "communal_gift", "cell_id": "c1", "interaction_id": "i1",
        "participants": ["a", "b"], "payload": {"gift": "bread"},
    })
    assert ok["admitted"] is True
    with pytest.raises(adapter.MembraneBreachError):
        adapter.admit({
            "mode": "communal_gift", "cell_id": "c1", "interaction_id": "i2",
            "participants": ["a"], "payload": {"price_cents": 500},
        })


def test_query_passthrough_neutral_verdict(adapter):
    out = adapter.query({
        "asker": "a", "target": "z", "cell_id": "c1", "now": "2026-01-01", "max_hops": 3,
        "graph": {"vouches": [], "facts": []},
    })
    assert out["verdict"] == "no_info_from_your_position"
    with pytest.raises(adapter.LegibilityBreachError):
        adapter.query({"asker": "", "target": "z", "cell_id": "c1", "now": "n", "max_hops": 3,
                       "graph": {"vouches": [], "facts": []}})


def test_match_never_raises_on_bad_model_output(adapter):
    # AC1.4: bad model output is dropped-and-counted, NEVER raised — the guardrail must not be
    # crashable by a prompt-injected model. A malformed REQUEST does raise.
    req = {
        "asker": "a", "cell_ids": ["c1"], "now": "2026-01-01", "expires_at": "2026-02-01",
        "max_proposals": 5, "self": {"needs": ["bread"]},
        "candidates": [{"token": "b", "cell_id": "c1", "offers": ["bread"],
                        "consent": {"surfaceable": True}}],
    }
    out = adapter.match(req, lambda ctx: [{"garbage": True}, "not-a-dict"])
    assert out["audit_trace"]["dropped_off_schema"] >= 1
    with pytest.raises(adapter.MatcherBreachError):
        adapter.match({"asker": ""}, lambda ctx: [])


def test_resolve_passthrough_and_distinct_exception_types(adapter):
    out = adapter.resolve({
        "campaign_id": "camp1", "cell_id": "c1", "kind": "binary", "threshold": 2,
        "expires_at": "2026-02-01",
        "pledges": [{"pledge_id": "p1", "participant_token": "x"}],
    })
    assert out["status"] == "refunds"
    # bad input -> ValueError (not AssuranceInvariantError, which is an internal abort)
    with pytest.raises(ValueError):
        adapter.resolve({"campaign_id": "c", "cell_id": "c1", "kind": "bogus", "threshold": 1,
                         "expires_at": "e", "pledges": []})


def test_sense_passthrough_integer_clock(adapter):
    out = adapter.sense({
        "cell_id": "c1", "now": 10, "window": 5, "velocity_cap": 3, "half_life": 4,
        "min_strength": 0.1,
        "traces": [{"about": "art1", "signal": "contribution", "strength": 1.0,
                    "created_at": 9, "cell_id": "c1"}],
    })
    assert out["verdict"] == "signals_sensed"
    with pytest.raises(adapter.StigmergyBreachError):
        adapter.sense({"cell_id": "c1", "now": "not-an-int", "window": 5, "velocity_cap": 3,
                       "half_life": 4, "min_strength": 0.1, "traces": []})


def test_decide_passthrough_reasons_not_identities(adapter):
    out = adapter.decide({
        "circle_id": "circle1", "proposal_id": "prop1", "now": "2026-01-01",
        "expires_at": "2026-02-01",
        "dispositions": [
            {"token": "x", "disposition": "consent", "circle_id": "circle1"},
            {"token": "y", "disposition": "object", "circle_id": "circle1",
             "objection": {"paramount": True, "reason": "unsafe"}},
        ],
    })
    assert out["verdict"] == "revisit"
    assert out["paramount_objections"] == [{"reason": "unsafe"}]
    # no objector token leaks anywhere in the output
    import json
    assert "\"y\"" not in json.dumps(out)
    with pytest.raises(adapter.GovernanceBreachError):
        adapter.decide({"circle_id": "", "proposal_id": "p", "now": "n", "expires_at": "e",
                        "dispositions": []})
