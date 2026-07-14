"""Pruebas de aceptación — Área c · módulo `modo` (calibración por hostilidad).

Cubre AC-M1, AC-c1..AC-c6 de
workflows/micorriza-politica-ve/area-c-modo/evals/acceptance.md.

`depurar()` y `validar_transicion()` son Área d (TA.5) y NO se prueban aquí.

Oráculo de tamaño INDEPENDIENTE: la serialización canónica se recalcula a mano (no se importa el
helper privado del módulo) para que el módulo no pueda autoconfirmar su propia medida.
"""
import importlib.util
import json
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, _SRC / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


modo_mod = _load("modo/modo.py", "modo_c")
validar_modo = modo_mod.validar_modo
ErrorDeModo = modo_mod.ErrorDeModo
MODOS = modo_mod.MODOS

membrana = _load("partition/membrana.py", "membrana_c")
legibilidad = _load("legibility/legibilidad.py", "legibilidad_c")
emparejador = _load("matcher/emparejador.py", "emparejador_c")
estigmergia = _load("stigmergy/estigmergia.py", "estigmergia_c")
gobernanza = _load("governance/gobernanza.py", "gobernanza_c")
aseguramiento = _load("assurance/aseguramiento.py", "aseguramiento_c")


# ---- oráculo independiente de tamaño ---------------------------------------
def _tam(request):
    """Bytes del envelope en JSON canónico — reimplementado a mano (no el helper del módulo)."""
    return len(json.dumps(request, sort_keys=True, ensure_ascii=False,
                          separators=(',', ':')).encode('utf-8'))


def _envelope_de_tamano(target, modo='catastrofe_severa'):
    """Construye un envelope {modo, relleno} que serializa a EXACTAMENTE `target` bytes."""
    base = {'modo': modo, 'relleno': ''}
    fill = target - _tam(base)
    assert fill >= 0, "target demasiado pequeño para el overhead del envelope"
    base['relleno'] = 'x' * fill
    assert _tam(base) == target
    return base


# ============================================================ AC-c2 — modo ausente/inválido
def test_acc2_modo_ausente_lanza():
    with pytest.raises(ErrorDeModo):
        validar_modo({'celula_id': 'c1'})


def test_acc2_modo_invalido_lanza():
    with pytest.raises(ErrorDeModo):
        validar_modo({'modo': 'guerra_total', 'celula_id': 'c1'})


def test_acc2_no_dict_lanza():
    with pytest.raises(ErrorDeModo):
        validar_modo(['modo', 'paz'])


def test_modos_validos_pasan():
    for m in MODOS:
        assert validar_modo({'modo': m, 'celula_id': 'c1'}) == m


# ============================================================ AC-M1 — mismo request, paz OK / severa rechazado
def test_acm1_retencion_paz_ok_severa_rechaza():
    # ~79 días de retención: dentro de paz (365), fuera de severa (7).
    req = {'celula_id': 'c1', 'expira_en': '2026-10-01', 'ahora': '2026-07-14'}
    assert validar_modo({**req, 'modo': 'paz'}) == 'paz'
    with pytest.raises(ErrorDeModo):
        validar_modo({**req, 'modo': 'catastrofe_severa'})


def test_acm1_max_hops_paz_ok_severa_rechaza():
    req = {'celula_id': 'c1', 'max_hops': 4}
    assert validar_modo({**req, 'modo': 'paz'}) == 'paz'          # 4 no excede 4
    with pytest.raises(ErrorDeModo):
        validar_modo({**req, 'modo': 'catastrofe_severa'})        # 4 > 2


def test_acm1_payload_paz_ok_severa_rechaza():
    req = _envelope_de_tamano(1000, modo='paz')
    assert validar_modo(req) == 'paz'                             # 1000 < 65536
    with pytest.raises(ErrorDeModo):
        validar_modo({**req, 'modo': 'catastrofe_severa'})        # 1000 > 512


def test_max_proposals_severa_rechaza():
    assert validar_modo({'modo': 'paz', 'max_proposals': 20}) == 'paz'
    with pytest.raises(ErrorDeModo):
        validar_modo({'modo': 'catastrofe_severa', 'max_proposals': 20})


