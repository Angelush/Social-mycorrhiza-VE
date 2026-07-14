"""Pruebas de aceptación para la gobernanza sociocrática de la Capa 6 (consentimiento, no consenso).

Corresponde a workflows/micorriza-politica/capa6/evals/acceptance.md AC1-AC12 + AC-X.

El componente es DETERMINISTA (sin LLM, sin stub, sin red). La prueba definitoria es AC1: la misma
propuesta en el mismo círculo produce el mismo veredicto sin importar la reputación que carguen los
miembros — una entrada ponderada/portadora de reputación se rechaza, y un-token-una-voz se sostiene.

Usa un oráculo de resolución INDEPENDIENTE escrito a mano (no la lógica propia del módulo) para que el
módulo no pueda autoconfirmar un error (AGD-045).
"""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

_MOD = Path(__file__).resolve().parent.parent / "src" / "governance" / "gobernanza.py"
_spec = importlib.util.spec_from_file_location("gobernanza", _MOD)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)
decidir = mod.decidir
ErrorDeBrechaGobernanza = mod.ErrorDeBrechaGobernanza

FORBIDDEN = ("score", "rating", "reputation", "rank", "blacklist", "ban",
             "penalty", "global_id", "dni")
WEIGHT = ("weight", "shares", "voting_power", "vote_count", "tally", "majority",
          "percent", "proxy", "seats", "quorum")

NOW = "2026-07-07T00:00:00Z"
SOON = "2026-08-01T00:00:00Z"
PAST = "2020-01-01T00:00:00Z"


