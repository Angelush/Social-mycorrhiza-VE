"""M6: property-based (P-C1..P-C4) + golden regression (G-C1) tests for Sim-C2C, via hypothesis.

These exercise invariants that must hold across ALL inputs, not just the seeds in the fixtures:
the matcher wrapper is uncrashable by any model output, forgetting is monotone in `now`, the
anti-cascade throttle bounds any burst, and campaigns are byte-reproducible across seeds.
"""
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from sim_c2c.adapter import C2CAdapter
from sim_c2c.campaign import build_campaign, default_config
from sim_c2c.track_a import _window_bucket

C2C_ROOT = Path(__file__).resolve().parent.parent.parent / "C2C-VE"
_ADAPTER = C2CAdapter(C2C_ROOT)


# P-C1: the matcher guardrail is UNCRASHABLE by any model output — a valid request never raises,
# whatever garbage the injected proposer returns (the prompt-injection wall, invariant 8).
@given(model_out=st.lists(st.one_of(
    st.none(), st.integers(), st.text(),
    st.dictionaries(st.text(min_size=1, max_size=8), st.text(max_size=8), max_size=4),
), max_size=6))
@settings(max_examples=60, deadline=None)
def test_pc1_matcher_uncrashable_by_any_model_output(model_out):
    req = {
        "consultante": "a", "celulas_ids": ["c1"], "ahora": "T1", "expira_en": "T9",
        "propuestas_max": 5, "propio": {"necesidades": ["bread"]},
        "candidatos": [{"ficha": "b", "celula_id": "c1", "ofertas": ["bread"],
                        "consentimiento": {"mostrable": True}}],
        "modo": "paz",
    }
    out = _ADAPTER.emparejar(req, lambda ctx: model_out)  # must never raise
    for p in out["propuestas"]:
        assert set(p.keys()) == {"ficha", "celula_id", "tipo", "razon", "hechos_citados", "expira_en"}


# P-C2: forgetting is monotone — a fact unexpired at a later `now` is also unexpired earlier; an
# expired fact never resurfaces as `now` advances past its expiry.
@given(expiry=st.integers(min_value=1, max_value=20), now=st.integers(min_value=0, max_value=25))
@settings(max_examples=60, deadline=None)
def test_pc2_forgetting_is_monotone_in_now(expiry, now):
    req = {
        "consultante": "a", "objetivo": "b", "celula_id": "c1", "ahora": "T%02d" % now,
        "saltos_max": 3, "modo": "paz",
        "grafo": {"avales": [],
                  "hechos": [{"sobre": "b", "afirmacion": "s", "celula_id": "c1",
                              "expira_en": "T%02d" % expiry}]},
    }
    out = _ADAPTER.consultar(req)
    surfaced = len(out["desde_tu_posicion"]["hechos"]) > 0
    # unexpired iff expira_en > ahora (lexicographic == numeric here, fixed width)
    assert surfaced == (("T%02d" % expiry) > ("T%02d" % now))


# P-C3: the anti-cascade throttle bounds ANY burst — sensed count per artifact never exceeds the
# velocity cap per window bucket, and Track A agrees a burst was throttled.
@given(burst=st.integers(min_value=1, max_value=12), cap=st.integers(min_value=1, max_value=5))
@settings(max_examples=60, deadline=None)
def test_pc3_velocity_cap_bounds_any_burst(burst, cap):
    now = 100
    traces = [{"about": "art", "senal": "contribucion", "fuerza": 1.0,
               "creado_en": now, "celula_id": "c1"} for _ in range(burst)]
    req = {"celula_id": "c1", "ahora": now, "ventana": 5, "tope_velocidad": cap,
           "vida_media": 4, "fuerza_min": 0.0, "trazas": traces, "modo": "paz"}
    out = _ADAPTER.sentir(req)
    sensed_for_art = sum(1 for s in out["sentidas"] if s["about"] == "art")
    assert sensed_for_art <= cap
    if burst > cap:
        assert out["traza_auditoria"]["amortiguadas_velocidad"] == burst - cap


# P-C4: campaigns are byte-reproducible for any seed.
@given(seed=st.integers(min_value=0, max_value=999))
@settings(max_examples=8, deadline=None)
def test_pc4_campaign_reproducible_for_any_seed(seed):
    a = build_campaign(default_config(seed=seed, T=12), C2C_ROOT, max_rounds=2)
    b = build_campaign(default_config(seed=seed, T=12), C2C_ROOT, max_rounds=2)
    assert a.history == b.history


# G-C1: golden regression — a pinned campaign stays clean and unhalted with a stable shape.
def test_gc1_golden_campaign_shape():
    result = build_campaign(default_config(seed=7), C2C_ROOT, max_rounds=3)
    assert not result.halted
    assert len(result.history) == 3
    metrics = set(result.history[0].welfare_report.metrics)
    assert metrics == {"reachability_of_cooperation", "vouch_graph_diversity",
                       "cascade_damping_ratio", "bootstrapping_cost"}
    assert set(result.history[0].integrity_report.results) == {
        "no_person_scalar", "no_market_leak", "asker_relative",
        "forgetting", "consent_privacy", "anti_cascade"}


def test_window_bucket_matches_stigmergy_definition():
    # sanity on Track A's replicated bucket math vs the module's own comment (D-04).
    assert _window_bucket(100, 100, 5) == 0
    assert _window_bucket(96, 100, 5) == 0     # elapsed 4 <= window 5 -> current bucket
    assert _window_bucket(94, 100, 5) == 1     # elapsed 6 -> next bucket
