# -*- coding: utf-8 -*-
"""Aceptación de D3 — visibilidad (AC-d3.1, AC-d3.2, AC-d3.4).

Cada test asegura las reglas de visibilidad y anonimización de extractos (statements)
de los miembros de la célula.
"""

import hashlib
import importlib.util
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

led = _load("mutual_credit_ledger_d3", "src/ledger/mutual_credit_ledger.py")


def _crear_estado_base():
    params = {
        "neg_line_bp": 100,
        "pos_line_bp": 1000,
        "velocity_window_s": 86400,
        "velocity_max_cents": 5_000_000,
        "moneda": "USD",
        "sal_seudonimo": "sal-secreta-xyz",
        "paused": False
    }
    state, _ = led.create_cell("test-cell", params, "ana", 1000)
    state, _ = led.add_member(state, {"id": "A", "turnover_cents": 100_000_000}, "ana", 1001)
    state, _ = led.add_member(state, {"id": "B", "turnover_cents": 100_000_000}, "ana", 1002)
    return state


@pytest.mark.parametrize("scope_invalido", ["admin", None, "", "publico ", "COMITE_CREDITO"])
def test_ac_d3_1_scope_obligatorio(scope_invalido):
    """Establece que el scope es obligatorio y solo acepta valores de la lista led.SCOPES.
    
    AC-d3.1: Previene que se asuman scopes por defecto inseguros o se consulten datos usando scopes inválidos.
    """
    state = _crear_estado_base()
    
    # Sin scope (llamado directo omitiéndolo) debe lanzar TypeError
    with pytest.raises(TypeError):
        led.member_statement(state, "A")
        
    # Scope inválido lanza ValueError con match="scope"
    with pytest.raises(ValueError, match="scope"):
        led.member_statement(state, "A", scope=scope_invalido)
        
    # CONTROL NEGATIVO obligatorio: los 3 scopes válidos NO lanzan.
    for scope_valido in led.SCOPES:
        solicitante = "A" if scope_valido == "miembro" else None
        res = led.member_statement(state, "A", scope=scope_valido, solicitante=solicitante)
        assert isinstance(res, dict)


def test_ac_d3_2_miembro_solo_se_ve_a_si_mismo():
    """Valida que un miembro solo pueda ver su propio extracto con el scope 'miembro'.
    
    AC-d3.2: Evita la fuga de datos financieros privados entre miembros de la célula.
    """
    state = _crear_estado_base()
    
    # scope="miembro", solicitante="A", member_id="A" -> devuelve dict; y DEBE ser == al de scope="comite_credito"
    dict_miembro = led.member_statement(state, "A", scope="miembro", solicitante="A")
    dict_comite = led.member_statement(state, "A", scope="comite_credito")
    assert dict_miembro == dict_comite
    
    # scope="miembro", solicitante="B", member_id="A" -> pytest.raises(ValueError, match="solicitante")
    with pytest.raises(ValueError, match="solicitante"):
        led.member_statement(state, "A", scope="miembro", solicitante="B")
        
    # scope="miembro" sin solicitante -> pytest.raises(ValueError, match="solicitante")
    with pytest.raises(ValueError, match="solicitante"):
        led.member_statement(state, "A", scope="miembro")
        
    # lo mismo para render_statement: solicitante ajeno -> raises(ValueError, match="solicitante")
    with pytest.raises(ValueError, match="solicitante"):
        led.render_statement(state, "A", scope="miembro", solicitante="B")
        
    # lo mismo para render_statement: sin solicitante -> raises(ValueError, match="solicitante")
    with pytest.raises(ValueError, match="solicitante"):
        led.render_statement(state, "A", scope="miembro")


