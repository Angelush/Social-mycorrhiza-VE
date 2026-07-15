# -*- coding: utf-8 -*-
"""Aceptación de D5 — `referencias_comerciales` (AC-8, AC-d5.1..d5.7).

La ÚNICA superficie de forma libre de la Fase 2 → el único sitio donde el firewall heredado
(D9) gana su sueldo. Este archivo salda AC-d9.5, pendiente desde TB.2.

Spec: B2B/workflows/micorriza-ve/d5-referencias-comerciales/{spec,constraints,failure-model}.md
      B2B/workflows/micorriza-ve/d5-referencias-comerciales/DESIGN-TB5.md
"""

import ast as _ast
import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

_BASE = Path(__file__).resolve().parent.parent


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, _BASE / rel)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


led = _load("mutual_credit_ledger_d5", "src/ledger/mutual_credit_ledger.py")
fw = _load("herencia_d5", "src/firewall/herencia.py")
exp = _load("exportes_d5", "src/ledger/exportes.py")


# Referencias válidas — y `bancoDeTiempo` NO es decorativo: es el control negativo de R2
# (tokens banco/de/tiempo, ninguno colisiona con `ban`). Datos sintéticos (N8/AC-d5.7): ningún
# valor con forma de identidad corresponde a una cédula o RIF emitidos.
_REFS_VALIDAS = [
    {"avalista": "B", "relacion_declarada": "proveedor", "antiguedad_meses": 36,
     "nota": "Buen proveedor desde 2023"},
    {"avalista": "bancoDeTiempo", "relacion_declarada": "ambos", "antiguedad_meses": 12},
]


_PARAMS = {
    "neg_line_bp": 100,
    "pos_line_bp": 1000,
    "velocity_window_s": 86400,
    "velocity_max_cents": 5_000_000,
    "moneda": "USD",
    "sal_seudonimo": "sal-secreta-xyz",
    "paused": False,
}


def _estado_base():
    state, _ = led.create_cell("celda-d5", _PARAMS, "ana", 1000)
    state, _ = led.add_member(state, {"id": "B", "turnover_cents": 100_000_000}, "ana", 1001)
    state, _ = led.add_member(state, {"id": "bancoDeTiempo", "turnover_cents": 100_000_000},
                              "ana", 1002)
    return state


def _con_refs(refs=None):
    """Estado con `A` dado de alta con `refs` (por defecto, las válidas)."""
    state = _estado_base()
    return led.add_member(state, {"id": "A", "turnover_cents": 100_000_000}, "ana", 1003,
                          referencias_comerciales=_REFS_VALIDAS if refs is None else refs)


def _estado_y_eventos():
    """Igual que `_con_refs`, pero devolviendo el STREAM COMPLETO.

    `replay`/`verify_chain`/`exportar_registros` reconstruyen desde `cell_created`: un prefijo
    que empiece por `member_added` no es un stream, es un fragmento.
    """
    eventos = []
    state, ev = led.create_cell("celda-d5", _PARAMS, "ana", 1000)
    eventos.append(ev)
    for mid, ts in (("B", 1001), ("bancoDeTiempo", 1002)):
        state, ev = led.add_member(state, {"id": mid, "turnover_cents": 100_000_000}, "ana", ts)
        eventos.append(ev)
    state, ev = led.add_member(state, {"id": "A", "turnover_cents": 100_000_000}, "ana", 1003,
                              referencias_comerciales=_REFS_VALIDAS)
    eventos.append(ev)
    return state, eventos


def _recorre(nodo):
    """Todos los valores escalares de una estructura anidada."""
    valores = []
    if isinstance(nodo, dict):
        for k, v in nodo.items():
            valores.extend(_recorre(v))
    elif isinstance(nodo, list):
        for v in nodo:
            valores.extend(_recorre(v))
    else:
        valores.append(nodo)
    return valores