# ---- oráculos independientes -------------------------------------------------
def scan_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from scan_keys(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from scan_keys(v)


def oracle_verdict(req):
    """Re-derivación independiente del veredicto + razones expuestas (separada del módulo)."""
    circle, now = req["circulo_id"], req["ahora"]
    paramount, concerns = [], []
    for d in req["posturas"]:
        if d["circulo_id"] != circle:
            continue
        exp = d.get("expira_en")
        if exp is not None and exp <= now:
            continue
        if d["postura"] == "objetar":
            obj = d["objecion"]
            if obj["primordial"]:
                paramount.append(obj["razon"])
            else:
                concerns.append(obj["razon"])
    verdict = "revisar" if paramount else "adoptada"
    return verdict, sorted(paramount), sorted(concerns)


# ---- constructores ------------------------------------------------------------
def _disp(token, postura="consentir", razon=None, primordial=None, circle="c1", expira_en=None):
    d = {"ficha": token, "postura": postura, "circulo_id": circle}
    if postura == "objetar":
        d["objecion"] = {"primordial": primordial, "razon": razon}
    if expira_en is not None:
        d["expira_en"] = expira_en
    return d


def _req(posturas=None, circle="c1", proposal="p1", now=NOW, expira_en=SOON):
    return {"circulo_id": circle, "propuesta_id": proposal, "ahora": now,
            "expira_en": expira_en, "posturas": posturas or []}


# ---- AC2 / A: el consentimiento adopta ----------------------------------------
def test_ac2_consent_adopts():
    r = _req([_disp("t1"), _disp("t2"), _disp("t3")])
    out = decidir(r)
    assert out["veredicto"] == "adoptada"
    assert out["objeciones_primordiales"] == []
    assert out["inquietudes"] == []
    assert out["expira_en"] == SOON
    assert oracle_verdict(r)[0] == "adoptada"


def test_ac2_empty_circle_adopts_vacuously():
    out = decidir(_req([]))
    assert out["veredicto"] == "adoptada"  # consentimiento vacuo (ST2)


# ---- AC4 / B: una sola objeción primordial bloquea ----------------------------
def test_ac4_single_paramount_blocks():
    disps = [_disp("t%d" % i) for i in range(5)]
    disps.append(_disp("tx", "objetar", razon="sin presupuesto hasta Q3", primordial=True))
    r = _req(disps)
    out = decidir(r)
    assert out["veredicto"] == "revisar"
    assert out["objeciones_primordiales"] == [{"razon": "sin presupuesto hasta Q3"}]
    v, p, c = oracle_verdict(r)
    assert v == "revisar" and p == ["sin presupuesto hasta Q3"]


def test_ac4_remove_objection_flips_to_adopted():
    disps = [_disp("t%d" % i) for i in range(5)]
    assert decidir(_req(disps))["veredicto"] == "adoptada"


def test_ac4_nonparamount_concern_does_not_block():
    r = _req([_disp("t1"), _disp("t2"),
              _disp("tc", "objetar", razon="prefiero una prueba", primordial=False)])
    out = decidir(r)
    assert out["veredicto"] == "adoptada"
    assert out["inquietudes"] == [{"razon": "prefiero una prueba"}]


# ---- AC1 / C: la voz es independiente de la reputación ------------------------
def test_ac1_weighted_voice_refused():
    for wk in ("weight", "shares", "voting_power", "vote_count", "proxy", "majority", "quorum"):
        d = _disp("t1")
        d[wk] = 10
        with pytest.raises(ErrorDeBrechaGobernanza):
            decidir(_req([d]))


def test_ac1_weight_nested_refused():
    d = _disp("tx", "objetar", razon="r", primordial=True)
    d["objecion"]["weight"] = 5
    with pytest.raises(ErrorDeBrechaGobernanza):
        decidir(_req([d]))


def test_ac1_verdict_invariant_to_token_labels():
    # una etiqueta "senior" es solo un token; no hay vía de ponderación, así que el veredicto no cambia
    r1 = _req([_disp("senior-elder"), _disp("newcomer"),
               _disp("tx", "objetar", razon="r", primordial=True)])
    r2 = _req([_disp("nobody-a"), _disp("nobody-b"),
               _disp("tx", "objetar", razon="r", primordial=True)])
    assert decidir(r1)["veredicto"] == decidir(r2)["veredicto"] == "revisar"


def test_ac8_one_token_one_voice_duplicate_refused():
    with pytest.raises(ErrorDeBrechaGobernanza):
        decidir(_req([_disp("t1"), _disp("t1")]))


# ---- AC2b / D: sin mayoría / sin recuento -------------------------------------
def test_ac2b_no_tally_number_in_output():
    disps = [_disp("t%d" % i) for i in range(5)]
    disps.append(_disp("tx", "objetar", razon="r", primordial=True))
    out = decidir(_req(disps))
    # el veredicto es una cadena categórica; ningún campo numérico de veredicto en el nivel superior
    assert isinstance(out["veredicto"], str)
    for k in ("percent", "majority", "tally", "for", "against", "approve_pct"):
        assert k not in out


# ---- AC3 / E: sin escalar-persona --------------------------------------------
def test_ac3_reputation_refused():
    d = _disp("tx", "objetar", razon="r", primordial=True)
    d["objecion"]["reputation"] = 5
    with pytest.raises(ErrorDeBrechaGobernanza):
        decidir(_req([d]))


def test_ac3_request_level_surveillance_refused():
    r = _req([_disp("t1")])
    r["member"] = {"trust_score": 88}
    with pytest.raises(ErrorDeBrechaGobernanza):
        decidir(r)


# ---- AC5 / F: una objeción es una pausa, nunca una marca ----------------------
def test_ac5_no_objector_token_in_output():
    r = _req([_disp("consenter"),
              _disp("objector-token", "objetar", razon="sin presupuesto", primordial=True)])
    out = decidir(r)
    all_values = list(scan_keys(out))
    # ningún token de objetor aparece en ningún lugar de la salida (claves o valores)
    def walk_values(o):
        if isinstance(o, dict):
            for v in o.values():
                yield from walk_values(v)
        elif isinstance(o, list):
            for v in o:
                yield from walk_values(v)
        else:
            yield o
    assert "objector-token" not in list(walk_values(out))
    assert "consenter" not in list(walk_values(out))


# ---- AC6 / G: local al círculo, sin auto-propagación --------------------------
def test_ac6_off_circle_dropped():
    r = _req([_disp("t1"),
              _disp("tx", "objetar", razon="r", primordial=True, circle="c2")])
    out = decidir(r)
    assert out["veredicto"] == "adoptada"  # la objeción de c2 no bloquea c1
    assert out["traza_auditoria"]["descartadas_fuera_de_circulo"] >= 1


def test_ac6_no_escalation_field():
    out = decidir(_req([_disp("t1")]))
    for k in ("parent", "escalate", "global", "propagate", "parent_circle"):
        assert k not in out


# ---- AC7 / H: el olvido -------------------------------------------------------
def test_ac7_expired_objection_dropped():
    r = _req([_disp("t1"),
              _disp("tx", "objetar", razon="r", primordial=True, expira_en=PAST)])
    out = decidir(r)
    assert out["veredicto"] == "adoptada"  # la objeción expirada ya no bloquea
    assert out["traza_auditoria"]["descartadas_expiradas"] >= 1


def test_ac7_fresh_objection_blocks_and_stamped():
    r = _req([_disp("t1"),
              _disp("tx", "objetar", razon="r", primordial=True, expira_en=SOON)])
    out = decidir(r)
    assert out["veredicto"] == "revisar"
    assert out["expira_en"] == SOON


# ---- D-03: un-token-una-voz es un invariante POR CÍRCULO -----------------------
def test_d03_off_circle_duplicate_token_does_not_block():
    # el mismo token consiente en c1 y reaparece en una postura fuera de círculo (c2); la entrada de
    # c2 se descarta, así que NO debe vetar la ronda de c1 (era un bloqueador/DoS antes de D-03).
    r = _req([_disp("alice"), _disp("bob"), _disp("alice", circle="c2")])
    out = decidir(r)
    assert out["veredicto"] == "adoptada"
    assert out["traza_auditoria"]["descartadas_fuera_de_circulo"] >= 1


def test_d03_expired_duplicate_token_does_not_block():
    r = _req([_disp("alice"), _disp("alice", expira_en=PAST)])  # dup expirado descartado, no fatal
    out = decidir(r)
    assert out["veredicto"] == "adoptada"
    assert out["traza_auditoria"]["descartadas_expiradas"] >= 1


def test_d03_in_circle_duplicate_still_refused():
    # el invariante aún muerde donde importa: dos voces vivas dentro del círculo, mismo token
    with pytest.raises(ErrorDeBrechaGobernanza):
        decidir(_req([_disp("alice"), _disp("alice")]))


# ---- AC9: determinismo + orden canónico ---------------------------------------
def test_ac9_determinism_and_canonical_order():
    disps = [_disp("t1", "objetar", razon="z-razon", primordial=True),
             _disp("t2", "objetar", razon="a-razon", primordial=True)]
    a = decidir(_req(disps))
    b = decidir(_req(list(reversed(disps))))
    assert a["objeciones_primordiales"] == [{"razon": "a-razon"}, {"razon": "z-razon"}]
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# ---- AC10: validación del envoltorio -------------------------------------------
@pytest.mark.parametrize("mutate", [
    lambda r: r.update(circulo_id=""),
    lambda r: r.pop("circulo_id"),
    lambda r: r.update(propuesta_id=""),
    lambda r: r.update(ahora=""),
    lambda r: r.update(expira_en=""),
    lambda r: r.update(posturas="x"),
    lambda r: r["posturas"].append("not a dict"),
    lambda r: r["posturas"].append({"ficha": "t", "postura": "consentir",
                                    "circulo_id": "c1", "priority": 1}),  # clave inválida
    lambda r: r["posturas"].append({"ficha": "t", "postura": "veto",
                                    "circulo_id": "c1"}),  # postura inválida
    lambda r: r["posturas"].append({"ficha": "t", "postura": "objetar",
                                    "circulo_id": "c1"}),  # objetar sin objecion
    lambda r: r["posturas"].append({"ficha": "t", "postura": "objetar", "circulo_id": "c1",
                                    "objecion": {"razon": "r"}}),  # sin primordial
    lambda r: r["posturas"].append({"ficha": "t", "postura": "objetar", "circulo_id": "c1",
                                    "objecion": {"primordial": True, "razon": ""}}),  # razón vacía
    lambda r: r["posturas"].append({"ficha": "t", "postura": "objetar", "circulo_id": "c1",
                                    "objecion": {"primordial": "yes", "razon": "r"}}),  # no bool
    lambda r: r["posturas"].append({"ficha": "t", "postura": "consentir", "circulo_id": "c1",
                                    "objecion": {"primordial": True, "razon": "r"}}),  # consentir+obj
    lambda r: r["posturas"].append({"ficha": "", "postura": "consentir", "circulo_id": "c1"}),
])
def test_ac10_envelope_validation(mutate):
    r = _req([_disp("seed")])
    mutate(r)
    with pytest.raises(ErrorDeBrechaGobernanza):
        decidir(r)


# ---- AC11: sin LLM / sin red / solo stdlib -------------------------------------
def test_ac11_no_network_imports():
    src = _MOD.read_text()
    for banned in ("import anthropic", "from anthropic", "import requests", "import httpx",
                   "import openai", "import urllib", "import socket"):
        assert banned not in src


def test_ac11_decide_takes_only_request():
    import inspect
    assert list(inspect.signature(decidir).parameters) == ["request"]


# ---- AC12: el bloqueador de mala fe se aplica como procedimiento, no juzgado ---
def test_ac12_spurious_paramount_still_blocks():
    r = _req([_disp("t1"), _disp("t2"),
              _disp("bad", "objetar", razon="simplemente no me gusta", primordial=True)])
    out = decidir(r)
    assert out["veredicto"] == "revisar"
    assert out["objeciones_primordiales"] == [{"razon": "simplemente no me gusta"}]


# ---- AC-X: consistencia entre capas --------------------------------------------
def test_acx_capa1_surveillance_shape_refused():
    r = _req([_disp("t1")])
    r["member"] = {"trust_score": 88}
    with pytest.raises(ErrorDeBrechaGobernanza):
        decidir(r)


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
    stig = load("src/stigmergy/estigmergia.py")
    assert (set(mod.FORBIDDEN_KEYS) == set(memb.FORBIDDEN_KEYS) == set(leg.FORBIDDEN_KEYS)
            == set(matcher.FORBIDDEN_KEYS) == set(stig.FORBIDDEN_KEYS))
