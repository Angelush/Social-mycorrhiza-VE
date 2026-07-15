# -*- coding: utf-8 -*-
"""Aceptación de D7 — exportación de registros (AC-d7.3, AC-d7.5, AC-d7.9, AC-d7.10).

Cada test asegura las reglas del módulo de exportación de registros fiscales/contables.
"""

import csv
import importlib.util
import io
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

led = _load("mutual_credit_ledger_d7", "src/ledger/mutual_credit_ledger.py")
exp = _load("exportes_d7", "src/ledger/exportes.py")


@pytest.fixture
def datos_prueba():
    """Fixture que crea una célula USD con miembros A y B y registra una obligación."""
    params = {
        "neg_line_bp": 100,
        "pos_line_bp": 1000,
        "velocity_window_s": 86400,
        "velocity_max_cents": 5_000_000,
        "moneda": "USD",
        "sal_seudonimo": "sal-x",
        "paused": False
    }
    events = []
    ts = 1000
    
    state, ev_create = led.create_cell("test-cell", params, "ana", ts)
    events.append(ev_create)
    
    ts += 1
    state, ev_a = led.add_member(state, {"id": "A", "turnover_cents": 100_000_000}, "ana", ts)
    events.append(ev_a)
    
    ts += 1
    state, ev_b = led.add_member(state, {"id": "B", "turnover_cents": 100_000_000}, "ana", ts)
    events.append(ev_b)
    
    ts += 1
    state, ev_ob = led.record_obligation(state, {"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 5000}, ts)
    events.append(ev_ob)
    
    return state, events


def test_ac_d7_3_enteros_sin_float(datos_prueba):
    """Asegura que todos los importes en JSON y CSV se representen como enteros estrictos.

    AC-d7.3: Evita que el formateo a flotantes (para presentación visual) introduzca errores de
    redondeo cuando los datos entran a un software contable o a una hoja de cálculo.
    """
    state, events = datos_prueba

    # Caso JSON:
    json_str = exp.exportar_registros(state, events, "A", 0, 9999, "comite_credito", formato="json")
    datos_json = json.loads(json_str)

    assert isinstance(datos_json["saldo_inicial"], int) and not isinstance(datos_json["saldo_inicial"], bool)
    assert isinstance(datos_json["saldo_final"], int) and not isinstance(datos_json["saldo_final"], bool)
    for line in datos_json["lineas"]:
        assert isinstance(line["importe_centavos"], int) and not isinstance(line["importe_centavos"], bool)

    # Ningún importe contiene '.' ni ',' en su formato string
    assert "." not in str(datos_json["saldo_inicial"])
    assert "," not in str(datos_json["saldo_inicial"])
    assert "." not in str(datos_json["saldo_final"])
    assert "," not in str(datos_json["saldo_final"])
    for line in datos_json["lineas"]:
        assert "." not in str(line["importe_centavos"])
        assert "," not in str(line["importe_centavos"])

    # Caso CSV:
    csv_str = exp.exportar_registros(state, events, "A", 0, 9999, "comite_credito", formato="csv")
    rows = list(csv.reader(io.StringIO(csv_str)))

    # Buscamos encabezado para saber la columna
    data_header_index = -1
    for i, r in enumerate(rows):
        if r and r[0] == "fecha":
            data_header_index = i
            break
    assert data_header_index != -1
    
    col_idx = rows[data_header_index].index("importe_centavos")

    for r in rows[data_header_index+1:]:
        val = r[col_idx]
        assert re.match(r"^-?\d+$", val), f"El importe '{val}' en CSV no es un entero válido"
        assert "." not in val
        assert "," not in val

    # Chequeamos también los importes en los comentarios de metadatos del CSV
    for r in rows:
        if r and r[0] == "#" and r[1] in ("saldo_inicial", "saldo_final"):
            val = r[2]
            assert re.match(r"^-?\d+$", val)
            assert "." not in val
            assert "," not in val


def test_ac_d7_5_la_moneda_va_una_vez(datos_prueba):
    """Verifica que la unidad monetaria figure únicamente en la cabecera.

    AC-d7.5: La presencia de la columna moneda por línea induce a confusión de multi-moneda
    e invita al llamador a deducir erróneamente tasas de conversión de cambio.
    """
    state, events = datos_prueba

    # Caso JSON:
    json_str = exp.exportar_registros(state, events, "A", 0, 9999, "comite_credito", formato="json")
    assert json_str.count('"moneda"') == 1

    datos_json = json.loads(json_str)
    for line in datos_json["lineas"]:
        assert "moneda" not in line

    # Caso CSV:
    csv_str = exp.exportar_registros(state, events, "A", 0, 9999, "comite_credito", formato="csv")
    rows = list(csv.reader(io.StringIO(csv_str)))

    header_row = None
    for r in rows:
        if r and r[0] == "fecha":
            header_row = r
            break
    assert header_row is not None
    assert "moneda" not in header_row

    # Ambas salidas no contienen palabras prohibidas de cambio
    for output in (json_str, csv_str):
        output_lower = output.lower()
        for forbidden in ("tasa", "tipo_de_cambio", "exchange_rate", "fx", "paralelo", "bcv"):
            assert forbidden not in output_lower


def test_ac_d7_9_csv_sin_inyeccion():
    """Valida la mitigación de inyección de fórmulas en hojas de cálculo.

    AC-d7.9: Los identificadores elegidos por humanos pueden contener prefijos de fórmula.
    El motor debe escapar los campos de texto, pero permitir que el número negativo empiece con '-'.
    """
    params = {
        "neg_line_bp": 100,
        "pos_line_bp": 1000,
        "velocity_window_s": 86400,
        "velocity_max_cents": 5_000_000,
        "moneda": "USD",
        "sal_seudonimo": "sal-x",
        "paused": False
    }
    events = []
    
    state, ev_create = led.create_cell("test-cell-injection", params, "ana", 1000)
    events.append(ev_create)
    
    # Miembros con nombres conflictivos
    for mid in ("A", "=cmd", "+x", "-y", "@z"):
        state, ev_m = led.add_member(state, {"id": mid, "turnover_cents": 100_000_000}, "ana", 1001)
        events.append(ev_m)
        
    # Obligación entre "=cmd" y "+x"
    state, ev_ob = led.record_obligation(
        state, 
        {"id": "o1", "debtor": "=cmd", "creditor": "+x", "amount_cents": 5000}, 
        1002
    )
    events.append(ev_ob)
    
    csv_str = exp.exportar_registros(state, events, "=cmd", 0, 9999, "comite_credito", formato="csv")
    rows = list(csv.reader(io.StringIO(csv_str)))
    
    # Buscamos encabezado para saber columnas
    data_header_index = -1
    for i, r in enumerate(rows):
        if r and r[0] == "fecha":
            data_header_index = i
            break
    assert data_header_index != -1
    
    col_importe_idx = rows[data_header_index].index("importe_centavos")
    
    for r_idx, r in enumerate(rows):
        for c_idx, cell in enumerate(r):
            # Control sobre importe centavos en las filas de datos
            if r_idx > data_header_index and c_idx == col_importe_idx:
                assert re.match(r"^-?\d+$", cell), f"El importe centavos no numérico: {cell}"
                # SÍ puede empezar por "-"
                continue
            
            # Control sobre saldo inicial/final
            if r and r[0] == "#" and r[1] in ("saldo_inicial", "saldo_final") and c_idx == 2:
                assert re.match(r"^-?\d+$", cell)
                continue
                
            # Resto de celdas de texto no deben empezar por fórmulas crudas
            assert not cell.startswith("="), f"Celda '{cell}' empieza con '=' crudo"
            assert not cell.startswith("+"), f"Celda '{cell}' empieza con '+' crudo"
            assert not cell.startswith("-"), f"Celda '{cell}' empieza con '-' crudo"
            assert not cell.startswith("@"), f"Celda '{cell}' empieza con '@' crudo"


def test_ac_d7_10_los_dos_formatos_coinciden(datos_prueba):
    """Asegura la coherencia exacta entre la salida JSON y CSV para una misma consulta.

    AC-d7.10: Un miembro del comité de crédito o el propio miembro deben ver exactamente
    los mismos datos de cabecera y líneas históricas sin importar el formato elegido.
    """
    state, events = datos_prueba

    json_str = exp.exportar_registros(state, events, "A", 0, 9999, "comite_credito", formato="json")
    csv_str = exp.exportar_registros(state, events, "A", 0, 9999, "comite_credito", formato="csv")

    datos_json = json.loads(json_str)
    rows = list(csv.reader(io.StringIO(csv_str)))

    # Parseamos la cabecera CSV
    datos_csv_cabecera = {}
    data_header_index = -1
    for i, r in enumerate(rows):
        if not r:
            continue
        if r[0] == "#":
            key = r[1]
            val = r[2]
            if key in ("saldo_inicial", "saldo_final"):
                val = int(val)
            datos_csv_cabecera[key] = val
        elif r[0] == "fecha":
            data_header_index = i
            break

    # 1) Verificación de cabeceras
    assert datos_json["celula_id"] == datos_csv_cabecera["celula_id"]
    assert datos_json["miembro_id"] == datos_csv_cabecera["miembro_id"]
    assert datos_json["moneda"] == datos_csv_cabecera["moneda"]
    assert datos_json["saldo_inicial"] == datos_csv_cabecera["saldo_inicial"]
    assert datos_json["saldo_final"] == datos_csv_cabecera["saldo_final"]

    # 2) Verificación de líneas
    json_lines = datos_json["lineas"]
    csv_lines = []
    
    if data_header_index != -1:
        headers = rows[data_header_index]
        for r in rows[data_header_index+1:]:
            line_dict = dict(zip(headers, r))
            # Conversión de tipos y desescape
            line_dict["fecha"] = int(line_dict["fecha"])
            line_dict["importe_centavos"] = int(line_dict["importe_centavos"])
            for k in ("contraparte", "referencia"):
                if line_dict[k].startswith("'"):
                    line_dict[k] = line_dict[k][1:]
            csv_lines.append(line_dict)

    assert len(json_lines) == len(csv_lines)
    for jl, cl in zip(json_lines, csv_lines):
        assert jl["fecha"] == cl["fecha"]
        assert jl["tipo"] == cl["tipo"]
        assert jl["contraparte"] == cl["contraparte"]
        assert jl["importe_centavos"] == cl["importe_centavos"]
        assert jl["referencia"] == cl["referencia"]
        assert jl["hash_evento"] == cl["hash_evento"]


# ══════════════════════════════════════════════════════════════════════════════
# Los AC de criterio (Opus): AC-d7.1/d7.2/d7.4/d7.6/d7.7/d7.8.
# ══════════════════════════════════════════════════════════════════════════════
import ast as _ast
import copy as _copy
from pathlib import Path as _Path


def test_ac_d7_1_el_scope_es_el_de_d3(datos_prueba):
    """AC-d7.1 — mismo scope que D3, sin control de acceso nuevo (C-d7.3).

    Dos controles de acceso divergen: se arregla uno y el otro se queda con el agujero (F-d7.5).
    """
    state, events = datos_prueba
    import inspect
    params = inspect.signature(exp.exportar_registros).parameters

    # Sin default: la firma de la spec §2 traía scope="miembro", que contradice C-d3.1 y su
    # propio AC-d7.1 («scope ausente -> ValueError»: con default no lanza nada). Ver DESIGN §0.1.
    assert params["scope"].default is inspect.Parameter.empty
    assert exp.exportar_registros.__module__ != led.__name__  # módulo propio, patrón anclaje.py

    with pytest.raises(TypeError):            # omitirlo: defensa de Python, más temprana
        exp.exportar_registros(state, events, "A", 0, 9999)
    for malo in ("admin", None, "", "COMITE_CREDITO"):
        with pytest.raises(ValueError, match="scope"):
            exp.exportar_registros(state, events, "A", 0, 9999, malo)
    with pytest.raises(ValueError, match="solicitante"):
        exp.exportar_registros(state, events, "A", 0, 9999, "miembro", solicitante="B")
    with pytest.raises(ValueError, match="solicitante"):
        exp.exportar_registros(state, events, "A", 0, 9999, "miembro")
    with pytest.raises(ValueError, match="formato"):
        exp.exportar_registros(state, events, "A", 0, 9999, "comite_credito", formato="pdf")

    # ADMISIÓN (AC-10): el miembro sobre sí mismo SÍ obtiene su exporte, y con sus líneas.
    propio = json.loads(exp.exportar_registros(state, events, "A", 0, 9999, "miembro", solicitante="A"))
    assert propio["miembro_id"] == "A" and len(propio["lineas"]) > 0


def test_ac_d7_2_pura_sin_io(datos_prueba):
    """AC-d7.2 — devuelve str, no escribe, no muta (C-d7.1).

    Mismo porqué que `anclar`: un motor sin disco ni red corre en un apagón y no es capturable.
    """
    state, events = datos_prueba
    est0, ev0 = _copy.deepcopy(state), _copy.deepcopy(events)

    salida = exp.exportar_registros(state, events, "A", 0, 9999, "comite_credito")
    assert isinstance(salida, str)
    assert state == est0 and events == ev0, "exportar_registros mutó sus argumentos"

    # No acepta ruta ni descriptor: no hay por dónde pedirle que escriba.
    import inspect
    params = set(inspect.signature(exp.exportar_registros).parameters)
    assert not (params & {"ruta", "path", "archivo", "file", "fd", "salida"})

    # Y no toca el disco ni la red aunque estén disponibles: con open/socket saboteados, completa.
    import builtins, socket
    _open, _socket = builtins.open, socket.socket
    def _boom(*a, **k):
        raise AssertionError("el motor tocó disco/red")
    builtins.open, socket.socket = _boom, _boom
    try:
        assert exp.exportar_registros(state, events, "A", 0, 9999, "comite_credito") == salida
    finally:
        builtins.open, socket.socket = _open, _socket


def test_ac_d7_4_no_declara_nada(datos_prueba):
    """AC-d7.4 — el motor no clasifica fiscalmente a nadie (N-d7.1, fija F-d7.1).

    El tratamiento del crédito mutuo es AMBIGUO y el riesgo es enforcement arbitrario, no
    incumplimiento de una norma clara (§5). Si el motor declarara y la interpretación fuera
    incorrecta, el sistema LE CREÓ el problema al miembro. Es lo que I3 reserva al humano.

    Se fija por AST, no por la palabra: un test de ausencia de «igtf» solo caza al que lo
    nombra. `igtf_centavos = importe * 0.03` no dice «igtf» en ningún string.
    """
    state, events = datos_prueba
    for formato in exp.FORMATOS:
        salida = exp.exportar_registros(state, events, "A", 0, 9999, "comite_credito",
                                        formato=formato).lower()
        for termino in ("igtf", "iva", "gravable", "retencion", "seniat", "impuesto",
                        "base_imponible", "tributo"):
            assert termino not in salida, f"{formato}: el exporte menciona {termino!r}"

    # AST sobre TODO src/: ninguna función multiplica/divide por una constante fraccionaria.
    #
    # REVISADAS Y ADMITIDAS, con motivo escrito — no una relajación de la regla:
    #   clearing_solver.py `reduction_pct = (gross_before-gross_after)/gross_before * 100.0`
    #   es un DIAGNÓSTICO de la ronda de compensación: un ratio ADIMENSIONAL (importe/importe)
    #   convertido a porcentaje. No es «un porcentaje SOBRE un importe» (que es la forma del
    #   IGTF), no produce centavos, no entra en el exporte y viene IDÉNTICO del upstream
    #   (misma expresión en B2B/src/clearing/clearing_solver.py). Verificado en TB.7.
    # Cualquier ocurrencia NUEVA rompe este test, que es justo lo que se quiere.
    ADMITIDAS = {("clearing_solver.py", 100.0)}

    ofensores = []
    for py in sorted(_Path(_BASE / "src").rglob("*.py")):
        arbol = _ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
        for nodo in _ast.walk(arbol):
            if isinstance(nodo, _ast.BinOp) and isinstance(nodo.op, (_ast.Mult, _ast.Div)):
                for lado in (nodo.left, nodo.right):
                    if isinstance(lado, _ast.Constant) and isinstance(lado.value, float):
                        if (py.name, lado.value) in ADMITIDAS:
                            continue
                        ofensores.append(f"{py.name}:{nodo.lineno} ({lado.value})")
    assert not ofensores, (
        f"Multiplicación/división por constante fraccionaria en src/: {ofensores}. "
        f"Es N-d7.1 (el motor clasificando fiscalmente al miembro bajo un marco ambiguo) o M4 "
        f"(el float que vuelve donde el número se convierte en dinero). Ninguna es aceptable. "
        f"Si de verdad es inocua, va a ADMITIDAS **con el porqué escrito**, no borrando la regla."
    )


def test_ac_d7_6_derivado_de_los_eventos_no_del_estado(datos_prueba):
    """AC-d7.6 — el exporte de [t0,t1] refleja los saldos AL FINAL DE t1 (C-d7.2, fija F-d7.7).

    Un exporte de marzo con los saldos de julio CUADRA CONSIGO MISMO Y ES FALSO. Por eso se
    compara contra `replay(prefijo)`, la maquinaria que ya reconstruye byte a byte.
    """
    state, events = datos_prueba
    # La cadena CONTINÚA después del período exportado: A liquida, su saldo cambia.
    state, ev = led.settle_obligation(state, "o1", 2500, 5000)
    events = events + [ev]

    saldo_actual = state["members"]["A"]["balance_cents"]
    datos = json.loads(exp.exportar_registros(state, events, "A", 0, 1003, "comite_credito"))

    esperado = led.replay([e for e in events if e["ts"] <= 1003])["members"]["A"]["balance_cents"]
    assert datos["saldo_final"] == esperado
    assert datos["saldo_final"] != saldo_actual, (
        "el exporte del período refleja el saldo ACTUAL: se derivó del estado, no de los eventos"
    )
    # Y ninguna línea del exporte es posterior al período.
    assert all(ln["fecha"] <= 1003 for ln in datos["lineas"])


def test_ac_d7_7_raiz_ancla_solo_si_hay_ancla(datos_prueba):
    """AC-d7.7 — sin ancla publicada, la clave `raiz_ancla` NO EXISTE (fija ST-d7.2).

    El motor no puede saber si un período está anclado: anclar != publicar, y publicar ocurre
    fuera (ST-d2.1). Rellenar la raíz al vuelo daría FALSA SENSACIÓN DE PRUEBA ante un tercero
    — peor que no dar nada, porque el tercero se la cree.
    """
    state, events = datos_prueba
    sin = json.loads(exp.exportar_registros(state, events, "A", 0, 9999, "comite_credito"))
    assert "raiz_ancla" not in sin, "raiz_ancla presente sin ancla publicada"
    # Y no está como None: una clave con None invita a rellenarla.
    assert "raiz_ancla" not in json.dumps(sin)

    con = json.loads(exp.exportar_registros(state, events, "A", 0, 9999, "comite_credito",
                                            ancla={"raiz": "ab" * 32}))
    assert con["raiz_ancla"] == "ab" * 32   # CONTROL: cuando SÍ hay ancla, el campo aparece


def test_ac_d7_8_el_exporte_es_verificable(datos_prueba):
    """AC-d7.8 — cada `hash_evento` corresponde a un evento real de la cadena (P-d7.1).

    Sin tribunales (§2.11), un exporte vale lo que valga su verificabilidad ante un tercero.
    """
    state, events = datos_prueba
    led.verify_chain(events)
    hashes_reales = {e["hash"] for e in events}
    datos = json.loads(exp.exportar_registros(state, events, "A", 0, 9999, "comite_credito"))
    assert datos["lineas"], "sin líneas no se prueba nada (control de vacuidad)"
    for ln in datos["lineas"]:
        assert ln["hash_evento"] in hashes_reales