# ── AC-8 — Ningún escalar de persona (EL QUE IMPORTA) ────────────────────────────────────────

def test_ac_8_1_por_tipo_de_salida():
    """AC-8(1) — el conjunto de claves es CERRADO y las referencias salen TAL CUAL entraron.

    Igualdad de CONJUNTOS, no una lista de nombres prohibidos: un `indice_relacional` futuro
    rompe este test sin que nadie lo hubiera previsto, que es justo lo que H1 pide (el muro es
    el tipo de salida; la lista de claves es lint secundario). Y igualdad PROFUNDA con el input:
    el motor las almacena y las devuelve, no las transforma.
    """
    state, _ = _con_refs()
    stmt = led.member_statement(state, "A", "comite_credito")

    assert set(stmt) == {
        "member_id", "status", "balance_cents", "credit_min_cents", "credit_max_cents",
        "owed_by_cents", "owed_to_cents", "projected_cents", "referencias_comerciales",
    }, "campo derivado en la salida del comité — ¿un score con otro nombre?"

    assert stmt["referencias_comerciales"] == _REFS_VALIDAS, \
        "las referencias no salen tal cual se guardaron"

    # …y el motor no le da al llamador un asa sobre su propio estado.
    stmt["referencias_comerciales"][0]["antiguedad_meses"] = 9999
    assert led.member_statement(state, "A", "comite_credito")["referencias_comerciales"] \
        == _REFS_VALIDAS


_D5_NOMBRES = {"referencias_comerciales", "avalista", "relacion_declarada",
               "antiguedad_meses", "nota"}

# El parámetro del validador, nombrado explícitamente: sin él, un `len(referencias)` DENTRO de
# `_validar_referencias` no se marcaría (el rastreo es intra-función y ese nombre no es una
# clave de D5). Barato y honesto.
_SEMILLA = _D5_NOMBRES | {"referencias"}

_AGREGADORES = {"len", "sum", "max", "min", "sorted", "round", "abs", "mean", "median"}


def _expr_contaminada(nodo, contaminados):
    """¿Este subárbol lee datos de D5? Un `Name` contaminado o el literal de una clave de D5."""
    for n in _ast.walk(nodo):
        if isinstance(n, _ast.Name) and n.id in contaminados:
            return True
        if isinstance(n, _ast.Constant) and isinstance(n.value, str) and n.value in _D5_NOMBRES:
            return True
    return False


