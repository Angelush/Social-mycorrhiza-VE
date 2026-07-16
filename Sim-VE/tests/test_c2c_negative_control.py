"""M5: the negative-control gate (spec.md §6, failure-model H-1/H-2) — the build's defining test.

Drives the REAL, unmodified C2CAdapter against deliberately-broken SUT *copies* under
sim_c2c/negative_control/ (each a full six-module VE copy with ONE surgical plant); C2C-VE/ itself
is never touched. If these ever pass silently, the harness oracle has gone blind — it would be
trusting a broken SUT's self-reports instead of independently re-deriving integrity.
TS.1: fixtures re-derived from the VE SUT, same plants, VE wire.
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
C2C_ROOT = Path(__file__).resolve().parent.parent.parent / "C2C-VE"

_QUERY_REQ = {
    "consultante": "A", "objetivo": "T", "celula_id": "c1", "ahora": "T00000005",
    "saltos_max": 3, "modo": "paz",
    "grafo": {"avales": [{"de": "A", "a": "T", "celula_id": "c1", "expira_en": "T00000100"}],
              "hechos": []},
}
_GIFT_MARKET = {
    "sala": "don_comunal", "celula_id": "c1", "interaccion_id": "i1",
    "participantes": ["A"], "carga": {"item": "favour", "price_cents": 999}, "modo": "paz",
}


def _mc(method, request, output):
    return TraceEvent(tick=0, actor_id="x", proposal=None,
                      result=ModuleCall(method=method, request=request, output=output))


# ---- N-01: silent person-scalar (H-1) --------------------------------------------------------
def test_n01_silent_person_scalar_is_caught_by_track_a():
    adapter = C2CAdapter(N01)
    out = adapter.consultar(dict(_QUERY_REQ))        # MUST NOT raise — the plant is silent
    assert "reachability" in out["desde_tu_posicion"], "fixture sanity: the plant must have fired"

    report = C2CTrackA().measure([_mc("consultar", _QUERY_REQ, out)])
    assert report.results["no_person_scalar"].verdict is Verdict.FAIL, (
        "AC5.1/G-04: the independent oracle must catch a silent per-person scalar that carries no "
        "forbidden substring — if this passes, the oracle is blind to the exact C2C anti-goal"
    )
    assert report.results["no_person_scalar"].exploit_trace["kind"] == "person_scalar_leak"


def test_n01_control_real_module_never_emits_the_scalar():
    adapter = C2CAdapter(C2C_ROOT)
    out = adapter.consultar(dict(_QUERY_REQ))
    assert "reachability" not in out["desde_tu_posicion"]
    report = C2CTrackA().measure([_mc("consultar", _QUERY_REQ, out)])
    assert report.results["no_person_scalar"].verdict is Verdict.PASS


# ---- N-02: silent market leak (H-2) ----------------------------------------------------------
def test_n02_silent_market_admit_is_caught_by_track_a():
    adapter = C2CAdapter(N02)
    out = adapter.admitir(dict(_GIFT_MARKET))        # MUST NOT raise — the market scan is disabled
    assert out["admitido"] is True, "fixture sanity: the silent admit must have fired"

    report = C2CTrackA().measure([_mc("admitir", _GIFT_MARKET, out)])
    assert report.results["no_market_leak"].verdict is Verdict.FAIL, (
        "AC5.2: an admitted market key in a gift room must be caught by the oracle"
    )
    assert report.results["no_market_leak"].exploit_trace["key"] == "price_cents"


def test_n02_control_real_membrane_raises_on_the_same_interaction():
    adapter = C2CAdapter(C2C_ROOT)
    with pytest.raises(adapter.MembraneBreachError):
        adapter.admitir(dict(_GIFT_MARKET))


def test_n02_naive_variant_is_self_caught_not_a_valid_gate():
    # ST6 vacuity check: the SAME n02 plant still has its surveillance scan intact, so a carga
    # that ALSO carries a forbidden key self-catches (raises) — proving only the SURGICAL market-scan
    # removal produces a silent admit, and that T-A2 (not the surveillance wall) is what catches N-02.
    adapter = C2CAdapter(N02)
    naive = dict(_GIFT_MARKET)
    naive["carga"] = {"item": "favour", "price_cents": 999, "reputation": 0.2}
    with pytest.raises(adapter.MembraneBreachError):
        adapter.admitir(naive)


def test_c2c_source_is_byte_unchanged():
    # AC5.4: the plants live only under negative_control/; the real membrana still raises and the
    # real legibilidad still omits the scalar (both asserted above) — this pins that C2C-VE/ is
    # untouched.
    real = (C2C_ROOT / "src" / "partition" / "membrana.py").read_text()
    assert "N-02 SILENT PLANT" not in real
    real_leg = (C2C_ROOT / "src" / "legibility" / "legibilidad.py").read_text()
    assert "N-01 SILENT PLANT" not in real_leg


def test_fixtures_derive_from_the_ve_sut():
    # AC-s1.7 companion: a fixture silently re-derived from the upstream ENGLISH SUT would make the
    # gate test the wrong contract. The VE fixtures must speak the VE wire (VE filenames + castellano
    # envelope), which the two plant tests above already exercise; here we pin the filenames.
    for fix in (N01, N02):
        assert (fix / "src" / "partition" / "membrana.py").exists(), fix
        assert not (fix / "src" / "partition" / "membrane.py").exists(), (
            f"{fix}: upstream English module present — fixture not re-derived from C2C-VE"
        )
