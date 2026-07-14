"""Compuerta de regresión de conjunto dorado para el motor de aseguramiento.

El paquete de spec (tests.md, README, audit.md) promete "re-run golden-set on any
change (DVH-007/008)" — pero nada cargaba las fixtures, así que podían desviarse
del motor en silencio. Esto conecta workflows/.../evals/golden-set/*.json a pytest
para que un cambio que altere la salida del motor falle aquí.

Redactado por Mistral vía multi-model-orchestration; revisado por Claude (anclaje
de ruta a la raíz del repo corregido para igualar el idioma de las pruebas
hermanas). Solo stdlib + pytest.
"""
import importlib.util
import json
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_ENGINE = _ROOT / "src" / "assurance" / "aseguramiento.py"
_spec = importlib.util.spec_from_file_location("aseguramiento_golden", _ENGINE)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
resolver = _mod.resolver

_GOLDEN = _ROOT / "workflows" / "micorriza-politica" / "evals" / "golden-set"


def _load(name):
    return json.loads((_GOLDEN / name).read_text())


@pytest.mark.parametrize("name", ["test_A.json", "test_B.json"])
def test_golden_full_equality(name):
    data = _load(name)
    assert resolver(data["input"]) == data["expected"]


@pytest.mark.parametrize("campaign_key", ["campaign_1", "campaign_2"])
def test_golden_status_check(campaign_key):
    entry = _load("test_C_crosscampaign.json")[campaign_key]
    assert resolver(entry["input"])["estado"] == entry["expected_status"]


@pytest.mark.parametrize("reject_key", list(_load("test_C_crosscampaign.json")["rejected_inputs"]))
def test_golden_rejected_inputs(reject_key):
    bad = _load("test_C_crosscampaign.json")["rejected_inputs"][reject_key]
    with pytest.raises(ValueError):
        resolver(bad)