def test_ac_8_2_ninguna_derivacion_por_ast():
    """AC-8(2) — ninguna función de `src/` deriva un número de las referencias. Por AST.

    NO por la palabra: `antiguedad_media = sum(...)/len(...)` no dice «score» en ningún sitio, y
    un test de nombres prohibidos (AC-d5.1) solo caza al que se delata. Se rastrea el DATO:
    qué nombres vienen de D5 dentro de cada función, y se prohíbe agregarlos o hacer aritmética
    con ellos. `Compare` sí se permite — `antiguedad_meses < 0` es validación, no derivación.

    Es el patrón de AC-d7.4 (que encontró un hit real por AST), aplicado al borde peligroso de
    ESTE delta: `antiguedad_meses` es un número sobre una relación y `len(referencias)` un
    número sobre una empresa. Sumarlos, promediarlos o ponderarlos produce un score (§3).
    """
    ofensores = []
    for py in sorted((_BASE / "src").rglob("*.py")):
        arbol = _ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
        for fn in _ast.walk(arbol):
            if not isinstance(fn, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
                continue

            contaminados = {a.arg for a in fn.args.args + fn.args.kwonlyargs
                            if a.arg in _SEMILLA}
            # Propagación intra-función: `refs = payload["referencias_comerciales"]` contamina
            # `refs`, así que renombrar la variable no evade el muro.
            for nodo in _ast.walk(fn):
                if isinstance(nodo, _ast.Assign) and _expr_contaminada(nodo.value, contaminados):
                    for t in nodo.targets:
                        if isinstance(t, _ast.Name):
                            contaminados.add(t.id)

            if not contaminados and not _expr_contaminada(fn, set()):
                continue

            for nodo in _ast.walk(fn):
                if isinstance(nodo, _ast.BinOp) and any(
                        _expr_contaminada(lado, contaminados) for lado in (nodo.left, nodo.right)):
                    ofensores.append(f"{py.name}:{nodo.lineno} aritmética sobre datos de D5")
                if isinstance(nodo, _ast.Call) and isinstance(nodo.func, _ast.Name) \
                        and nodo.func.id in _AGREGADORES:
                    if any(_expr_contaminada(a, contaminados) for a in nodo.args):
                        ofensores.append(
                            f"{py.name}:{nodo.lineno} {nodo.func.id}() sobre datos de D5")

    assert not ofensores, (
        "El motor deriva un número de las referencias comerciales — eso ES un score, se llame "
        f"`confianza`, `n_avales` o `antiguedad_media` (C-d5.1/N-d5.1): {ofensores}"
    )


def test_ac_d5_1_canario_de_nombres():
    """AC-d5.1 — el canario, con los nombres que un ejecutor elegiría.

    Esta lista NO es el test (lo es AC-8): es lo que hace LEGIBLE el fallo cuando ocurre.
    """
    prohibidos = ("confianza", "fiabilidad", "indice_relacional", "antiguedad_media",
                  "n_avales", "salud_crediticia", "linea_sugerida", "percentil")
    state, _ = _con_refs()
    stmt = led.member_statement(state, "A", "comite_credito")
    for nombre in prohibidos:
        assert nombre not in stmt, f"salida con `{nombre}`"
        for modulo in (led, exp):
            assert not any(n == nombre or n.startswith(nombre)
                           for n in dir(modulo)), f"{modulo.__name__} expone `{nombre}`"


# ── AC-d5.2 — Esquema cerrado ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("refs,match", [
    ([{"avalista": "Z", "relacion_declarada": "proveedor", "antiguedad_meses": 1}],
     "avalista"),                                                    # inexistente
    ([{"avalista": "A", "relacion_declarada": "proveedor", "antiguedad_meses": 1}],
     "auto-aval"),                                                   # N-d5.4
    ([{"avalista": "B", "relacion_declarada": "socio", "antiguedad_meses": 1}],
     "relacion_declarada"),                                          # fuera del enum
    ([{"avalista": "B", "relacion_declarada": "proveedor", "antiguedad_meses": -1}],
     "antiguedad_meses"),
    ([{"avalista": "B", "relacion_declarada": "proveedor", "antiguedad_meses": "36"}],
     "antiguedad_meses"),
    ([{"avalista": "B", "relacion_declarada": "proveedor", "antiguedad_meses": True}],
     "antiguedad_meses"),                                            # bool NO es int (M4)
    # HALLAZGO — la spec §AC-d5.2 propone `"puntaje_interno": 5` como ejemplo de «clave
    # desconocida», pero `puntaje` ESTÁ en FORBIDDEN_KEYS: su propio vector de esquema es un
    # vector de firewall. Lo mata el firewall, no la lista blanca, y eso es el ORDEN de §0.4
    # funcionando — no un fallo. Se conserva el vector y se corrige la expectativa; el caso de
    # esquema necesita una clave desconocida BENIGNA (abajo), que es la única forma de que las
    # dos defensas queden demostrables por separado.
    ([{"avalista": "B", "relacion_declarada": "proveedor", "antiguedad_meses": 1,
       "puntaje_interno": 5}],
     "referencias_comerciales: firewall"),
    ([{"avalista": "B", "relacion_declarada": "proveedor", "antiguedad_meses": 1,
       "color": "azul"}],
     "clave desconocida"),
    ([{"avalista": "B", "relacion_declarada": "proveedor"}],
     "clave ausente"),
    (["no soy un dict"], "referencia"),
    ("no soy una lista", "referencias_comerciales"),
])
def test_ac_d5_2_esquema_cerrado_rechaza(refs, match):
    """AC-d5.2 — lista blanca: lo que no está en el esquema no entra (C-d5.3).

    `match=` en todo `raises`: un `pytest.raises(ValueError)` pelado atrapa CUALQUIER
    ValueError y pasa con el mecanismo muerto (lección de TB.2).
    """
    state = _estado_base()
    with pytest.raises(ValueError, match=match):
        led.add_member(state, {"id": "A", "turnover_cents": 100_000_000}, "ana", 1003,
                       referencias_comerciales=refs)