def test_ac_d3_4_seudonimo_resiste_fuerza_bruta():
    """Verifica que el seudónimo resiste un ataque de fuerza bruta gracias al uso de la sal.
    
    AC-d3.4: Garantiza que un atacante no pueda deducir la identidad real a partir del hash sin conocer la sal.
    """
    params = {
        "neg_line_bp": 100,
        "pos_line_bp": 1000,
        "velocity_window_s": 86400,
        "velocity_max_cents": 5_000_000,
        "moneda": "USD",
        "sal_seudonimo": "sal-secreta-xyz",
        "paused": False
    }
    state, _ = led.create_cell("test-cell", params, "ana", 1000)
    
    # Célula con 500 miembros ("m0".."m499")
    ts = 1001
    for i in range(500):
        mid = f"m{i}"
        state, _ = led.add_member(state, {"id": mid, "turnover_cents": 100_000_000}, "ana", ts)
        ts += 1
        
    # Obtiene seudónimo del miembro "m42"
    seudo = led.member_statement(state, "m42", scope="publico")["seudonimo"]
    
    # ATAQUE SIN SAL: comprobar que ninguno coincide con el seudónimo
    coincidencia_sin_sal = False
    for i in range(500):
        mid = f"m{i}"
        candidato = hashlib.sha256(led.canonical([state["cell_id"], mid])).hexdigest()[:16]
        if candidato == seudo:
            coincidencia_sin_sal = True
            break
    assert not coincidencia_sin_sal, "El ataque sin sal no debería tener éxito"
    
    # CONTROL NEGATIVO: comprobar que con sal real sí encuentra a "m42"
    encontrado = None
    for i in range(500):
        mid = f"m{i}"
        candidato = hashlib.sha256(led.canonical([state["cell_id"], mid, "sal-secreta-xyz"])).hexdigest()[:16]
        if candidato == seudo:
            encontrado = mid
            break
            
    assert encontrado == "m42", f"El ataque con sal debería haber encontrado 'm42', pero obtuvo: {encontrado}"


# ══════════════════════════════════════════════════════════════════════════════
# Los AC de criterio (Opus): AC-7, AC-10, AC-d3.3, AC-d3.5.
# ══════════════════════════════════════════════════════════════════════════════

def _recorre(obj):
    """Aplana cualquier salida a (claves, valores escalares), recursivo por dict/list/tuple."""
    claves, valores = set(), []
    def _baja(o):
        if isinstance(o, dict):
            for k, v in o.items():
                claves.add(k); _baja(v)
        elif isinstance(o, (list, tuple)):
            for v in o:
                _baja(v)
        else:
            valores.append(o)
    _baja(obj)
    return claves, valores


