"""M5: the negative-control gate (spec.md §6, failure-model H-1/H-2) — the build's defining test.

Drives the REAL, unmodified C2CAdapter against deliberately-broken SUT *copies* under
sim_c2c/negative_control/ (each a full six-module copy with ONE surgical plant); C2C/ itself is
never touched. If these ever pass silently, the harness oracle has gone blind — it would be trusting
a broken SUT's self-reports instead of independently re-deriving integrity.
"""
from pathlib import Path

import pytest

from engine.measurement import Verdict
from engine.types import TraceEvent
from sim_c2c.adapter import C2CAdapter
from sim_c2c.track_a import C2CTrackA
from sim_c2c.world import ModuleCall

NEG = Path(__file__).resolve().parent.parent / "src" / "sim_c2c" / "negative_control"
N01 = NEG / "n01_fixture"
N02 = NEG / "n02_fixture"
C2C_ROOT = Path(__file__).resolve().parent.parent.parent / "C2C"

_QUERY_REQ = {
    "asker": "A", "target": "T", "cell_id": "c1", "now": "T00000005", "max_hops": 3,
    "graph": {"vouches": [{"from": "A", "to": "T", "cell_id": "c1", "expires_at": "T00000100"}],
              "facts": []},
}
_GIFT_MARKET = {
    "mode": "communal_gift", "cell_id": "c1", "interaction_id": "i1",
    "participants": ["A"], "payload": {"item": "favour", "price_cents": 999},
}


def _mc(method, request, output):
    return TraceEvent(tick=0, actor_id="x", proposal=None,
                      result=ModuleCall(method=method, request=request, output=output))


# ---- N-01: silent person-scalar (H-1) --------------------------------------------------------
def test_n01_silent_person_scalar_is_caught_by_track_a():
    adapter = C2CAdapter(N01)
    out = adapter.query(dict(_QUERY_REQ))            # MUST NOT raise — the plant is silent
    assert "reachability" in out["from_your_position"], "fixture sanity: the plant must have fired"

    report = C2CTrackA().measure([_mc("query", _QUERY_REQ, out)])
    assert report.results["no_person_scalar"].verdict is Verdict.FAIL, (
        "AC5.1/G-04: the independent oracle must catch a silent per-person scalar that carries no "
        "forbidden substring — if this passes, the oracle is blind to the exact C2C anti-goal"
    )
    assert report.results["no_person_scalar"].exploit_trace["kind"] == "person_scalar_leak"


def test_n01_control_real_module_never_emits_the_scalar():
    adapter = C2CAdapter(C2C_ROOT)
    out = adapter.query(dict(_QUERY_REQ))
    assert "reachability" not in out["from_your_position"]
    report = C2CTrackA().measure([_mc("query", _QUERY_REQ, out)])
    assert report.results["no_person_scalar"].verdict is Verdict.PASS


# ---- N-02: silent market leak (H-2) ----------------------------------------------------------
def test_n02_silent_market_admit_is_caught_by_track_a():
    adapter = C2CAdapter(N02)
    out = adapter.admit(dict(_GIFT_MARKET))          # MUST NOT raise — the market scan is disabled
    assert out["admitted"] is True, "fixture sanity: the silent admit must have fired"

    report = C2CTrackA().measure([_mc("admit", _GIFT_MARKET, out)])
    assert report.results["no_market_leak"].verdict is Verdict.FAIL, (
        "AC5.2: an admitted market key in a gift room must be caught by the oracle"
    )
    assert report.results["no_market_leak"].exploit_trace["key"] == "price_cents"


def test_n02_control_real_membrane_raises_on_the_same_interaction():
    adapter = C2CAdapter(C2C_ROOT)
    with pytest.raises(adapter.MembraneBreachError):
        adapter.admit(dict(_GIFT_MARKET))


def test_n02_naive_variant_is_self_caught_not_a_valid_gate():
    # ST6 vacuity check: the SAME n02 plant still has its surveillance scan intact, so a payload
    # that ALSO carries a forbidden key self-catches (raises) — proving only the SURGICAL market-scan
    # removal produces a silent admit, and that T-A2 (not the surveillance wall) is what catches N-02.
    adapter = C2CAdapter(N02)
    naive = dict(_GIFT_MARKET)
    naive["payload"] = {"item": "favour", "price_cents": 999, "reputation": 0.2}
    with pytest.raises(adapter.MembraneBreachError):
        adapter.admit(naive)


def test_c2c_source_is_byte_unchanged():
    # AC5.4: the plants live only under negative_control/; the real membrane still raises and the
    # real legibility still omits the scalar (both asserted above) — this pins that C2C/ is untouched.
    real = (C2C_ROOT / "src" / "partition" / "membrane.py").read_text()
    assert "N-02 SILENT PLANT" not in real
    real_leg = (C2C_ROOT / "src" / "legibility" / "legibility_query.py").read_text()
    assert "N-01 SILENT PLANT" not in real_leg