def test_ac_d5_2_admision():
    """AC-d5.2 — ADMISIÓN (AC-10): la lista válida entra y el campo ausente también.

    Un firewall que mata al paciente pasa cualquier test que solo compruebe rechazos (F-d9.1).
    """
    state, ev = _con_refs()
    assert state["members"]["A"]["referencias_comerciales"] == _REFS_VALIDAS
    assert ev["payload"]["referencias_comerciales"] == _REFS_VALIDAS

    # Campo ausente → alta normal (P-d5.1: el veteo es la reunión, no el campo). Y la clave no
    # existe: ausente, no `None` — ni en el payload ni en el estado (patrón `ancla` de TB.7).
    state2 = _estado_base()
    state2, ev2 = led.add_member(state2, {"id": "A", "turnover_cents": 100_000_000}, "ana", 1003)
    assert "referencias_comerciales" not in state2["members"]["A"]
    assert "referencias_comerciales" not in ev2["payload"]


def test_ac_d5_2_update_member_y_semantica_none_vs_vacia():
    """`None` = «no las toques» · `[]` = «vacíala». Y `allowed_keys` NO se relaja (AC-d9.6)."""
    state, _ = _con_refs()

    # Un ajuste de línea de crédito NO borra el veteo en silencio.
    state, _ = led.update_member(state, "A", {"credit_max_cents": 5_000_000}, "ana", 1004)
    assert state["members"]["A"]["referencias_comerciales"] == _REFS_VALIDAS

    # Sustituir.
    nuevas = [{"avalista": "B", "relacion_declarada": "cliente", "antiguedad_meses": 48}]
    state, _ = led.update_member(state, "A", {}, "ana", 1005, referencias_comerciales=nuevas)
    assert state["members"]["A"]["referencias_comerciales"] == nuevas

    # Vaciar: el estado converge a «sin clave» (una sola representación del hecho); el EVENTO
    # conserva el acto de vaciar.
    state, ev = led.update_member(state, "A", {}, "ana", 1006, referencias_comerciales=[])
    assert "referencias_comerciales" not in state["members"]["A"]
    assert ev["payload"]["referencias_comerciales"] == []

    # La lista blanca heredada sigue siendo la lista blanca heredada.
    with pytest.raises(ValueError, match="changes"):
        led.update_member(state, "A", {"referencias_comerciales": _REFS_VALIDAS}, "ana", 1007)

    # …y el firewall también corre por esta vía.
    with pytest.raises(ValueError, match="referencias_comerciales: firewall"):
        led.update_member(state, "A", {}, "ana", 1008, referencias_comerciales=[
            {"avalista": "B", "relacion_declarada": "cliente", "antiguedad_meses": 1,
             "puntuacion": 9}])


# ── AC-d5.3 — El firewall se aplica de verdad, end-to-end (salda AC-d9.5 / fija F-d5.4) ──────

