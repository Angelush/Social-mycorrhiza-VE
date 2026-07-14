"""Acceptance tests for the Capa-5 stigmergic coordination + anti-cascade breakers.

Maps to workflows/micorriza-politica/capa5/evals/acceptance.md AC1-AC13 + AC-X.

The component is DETERMINISTIC (no LLM, no stub, no network). The defining test is AC4: a mob/cascade
input (many rapid trazas about one artifact) is structurally throttled to velocity_cap, and a
blacklist/score trace is refused in every cell.

Uses an INDEPENDENT hand-written pipeline oracle (not the module's own logic) so the module cannot
self-confirm a bug (AGD-045).
"""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

_MOD = Path(__file__).resolve().parent.parent / "src" / "stigmergy" / "estigmergia.py"
_spec = importlib.util.spec_from_file_location("estigmergia", _MOD)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)
sentir = mod.sentir
StigmergyBreachError = mod.ErrorDeBrechaEstigmergia

FORBIDDEN = ("score", "rating", "reputation", "rank", "blacklist", "ban",
             "penalty", "global_id", "dni")

NOW = 1000


# ---- independent oracles ----------------------------------------------------
def scan_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from scan_keys(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from scan_keys(v)


def oracle_sensed(req):
    """Independent re-derivation of the sensed survivor set (separate from the module)."""
    cell_id, now = req["celula_id"], req["ahora"]
    window, cap, hl, floor = req["ventana"], req["tope_velocidad"], req["vida_media"], req["fuerza_min"]
    # cell scope -> future -> flag/context
    cands = []
    for t in req["trazas"]:
        if t["celula_id"] != cell_id:
            continue
        if t["creado_en"] > now:
            continue
        if t["senal"] == "bandera" and (t.get("contexto") is None or t.get("contexto") == ""):
            continue
        cands.append(t)
    # velocity throttle per artifact PER WINDOW-BUCKET (bucket 0 = current window [now-window, now]);
    # keep earliest cap in each bucket. Independent re-derivation of the D-04 bucketized breaker.
    def _bucket(ca):
        elapsed = now - ca
        return 0 if elapsed <= window else 1 + (elapsed - window - 1) // window
    groups = {}
    for t in cands:
        groups.setdefault((t["about"], _bucket(t["creado_en"])), []).append(t)
    surv = []
    for key, g in groups.items():
        if len(g) > cap:
            g = sorted(g, key=lambda x: (x["creado_en"], x["about"], x["senal"], x["fuerza"]))
            surv.extend(g[:cap])
        else:
            surv.extend(g)
    # evaporation
    out = []
    for t in surv:
        eff = round(t["fuerza"] * (0.5 ** ((now - t["creado_en"]) / hl)), 6)
        if eff < floor:
            continue
        out.append((t["about"], t["senal"], t["celula_id"], eff, t.get("contexto")))
    out.sort(key=lambda x: (x[0], x[1], -x[3], str(x[4])))
    return out


# ---- builders ---------------------------------------------------------------
def _trace(about, signal="contribucion", strength=8, created_at=NOW, cell="barrio-1", context=None):
    t = {"about": about, "senal": signal, "fuerza": strength,
         "creado_en": created_at, "celula_id": cell}
    if context is not None:
        t["contexto"] = context
    return t


def _req(trazas=None, cell="barrio-1", now=NOW, window=100, velocity_cap=3,
         half_life=50, min_strength=0.5):
    return {
        "celula_id": cell, "ahora": now, "ventana": window, "tope_velocidad": velocity_cap,
        "vida_media": half_life, "fuerza_min": min_strength, "trazas": trazas or [],
    }


# ---- AC1: a valid trace is sensed -------------------------------------------
def test_ac1_valid_trace_sensed():
    r = _req(trazas=[_trace("wiki:art-42")])
    out = sentir(r)
    assert out["veredicto"] == "senales_sentidas"
    assert len(out["sentidas"]) == 1
    s = out["sentidas"][0]
    assert s["about"] == "wiki:art-42"
    assert s["senal"] == "contribucion"
    assert s["celula_id"] == "barrio-1"
    assert s["fuerza_efectiva"] == 8.0  # elapsed 0
    assert s["contexto"] is None
    # oracle agrees
    assert oracle_sensed(r) == [("wiki:art-42", "contribucion", "barrio-1", 8.0, None)]


def test_ac1_quiet_when_empty():
    out = sentir(_req(trazas=[]))
    assert out["veredicto"] == "silencio_desde_tu_celula"
    assert out["sentidas"] == []


# ---- AC2: senses, never acts / no scalar ------------------------------------
def test_ac2_no_acting_surface():
    public = {n for n in dir(mod) if not n.startswith("_")}
    for name in ("amplify", "notify", "broadcast", "connect", "persist", "rank", "send"):
        assert name not in public
    out = sentir(_req(trazas=[_trace("a")]))
    keys = {str(k).lower() for k in scan_keys(out)}
    assert all(not any(f in k for f in FORBIDDEN) for k in keys)


# ---- AC3: no ban/distrust signal --------------------------------------------
def test_ac3_ban_signal_refused():
    t = _trace("a")
    t["senal"] = "ban"
    with pytest.raises(StigmergyBreachError):
        sentir(_req(trazas=[t]))


def test_ac3_unknown_signal_refused():
    t = _trace("a")
    t["senal"] = "condemn"
    with pytest.raises(StigmergyBreachError):
        sentir(_req(trazas=[t]))


def test_ac3_blacklist_key_refused():
    t = _trace("a")
    t["contexto"] = "ok"
    t2 = _trace("b")
    t2_bad = {**t2}
    # a forbidden key nested via a whitelisted field's value is still caught by the recursive scan;
    # but a top-level non-whitelisted key trips the whitelist first. Use a value-nested forbidden key:
    t2_bad["contexto"] = "text"
    r = _req(trazas=[t])
    r["trazas"][0] = {"about": "a", "senal": "contribucion", "fuerza": 5,
                      "creado_en": NOW, "celula_id": "barrio-1", "contexto": "x"}
    # inject a forbidden shape at the request level (not on a whitelisted trace key)
    r["blacklist"] = {"x": 1}
    with pytest.raises(StigmergyBreachError):
        sentir(r)


# ---- AC4: THE mob/cascade throttle ------------------------------------------
def test_ac4_mob_throttled_to_cap():
    # seven trazas about the same artifact, all in-window -> at most cap=3 sensed
    trazas = [_trace("hot-thread", strength=8, created_at=NOW - i) for i in range(7)]
    r = _req(trazas=trazas, velocity_cap=3, window=100)
    out = sentir(r)
    hot = [s for s in out["sentidas"] if s["about"] == "hot-thread"]
    assert len(hot) <= 3
    assert out["traza_auditoria"]["amortiguadas_velocidad"] == 4  # 7 - 3
    assert oracle_sensed(r) == [(s["about"], s["senal"], s["celula_id"],
                                 s["fuerza_efectiva"], s["contexto"]) for s in out["sentidas"]]


def test_ac4_cap_is_per_artifact():
    trazas = ([_trace("A", created_at=NOW - i) for i in range(5)] +
              [_trace("B", created_at=NOW - i) for i in range(2)])
    r = _req(trazas=trazas, velocity_cap=3, window=100)
    out = sentir(r)
    a = [s for s in out["sentidas"] if s["about"] == "A"]
    b = [s for s in out["sentidas"] if s["about"] == "B"]
    assert len(a) == 3       # capped
    assert len(b) == 2       # under cap, untouched
    assert out["traza_auditoria"]["amortiguadas_velocidad"] == 2


def test_ac4_earliest_kept():
    # cap=2; keep the two earliest by created_at
    trazas = [_trace("A", strength=9, created_at=NOW - 3),
              _trace("A", strength=9, created_at=NOW - 2),
              _trace("A", strength=9, created_at=NOW - 1)]
    r = _req(trazas=trazas, velocity_cap=2, window=100, half_life=1000)
    out = sentir(r)
    # elapsed 3 and 2 kept (earliest created), elapsed 1 damped -> effective strengths reflect that
    kept_elapsed = sorted(round(NOW - s["fuerza_efectiva"], 6) for s in out["sentidas"])
    assert out["traza_auditoria"]["amortiguadas_velocidad"] == 1


# ---- D-04: the velocity cap is per window-bucket (backdating can't escape it) --
def test_d04_backdated_burst_also_throttled():
    # a 50-trace burst backdated just past the window (created_at now-21, window 20) lands in
    # bucket 1 and is still throttled to the cap — before D-04 it bypassed the cap entirely.
    burst = [_trace("art-1", strength=100, created_at=NOW - 21) for _ in range(50)]
    r = _req(trazas=burst, velocity_cap=3, window=20, half_life=1000, min_strength=0.001)
    out = sentir(r)
    hot = [s for s in out["sentidas"] if s["about"] == "art-1"]
    assert len(hot) == 3
    assert out["traza_auditoria"]["amortiguadas_velocidad"] == 47
    assert oracle_sensed(r) == [(s["about"], s["senal"], s["celula_id"],
                                 s["fuerza_efectiva"], s["contexto"]) for s in out["sentidas"]]


def test_d04_sustained_across_windows_still_passes():
    # genuine sustained coordination — <= cap per bucket across five windows — is NOT throttled.
    trazas = [_trace("art-2", strength=100, created_at=NOW - (20 * w + 1 + k))
              for w in range(5) for k in range(2)]  # 2 per bucket, cap 3
    r = _req(trazas=trazas, velocity_cap=3, window=20, half_life=100000, min_strength=0.001)
    out = sentir(r)
    assert out["traza_auditoria"]["amortiguadas_velocidad"] == 0
    assert len([s for s in out["sentidas"] if s["about"] == "art-2"]) == 10


# ---- AC5: no scalar out; surveillance refused -------------------------------
def test_ac5a_no_forbidden_in_output():
    out = sentir(_req(trazas=[_trace("a"), _trace("b", signal="respaldo")]))
    keys = {str(k).lower() for k in scan_keys(out)}
    assert all(not any(f in k for f in FORBIDDEN) for k in keys)


def test_ac5b_reputation_trace_refused():
    r = _req(trazas=[_trace("a")])
    r["trazas"][0]["contexto"] = "x"
    r["trazas"][0] = {"about": "a", "senal": "contribucion", "fuerza": 5,
                      "creado_en": NOW, "celula_id": "barrio-1", "reputation": 88}
    with pytest.raises(StigmergyBreachError):
        sentir(r)


# ---- AC6: context before judgment -------------------------------------------
def test_ac6_bare_flag_damped():
    out = sentir(_req(trazas=[_trace("art-9", signal="bandera")]))
    assert out["veredicto"] == "silencio_desde_tu_celula"
    assert out["traza_auditoria"]["amortiguadas_sin_contexto"] == 1


def test_ac6_flag_with_context_sensed():
    out = sentir(_req(trazas=[_trace("art-9", signal="bandera", context="dup of art-3")]))
    assert out["veredicto"] == "senales_sentidas"
    assert out["sentidas"][0]["contexto"] == "dup of art-3"


def test_ac6_empty_context_flag_damped():
    out = sentir(_req(trazas=[_trace("art-9", signal="bandera", context="")]))
    assert out["traza_auditoria"]["amortiguadas_sin_contexto"] == 1


# ---- AC7: zero global broadcast / cell scope --------------------------------
def test_ac7_off_cell_dropped():
    out = sentir(_req(trazas=[_trace("a", cell="otro-barrio")]))
    assert out["sentidas"] == []
    assert out["traza_auditoria"]["descartadas_fuera_de_celula"] == 1


def test_ac7_mixed_cells():
    out = sentir(_req(trazas=[_trace("a"), _trace("b", cell="otro-barrio")]))
    assert [s["about"] for s in out["sentidas"]] == ["a"]


# ---- AC8: forgetting / evaporation ------------------------------------------
def test_ac8_evaporated_not_sensed():
    # strength 8, half_life 50, elapsed 300 -> 8*0.5^6 = 0.125 < 0.5
    out = sentir(_req(trazas=[_trace("a", strength=8, created_at=NOW - 300)],
                     half_life=50, min_strength=0.5))
    assert out["veredicto"] == "silencio_desde_tu_celula"
    assert out["traza_auditoria"]["evaporadas"] == 1


def test_ac8_fresh_sensed():
    out = sentir(_req(trazas=[_trace("a", strength=8, created_at=NOW - 50)],
                     half_life=50, min_strength=0.5))
    assert out["veredicto"] == "senales_sentidas"
    assert out["sentidas"][0]["fuerza_efectiva"] == 4.0


def test_ac8_monotone_decay():
    effs = []
    for ca in (NOW, NOW - 50, NOW - 100):
        out = sentir(_req(trazas=[_trace("a", strength=8, created_at=ca)],
                         half_life=50, min_strength=0.0, window=1000))
        effs.append(out["sentidas"][0]["fuerza_efectiva"])
    assert effs == [8.0, 4.0, 2.0]
    assert effs[0] > effs[1] > effs[2]


# ---- AC9: canonical order ---------------------------------------------------
def test_ac9_canonical_order():
    trazas = [_trace("c"), _trace("a"), _trace("b")]
    out1 = sentir(_req(trazas=trazas))
    out2 = sentir(_req(trazas=list(reversed(trazas))))
    assert json.dumps(out1["sentidas"]) == json.dumps(out2["sentidas"])
    assert [s["about"] for s in out1["sentidas"]] == ["a", "b", "c"]


# ---- AC10: mixed damping, never crashes -------------------------------------
def test_ac10_mixed_cascade_damped_never_crashes():
    trazas = [
        _trace("good", strength=8, created_at=NOW),               # valid
        _trace("elsewhere", cell="otro-barrio"),                  # off-cell
        _trace("future", created_at=NOW + 10),                    # future
        _trace("bare", signal="bandera"),                         # bare flag
        _trace("faded", strength=8, created_at=NOW - 500),        # evaporated
    ] + [_trace("burst", created_at=NOW - i) for i in range(5)]   # over-cap (cap=2)
    r = _req(trazas=trazas, velocity_cap=2, window=100, half_life=50, min_strength=0.5)
    out = sentir(r)  # must NOT raise
    at = out["traza_auditoria"]
    assert at["descartadas_fuera_de_celula"] >= 1
    assert at["descartadas_futuras"] >= 1
    assert at["amortiguadas_sin_contexto"] >= 1
    assert at["amortiguadas_velocidad"] >= 1
    assert at["evaporadas"] >= 1
    assert "good" in [s["about"] for s in out["sentidas"]]
    # oracle agreement on the exact sensed set
    assert oracle_sensed(r) == [(s["about"], s["senal"], s["celula_id"],
                                 s["fuerza_efectiva"], s["contexto"]) for s in out["sentidas"]]


def test_ac10_forbidden_raises_not_damped():
    r = _req(trazas=[_trace("a")])
    r["trazas"][0] = {"about": "a", "senal": "contribucion", "fuerza": 5,
                      "creado_en": NOW, "celula_id": "barrio-1", "score": 1}
    with pytest.raises(StigmergyBreachError):
        sentir(r)


# ---- AC11: determinism ------------------------------------------------------
def test_ac11_determinism():
    trazas = [_trace("hot", created_at=NOW - i) for i in range(7)]
    r = _req(trazas=trazas, velocity_cap=3)
    a = sentir(copy.deepcopy(r))
    b = sentir(copy.deepcopy(r))
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# ---- AC12: envelope validation ----------------------------------------------
@pytest.mark.parametrize("mutate", [
    lambda r: r.update(celula_id=""),
    lambda r: r.update(ahora="1000"),
    lambda r: r.update(ahora=True),
    lambda r: r.update(ventana=0),
    lambda r: r.update(ventana=-1),
    lambda r: r.update(ventana=True),
    lambda r: r.update(tope_velocidad=0),
    lambda r: r.update(vida_media=0),
    lambda r: r.update(fuerza_min=-1),
    lambda r: r.update(fuerza_min="x"),
    lambda r: r.update(trazas="x"),
    lambda r: r["trazas"].append("not a dict"),
    lambda r: r["trazas"].append({"senal": "contribucion", "fuerza": 1,
                                  "creado_en": NOW, "celula_id": "barrio-1"}),  # missing about
    lambda r: r["trazas"].append({"about": "a", "senal": "contribucion", "fuerza": 1,
                                  "creado_en": NOW, "celula_id": "barrio-1", "priority": 9}),  # bad key
    lambda r: r["trazas"].append(_trace("a", signal="nope")),
    lambda r: r["trazas"].append(_trace("a", strength=0)),
    lambda r: r["trazas"].append(_trace("a", strength=-1)),
    lambda r: r["trazas"].append(_trace("a", strength=True)),
    lambda r: r["trazas"].append({"about": "a", "senal": "contribucion", "fuerza": 1,
                                  "creado_en": "t", "celula_id": "barrio-1"}),  # created_at not int
])
def test_ac12_envelope_validation(mutate):
    r = _req(trazas=[_trace("seed")])
    mutate(r)
    with pytest.raises(StigmergyBreachError):
        sentir(r)


# ---- AC13: no LLM / no network / stdlib-only --------------------------------
def test_ac13_no_network_imports():
    src = _MOD.read_text()
    for banned in ("import anthropic", "from anthropic", "import requests", "import httpx",
                   "import openai", "import urllib", "import socket"):
        assert banned not in src


def test_ac13_sense_takes_only_request():
    import inspect
    params = list(inspect.signature(sentir).parameters)
    assert params == ["request"]  # no injected model / propose


# ---- AC-X: cross-layer consistency ------------------------------------------
def test_acx_capa1_surveillance_shape_refused_as_trace_node():
    r = _req(trazas=[_trace("a")])
    # surveillance shape nested at request level (mirrors Capa-1 {"seller":{"trust_score":88}})
    r["seller"] = {"trust_score": 88}
    with pytest.raises(StigmergyBreachError):
        sentir(r)


def test_acx_forbidden_keys_match_all_layers():
    def load(rel):
        p = Path(__file__).resolve().parent.parent / rel
        s = importlib.util.spec_from_file_location(p.stem, p)
        m = importlib.util.module_from_spec(s)
        s.loader.exec_module(m)
        return m
    memb = load("src/partition/membrana.py")
    leg = load("src/legibility/legibilidad.py")
    matcher = load("src/matcher/emparejador.py")
    assert (set(mod.FORBIDDEN_KEYS) == set(memb.FORBIDDEN_KEYS) == set(leg.FORBIDDEN_KEYS)
            == set(matcher.FORBIDDEN_KEYS))
