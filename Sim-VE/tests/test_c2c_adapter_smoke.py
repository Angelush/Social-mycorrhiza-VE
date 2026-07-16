"""M1: C2CAdapter — thin 1:1 wrapper over the real six Capa VE modules (AC1.1–AC1.4).

Drives the REAL C2C-VE code (never mocked; the only stub allowed anywhere in Sim-C2C is the
injected matcher `proponer`). Confirms each method forwards verbatim: real returns come
back unchanged, and the real modules' own raises propagate untouched through the adapter.
TS.1: envelopes speak the VE wire (castellano keys, `modo`, `moneda` in Capa 4).
"""
from pathlib import Path

import pytest

from engine.sut_adapter import SUTIntegrityError, compute_pin
from sim_c2c.adapter import C2CAdapter

C2C_ROOT = Path(__file__).resolve().parent.parent.parent / "C2C-VE"


@pytest.fixture
def adapter():
    return C2CAdapter(C2C_ROOT)


def test_pin_in_fork_monorepo(adapter):
    # AC1.1: content_hash is the real pin. In this fork the C2C-VE tree lives inside
    # the fork's monorepo, so the supplementary git_commit resolves to its HEAD.
    assert isinstance(adapter.pin.content_hash, str) and len(adapter.pin.content_hash) == 64
    assert len(adapter.pin.source_paths) == 6
    assert adapter.pin.git_commit is not None and len(adapter.pin.git_commit) == 40


def test_pin_points_at_ve_tree(adapter):
    # AC-s1.6: the pin fixes files inside C2C-VE/ — if someone re-points the adapter at the
    # upstream C2C/ tree, this says so.
    for p in adapter.pin.source_paths:
        assert f"{Path(p).parts[-4]}" == "C2C-VE", p


def test_pin_git_commit_none_outside_any_repo(tmp_path):
    # The graceful-None property the original (pre-fork) test pinned: with no
    # enclosing repo, git_commit is None — never an error. content_hash still computes.
    src = tmp_path / "module.py"
    src.write_text("X = 1\n")
    pin = compute_pin([src], repo_dir=tmp_path)
    assert pin.git_commit is None
    assert len(pin.content_hash) == 64


def test_assert_pinned_passes_when_unchanged(adapter):
    adapter.assert_pinned()  # must not raise


def test_assert_pinned_fails_if_a_source_byte_changes(adapter, tmp_path):
    # AC1.3: copy the real tree, pin, mutate one byte, expect SUTIntegrityError.
    import shutil

    dst = tmp_path / "C2C-VE"
    shutil.copytree(C2C_ROOT, dst)
    a = C2CAdapter(dst)
    a.assert_pinned()
    membrana = dst / "src" / "partition" / "membrana.py"
    membrana.write_text(membrana.read_text() + "\n# mutated\n")
    with pytest.raises(SUTIntegrityError):
        a.assert_pinned()


def test_admitir_passthrough_and_raise(adapter):
    # AC1.2/AC1.4: a clean gift interaction returns admitido=True; a market key raises verbatim.
    ok = adapter.admitir({
        "sala": "don_comunal", "celula_id": "c1", "interaccion_id": "i1",
        "participantes": ["a", "b"], "carga": {"gift": "bread"}, "modo": "paz",
    })
    assert ok["admitido"] is True
    with pytest.raises(adapter.MembraneBreachError):
        adapter.admitir({
            "sala": "don_comunal", "celula_id": "c1", "interaccion_id": "i2",
            "participantes": ["a"], "carga": {"price_cents": 500}, "modo": "paz",
        })


def test_admitir_modo_invalido_raises_through_adapter(adapter):
    # AC-s1.2 (half of it): the `modo` key reaches the wire — an invalid value is rejected by
    # the REAL module through the adapter, verbatim as ErrorDeBrechaMembrana.
    with pytest.raises(adapter.MembraneBreachError, match="modo"):
        adapter.admitir({
            "sala": "don_comunal", "celula_id": "c1", "interaccion_id": "i3",
            "participantes": ["a"], "carga": {"gift": "bread"}, "modo": "guerra_total",
        })


