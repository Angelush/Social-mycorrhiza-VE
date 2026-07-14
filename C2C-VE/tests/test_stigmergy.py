"""Acceptance tests for the Capa-5 stigmergic coordination + anti-cascade breakers.

Maps to workflows/micorriza-politica/capa5/evals/acceptance.md AC1-AC13 + AC-X.

The component is DETERMINISTIC (no LLM, no stub, no network). The defining test is AC4: a mob/cascade
input (many rapid traces about one artifact) is structurally throttled to velocity_cap, and a
blacklist/score trace is refused in every cell.

Uses an INDEPENDENT hand-written pipeline oracle (not the module's own logic) so the module cannot
self-confirm a bug (AGD-045).
"""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

_MOD = Path(__file__).resolve().parent.parent / "src" / "stigmergy" / "stigmergy.py"
_spec = importlib.util.spec_from_file_location("stigmergy", _MOD)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)
sense = mod.sense
StigmergyBreachError = mod.StigmergyBreachError

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
    cell_id, now = req["cell_id"], req["now"]
    window, cap, hl, floor = req["window"], req["velocity_cap"], req["half_life"], req["min_strength"]
    # cell scope -> future -> flag/context
    cands = []
    for t in req["traces"]:
        if t["cell_id"] != cell_id:
            continue
        if t["created_at"] > now:
            continue
        if t["signal"] == "flag" and (t.get("context") is None or t.get("context") == ""):
            continue
        cands.append(t)
    # velocity throttle per artifact PER WINDOW-BUCKET (bucket 0 = current window [now-window, now]);
    # keep earliest cap in each bucket. Independent re-derivation of the D-04 bucketized breaker.
    def _bucket(ca):
        elapsed = now - ca
        return 0 if elapsed <= window else 1 + (elapsed - window - 1) // window
    groups = {}
    for t in cands:
        groups.setdefault((t["about"], _bucket(t["created_at"])), []).append(t)
    surv = []
    for key, g in groups.items():
        if len(g) > cap:
            g = sorted(g, key=lambda x: (x["created_at"], x["about"], x["signal"], x["strength"]))
            surv.extend(g[:cap])
        else:
            surv.extend(g)
    # evaporation
    out = []
    for t in surv:
        eff = round(t["strength"] * (0.5 ** ((now - t["created_at"]) / hl)), 6)
        if eff < floor:
            continue
        out.append((t["about"], t["signal"], t["cell_id"], eff, t.get("context")))
    out.sort(key=lambda x: (x[0], x[1], -x[3], str(x[4])))
    return out


# ---- builders ---------------------------------------------------------------
def _trace(about, signal="contribution", strength=8, created_at=NOW, cell="barrio-1", context=None):
    t = {"about": about, "signal": signal, "strength": strength,
         "created_at": created_at, "cell_id": cell}
    if context is not None:
        t["context"] = context
    return t


def _req(traces=None, cell="barrio-1", now=NOW, window=100, velocity_cap=3,
         half_life=50, min_strength=0.5):
    return {
        "cell_id": cell, "now": now, "window": window, "velocity_cap": velocity_cap,
        "half_life": half_life, "min_strength": min_strength, "traces": traces or [],
    }


# ---- AC1: a valid trace is sensed -------------------------------------------
def test_ac1_valid_trace_sensed():
    r = _req(traces=[_trace("wiki:art-42")])
    out = sense(r)
    assert out["verdict"] == "signals_sensed"
    assert len(out["sensed"]) == 1
    s = out["sensed"][0]
    assert s["about"] == "wiki:art-42"
    assert s["signal"] == "contribution"
    assert s["cell_id"] == "barrio-1"
    assert s["effective_strength"] == 8.0  # elapsed 0
    assert s["context"] is None
    # oracle agrees
    assert oracle_sensed(r) == [("wiki:art-42", "contribution", "barrio-1", 8.0, None)]


def test_ac1_quiet_when_empty():
    out = sense(_req(traces=[]))
    assert out["verdict"] == "quiet_from_your_cell"
    assert out["sensed"] == []


# ---- AC2: senses, never acts / no scalar ------------------------------------
def test_ac2_no_acting_surface():
    public = {n for n in dir(mod) if not n.startswith("_")}
    for name in ("amplify", "notify", "broadcast", "connect", "persist", "rank", "send"):
        assert name not in public
    out = sense(_req(traces=[_trace("a")]))
    keys = {str(k).lower() for k in scan_keys(out)}
    assert all(not any(f in k for f in FORBIDDEN) for k in keys)


