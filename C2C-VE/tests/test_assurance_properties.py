"""Pruebas basadas en propiedades para el motor de aseguramiento (no-pérdida,
conservación del bono, determinismo, forma anti-vigilancia) sobre campañas
generadas aleatoriamente.

Apunta a la cola de la distribución (AGD-016). Requiere `hypothesis`.
"""
import copy
import importlib.util
import json
from collections import Counter
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

_ENGINE = Path(__file__).resolve().parent.parent / "src" / "assurance" / "aseguramiento.py"
_spec = importlib.util.spec_from_file_location("aseguramiento_p", _ENGINE)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)
resolver = mod.resolver

FORBIDDEN = ("score", "rating", "reputation", "rank", "blacklist", "ban",
             "penalty", "global_id", "dni")
TOKENS = ["t1", "t2", "t3", "t4", "t5"]


@st.composite
def campanas(draw):
    tipo = draw(st.sampled_from(["binario", "monetario"]))
    n = draw(st.integers(min_value=0, max_value=12))
    compromisos = []
    for i in range(n):
        p = {"compromiso_id": f"p{i}", "ficha_participante": draw(st.sampled_from(TOKENS))}
        if tipo == "monetario":
            p["monto_centavos"] = draw(st.integers(min_value=0, max_value=100000))
        compromisos.append(p)
    # Un bono de garantía dominante solo es válido en una campaña monetaria; una
    # campaña binaria debe llevar bono 0 (membrana + anti-Sybil), así que no se genera.
    bono = draw(st.integers(min_value=0, max_value=99999)) if tipo == "monetario" else 0
    return {
        "campana_id": "c", "celula_id": "cell", "tipo": tipo,
        "umbral": draw(st.integers(min_value=1, max_value=8)),
        "bono_patrocinador_centavos": bono,
        "expira_en": "2026-12-31T00:00:00Z", "compromisos": compromisos,
    }


def _scan_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _scan_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _scan_keys(v)


@settings(max_examples=400)
@given(campanas())
def test_no_loss(camp):
    out = resolver(copy.deepcopy(camp))
    if out["estado"] != "reembolsa" or camp["tipo"] != "monetario":
        return
    sums = Counter()
    for p in camp["compromisos"]:
        sums[p["ficha_participante"]] += p["monto_centavos"]
    reembolsos = {r["ficha_participante"]: r["reembolso_centavos"]
                  for r in out["resolucion"]["reembolsos"]}
    for token, total in sums.items():
        assert reembolsos[token] == total  # nadie queda corto jamás


@settings(max_examples=400)
@given(campanas())
def test_bonus_conservation(camp):
    out = resolver(copy.deepcopy(camp))
    bonos = [r["bono_centavos"] for r in out["resolucion"]["reembolsos"]]
    if out["estado"] == "reembolsa" and out["comprometidos_distintos"] > 0:
        # el bono se reparte exactamente entre comprometidos; con cero comprometidos
        # no se distribuye (vuelve al patrocinador), así que la conservación solo
        # aplica cuando > 0.
        assert sum(bonos) == camp["bono_patrocinador_centavos"]
        assert max(bonos) - min(bonos) <= 1
    elif out["estado"] == "se_activa":
        assert bonos == []


@settings(max_examples=300)
@given(campanas())
def test_determinism(camp):
    a = resolver(copy.deepcopy(camp))
    b = resolver(copy.deepcopy(camp))
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


@settings(max_examples=300)
@given(campanas())
def test_no_surveillance_shape(camp):
    out = resolver(copy.deepcopy(camp))
    keys = {k.lower() for k in _scan_keys(out)}
    assert keys.isdisjoint(FORBIDDEN)


@settings(max_examples=300)
@given(campanas())
def test_threshold_rule(camp):
    out = resolver(copy.deepcopy(camp))
    distinct = len(set(p["ficha_participante"] for p in camp["compromisos"]))
    assert out["comprometidos_distintos"] == distinct
    assert out["estado"] == ("se_activa" if distinct >= camp["umbral"] else "reembolsa")