def test_consultar_passthrough_neutral_verdict(adapter):
    out = adapter.consultar({
        "consultante": "a", "objetivo": "z", "celula_id": "c1", "ahora": "2026-01-01",
        "saltos_max": 3, "grafo": {"avales": [], "hechos": []}, "modo": "paz",
    })
    assert out["veredicto"] == "sin_informacion_desde_tu_posicion"
    with pytest.raises(adapter.LegibilityBreachError):
        adapter.consultar({"consultante": "", "objetivo": "z", "celula_id": "c1", "ahora": "n",
                           "saltos_max": 3, "grafo": {"avales": [], "hechos": []}, "modo": "paz"})


def test_emparejar_never_raises_on_bad_model_output(adapter):
    # AC1.4: bad model output is dropped-and-counted, NEVER raised — the guardrail must not be
    # crashable by a prompt-injected model. A malformed REQUEST does raise.
    req = {
        "consultante": "a", "celulas_ids": ["c1"], "ahora": "2026-01-01",
        "expira_en": "2026-02-01", "propuestas_max": 5,
        "propio": {"necesidades": ["bread"]},
        "candidatos": [{"ficha": "b", "celula_id": "c1", "ofertas": ["bread"],
                        "consentimiento": {"mostrable": True}}],
        "modo": "paz",
    }
    out = adapter.emparejar(req, lambda ctx: [{"garbage": True}, "not-a-dict"])
    assert out["traza_auditoria"]["descartadas_fuera_de_esquema"] >= 1
    with pytest.raises(adapter.MatcherBreachError):
        adapter.emparejar({"consultante": ""}, lambda ctx: [])


def test_resolver_passthrough_and_distinct_exception_types(adapter):
    out = adapter.resolver({
        "campana_id": "camp1", "celula_id": "c1", "tipo": "binario", "umbral": 2,
        "expira_en": "2026-02-01", "moneda": "USD", "modo": "paz",
        "compromisos": [{"compromiso_id": "p1", "ficha_participante": "x"}],
    })
    assert out["estado"] == "reembolsa"
    # bad input -> ValueError (not AssuranceInvariantError, which is an internal abort)
    with pytest.raises(ValueError):
        adapter.resolver({"campana_id": "c", "celula_id": "c1", "tipo": "bogus", "umbral": 1,
                          "expira_en": "e", "moneda": "USD", "compromisos": []})


def test_sentir_passthrough_integer_clock(adapter):
    out = adapter.sentir({
        "celula_id": "c1", "ahora": 10, "ventana": 5, "tope_velocidad": 3, "vida_media": 4,
        "fuerza_min": 0.1, "modo": "paz",
        "trazas": [{"about": "art1", "senal": "contribucion", "fuerza": 1.0,
                    "creado_en": 9, "celula_id": "c1"}],
    })
    assert out["veredicto"] == "senales_sentidas"
    with pytest.raises(adapter.StigmergyBreachError):
        adapter.sentir({"celula_id": "c1", "ahora": "not-an-int", "ventana": 5,
                        "tope_velocidad": 3, "vida_media": 4, "fuerza_min": 0.1, "trazas": []})


def test_decidir_passthrough_reasons_not_identities(adapter):
    out = adapter.decidir({
        "circulo_id": "circle1", "propuesta_id": "prop1", "ahora": "2026-01-01",
        "expira_en": "2026-02-01", "modo": "paz",
        "posturas": [
            {"ficha": "x", "postura": "consentir", "circulo_id": "circle1"},
            {"ficha": "y", "postura": "objetar", "circulo_id": "circle1",
             "objecion": {"primordial": True, "razon": "unsafe"}},
        ],
    })
    assert out["veredicto"] == "revisar"
    assert out["objeciones_primordiales"] == [{"razon": "unsafe"}]
    # no objector token leaks anywhere in the output
    import json
    assert "\"y\"" not in json.dumps(out)
    with pytest.raises(adapter.GovernanceBreachError):
        adapter.decidir({"circulo_id": "", "propuesta_id": "p", "ahora": "n",
                         "expira_en": "e", "posturas": []})