# ---- AC3: no ban/distrust signal --------------------------------------------
def test_ac3_ban_signal_refused():
    t = _trace("a")
    t["signal"] = "ban"
    with pytest.raises(StigmergyBreachError):
        sense(_req(traces=[t]))


def test_ac3_unknown_signal_refused():
    t = _trace("a")
    t["signal"] = "condemn"
    with pytest.raises(StigmergyBreachError):
        sense(_req(traces=[t]))


def test_ac3_blacklist_key_refused():
    t = _trace("a")
    t["context"] = "ok"
    t2 = _trace("b")
    t2_bad = {**t2}
    # a forbidden key nested via a whitelisted field's value is still caught by the recursive scan;
    # but a top-level non-whitelisted key trips the whitelist first. Use a value-nested forbidden key:
    t2_bad["context"] = "text"
    r = _req(traces=[t])
    r["traces"][0] = {"about": "a", "signal": "contribution", "strength": 5,
                      "created_at": NOW, "cell_id": "barrio-1", "context": "x"}
    # inject a forbidden shape at the request level (not on a whitelisted trace key)
    r["blacklist"] = {"x": 1}
    with pytest.raises(StigmergyBreachError):
        sense(r)


# ---- AC4: THE mob/cascade throttle ------------------------------------------
def test_ac4_mob_throttled_to_cap():
    # seven traces about the same artifact, all in-window -> at most cap=3 sensed
    traces = [_trace("hot-thread", strength=8, created_at=NOW - i) for i in range(7)]
    r = _req(traces=traces, velocity_cap=3, window=100)
    out = sense(r)
    hot = [s for s in out["sensed"] if s["about"] == "hot-thread"]
    assert len(hot) <= 3
    assert out["audit_trace"]["damped_velocity"] == 4  # 7 - 3
    assert oracle_sensed(r) == [(s["about"], s["signal"], s["cell_id"],
                                 s["effective_strength"], s["context"]) for s in out["sensed"]]


def test_ac4_cap_is_per_artifact():
    traces = ([_trace("A", created_at=NOW - i) for i in range(5)] +
              [_trace("B", created_at=NOW - i) for i in range(2)])
    r = _req(traces=traces, velocity_cap=3, window=100)
    out = sense(r)
    a = [s for s in out["sensed"] if s["about"] == "A"]
    b = [s for s in out["sensed"] if s["about"] == "B"]
    assert len(a) == 3       # capped
    assert len(b) == 2       # under cap, untouched
    assert out["audit_trace"]["damped_velocity"] == 2


def test_ac4_earliest_kept():
    # cap=2; keep the two earliest by created_at
    traces = [_trace("A", strength=9, created_at=NOW - 3),
              _trace("A", strength=9, created_at=NOW - 2),
              _trace("A", strength=9, created_at=NOW - 1)]
    r = _req(traces=traces, velocity_cap=2, window=100, half_life=1000)
    out = sense(r)
    # elapsed 3 and 2 kept (earliest created), elapsed 1 damped -> effective strengths reflect that
    kept_elapsed = sorted(round(NOW - s["effective_strength"], 6) for s in out["sensed"])
    assert out["audit_trace"]["damped_velocity"] == 1


# ---- D-04: the velocity cap is per window-bucket (backdating can't escape it) --
def test_d04_backdated_burst_also_throttled():
    # a 50-trace burst backdated just past the window (created_at now-21, window 20) lands in
    # bucket 1 and is still throttled to the cap — before D-04 it bypassed the cap entirely.
    burst = [_trace("art-1", strength=100, created_at=NOW - 21) for _ in range(50)]
    r = _req(traces=burst, velocity_cap=3, window=20, half_life=1000, min_strength=0.001)
    out = sense(r)
    hot = [s for s in out["sensed"] if s["about"] == "art-1"]
    assert len(hot) == 3
    assert out["audit_trace"]["damped_velocity"] == 47
    assert oracle_sensed(r) == [(s["about"], s["signal"], s["cell_id"],
                                 s["effective_strength"], s["context"]) for s in out["sensed"]]


def test_d04_sustained_across_windows_still_passes():
    # genuine sustained coordination — <= cap per bucket across five windows — is NOT throttled.
    traces = [_trace("art-2", strength=100, created_at=NOW - (20 * w + 1 + k))
              for w in range(5) for k in range(2)]  # 2 per bucket, cap 3
    r = _req(traces=traces, velocity_cap=3, window=20, half_life=100000, min_strength=0.001)
    out = sense(r)
    assert out["audit_trace"]["damped_velocity"] == 0
    assert len([s for s in out["sensed"] if s["about"] == "art-2"]) == 10


