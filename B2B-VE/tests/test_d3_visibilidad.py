# -*- coding: utf-8 -*-
"""Aceptación de D3 — visibilidad (AC-d3.1, AC-d3.2, AC-d3.4).

Cada test asegura las reglas de visibilidad y anonimización de extractos (statements)
de los miembros de la célula.
"""

import hashlib
import importlib.util
import json
import re
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
    # LOS MÓDULOS SE DESCUBREN POR GLOB, NO POR LISTA (endurecido en TB.8).
    #
    # Hasta TB.7 esto era una lista literal `[led, anclaje, exportes]`, y ahí vivía el mismo
    # defecto que este test existe para prevenir, un nivel más arriba: TB.4 mató la lista de
    # FUNCIONES que envejece y dejó viva una lista de MÓDULOS que envejece igual. F-d7.5 ya
    # obligó a parchearla a mano una vez (prometía que AC-7 cubría `exportar_registros`
    # «automáticamente», y era falso viviendo en otro módulo).
    #
    # TB.8 lo confirmó por evidencia, no por sospecha: al escribir `src/gobernanza/multisig.py`
    # con TRES funciones públicas nuevas, este test SIGUIÓ VERDE. Un módulo nuevo no rompía
    # nada — sus funciones simplemente no se enumeraban. A la segunda no se parchea: se
    # arregla. Ahora un paquete nuevo entra solo, y su autor tiene que clasificar lo que
    # escriba el día que lo escriba.
    #
    # Coste asumido a propósito: entran también `clearing_solver.py` y `firewall/herencia.py`,
    # que nadie enumeraba y sobre los que nadie había decidido nada. Clasificarlas es trabajo
    # real y es el correcto.
    archivos = sorted((_BASE / "src").rglob("*.py"))
    modulos = [_load("ac7_%s" % p.relative_to(_BASE / "src").as_posix().replace("/", "_")[:-3],
                     p.relative_to(_BASE).as_posix())
               for p in archivos]

    # LA ENUMERACIÓN SE DECLARA COMPLETA, Y SE COMPRUEBA.
    #
    # Esto lo puso la MUTACIÓN, no el diseño: al volver `modulos` a una lista literal, la suite
    # entera se quedaba VERDE — `multisig.py` dejaba de enumerarse y nadie protestaba. La
    # defensa de arriba no hablaba. Con el glob el assert es trivialmente cierto; con una lista
    # literal falla Y DICE QUÉ MÓDULO FALTA, que es lo que lo hace una defensa y no una
    # convención. Sin esta línea, todo el endurecimiento de TB.8 se deshace con un `git revert`
    # silencioso.
    cubiertos = {m.__file__ for m in modulos}
    assert cubiertos == {str(p) for p in archivos}, (
        "La enumeración de AC-7 no cubre todo `src/`. Faltan: %s. NO la conviertas en una "
        "lista literal: una lista de módulos envejece igual que la lista de funciones que "
        "este test existe para evitar (F-d7.5 ya obligó a parchearla a mano una vez, y en "
        "TB.8 un paquete nuevo con 3 públicas pasó sin que nada se pusiera rojo)."
        % sorted({str(p) for p in archivos} - cubiertos))
    publicas = {n for m in modulos for n in dir(m)
                if not n.startswith("_")
                and inspect.isfunction(getattr(m, n))
                and getattr(m, n).__module__ == m.__name__}

    CON_SCOPE = {"member_statement", "render_statement", "exportar_registros"}

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
        # D6 (TB.6) — `salida_con_saldo`. La objeción hay que contestarla, no esquivarla:
        # DEVUELVE SALDO E IDENTIDAD. Cierto, y no la hace un punto de consulta: devuelve el par
        # canónico `(state, event)`, el mismo que `add_member` o `settle_obligation`, que también
        # devuelven un `state` lleno de saldos e identidades reales. Si ese par contara como
        # salida acotable, los ocho mutadores de arriba estarían mal clasificados desde TB.4.
        # Lo que decide es el PORQUÉ de C-d3.1, no la forma del valor de retorno:
        #  1. Un mutador no tiene a quién acotar: quien llama no consulta, RATIFICA — ya pasó la
        #     puerta de M8 y trae `ratified_by`. Un `scope="publico"` aquí no significaría nada:
        #     ¿una salida que se ejecuta pero devuelve el saldo tachado? El estado ya está mutado.
        #  2. Acotar el `state` de vuelta ROMPERÍA `replay`: AC-7 de D6 exige que reconstruya el
        #     estado byte a byte, y un estado filtrado no es el estado. El muro «cero numéricos»
        #     aplicado a un mutador mata al paciente (F-d9.1, la clase que el control negativo
        #     existe para cazar).
        #  3. La fuga real de una salida no está en su retorno: está en su EVENTO, que lleva
        #     `member_id` y la `resolucion` — y con ella quién avaló a quién, que D5 reserva al
        #     comité (C-d5.5). Y el evento YA está cubierto: `anclar` solo emite hashes y
        #     `exportar_registros` está en CON_SCOPE desde TB.7. Poner scope en el mutador no
        #     taparía esa fuga; taparla donde ya está tapada es teatro.
        "salida_con_saldo",
        # D2 (`anclaje.py`) — emiten HASHES y raíces, jamás payloads: no hay identidad ni
        # importe que acotar. `anclar` es read/emit sobre la cadena; `verificar_inclusion` es
        # la función del ÁRBITRO y ni siquiera recibe `events` (C-d2.5). Darles scope no
        # protegería nada y rompería al árbitro, que es a quien sirven.
        "anclar", "prueba_de_inclusion", "verificar_inclusion",
        # D8 (TB.6b) — mismo motivo que `salida_con_saldo`, y más fácil: mueven un booleano de
        # `params`. No devuelven ni saldo ni identidad de nadie, y quien llama RATIFICA (traen
        # `ratified_by` por la puerta de M8), no consulta. El hecho que registran —el puente
        # está parado— es de la CÉLULA, no de una persona: `cell_metrics` ya lo expone y es
        # agregado. No hay nada que acotar.
        "puente_pausar", "puente_reanudar",
        # D4 (TB.8) — `src/gobernanza/multisig.py`. No reciben `state`: NO HAY MIEMBRO QUE
        # ACOTAR. Ni saldo, ni identidad, ni nada del ledger — el módulo ni siquiera lo
        # importa. `describir_politica` sí rinde una vista legible, pero DE LA POLÍTICA (un
        # documento de gobernanza sobre una reserva que vive fuera del motor), no del libro:
        # lo que expone son alias, cargos y etiquetas opacas que el llamador acaba de pasar.
        # Y no queda sin acotar: AC-d4.7 la acota por su cuenta (direcciones truncadas, nada
        # que no estuviera en la política) — que es la misma propiedad que persigue C-d3.1,
        # aplicada donde sí hay algo que filtrar.
        "verificar_umbral", "verificar_formato_direccion", "describir_politica",
        # CLEARING (upstream) — las descubre el glob de TB.8; hasta ahora nadie las enumeraba
        # y nadie había decidido nada sobre ellas. Se clasifican, no se ignoran.
        #   `clear` es el solver: corre DENTRO de la célula sobre el input que le da
        #   `to_clearing_input`, que ya está en SIN_SCOPE por ST-d3.4 y por el mismo motivo.
        #   Acotar el solver es acotar la compensación, que es el producto de la célula.
        #   `render_report` es la CARA de `clear`: rinde la propuesta de liquidación para el
        #   comité de crédito, con IDs e importes. Es el par simétrico de `to_clearing_input`
        #   —uno es el input del solver y el otro su salida— y vive del mismo lado de la
        #   membrana: dentro. Un scope aquí rompería el clearing sin proteger nada, porque
        #   quien lo lee ya está dentro. Lo que salga de la célula pasa por
        #   `exportar_registros`, que SÍ lleva scope desde TB.7 — ahí es donde está la fuga
        #   y ahí es donde está tapada.
        "clear", "render_report",
    }

    sin_clasificar = publicas - CON_SCOPE - SIN_SCOPE
    assert not sin_clasificar, (
        f"Función pública nueva sin clasificar: {sin_clasificar}. Si es un punto de consulta, "
        f"dale `scope` y añádela a CON_SCOPE. Si no lo es, añádela a SIN_SCOPE CON EL MOTIVO "
        f"escrito. No la añadas a SIN_SCOPE para poner el test verde: esa decisión es el delta."
    )
    def _buscar(nombre):
        for m in modulos:
            if hasattr(m, nombre):
                return getattr(m, nombre)
        raise AssertionError(nombre)

    for nombre in CON_SCOPE:
        params = inspect.signature(_buscar(nombre)).parameters
        assert "scope" in params, f"{nombre} está en CON_SCOPE pero no acepta scope"
        # …y sin default: un default es la configuración que nadie revisa (C-d3.1/F-d3.1).
        assert params["scope"].default is inspect.Parameter.empty, \
            f"{nombre}: `scope` tiene default — el delta queda instalado y desactivado a la vez"

    state = _crear_estado_base()
    state, ev = led.record_obligation(
        state, {"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 5000}, 1050)
    ids_reales = set(state["members"])
    eventos = [ev]

    # Cada firma se invoca con lo suyo; lo que se asevera es idéntico para todas.
    _INVOCAR = {
        "member_statement":   lambda f, mid: f(state, mid, "publico"),
        "render_statement":   lambda f, mid: f(state, mid, "publico"),
        "exportar_registros": lambda f, mid: f(state, eventos, mid, 0, 9999, "publico"),
    }
    assert set(_INVOCAR) == CON_SCOPE, "toda función con scope necesita su invocación aquí"

    for nombre in sorted(CON_SCOPE):
        for mid in sorted(ids_reales):
            salida = _INVOCAR[nombre](_buscar(nombre), mid)
            texto = salida if isinstance(salida, str) else str(salida)

            # 1) IDENTIDAD — vale para toda forma de salida: búsqueda de subcadena sobre la
            #    salida CRUDA, así que da igual que sea dict, markdown o CSV.
            assert not any(m in texto for m in ids_reales), \
                f"{nombre}: identidad real en la salida publico"

            # 2) IMPORTES — el muro depende de la FORMA de la salida, y decirlo es el punto:
            if isinstance(salida, dict):
                # Salida estructurada: muro de TIPO. Cero numéricos. No una lista de importes
                # conocidos — comparar contra {5000, -5000, …} es la lista que envejece que
                # este AC existe para evitar: un saldo de 0, o un importe que el fixture no
                # usa, pasaría limpio. (Descubierto POR MUTACIÓN: filtrar balance_cents=0
                # pasaba este test.) Bajo `publico` no hay nada numérico que devolver.
                _, valores = _recorre(salida)
                numeros = [v for v in valores
                           if isinstance(v, (int, float)) and not isinstance(v, bool)]
                assert not numeros, f"{nombre}: numérico {numeros} bajo publico — ¿un importe?"
            else:
                # Salida SERIALIZADA (str). El muro de tipo NO transfiere y fingir que sí sería
                # peor que no tenerlo: `_recorre` sobre un str no ve ningún int, así que el
                # chequeo pasaría POR VACUIDAD. (Se descubrió así: AC-7 daba verde sobre el
                # exporte sin comprobar un solo importe.) Y el muro tampoco puede ser «cero
                # dígitos»: la cabecera lleva `periodo`, que son ints legítimos.
                # El invariante real: los importes individuales viven en `lineas`, y bajo
                # `publico` no hay líneas que dar.
                if nombre == "exportar_registros":
                    datos = json.loads(salida)
                    assert datos["lineas"] == [], \
                        f"{nombre}: líneas con importes individuales bajo publico"
                    assert "saldo_inicial" not in datos and "saldo_final" not in datos, \
                        f"{nombre}: saldo del miembro bajo publico"
                    assert "miembro_id" not in datos, f"{nombre}: miembro_id bajo publico"
                else:
                    # Markdown de `render_statement`. Tampoco vale «cero dígitos»: el seudónimo
                    # es hexadecimal y los lleva. El muro es la FORMA CERRADA, igual que la
                    # igualdad exacta de claves de AC-d3.3: la salida es exactamente la línea
                    # del seudónimo, así que no hay hueco donde quepa un importe.
                    seudo = led.member_statement(state, mid, scope="publico")["seudonimo"]
                    assert texto == f"# Statement — {seudo}\n", \
                        f"{nombre}: el render publico no es exactamente la línea del seudónimo"