@pytest.mark.parametrize("ref,quien", [
    # Claves — taxonomía heredada. `firewall`, NO `clave desconocida`: si el esquema cerrado
    # matara estos vectores primero, AC-d5.3 pasaría en verde con el firewall DESCABLEADO, que
    # es literalmente F-d5.4 — el fallo que este AC existe para detectar. El `match=` es lo que
    # distingue «lo mató el firewall» de «lo mató la lista blanca», y esa distinción ES AC-d9.5.
    ({"avalista": "B", "relacion_declarada": "proveedor", "antiguedad_meses": 1,
      "puntuacion": 9}, "firewall"),
    ({"avalista": "B", "relacion_declarada": "proveedor", "antiguedad_meses": 1,
      "scoreRelacional": 9}, "firewall"),                    # camelCase → token `score`
    ({"avalista": "B", "relacion_declarada": "proveedor", "antiguedad_meses": 1,
      "lista_negra": True}, "firewall"),                     # bigrama
    # Valores con forma de identidad — el dossier por la puerta de servicio (F-d5.3). Vectores
    # SINTÉTICOS (N8/AC-d5.7).
    ({"avalista": "B", "relacion_declarada": "proveedor", "antiguedad_meses": 1,
      "nota": "Pedro V-12.345.678 lleva 3 años"}, "firewall"),
    ({"avalista": "B", "relacion_declarada": "proveedor", "antiguedad_meses": 1,
      "nota": "RIF J-12345678-9, buen pagador"}, "firewall"),
])
def test_ac_d5_3_firewall_end_to_end(ref, quien):
    """AC-d5.3 — sobre `add_member` REAL, no sobre el escáner aislado.

    Un módulo importado y nunca llamado aparenta una defensa que no existe (F-d9.5). Los
    vectores salen de R2 (Fase 1), no se inventan aquí — el test del escáner lo escribe quien
    cableó el escáner (ST-d5.4).
    """
    state = _estado_base()
    with pytest.raises(ValueError, match=f"referencias_comerciales: {quien}"):
        led.add_member(state, {"id": "A", "turnover_cents": 100_000_000}, "ana", 1003,
                       referencias_comerciales=[ref])


def test_ac_d5_3_control_negativo_el_firewall_no_mata_al_paciente():
    """AC-d5.3 — EL CASO POSITIVO ES OBLIGATORIO.

    Un firewall que rechaza todo pasa cualquier test que solo compruebe rechazos (F-d9.1,
    AC-10). Sin este caso no hay delta: hay un muro. `bancoDeTiempo` (tokens banco/de/tiempo)
    NO colisiona con `ban` — es exactly R2 — y una nota honesta del comité pasa limpia.
    """
    state, _ = _con_refs()
    guardadas = state["members"]["A"]["referencias_comerciales"]
    assert guardadas[0]["nota"] == "Buen proveedor desde 2023"
    assert guardadas[1]["avalista"] == "bancoDeTiempo"


def test_ac_d5_5_las_claves_de_d5_no_colisionan():
    """AC-d5.5 — el centinela de la colisión dormida `veto`/`sancion`/`penalizacion`.

    Por test, no por lectura. Si alguna diera True se renombra LA CLAVE, jamás la taxonomía
    (E-d5.2/N-d9.1): es compartida con seis capas C2C-VE donde esos tokens sí nombran
    vigilancia. Es la instancia local de AC-d9.4.
    """
    for clave in ("referencias_comerciales", "avalista", "relacion_declarada",
                  "antiguedad_meses", "nota"):
        assert fw._key_matches_taxonomy(clave, fw.FORBIDDEN_KEYS) is False, \
            f"`{clave}` colisiona con FORBIDDEN_KEYS — renombra la clave, no la taxonomía"

    # La colisión NO desapareció: sigue ahí, y estos nombres naturales del dominio seguirían
    # rechazados. Por eso el campo se llama `avalista` y no `veto_del_comite` (F-d5.5).
    for natural in ("veto_del_comite", "sancion_previa", "penalizacion"):
        assert fw._key_matches_taxonomy(natural, fw.FORBIDDEN_KEYS) is True