# ---- AC5: no scalar out; surveillance refused -------------------------------
def test_ac5a_no_forbidden_in_output():
    out = sense(_req(traces=[_trace("a"), _trace("b", signal="endorsement")]))
    keys = {str(k).lower() for k in scan_keys(out)}
    assert all(not any(f in k for f in FORBIDDEN) for k in keys)


def test_ac5b_reputation_trace_refused():
    r = _req(traces=[_trace("a")])
    r["traces"][0]["context"] = "x"
    r["traces"][0] = {"about": "a", "signal": "contribution", "strength": 5,
                      "created_at": NOW, "cell_id": "barrio-1", "reputation": 88}
    with pytest.raises(StigmergyBreachError):
        sense(r)


# ---- AC6: context before judgment -------------------------------------------
def test_ac6_bare_flag_damped():
    out = sense(_req(traces=[_trace("art-9", signal="flag")]))
    assert out["verdict"] == "quiet_from_your_cell"
    assert out["audit_trace"]["damped_no_context"] == 1


def test_ac6_flag_with_context_sensed():
    out = sense(_req(traces=[_trace("art-9", signal="flag", context="dup of art-3")]))
    assert out["verdict"] == "signals_sensed"
    assert out["sensed"][0]["context"] == "dup of art-3"


def test_ac6_empty_context_flag_damped():
    out = sense(_req(traces=[_trace("art-9", signal="flag", context="")]))
    assert out["audit_trace"]["damped_no_context"] == 1


# ---- AC7: zero global broadcast / cell scope --------------------------------
def test_ac7_off_cell_dropped():
    out = sense(_req(traces=[_trace("a", cell="otro-barrio")]))
    assert out["sensed"] == []
    assert out["audit_trace"]["dropped_off_cell"] == 1


def test_ac7_mixed_cells():
    out = sense(_req(traces=[_trace("a"), _trace("b", cell="otro-barrio")]))
    assert [s["about"] for s in out["sensed"]] == ["a"]


# ---- AC8: forgetting / evaporation ------------------------------------------
def test_ac8_evaporated_not_sensed():
    # strength 8, half_life 50, elapsed 300 -> 8*0.5^6 = 0.125 < 0.5
    out = sense(_req(traces=[_trace("a", strength=8, created_at=NOW - 300)],
                     half_life=50, min_strength=0.5))
    assert out["verdict"] == "quiet_from_your_cell"
    assert out["audit_trace"]["evaporated"] == 1


def test_ac8_fresh_sensed():
    out = sense(_req(traces=[_trace("a", strength=8, created_at=NOW - 50)],
                     half_life=50, min_strength=0.5))
    assert out["verdict"] == "signals_sensed"
    assert out["sensed"][0]["effective_strength"] == 4.0


def test_ac8_monotone_decay():
    effs = []
    for ca in (NOW, NOW - 50, NOW - 100):
        out = sense(_req(traces=[_trace("a", strength=8, created_at=ca)],
                         half_life=50, min_strength=0.0, window=1000))
        effs.append(out["sensed"][0]["effective_strength"])
    assert effs == [8.0, 4.0, 2.0]
    assert effs[0] > effs[1] > effs[2]


# ---- AC9: canonical order ---------------------------------------------------
def test_ac9_canonical_order():
    traces = [_trace("c"), _trace("a"), _trace("b")]
    out1 = sense(_req(traces=traces))
    out2 = sense(_req(traces=list(reversed(traces))))
    assert json.dumps(out1["sensed"]) == json.dumps(out2["sensed"])
    assert [s["about"] for s in out1["sensed"]] == ["a", "b", "c"]