# ============================================================ AC-c1 — frontera exacta 512/513 en severa
def test_acc1_frontera_payload_severa():
    admitido = _envelope_de_tamano(512, modo='catastrofe_severa')
    assert validar_modo(admitido) == 'catastrofe_severa'         # 512 admitido
    rechazado = _envelope_de_tamano(513, modo='catastrofe_severa')
    with pytest.raises(ErrorDeModo):
        validar_modo(rechazado)                                  # 513 rechazado


# ============================================================ AC-c3 — rechazo, nunca recorte
def test_acc3_rechazo_no_recorte():
    req = {'modo': 'catastrofe_severa', 'celula_id': 'c1',
           'expira_en': '2027-01-01', 'ahora': '2026-07-14'}
    antes = dict(req)
    with pytest.raises(ErrorDeModo):
        validar_modo(req)
    assert req == antes                                          # el request NO se mutó/recortó


# ============================================================ AC-c4 — integración en las 6 capas
def test_acc4_membrana_rechaza_con_su_error():
    with pytest.raises(membrana.ErrorDeBrechaMembrana):
        membrana.admitir({**_envelope_de_tamano(2000), 'carga': {}})


def test_acc4_legibilidad_rechaza_con_su_error():
    with pytest.raises(legibilidad.ErrorDeBrechaLegibilidad):
        legibilidad.consultar(_envelope_de_tamano(2000))


def test_acc4_emparejador_rechaza_con_su_error():
    with pytest.raises(emparejador.ErrorDeBrechaEmparejador):
        emparejador.emparejar(_envelope_de_tamano(2000), lambda ctx: [])


def test_acc4_estigmergia_rechaza_con_su_error():
    with pytest.raises(estigmergia.ErrorDeBrechaEstigmergia):
        estigmergia.sentir(_envelope_de_tamano(2000))


def test_acc4_gobernanza_rechaza_con_su_error():
    with pytest.raises(gobernanza.ErrorDeBrechaGobernanza):
        gobernanza.decidir(_envelope_de_tamano(2000))


def test_acc4_aseguramiento_rechaza_con_valueerror():
    # Capa 4 usa ValueError como convención de rechazo de sobre (ver TA.3).
    with pytest.raises(ValueError):
        aseguramiento.resolver(_envelope_de_tamano(2000))


def test_acc4_sin_modo_las_capas_no_enganchan():
    # Un envelope grande SIN `modo` no dispara `validar_modo` (compat): la capa sigue su
    # validación propia (aquí, otro error de sobre, no el de payload de modo).
    grande = {'relleno': 'x' * 2000}
    with pytest.raises(membrana.ErrorDeBrechaMembrana):
        membrana.admitir(grande)  # falla por clave desconocida / sobre, no por modo


# ============================================================ AC-c5 — estrictez de velocity_cap monótona
def test_acc5_estrictez_velocidad_monotona():
    orden = ['paz', 'catastrofe_acotada', 'catastrofe_severa']
    estrictez = [modo_mod.estrictez_velocidad(m) for m in orden]
    assert estrictez == sorted(estrictez)
    assert estrictez[0] < estrictez[-1]                          # paz estrictamente < severa
    # La cota concreta propuesta decrece (menor tope = más estricto).
    topes = [modo_mod.TOPE_VELOCIDAD_MAX[m] for m in orden]
    assert topes == sorted(topes, reverse=True)


def test_acc5_tope_velocidad_aplicado():
    assert validar_modo({'modo': 'paz', 'tope_velocidad': 50}) == 'paz'
    with pytest.raises(ErrorDeModo):
        validar_modo({'modo': 'catastrofe_severa', 'tope_velocidad': 50})


# ============================================================ AC-c6 — el modo no cruza los invariantes
def _sobre_membrana(modo, carga):
    return {'sala': 'igualdad', 'celula_id': 'c1', 'interaccion_id': 'i1',
            'participantes': ['a'], 'carga': carga, 'modo': modo}


def test_acc6_forma_prohibida_rechazada_en_todos_los_modos():
    for m in MODOS:
        with pytest.raises(membrana.ErrorDeBrechaMembrana):
            membrana.admitir(_sobre_membrana(m, {'score': 5}))


def test_acc6_envelope_limpio_admitido_en_todos_los_modos():
    for m in MODOS:
        res = membrana.admitir(_sobre_membrana(m, {'nota': 'hola'}))
        assert res['admitido'] is True
