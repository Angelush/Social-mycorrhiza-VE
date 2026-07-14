import copy
import importlib.util
from pathlib import Path
from hypothesis import given, settings
from hypothesis import strategies as st
import pytest

_ROOT = Path(__file__).resolve().parent.parent
def _load(nombre_mod, ruta_rel):
    spec = importlib.util.spec_from_file_location(nombre_mod, _ROOT / ruta_rel)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

_aseg = _load("aseguramiento_e", "src/assurance/aseguramiento.py")
resolver = _aseg.resolver
ErrorDeBrechaAseguramiento = _aseg.ErrorDeBrechaAseguramiento
_memb = _load("membrana_e", "src/partition/membrana.py")
admitir = _memb.admitir
ErrorDeBrechaMembrana = _memb.ErrorDeBrechaMembrana

BASE = {
    "campana_id": "c",
    "celula_id": "cel",
    "tipo": "monetario",
    "moneda": "VES",
    "umbral": 5,
    "bono_patrocinador_centavos": 1000,
    "expira_en": "2026-12-31T00:00:00Z",
    "compromisos": [
        {"compromiso_id": "p1", "ficha_participante": "t1", "monto_centavos": 2000},
        {"compromiso_id": "p2", "ficha_participante": "t2", "monto_centavos": 3000}
    ]
}

SOBRE = {
    "sala": "precio_de_mercado",
    "celula_id": "cel",
    "interaccion_id": "i1",
    "participantes": ["t1"],
    "carga": {}
}

# ==============================================================================
# AC-e1: Validación de obligatoriedad y valor de la moneda de la campaña
# ==============================================================================

def test_campana_sin_moneda_lanza_error():
    campana = copy.deepcopy(BASE)
    del campana["moneda"]
    with pytest.raises(ErrorDeBrechaAseguramiento):
        resolver(campana)

def test_campana_con_moneda_invalida_lanza_error():
    campana = copy.deepcopy(BASE)
    campana["moneda"] = "EUR"
    with pytest.raises(ErrorDeBrechaAseguramiento):
        resolver(campana)

# ==============================================================================
# AC-D1: Validación de consistencia de doble moneda sin conversión
# ==============================================================================

def test_campana_usd_con_compromiso_ves_es_rechazada():
    campana = copy.deepcopy(BASE)
    campana["moneda"] = "USD"
    campana["compromisos"][0]["moneda"] = "VES"
    with pytest.raises(ErrorDeBrechaAseguramiento):
        resolver(campana)

def test_campana_ves_con_compromiso_usd_es_rechazada():
    campana = copy.deepcopy(BASE)
    campana["moneda"] = "VES"
    campana["compromisos"][0]["moneda"] = "USD"
    with pytest.raises(ErrorDeBrechaAseguramiento):
        resolver(campana)

def test_campana_usd_con_bono_moneda_ves_es_rechazada():
    campana = copy.deepcopy(BASE)
    campana["moneda"] = "USD"
    campana["bono_moneda"] = "VES"
    with pytest.raises(ErrorDeBrechaAseguramiento):
        resolver(campana)

def test_campana_monomoneda_coherente_no_lanza_error():
    campana = copy.deepcopy(BASE)
    campana["moneda"] = "USD"
    campana["bono_moneda"] = "USD"
    campana["compromisos"][0]["moneda"] = "USD"
    campana["compromisos"][1]["moneda"] = "USD"
    # umbral 5 con 2 compromisos (t1, t2) -> se activa reembolsa
    resultado = resolver(campana)
    assert resultado["estado"] == "reembolsa"
    assert resultado["moneda"] == "USD"

# ==============================================================================
# AC-D3: Prohibición estricta de cualquier clave de tipo de cambio
# ==============================================================================

@pytest.mark.parametrize("clave_prohibida", [
    "tasa_de_cambio", "tipo_de_cambio", "exchange_rate", "fx", "paralelo", "bcv",
    "tasadecambio", "tipodecambio", "exchangerate", "TASA_DE_CAMBIO", "FX"
])
def test_claves_tipo_cambio_raiz_lanzan_error(clave_prohibida):
    campana = copy.deepcopy(BASE)
    campana[clave_prohibida] = 36.5
    with pytest.raises(ErrorDeBrechaAseguramiento):
        resolver(campana)

def test_clave_tipo_cambio_anidada_lanza_error():
    campana = copy.deepcopy(BASE)
    campana["datos"] = {"tasa_de_cambio": 3600}
    with pytest.raises(ErrorDeBrechaAseguramiento):
        resolver(campana)

def test_clave_tipo_cambio_camel_case_lanza_error():
    campana = copy.deepcopy(BASE)
    campana["tasaDeCambio"] = 3600
    with pytest.raises(ErrorDeBrechaAseguramiento):
        resolver(campana)