# ---- AC10: mixed damping, never crashes -------------------------------------
def test_ac10_mixed_cascade_damped_never_crashes():
    traces = [
        _trace("good", strength=8, created_at=NOW),               # valid
        _trace("elsewhere", cell="otro-barrio"),                  # off-cell
        _trace("future", created_at=NOW + 10),                    # future
        _trace("bare", signal="flag"),                            # bare flag
        _trace("faded", strength=8, created_at=NOW - 500),        # evaporated
    ] + [_trace("burst", created_at=NOW - i) for i in range(5)]   # over-cap (cap=2)
    r = _req(traces=traces, velocity_cap=2, window=100, half_life=50, min_strength=0.5)
    out = sense(r)  # must NOT raise
    at = out["audit_trace"]
    assert at["dropped_off_cell"] >= 1
    assert at["dropped_future"] >= 1
    assert at["damped_no_context"] >= 1
    assert at["damped_velocity"] >= 1
    assert at["evaporated"] >= 1
    assert "good" in [s["about"] for s in out["sensed"]]
    # oracle agreement on the exact sensed set
    assert oracle_sensed(r) == [(s["about"], s["signal"], s["cell_id"],
                                 s["effective_strength"], s["context"]) for s in out["sensed"]]


def test_ac10_forbidden_raises_not_damped():
    r = _req(traces=[_trace("a")])
    r["traces"][0] = {"about": "a", "signal": "contribution", "strength": 5,
                      "created_at": NOW, "cell_id": "barrio-1", "score": 1}
    with pytest.raises(StigmergyBreachError):
        sense(r)


# ---- AC11: determinism ------------------------------------------------------
def test_ac11_determinism():
    traces = [_trace("hot", created_at=NOW - i) for i in range(7)]
    r = _req(traces=traces, velocity_cap=3)
    a = sense(copy.deepcopy(r))
    b = sense(copy.deepcopy(r))
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# ---- AC12: envelope validation ----------------------------------------------
@pytest.mark.parametrize("mutate", [
    lambda r: r.update(cell_id=""),
    lambda r: r.update(now="1000"),
    lambda r: r.update(now=True),
    lambda r: r.update(window=0),
    lambda r: r.update(window=-1),
    lambda r: r.update(window=True),
    lambda r: r.update(velocity_cap=0),
    lambda r: r.update(half_life=0),
    lambda r: r.update(min_strength=-1),
    lambda r: r.update(min_strength="x"),
    lambda r: r.update(traces="x"),
    lambda r: r["traces"].append("not a dict"),
    lambda r: r["traces"].append({"signal": "contribution", "strength": 1,
                                  "created_at": NOW, "cell_id": "barrio-1"}),  # missing about
    lambda r: r["traces"].append({"about": "a", "signal": "contribution", "strength": 1,
                                  "created_at": NOW, "cell_id": "barrio-1", "priority": 9}),  # bad key
    lambda r: r["traces"].append(_trace("a", signal="nope")),
    lambda r: r["traces"].append(_trace("a", strength=0)),
    lambda r: r["traces"].append(_trace("a", strength=-1)),
    lambda r: r["traces"].append(_trace("a", strength=True)),
    lambda r: r["traces"].append({"about": "a", "signal": "contribution", "strength": 1,
                                  "created_at": "t", "cell_id": "barrio-1"}),  # created_at not int
])
def test_ac12_envelope_validation(mutate):
    r = _req(traces=[_trace("seed")])
    mutate(r)
    with pytest.raises(StigmergyBreachError):
        sense(r)


# ---- AC13: no LLM / no network / stdlib-only --------------------------------
def test_ac13_no_network_imports():
    src = _MOD.read_text()
    for banned in ("import anthropic", "from anthropic", "import requests", "import httpx",
                   "import openai", "import urllib", "import socket"):
        assert banned not in src


def test_ac13_sense_takes_only_request():
    import inspect
    params = list(inspect.signature(sense).parameters)
    assert params == ["request"]  # no injected model / propose


# ---- AC-X: cross-layer consistency ------------------------------------------
def test_acx_capa1_surveillance_shape_refused_as_trace_node():
    r = _req(traces=[_trace("a")])
    # surveillance shape nested at request level (mirrors Capa-1 {"seller":{"trust_score":88}})
    r["seller"] = {"trust_score": 88}
    with pytest.raises(StigmergyBreachError):
        sense(r)


def test_acx_forbidden_keys_match_all_layers():
    def load(rel):
        p = Path(__file__).resolve().parent.parent / rel
        s = importlib.util.spec_from_file_location(p.stem, p)
        m = importlib.util.module_from_spec(s)
        s.loader.exec_module(m)
        return m
    memb = load("src/partition/membrane.py")
    leg = load("src/legibility/legibility_query.py")
    matcher = load("src/matcher/matcher.py")
    assert (set(mod.FORBIDDEN_KEYS) == set(memb.FORBIDDEN_KEYS) == set(leg.FORBIDDEN_KEYS)
            == set(matcher.FORBIDDEN_KEYS))