def test_ac_10_el_comite_puede_hacer_su_trabajo():
    """AC-10 — control de ADMISIÓN. Un scope que no deja ver nada a nadie pasa cualquier test
    de no-exposición: un `return {}` pasaría AC-7, AC-d3.3 y AC-d3.5 a la vez. El comité TIENE
    que poder trabajar, así que se fijan los VALORES, no solo que no lance.
    """
    state = _crear_estado_base()
    state, _ = led.record_obligation(
        state, {"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 5000}, 1050)

    stmt = led.member_statement(state, "A", scope="comite_credito")
    assert set(stmt.keys()) == {
        "member_id", "status", "balance_cents", "credit_min_cents",
        "credit_max_cents", "owed_by_cents", "owed_to_cents", "projected_cents"}
    assert stmt["member_id"] == "A"
    assert stmt["owed_by_cents"] == 5000          # A debe: lo ve el comité
    assert stmt["projected_cents"] == -5000       # y ve la proyección que decide el crédito

    # `miembro` sobre sí mismo ve EXACTAMENTE lo mismo (no una versión degradada).
    assert led.member_statement(state, "A", scope="miembro", solicitante="A") == stmt

    # El render del comité lleva importes de verdad.
    md = led.render_statement(state, "A", scope="comite_credito")
    assert "50.00 $" in md and "Projected Balance" in md


def test_ac_d3_3_el_tipo_de_salida_publica_es_cerrado():
    """AC-d3.3 — bajo `publico` el conjunto de claves es EXACTAMENTE {"seudonimo"}.

    Igualdad exacta de conjuntos, no «subconjunto de lo permitido»: el muro es el TIPO de
    salida (H1), no una lista de nombres prohibidos. Un `salud_crediticia` o un
    `percentil_de_actividad` futuro (F-d3.4: el escalar con nombre benigno) rompe este test
    SIN que nadie tuviera que preverlo. Una lista negra no lo cazaría; una blanca cerrada sí.
    """
    state = _crear_estado_base()
    salida = led.member_statement(state, "A", scope="publico")
    assert set(salida.keys()) == {"seudonimo"}

    # N-d3.2 — ni el `status`: la escalera de sanciones sobre un seudónimo estable es una marca.
    assert "status" not in salida

    # El seudónimo es estable (D2 necesita enlazar) y distinto por miembro.
    assert salida == led.member_statement(state, "A", scope="publico")
    assert salida["seudonimo"] != led.member_statement(state, "B", scope="publico")["seudonimo"]

    # El render público tampoco filtra importes (N-d3.1).
    md = led.render_statement(state, "A", scope="publico")
    assert salida["seudonimo"] in md
    assert "Balance" not in md and "$" not in md


def test_ac_d3_5_la_sal_no_sale_nunca():
    """AC-d3.5 — la sal no aparece en NINGUNA salida pública. Una sal filtrada revela todos los
    seudónimos a la vez (F-d3.3), así que es un fallo de todo o nada.

    `cell_metrics` ya no puede filtrarla por construcción (expone 5 campos nombrados, no
    `params` entero), pero se fija igual: es regresión contra el futuro, no contra el presente.
    """
    state = _crear_estado_base()
    state, _ = led.record_obligation(
        state, {"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 5000}, 1050)
    SAL = state["params"]["sal_seudonimo"]

    for salida in (led.member_statement(state, "A", scope="publico"),
                   led.render_statement(state, "A", scope="publico"),
                   led.cell_metrics(state)):
        _, valores = _recorre(salida)
        assert SAL not in valores
        assert SAL not in str(salida)   # atrapa la sal incrustada en el markdown


def test_ac_7_ningun_punto_de_consulta_publico_expone_saldo_mas_identidad():
    """AC-7 (el que importa) — N7/I-VE3: el libro de saldos legible es el mapa de matraqueo.

    Por ENUMERACIÓN, no por lista de casos: una lista de funciones a probar envejece — el delta
    siguiente añade una vista, nadie actualiza la lista, y el test sigue verde.

    La lectura ingenua («llamar con scope=publico donde lo acepte») NO cumple su propio porqué:
    una vista nueva SIN scope no se llamaría y no rompería nada. Por eso se parte la superficie
    pública en dos con motivo escrito, y una función nueva que no esté en ninguna de las dos
    listas ROMPE este test el día que se escribe, obligando a su autor a decidir.
    """
    import inspect
    publicas = {n for n in dir(led)
                if not n.startswith("_")
                and inspect.isfunction(getattr(led, n))
                and getattr(led, n).__module__ == led.__name__}

    CON_SCOPE = {"member_statement", "render_statement"}

    SIN_SCOPE = {
        # ST-d3.4 — vista INTERNA: es el input del solver, que corre DENTRO de la célula.
        # Ponerle scope rompería el clearing sin proteger nada. No se «completa» el delta aquí.
        "to_clearing_input",
        # Agregado de CÉLULA, no de persona (§3). Un agregado no se convierte en escalar de
        # persona por mucho que se le insista — el muro es el tipo de salida.
        "cell_metrics",
        # Mutadores por la puerta de ratificación (M8) y maquinaria: no son puntos de consulta.
        "create_cell", "add_member", "update_member", "record_obligation",
        "apply_clearing", "settle_obligation", "pause_cell", "resume_cell",
        "replay", "verify_chain", "canonical",
    }

    sin_clasificar = publicas - CON_SCOPE - SIN_SCOPE
    assert not sin_clasificar, (
        f"Función pública nueva sin clasificar: {sin_clasificar}. Si es un punto de consulta, "
        f"dale `scope` y añádela a CON_SCOPE. Si no lo es, añádela a SIN_SCOPE CON EL MOTIVO "
        f"escrito. No la añadas a SIN_SCOPE para poner el test verde: esa decisión es el delta."
    )
    for nombre in CON_SCOPE:
        assert "scope" in inspect.signature(getattr(led, nombre)).parameters

    state = _crear_estado_base()
    state, _ = led.record_obligation(
        state, {"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 5000}, 1050)
    ids_reales = set(state["members"])

    for nombre in sorted(CON_SCOPE):
        for mid in sorted(ids_reales):
            salida = getattr(led, nombre)(state, mid, "publico")
            claves, valores = _recorre(salida)
            texto = str(salida)
            # Ni identidad…
            assert not (ids_reales & claves), f"{nombre}: member_id como clave bajo publico"
            assert not (ids_reales & {v for v in valores if isinstance(v, str)}), \
                f"{nombre}: member_id como valor bajo publico"
            assert not any(m in texto for m in ids_reales), f"{nombre}: identidad en el texto"
            # …ni NINGÚN número. El muro es el TIPO, no una lista de importes conocidos:
            # comparar contra {5000, -5000, …} es la lista que envejece que este AC existe para
            # evitar — un saldo de 0, o un importe que el fixture no usa, pasaría limpio.
            # Bajo `publico` no hay nada numérico que devolver, así que la regla es total.
            # (Descubierto por MUTACIÓN: filtrar balance_cents=0 pasaba este test.)
            numeros = [v for v in valores if isinstance(v, (int, float)) and not isinstance(v, bool)]
            assert not numeros, f"{nombre}: valor numérico {numeros} bajo publico — ¿un importe?"
