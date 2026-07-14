"""Property-based tests (hypothesis) for the Capa-5 stigmergic breaker.

Maps to workflows/micorriza-politica/capa5/evals/tests.md P1-P7. Deterministic and offline.
The properties assert the structural walls hold for ANY input: no person-scalar out, a mob is
ALWAYS throttled below the cap, an evaporated/off-cell trace NEVER surfaces, the order is canonical,
and the breaker never crashes on cascade-shaped content (only the envelope raises).
"""
import importlib.util
from pathlib import Path

from hypothesis import given, settings, strategies as st

_MOD = Path(__file__).resolve().parent.parent / "src" / "stigmergy" / "stigmergy.py"
_spec = importlib.util.spec_from_file_location("stigmergy", _MOD)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)
sense = mod.sense
StigmergyBreachError = mod.StigmergyBreachError

FORBIDDEN = ("score", "rating", "reputation", "rank", "blacklist", "ban",
             "penalty", "global_id", "dni")
NOW = 1000


def scan_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from scan_keys(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from scan_keys(v)


signals = st.sampled_from(["contribution", "path", "endorsement", "presence"])
abouts = st.sampled_from(["a", "b", "c", "d"])
cells = st.sampled_from(["barrio-1", "otro-barrio"])


@st.composite
def clean_trace(draw):
    return {
        "about": draw(abouts),
        "signal": draw(signals),
        "strength": draw(st.floats(min_value=0.01, max_value=1000,
                                   allow_nan=False, allow_infinity=False)),
        "created_at": draw(st.integers(min_value=0, max_value=NOW)),
        "cell_id": draw(cells),
    }


def _req(traces, cap=3, window=100, hl=50, floor=0.5):
    return {"cell_id": "barrio-1", "now": NOW, "window": window, "velocity_cap": cap,
            "half_life": hl, "min_strength": floor, "traces": traces}


# P1 — no scalar/forbidden key ever in output
@settings(max_examples=150)
@given(st.lists(clean_trace(), max_size=12))
def test_p1_no_forbidden_out(traces):
    out = sense(_req(traces))
    keys = {str(k).lower() for k in scan_keys(out)}
    assert all(not any(f in k for f in FORBIDDEN) for k in keys)


# P2 — a mob is ALWAYS throttled: sensed count per artifact <= cap
@settings(max_examples=150)
@given(st.integers(min_value=1, max_value=6), st.integers(min_value=1, max_value=15))
def test_p2_mob_always_capped(cap, n):
    # n in-window traces about ONE artifact, strong + slow decay so none evaporate
    traces = [{"about": "hot", "signal": "contribution", "strength": 1000,
               "created_at": NOW - (i % 50), "cell_id": "barrio-1"} for i in range(n)]
    out = sense(_req(traces, cap=cap, window=100, hl=100000, floor=0.0))
    hot = [s for s in out["sensed"] if s["about"] == "hot"]
    assert len(hot) <= cap


# P3 — an evaporated trace never surfaces
@settings(max_examples=150)
@given(clean_trace())
def test_p3_evaporated_never_surfaces(t):
    t["cell_id"] = "barrio-1"
    out = sense(_req([t], hl=50, floor=0.5, window=100000))
    eff = round(t["strength"] * (0.5 ** ((NOW - t["created_at"]) / 50)), 6)
    if eff < 0.5:
        assert all(s["about"] != t["about"] or s["effective_strength"] != eff
                   for s in out["sensed"]) or out["sensed"] == []


# P4 — an off-cell trace never surfaces
@settings(max_examples=150)
@given(st.lists(clean_trace(), max_size=12))
def test_p4_off_cell_never_surfaces(traces):
    out = sense(_req(traces, hl=100000, floor=0.0, window=100000))
    for s in out["sensed"]:
        assert s["cell_id"] == "barrio-1"


# P5 — surveillance refused at any depth
@settings(max_examples=100)
@given(st.integers(min_value=0, max_value=4), st.sampled_from(FORBIDDEN))
def test_p5_surveillance_refused_any_depth(depth, key):
    node = {key: 1}
    for _ in range(depth):
        node = {"nest": node}
    req = _req([{"about": "a", "signal": "contribution", "strength": 5,
                 "created_at": NOW, "cell_id": "barrio-1"}])
    req["extra"] = node  # forbidden key nested at random depth in a non-whitelisted request field
    try:
        sense(req)
        assert False, "should have refused"
    except StigmergyBreachError:
        pass


# P6 — never crashes on cascade-shaped content (only envelope raises)
@settings(max_examples=150)
@given(st.lists(clean_trace(), max_size=15),
       st.integers(min_value=1, max_value=5),
       st.integers(min_value=1, max_value=200))
def test_p6_never_crashes_on_content(traces, cap, window):
    # add future + off-cell + bare flag noise; none is an envelope breach
    traces = traces + [
        {"about": "f", "signal": "contribution", "strength": 5,
         "created_at": NOW + 5, "cell_id": "barrio-1"},
        {"about": "flg", "signal": "flag", "strength": 5,
         "created_at": NOW, "cell_id": "barrio-1"},
    ]
    out = sense(_req(traces, cap=cap, window=window))
    assert out["verdict"] in ("signals_sensed", "quiet_from_your_cell")


# P7 — order is canonical (permutation-invariant)
@settings(max_examples=150)
@given(st.lists(clean_trace(), min_size=1, max_size=10), st.integers(min_value=0, max_value=9))
def test_p7_order_canonical(traces, rot):
    rot = rot % len(traces)
    permuted = traces[rot:] + traces[:rot]
    a = sense(_req(traces, hl=100000, floor=0.0, window=100000))
    b = sense(_req(permuted, hl=100000, floor=0.0, window=100000))
    assert a["sensed"] == b["sensed"]