# ── AC-d5.4 — Las referencias no son públicas ────────────────────────────────────────────────

def test_ac_d5_4_solo_el_comite_las_ve():
    """AC-d5.4 — `publico` jamás; `miembro` tampoco; `comite_credito` sí (C-d5.5).

    EL MIEMBRO NO VE QUIÉN LE AVALA, y es criterio escrito: dárselo al propio avalado convierte
    el aval en una posición negociable —«sé que me avalaste»— y por tanto presionable. El comité
    las lee porque decide; el miembro no decide.
    """
    state, _ = _con_refs()

    publico = led.member_statement(state, "A", "publico")
    assert publico == {"seudonimo": led._seudonimo(state, "A")}      # conjunto CERRADO

    propio = led.member_statement(state, "A", "miembro", solicitante="A")
    assert "referencias_comerciales" not in propio

    # AC-10 — la ADMISIÓN: el comité SÍ hace su trabajo. Sin esto, un `return {}` pasaría todos
    # los tests de no-exposición a la vez.
    comite = led.member_statement(state, "A", "comite_credito")
    assert comite["referencias_comerciales"] == _REFS_VALIDAS

    # Ni el nombre de un avalista aparece en ninguna salida no-comité — subcadena sobre la
    # salida cruda, así da igual la forma.
    for scope, kwargs in (("publico", {}), ("miembro", {"solicitante": "A"})):
        for salida in (led.member_statement(state, "A", scope, **kwargs),
                       led.render_statement(state, "A", scope, **kwargs)):
            texto = salida if isinstance(salida, str) else json.dumps(salida)
            assert "bancoDeTiempo" not in texto and "proveedor" not in texto


def test_ac_d5_4_el_exporte_no_las_lleva():
    """AC-d5.4 — `exportar_registros` (D7) tampoco, en ningún scope ni formato.

    Ya es cierto por construcción (el exporte deriva de eventos de obligación y su cabecera es
    un dict cerrado), y aun así se escribe: es regresión contra el FUTURO, no contra el
    presente — patrón de AC-d3.5. El exporte es la superficie de fuga más probable y no por un
    bug: su propósito es salir del sistema (ST-d7.1).
    """
    state, eventos = _estado_y_eventos()
    for scope, kwargs in (("publico", {}), ("miembro", {"solicitante": "A"}),
                          ("comite_credito", {})):
        for formato in exp.FORMATOS:
            salida = exp.exportar_registros(state, eventos, "A", 0, 9999, scope,
                                            formato=formato, **kwargs)
            for rastro in ("referencias_comerciales", "avalista", "bancoDeTiempo",
                           "Buen proveedor"):
                assert rastro not in salida, f"{scope}/{formato}: el exporte filtra `{rastro}`"


def test_ac_d5_6_las_referencias_quedan_en_la_cadena():
    """AC-d5.6 — payload → cadena → `replay` byte a byte, y anclable (D2).

    Por eso van al payload Y al estado, no solo a uno: solo-payload y el comité no puede leer
    por el motor lo que el motor guarda para que lea (AC-d5.4 pasaría por VACUIDAD); solo-estado
    y el veteo no es auditable. Sin tribunales, la evidencia de POR QUÉ se admitió a alguien
    importa (§5.4).
    """
    state, eventos = _estado_y_eventos()

    assert eventos[-1]["payload"]["referencias_comerciales"] == _REFS_VALIDAS
    led.verify_chain(eventos)
    assert led.canonical(led.replay(eventos)) == led.canonical(state)

    # El evento entero está cubierto por el hash de la cadena → una referencia alterada a
    # posteriori rompe la cadena. Eso es lo que hace auditable el veteo.
    manipulados = copy.deepcopy(eventos)
    manipulados[-1]["payload"]["referencias_comerciales"][0]["antiguedad_meses"] = 999
    with pytest.raises(ValueError, match="hash"):
        led.verify_chain(manipulados)