# ==============================================================================
# AC-D2: Conservación exacta con céntimos de alta precisión (>15 dígitos)
# ==============================================================================

def test_conservacion_exacta_centimos_ves_alta_precision():
    campana = copy.deepcopy(BASE)
    bono_grande = 123456789012345678
    campana["bono_patrocinador_centavos"] = bono_grande
    campana["umbral"] = 10  # Forzar reembolsa al tener solo 2 participantes distintos
    
    resultado = resolver(campana)
    assert resultado["estado"] == "reembolsa"
    
    reembolsos = resultado["resolucion"]["reembolsos"]
    suma_bonos = sum(r["bono_centavos"] for r in reembolsos)
    assert suma_bonos == bono_grande
    
    # Validamos que cada reembolso_centavos sea igual a la suma de los compromisos de esa ficha
    ficha_montos = {}
    for c in campana["compromisos"]:
        ficha = c["ficha_participante"]
        ficha_montos[ficha] = ficha_montos.get(ficha, 0) + c["monto_centavos"]
        
    for r in reembolsos:
        ficha = r["ficha_participante"]
        assert r["reembolso_centavos"] == ficha_montos[ficha]

# ==============================================================================
# AC-e2: Control de denominaciones en salas (Membrana de Capa 1)
# ==============================================================================

@pytest.mark.parametrize("sala_restringida", ["don_comunal", "igualdad"])
@pytest.mark.parametrize("clave_denominada", [
    "usd", "ves", "dolar", "dolares", "bolivar", "bolivares", "moneda", "precio"
])
def test_claves_moneda_prohibidas_en_salas_restringidas(sala_restringida, clave_denominada):
    sobre = copy.deepcopy(SOBRE)
    sobre["sala"] = sala_restringida
    sobre["carga"] = {clave_denominada: 100}
    with pytest.raises(ErrorDeBrechaMembrana):
        admitir(sobre)

@pytest.mark.parametrize("clave_denominada", [
    "usd", "ves", "dolar", "dolares", "bolivar", "bolivares", "moneda", "precio"
])
def test_claves_moneda_permitidas_en_precio_de_mercado(clave_denominada):
    sobre = copy.deepcopy(SOBRE)
    sobre["sala"] = "precio_de_mercado"
    sobre["carga"] = {clave_denominada: 100}
    res = admitir(sobre)
    assert res.get("admitido") is True

# ==============================================================================
# AC-e3: Reembolso completo en la moneda correcta al no alcanzar el umbral
# ==============================================================================

def test_reembolso_completo_y_moneda_al_no_alcanzar_umbral():
    campana = copy.deepcopy(BASE)
    campana["moneda"] = "VES"
    campana["umbral"] = 5
    # Participantes: t1 (2000 centavos), t2 (3000 centavos) -> Total distintos: 2 < 5
    
    resultado = resolver(campana)
    assert resultado["estado"] == "reembolsa"
    assert resultado["moneda"] == "VES"
    
    reembolsos = resultado["resolucion"]["reembolsos"]
    assert len(reembolsos) == 2
    
    reembolso_t1 = next(r for r in reembolsos if r["ficha_participante"] == "t1")
    reembolso_t2 = next(r for r in reembolsos if r["ficha_participante"] == "t2")
    
    assert reembolso_t1["reembolso_centavos"] == 2000
    assert reembolso_t2["reembolso_centavos"] == 3000

# ==============================================================================
# PB-e1: Test de propiedad con Hypothesis (conservación del bono patrocinador)
# ==============================================================================

@settings(max_examples=200)
@given(
    bono_patrocinador=st.integers(min_value=0, max_value=10**30),
    montos=st.lists(st.integers(min_value=0, max_value=10**20), min_size=1, max_size=15)
)
def test_propiedad_conservacion_bono_patrocinador_en_reembolso(bono_patrocinador, montos):
    campana = {
        "campana_id": "c_prop",
        "celula_id": "cel_prop",
        "tipo": "monetario",
        "moneda": "VES",
        "umbral": 100, # Umbral alto para garantizar la rama reembolsa
        "bono_patrocinador_centavos": bono_patrocinador,
        "expira_en": "2026-12-31T00:00:00Z",
        "compromisos": []
    }
    
    # Creamos los compromisos usando fichas incrementales
    # Usamos máximo 15 compromisos, garantizando que los participantes distintos sean <= 15 < 100 (umbral)
    for idx, monto in enumerate(montos):
        campana["compromisos"].append({
            "compromiso_id": f"p_{idx}",
            "ficha_participante": f"t_{idx}",
            "monto_centavos": monto
        })
        
    resultado = resolver(campana)
    assert resultado["estado"] == "reembolsa"
    
    reembolsos = resultado["resolucion"]["reembolsos"]
    suma_bonos = sum(r["bono_centavos"] for r in reembolsos)
    assert suma_bonos == bono_patrocinador
