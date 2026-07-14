"""Property-based tests (hypothesis) for the Capa-5 stigmergic breaker.

Maps to workflows/micorriza-politica/capa5/evals/tests.md P1-P7. Deterministic and offline.
The properties assert the structural walls hold for ANY input: no person-scalar out, a mob is
ALWAYS throttled below the cap, an evaporated/off-cell trace NEVER surfaces, the order is canonical,
and the breaker never crashes on cascade-shaped content (only the envelope raises).
"""
import importlib.util
from pathlib import Path

from hypothesis import given, settings, strategies as st

_MOD = Path(__file__).resolve().parent.parent / "src" / "stigmergy" / "estigmergia.py"
_spec = importlib.util.spec_from_file_location("estigmergia", _MOD)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)
sentir = mod.sentir
StigmergyBreachError = mod.ErrorDeBrechaEstigmergia

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


signals = st.sampled_from(["contribucion", "ruta", "respaldo", "presencia"])
abouts = st.sampled_from(["a", "b", "c", "d"])
cells = st.sampled_from(["barrio-1", "otro-barrio"])


@st.composite
def clean_trace(draw):
    return {
        "about": draw(abouts),
        "senal": draw(signals),
        "fuerza": draw(st.floats(min_value=0.01, max_value=1000,
                                   allow_nan=False, allow_infinity=False)),
        "creado_en": draw(st.integers(min_value=0, max_value=NOW)),
        "celula_id": draw(cells),
    }


def _req(trazas, cap=3, window=100, hl=50, floor=0.5):
    return {"celula_id": "barrio-1", "ahora": NOW, "ventana": window, "tope_velocidad": cap,
            "vida_media": hl, "fuerza_min": floor, "trazas": trazas}


# P1 — no scalar/forbidden key ever in output
@settings(max_examples=150)
@given(st.lists(clean_trace(), max_size=12))
def test_p1_no_forbidden_out(trazas):
    out = sentir(_req(trazas))
    keys = {str(k).lower() for k in scan_keys(out)}
    assert all(not any(f in k for f in FORBIDDEN) for k in keys)


# P2 — a mob is ALWAYS throttled: sensed count per artifact <= cap
@settings(max_examples=150)
@given(st.integers(min_value=1, max_value=6), st.integers(min_value=1, max_value=15))
def test_p2_mob_always_capped(cap, n):
    # n in-window trazas about ONE artifact, strong + slow decay so none evaporate
    trazas = [{"about": "hot", "senal": "contribucion", "fuerza": 1000,
               "creado_en": NOW - (i % 50), "celula_id": "barrio-1"} for i in range(n)]
    out = sentir(_req(trazas, cap=cap, window=100, hl=100000, floor=0.0))
    hot = [s for s in out["sentidas"] if s["about"] == "hot"]
    assert len(hot) <= cap


# P3 — an evaporated trace never surfaces
@settings(max_examples=150)
@given(clean_trace())
def test_p3_evaporated_never_surfaces(t):
    t["celula_id"] = "barrio-1"
    out = sentir(_req([t], hl=50, floor=0.5, window=100000))
    eff = round(t["fuerza"] * (0.5 ** ((NOW - t["creado_en"]) / 50)), 6)
    if eff < 0.5:
        assert all(s["about"] != t["about"] or s["fuerza_efectiva"] != eff
                   for s in out["sentidas"]) or out["sentidas"] == []


# P4 — an off-cell trace never surfaces
@settings(max_examples=150)
@given(st.lists(clean_trace(), max_size=12))
def test_p4_off_cell_never_surfaces(trazas):
    out = sentir(_req(trazas, hl=100000, floor=0.0, window=100000))
    for s in out["sentidas"]:
        assert s["celula_id"] == "barrio-1"


# P5 — surveillance refused at any depth
@settings(max_examples=100)
@given(st.integers(min_value=0, max_value=4), st.sampled_from(FORBIDDEN))
def test_p5_surveillance_refused_any_depth(depth, key):
    node = {key: 1}
    for _ in range(depth):
        node = {"nest": node}
    req = _req([{"about": "a", "senal": "contribucion", "fuerza": 5,
                 "creado_en": NOW, "celula_id": "barrio-1"}])
    req["extra"] = node  # forbidden key nested at random depth in a non-whitelisted request field
    try:
        sentir(req)
        assert False, "should have refused"
    except StigmergyBreachError:
        pass


# P6 — never crashes on cascade-shaped content (only envelope raises)
@settings(max_examples=150)
@given(st.lists(clean_trace(), max_size=15),
       st.integers(min_value=1, max_value=5),
       st.integers(min_value=1, max_value=200))
def test_p6_never_crashes_on_content(trazas, cap, window):
    # add future + off-cell + bare flag noise; none is an envelope breach
    trazas = trazas + [
        {"about": "f", "senal": "contribucion", "fuerza": 5,
         "creado_en": NOW + 5, "celula_id": "barrio-1"},
        {"about": "flg", "senal": "bandera", "fuerza": 5,
         "creado_en": NOW, "celula_id": "barrio-1"},
    ]
    out = sentir(_req(trazas, cap=cap, window=window))
    assert out["veredicto"] in ("senales_sentidas", "silencio_desde_tu_celula")


# P7 — order is canonical (permutation-invariant)
@settings(max_examples=150)
@given(st.lists(clean_trace(), min_size=1, max_size=10), st.integers(min_value=0, max_value=9))
def test_p7_order_canonical(trazas, rot):
    rot = rot % len(trazas)
    permuted = trazas[rot:] + trazas[:rot]
    a = sentir(_req(trazas, hl=100000, floor=0.0, window=100000))
    b = sentir(_req(permuted, hl=100000, floor=0.0, window=100000))
    assert a["sentidas"] == b["sentidas"]
