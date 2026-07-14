import importlib.util
from pathlib import Path
import pytest

_MOD = Path(__file__).resolve().parent.parent / "src" / "stigmergy" / "estigmergia.py"
_spec = importlib.util.spec_from_file_location("estigmergia", _MOD)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)
sentir = mod.sentir
ErrorDeBrechaEstigmergia = mod.ErrorDeBrechaEstigmergia
ALLOWED_SIGNALS = mod.ALLOWED_SIGNALS

NOW = 1000

def _trace(about="zona:la-guaira-01", senal="presencia", fuerza=5, creado_en=NOW,
           celula_id="barrio-1", contexto=None):
    t = {"about": about, "senal": senal, "fuerza": fuerza, "creado_en": creado_en,
         "celula_id": celula_id}
    if contexto is not None:
        t["contexto"] = contexto
    return t

def _req(trazas=None, cell="barrio-1", now=NOW, window=100, velocity_cap=3,
         half_life=50, min_strength=0.5, modo=None):
    r = {"celula_id": cell, "ahora": now, "ventana": window, "tope_velocidad": velocity_cap,
         "vida_media": half_life, "fuerza_min": min_strength, "trazas": trazas or []}
    if modo is not None:
        r["modo"] = modo
    return r

def test_ac_c1_rafaga_y_exclusiones():
    trazas = [_trace(about="zona:la-guaira-01", senal="presencia", creado_en=NOW) for _ in range(6)]
    req_a = _req(trazas=trazas, velocity_cap=3)
    res_a = sentir(req_a)
    assert res_a["traza_auditoria"]["amortiguadas_velocidad"] > 0

    trazas_b = [_trace(about="zona:la-guaira-01", senal="paso_maquinaria")]
    req_b = _req(trazas=trazas_b)
    res_b = sentir(req_b)
    assert any(s["senal"] == "paso_maquinaria" for s in res_b["sentidas"])

    trazas_c = [_trace(about="persona:fulano", senal="presencia")]
    req_c = _req(trazas=trazas_c)
    with pytest.raises(ErrorDeBrechaEstigmergia):
        sentir(req_c)

def test_ac_f1_bandera_contexto():
    trazas_sin = [_trace(about="zona:la-guaira-01", senal="bandera", contexto=None)]
    req_sin = _req(trazas=trazas_sin)
    res_sin = sentir(req_sin)
    assert not any(s["senal"] == "bandera" for s in res_sin["sentidas"])
    assert res_sin["traza_auditoria"]["amortiguadas_sin_contexto"] >= 1

    trazas_con = [_trace(about="zona:la-guaira-01", senal="bandera", contexto="hubo un derrumbe")]
    req_con = _req(trazas=trazas_con)
    res_con = sentir(req_con)
    assert any(s["senal"] == "bandera" and s["contexto"] == "hubo un derrumbe" for s in res_con["sentidas"])

def test_ac_f2_modos_y_velocidad():
    req_a = _req(modo="catastrofe_severa", velocity_cap=4)
    with pytest.raises(ErrorDeBrechaEstigmergia):
        sentir(req_a)

    req_b = _req(modo="catastrofe_severa", velocity_cap=3)
    sentir(req_b)

    req_c1 = _req(modo="paz", velocity_cap=50)
    sentir(req_c1)

    req_c2 = _req(modo="paz", velocity_cap=51)
    with pytest.raises(ErrorDeBrechaEstigmergia):
        sentir(req_c2)

    assert hasattr(mod, "TOPE_VELOCIDAD_MAX")
    topes = mod.TOPE_VELOCIDAD_MAX
    assert topes["catastrofe_severa"] == 3
    assert topes["catastrofe_acotada"] == 10
    assert topes["paz"] == 50

def test_ac_f3_celula_id_alcance():
    trazas = [_trace(celula_id="otro-barrio")]
    req = _req(trazas=trazas, cell="barrio-1")
    res = sentir(req)
    assert not any(s["celula_id"] == "otro-barrio" for s in res["sentidas"])
    assert res["traza_auditoria"]["descartadas_fuera_de_celula"] >= 1

def test_ac_f4_paso_maquinaria_restricciones():
    assert "paso_maquinaria" in ALLOWED_SIGNALS

    trazas_a = [_trace(about="motor-3", senal="paso_maquinaria")]
    req_a = _req(trazas=trazas_a)
    with pytest.raises(ErrorDeBrechaEstigmergia):
        sentir(req_a)

    trazas_b = [_trace(about="persona:x", senal="paso_maquinaria")]
    req_b = _req(trazas=trazas_b)
    with pytest.raises(ErrorDeBrechaEstigmergia):
        sentir(req_b)
