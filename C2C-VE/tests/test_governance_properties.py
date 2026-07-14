"""Pruebas basadas en propiedades (hypothesis) para la gobernanza sociocrática de la Capa 6.

Corresponde a workflows/micorriza-politica/capa6/evals/tests.md P1-P7. Determinista y sin conexión.
Las propiedades afirman que los muros estructurales se sostienen para CUALQUIER entrada: el veredicto
es invariante a la reputación (no representable), una sola objeción primordial SIEMPRE bloquea sin
importar cuántos consientan, una entrada ponderada / duplicada / con forma de vigilancia SIEMPRE se
rechaza, ningún token de objetor emerge jamás, y la función nunca falla ante contenido delimitado.
"""
import importlib.util
from pathlib import Path

from hypothesis import given, settings, strategies as st

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


def walk_values(o):
    if isinstance(o, dict):
        for v in o.values():
            yield from walk_values(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk_values(v)
    else:
        yield o


def _req(posturas, circle="c1"):
    return {"circulo_id": circle, "propuesta_id": "p1", "ahora": NOW,
            "expira_en": SOON, "posturas": posturas}


tokens = st.text(alphabet="abcdefghijk", min_size=1, max_size=5)


@st.composite
def consent_disp(draw, token):
    return {"ficha": token, "postura": draw(st.sampled_from(["consentir", "abstenerse"])),
            "circulo_id": "c1"}


def _unique_tokens(n):
    return ["tok%d" % i for i in range(n)]


# P1/P2 — una sola objeción primordial SIEMPRE bloquea, sin importar cuántos consientan
@settings(max_examples=200)
@given(st.integers(min_value=0, max_value=20))
def test_p2_one_paramount_always_blocks(n_consent):
    disps = [{"ficha": t, "postura": "consentir", "circulo_id": "c1"}
             for t in _unique_tokens(n_consent)]
    disps.append({"ficha": "blocker", "postura": "objetar", "circulo_id": "c1",
                  "objecion": {"primordial": True, "razon": "r"}})
    out = decidir(_req(disps))
    assert out["veredicto"] == "revisar"


# P1 — el veredicto solo depende de la objeción primordial (sin vía de ponderación)
@settings(max_examples=150)
@given(st.lists(tokens, min_size=0, max_size=8, unique=True), st.booleans())
def test_p1_verdict_only_depends_on_paramount(toks, add_block):
    disps = [{"ficha": t, "postura": "consentir", "circulo_id": "c1"} for t in toks]
    if add_block:
        disps.append({"ficha": "zzz-block", "postura": "objetar", "circulo_id": "c1",
                      "objecion": {"primordial": True, "razon": "r"}})
    out = decidir(_req(disps))
    assert out["veredicto"] == ("revisar" if add_block else "adoptada")


# P3 — una clave de voz ponderada a cualquier profundidad siempre se rechaza
@settings(max_examples=100)
@given(st.integers(min_value=0, max_value=3), st.sampled_from(WEIGHT))
def test_p3_weight_always_refused(depth, key):
    node = {key: 3}
    for _ in range(depth):
        node = {"nest": node}
    r = _req([{"ficha": "t1", "postura": "consentir", "circulo_id": "c1"}])
    r["extra"] = node
    try:
        decidir(r)
        assert False, "debería rechazar la voz ponderada"
    except ErrorDeBrechaGobernanza:
        pass


# P4 — un token duplicado siempre se rechaza
@settings(max_examples=100)
@given(st.integers(min_value=2, max_value=6))
def test_p4_duplicate_token_refused(n):
    disps = [{"ficha": "same", "postura": "consentir", "circulo_id": "c1"} for _ in range(n)]
    try:
        decidir(_req(disps))
        assert False, "debería rechazar el token duplicado"
    except ErrorDeBrechaGobernanza:
        pass


# P5 — ningún token de objetor emerge jamás
@settings(max_examples=150)
@given(st.lists(tokens, min_size=1, max_size=8, unique=True))
def test_p5_no_objector_token_out(toks):
    disps = []
    for i, t in enumerate(toks):
        if i == 0:
            disps.append({"ficha": t, "postura": "objetar", "circulo_id": "c1",
                          "objecion": {"primordial": True, "razon": "razon-" + t}})
        else:
            disps.append({"ficha": t, "postura": "consentir", "circulo_id": "c1"})
    out = decidir(_req(disps))
    values = list(walk_values(out))
    for t in toks:
        assert t not in values  # los tokens nunca emergen; solo las razones


# P6 — la vigilancia se rechaza a cualquier profundidad
@settings(max_examples=100)
@given(st.integers(min_value=0, max_value=3), st.sampled_from(FORBIDDEN))
def test_p6_surveillance_refused_any_depth(depth, key):
    node = {key: 1}
    for _ in range(depth):
        node = {"nest": node}
    r = _req([{"ficha": "t1", "postura": "consentir", "circulo_id": "c1"}])
    r["extra"] = node
    try:
        decidir(r)
        assert False, "debería rechazar la forma de vigilancia"
    except ErrorDeBrechaGobernanza:
        pass


# P7 — nunca falla ante contenido delimitado (fuera de círculo / expirado), solo el envoltorio lanza
@settings(max_examples=150)
@given(st.lists(tokens, min_size=0, max_size=8, unique=True))
def test_p7_never_crashes_on_scoped_content(toks):
    disps = []
    for i, t in enumerate(toks):
        circle = "c1" if i % 2 == 0 else "c2"                 # algunas fuera de círculo
        exp = SOON if i % 3 else "2000-01-01T00:00:00Z"       # algunas expiradas
        disps.append({"ficha": t, "postura": "consentir", "circulo_id": circle,
                      "expira_en": exp})
    out = decidir(_req(disps))
    assert out["veredicto"] in ("adoptada", "revisar")
