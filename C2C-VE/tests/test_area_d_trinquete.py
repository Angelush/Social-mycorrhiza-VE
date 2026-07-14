"""Pruebas de aceptación — Área d · Trinquete asimétrico + evacuación pura (TA.5).

Cubre AC-M2, AC-d1..AC-d4 y PB-d1 (monotonía, hypothesis) de
workflows/micorriza-politica-ve/area-d-trinquete/evals/acceptance.md, más el acoplamiento
escalada→`depurar` (AC-M3, idempotencia).

`validar_transicion`, `depurar` y `tras_escalada` viven en `src/modo/modo.py`. La `decision` de
Capa 6 se construye con la forma REAL que devuelve `gobernanza.decidir` (veredicto/propuesta_id/
circulo_id): no se reimplementa gobernanza, se consume su veredicto (C-d5).
"""
import importlib.util
from pathlib import Path

import pytest
from hypothesis import given, strategies as st

_SRC = Path(__file__).resolve().parent.parent / "src"


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, _SRC / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


modo_mod = _load("modo/modo.py", "modo_d")
validar_transicion = modo_mod.validar_transicion
depurar = modo_mod.depurar
tras_escalada = modo_mod.tras_escalada
ErrorDeModo = modo_mod.ErrorDeModo
MODOS = modo_mod.MODOS  # ('paz', 'catastrofe_acotada', 'catastrofe_severa')

PAZ, ACOTADA, SEVERA = MODOS


def _decision(circulo, destino, veredicto='adoptada'):
    """Forma de un veredicto de `gobernanza.decidir` sobre una propuesta `cambiar_modo`.

    Convención del `propuesta_id`: cambiar_modo:{circulo_id}:{modo_destino} (ver DESIGN-TA5.md).
    """
    return {
        'circulo_id': circulo,
        'propuesta_id': f"cambiar_modo:{circulo}:{destino}",
        'veredicto': veredicto,
    }


# ============================================================ AC-M2 — asimetría del trinquete
def test_acm2_escalada_sin_decision_es_valida():
    assert validar_transicion(PAZ, ACOTADA) == 'escalada'
    assert validar_transicion(ACOTADA, SEVERA) == 'escalada'


def test_acm2_desescalada_sin_decision_rechazada():
    with pytest.raises(ErrorDeModo):
        validar_transicion(SEVERA, PAZ)
    with pytest.raises(ErrorDeModo):
        validar_transicion(ACOTADA, PAZ, decision_capa6=None)


def test_acm2_desescalada_con_adoptada_correcta_es_valida():
    assert validar_transicion(SEVERA, PAZ, _decision('c1', PAZ)) == 'desescalada'
    assert validar_transicion(SEVERA, ACOTADA, _decision('c1', ACOTADA)) == 'desescalada'


def test_acm2_desescalada_con_revisar_rechazada():
    with pytest.raises(ErrorDeModo):
        validar_transicion(SEVERA, PAZ, _decision('c1', PAZ, veredicto='revisar'))


# ============================================================ AC-d1 — salto directo es escalada
def test_acd1_salto_directo_paz_a_severa_es_escalada():
    assert validar_transicion(PAZ, SEVERA) == 'escalada'


# ============================================================ AC-d2 — consentimiento local y específico
def test_acd2_otra_propuesta_rechazada():
    # veredicto adoptada, pero la propuesta no es un cambiar_modo hacia `propuesto`.
    d = {'circulo_id': 'c1', 'propuesta_id': 'otra_cosa:xyz', 'veredicto': 'adoptada'}
    with pytest.raises(ErrorDeModo):
        validar_transicion(SEVERA, PAZ, d)


def test_acd2_destino_equivocado_rechazado():
    # adoptada para cambiar a ACOTADA no autoriza desescalar hasta PAZ.
    with pytest.raises(ErrorDeModo):
        validar_transicion(SEVERA, PAZ, _decision('c1', ACOTADA))


def test_acd2_otro_circulo_rechazado():
    # La propuesta nombra el círculo 'c2' pero la decisión adoptada es del círculo 'c1':
    # una decisión de c1 no autoriza la propuesta de c2 (sin auto-propagación).
    d = {'circulo_id': 'c1', 'propuesta_id': f'cambiar_modo:c2:{PAZ}', 'veredicto': 'adoptada'}
    with pytest.raises(ErrorDeModo):
        validar_transicion(SEVERA, PAZ, d)


# ============================================================ AC-d3 — no-op explícito
def test_acd3_no_op_no_es_transicion_ni_error():
    for m in MODOS:
        assert validar_transicion(m, m) == 'no_op'
        assert validar_transicion(m, m, _decision('c1', m)) == 'no_op'


def test_modo_invalido_rechazado():
    with pytest.raises(ErrorDeModo):
        validar_transicion('inexistente', PAZ)
    with pytest.raises(ErrorDeModo):
        validar_transicion(PAZ, 'inexistente')


# ============================================================ PB-d1 — monotonía (hypothesis)
@given(st.sampled_from(MODOS), st.sampled_from(MODOS))
def test_pbd1_monotonia_del_trinquete(actual, propuesto):
    ia, ip = MODOS.index(actual), MODOS.index(propuesto)
    if ip > ia:
        # Toda escalada es válida sin decisión.
        assert validar_transicion(actual, propuesto) == 'escalada'
    elif ip == ia:
        assert validar_transicion(actual, propuesto) == 'no_op'
    else:
        # Ninguna desescalada es válida sin decisión adoptada correspondiente.
        with pytest.raises(ErrorDeModo):
            validar_transicion(actual, propuesto)
        # …y sí lo es con la decisión correcta (el trinquete deja volver por consentimiento).
        assert validar_transicion(actual, propuesto, _decision('c1', propuesto)) == 'desescalada'


@given(st.sampled_from(MODOS), st.sampled_from(MODOS))
def test_pbd1_adoptada_de_otro_circulo_nunca_desescala(actual, propuesto):
    # Una adoptada del círculo 'A' jamás autoriza una propuesta ligada al círculo 'B'.
    if MODOS.index(propuesto) < MODOS.index(actual):
        d = {'circulo_id': 'A', 'propuesta_id': f'cambiar_modo:B:{propuesto}',
             'veredicto': 'adoptada'}
        with pytest.raises(ErrorDeModo):
            validar_transicion(actual, propuesto, d)


# ============================================================ depurar — evacuación pura por tipo
def test_depurar_elimina_datos_fuera_de_ventana():
    # severa: retencion_max_dias = 7. ahora = 2026-07-14.
    items = [
        {'tipo': 'dato', 'id': 'fresco', 'creado_en': '2026-07-10'},   # 4 días → sobrevive
        {'tipo': 'dato', 'id': 'viejo', 'creado_en': '2026-07-01'},    # 13 días → eliminado
    ]
    res = depurar(items, SEVERA, '2026-07-14')
    ids = {i['id'] for i in res}
    assert ids == {'fresco'}


def test_depurar_recorta_trazas_no_las_elimina():
    # severa: retencion_trazas_dias = 3. Una traza creada el 2026-07-01 con TTL largo:
    # se conserva pero su expira_en se recorta a creado_en + 3 = 2026-07-04.
    items = [{'tipo': 'traza', 'id': 't', 'creado_en': '2026-07-01', 'expira_en': '2026-12-31'}]
    res = depurar(items, SEVERA, '2026-07-14')
    assert len(res) == 1
    assert res[0]['expira_en'] == '2026-07-04'


def test_depurar_no_extiende_ttl_ya_corto():
    # Si el expira_en original ya es más corto que la ventana, no se alarga (min).
    items = [{'tipo': 'traza', 'id': 't', 'creado_en': '2026-07-01', 'expira_en': '2026-07-02'}]
    res = depurar(items, PAZ, '2026-07-14')
    assert res[0]['expira_en'] == '2026-07-02'


def test_depurar_descarta_malformados():
    items = [
        {'tipo': 'dato', 'id': 'sin_fecha'},
        {'tipo': 'traza', 'id': 'traza_sin_fecha'},
        {'tipo': 'dato', 'id': 'fecha_basura', 'creado_en': 'ayer'},
    ]
    assert depurar(items, PAZ, '2026-07-14') == []


def test_depurar_no_muta_las_entradas():
    items = [{'tipo': 'traza', 'id': 't', 'creado_en': '2026-07-01', 'expira_en': '2026-12-31'}]
    original = dict(items[0])
    depurar(items, SEVERA, '2026-07-14')
    assert items[0] == original  # la entrada original no cambió


def test_depurar_idempotente_acm3():
    items = [
        {'tipo': 'dato', 'id': 'd', 'creado_en': '2026-07-13'},
        {'tipo': 'traza', 'id': 't', 'creado_en': '2026-07-10', 'expira_en': '2026-12-31'},
    ]
    una = depurar(items, ACOTADA, '2026-07-14')
    dos = depurar(una, ACOTADA, '2026-07-14')
    assert una == dos


def test_depurar_modo_invalido_y_ahora_invalido():
    with pytest.raises(ErrorDeModo):
        depurar([], 'inexistente', '2026-07-14')
    with pytest.raises(ErrorDeModo):
        depurar([], PAZ, 'no-es-fecha')


# ============================================================ AC-d4 — escalada obliga a depurar (convención)
def test_acd4_tras_escalada_depura_a_la_nueva_ventana():
    # De paz a severa: los datos que exceden la ventana de severa (7 días) desaparecen.
    items = [
        {'tipo': 'dato', 'id': 'fresco', 'creado_en': '2026-07-12'},   # 2 días → sobrevive
        {'tipo': 'dato', 'id': 'viejo', 'creado_en': '2026-05-01'},    # meses → eliminado
    ]
    res = tras_escalada(items, PAZ, SEVERA, '2026-07-14')
    assert {i['id'] for i in res} == {'fresco'}


def test_acd4_tras_escalada_rechaza_desescalada():
    with pytest.raises(ErrorDeModo):
        tras_escalada([], SEVERA, PAZ, '2026-07-14')
    with pytest.raises(ErrorDeModo):
        tras_escalada([], PAZ, PAZ, '2026-07-14')  # no-op no es escalada


# ============================================================ PB-d (idempotencia) — propiedad (TA.8)
@given(n_datos=st.integers(0, 6), n_trazas=st.integers(0, 6))
def test_pbd_depurar_idempotente_propiedad(n_datos, n_trazas):
    """`depurar` es idempotente sobre listas mixtas de datos y trazas (AC-M3, como propiedad)."""
    items = [{'tipo': 'dato', 'creado_en': '2026-01-01'} for _ in range(n_datos)]
    items += [{'tipo': 'traza', 'creado_en': '2026-01-01', 'expira_en': '2026-12-31'}
              for _ in range(n_trazas)]
    modo, ahora = 'catastrofe_acotada', '2026-06-01'
    primer = depurar(items, modo, ahora)
    assert depurar(primer, modo, ahora) == primer
