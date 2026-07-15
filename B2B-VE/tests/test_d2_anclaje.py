# -*- coding: utf-8 -*-
"""Aceptación de D2 — anclaje (AC-7 global; AC-d2.1..d2.8).

Escrito por Opus en TB.3, sin fan-out: AC-d2.4 es justamente el caso de ST-d2.3
(auto-confirmación) — quien no entiende la promoción escribe un test que verifica la
implementación contra sí misma y pasa en verde con el árbol roto. Ese test ES el delta.

Todos los `pytest.raises(ValueError)` llevan `match=`: a secas atrapa CUALQUIER ValueError y
pasa aunque el mecanismo esté muerto (lección de TB.2).
"""

import copy
import hashlib
import importlib.util
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
from hypothesis import given, settings, strategies as st

_BASE = Path(__file__).resolve().parent.parent

def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, _BASE / rel)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m

led = _load("mutual_credit_ledger_d2", "src/ledger/mutual_credit_ledger.py")
anc = _load("anclaje_d2", "src/ledger/anclaje.py")


# ---------------------------------------------------------------------------
# Cadenas sintéticas: `anclar` solo exige lo que exige `verify_chain` (enlace y
# recómputo del hash), no semántica de dominio. Construirlas así permite property
# tests de n∈[1,50] sin fabricar 50 operaciones de negocio. La ADMISIÓN sobre un
# flujo REAL del ledger se prueba aparte, en test_admision_flujo_real.
# ---------------------------------------------------------------------------
def cadena(n, kinds=None):
    events = []
    prev = ""
    for i in range(1, n + 1):
        core = {
            "seq": i,
            "ts": 1000 + i,
            "kind": (kinds[i - 1] if kinds else "evento_%d" % i),
            "payload": {"n": i},
            "prev_hash": prev,
        }
        h = hashlib.sha256(led.canonical(core)).hexdigest()
        ev = dict(core, hash=h)
        events.append(ev)
        prev = h
    return events


def hoja_de(events, seq):
    return next(e["hash"] for e in events if e["seq"] == seq)


def flujo_real():
    """Flujo real del ledger (célula USD, D1) → eventos encadenados de verdad."""
    params = {"neg_line_bp": 100, "pos_line_bp": 1000, "velocity_window_s": 86400,
              "velocity_max_cents": 5_000_000, "moneda": "USD", "sal_seudonimo": "sal-de-prueba-cell1", "paused": False}
    state, ev = led.create_cell("cell1", params, "ana", 1000)
    events = [ev]
    for mid in ("A", "B"):
        state, ev = led.add_member(
            state, {"id": mid, "turnover_cents": 100_000_000}, "ana", 1001)
        events.append(ev)
    state, ev = led.record_obligation(
        state, {"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 50_000}, 1002)
    events.append(ev)
    return state, events


# ===========================================================================
# AC-7 — `anclar` es determinista
# ===========================================================================
def test_ac7_determinista_mismos_bytes():
    events = cadena(7)
    a = anc.anclar(events, 1, 7)
    b = anc.anclar(events, 1, 7)
    assert led.canonical(a) == led.canonical(b)


def test_ac7_determinista_entre_procesos_pythonhashseed():
    """I4/L4: dos nodos que emitan raíces distintas para el mismo período parten la célula en
    dos verdades. Se corre en SUBPROCESOS reales con PYTHONHASHSEED distinto."""
    guion = textwrap.dedent("""
        import importlib.util, sys, hashlib
        B = {base!r}

        def L(nombre, rel):
            spec = importlib.util.spec_from_file_location(nombre, B + rel)
            m = importlib.util.module_from_spec(spec)
            sys.modules[nombre] = m
            spec.loader.exec_module(m)
            return m

        led = L('l', '/src/ledger/mutual_credit_ledger.py')
        anc = L('a', '/src/ledger/anclaje.py')
        ev, p = [], ''
        for i in range(1, 8):
            c = {{'seq': i, 'ts': 1000 + i, 'kind': 'evento_%d' % i,
                  'payload': {{'n': i}}, 'prev_hash': p}}
            h = hashlib.sha256(led.canonical(c)).hexdigest()
            ev.append(dict(c, hash=h))
            p = h
        print(anc.anclar(ev, 1, 7)['raiz'])
    """).format(base=str(_BASE))
    raices = []
    for semilla in ("1", "12345"):
        out = subprocess.run([sys.executable, "-c", guion], capture_output=True, text=True,
                             env={"PYTHONHASHSEED": semilla, "PATH": "/usr/bin:/bin"})
        assert out.returncode == 0, out.stderr
        raices.append(out.stdout.strip())
    assert raices[0] == raices[1]
    assert raices[0] == anc.anclar(cadena(7), 1, 7)["raiz"]


# ===========================================================================
# AC-d2.1 — La raíz depende del orden de `seq`, no del hash
# ===========================================================================
def test_acd21_orden_por_seq_no_por_hash():
    events = cadena(6)
    hojas_seq = [e["hash"] for e in events]
    hojas_hash = sorted(hojas_seq)
    assert hojas_seq != hojas_hash, "fixture inútil: los dos órdenes coinciden"
    assert anc._raiz_merkle(hojas_seq) != anc._raiz_merkle(hojas_hash)
    assert anc.anclar(events, 1, 6)["raiz"] == anc._raiz_merkle(hojas_seq)


# ===========================================================================
# AC-d2.2 — `anclar` es pura (C-d2.1/N5)
# ===========================================================================
def test_acd22_no_muta_los_eventos():
    events = cadena(5)
    antes = copy.deepcopy(events)
    anc.anclar(events, 1, 5)
    anc.prueba_de_inclusion(events, 1, 5, 3)
    assert events == antes


def test_acd22_sin_state_ni_ratified_by_en_la_firma():
    """F-d2.6: `anclar` es read/emit, no mueve valor → no pasa por la puerta de M8."""
    import inspect
    params = inspect.signature(anc.anclar).parameters
    assert list(params) == ["events", "desde_seq", "hasta_seq"]
    assert "state" not in params and "ratified_by" not in params


def test_acd22_sin_red_ni_disco(monkeypatch):
    """Un motor con red se cae en el apagón (§2.9) y se vuelve capturable."""
    import socket

    def explota(*a, **k):
        raise AssertionError("anclar tocó red o disco")

    monkeypatch.setattr(socket, "socket", explota)
    monkeypatch.setattr("builtins.open", explota)
    events = cadena(9)
    resultado = anc.anclar(events, 1, 9)
    prueba = anc.prueba_de_inclusion(events, 1, 9, 4)
    assert anc.verificar_inclusion(hoja_de(events, 4), prueba, resultado["raiz"])


# ===========================================================================
# AC-d2.3 — La prueba de inclusión no necesita el libro (C-d2.5/F-d2.4)
# ===========================================================================
def test_acd23_verificar_sin_los_eventos_en_el_ambito():
    events = cadena(11)
    raiz = anc.anclar(events, 1, 11)["raiz"]
    prueba = anc.prueba_de_inclusion(events, 1, 11, 6)
    hoja = hoja_de(events, 6)
    del events  # el árbitro NO recibe el ledger (N7)
    assert anc.verificar_inclusion(hoja, prueba, raiz) is True


def test_acd23_firma_sin_events():
    import inspect
    assert list(inspect.signature(anc.verificar_inclusion).parameters) == [
        "hoja_hash", "prueba", "raiz"]


def test_acd23_prueba_manipulada_es_falsa():
    events = cadena(11)
    raiz = anc.anclar(events, 1, 11)["raiz"]
    prueba = anc.prueba_de_inclusion(events, 1, 11, 6)
    hoja = hoja_de(events, 6)
    assert anc.verificar_inclusion(hoja, prueba, raiz) is True  # control positivo

    hash_alterado = copy.deepcopy(prueba)
    hash_alterado[0]["hash"] = hashlib.sha256(b"otro").hexdigest()
    assert anc.verificar_inclusion(hoja, hash_alterado, raiz) is False

    lado_alterado = copy.deepcopy(prueba)
    lado_alterado[0]["lado"] = "izq" if lado_alterado[0]["lado"] == "der" else "der"
    assert anc.verificar_inclusion(hoja, lado_alterado, raiz) is False

    assert anc.verificar_inclusion(hoja_de(events, 7), prueba, raiz) is False
    assert anc.verificar_inclusion(hoja, prueba[:-1], raiz) is False
    assert anc.verificar_inclusion(hoja, prueba, hashlib.sha256(b"x").hexdigest()) is False


# ===========================================================================
# AC-d2.4 — Sin colisión por hoja impar (EL AC QUE IMPORTA)
# ===========================================================================
def test_acd24_promocion_no_duplicacion_sin_colision():
    """F-d2.1 / CVE-2012-2459. Se construye EXPLÍCITAMENTE el par que la duplicación
    (`if impar: hojas.append(hojas[-1])`) colapsaría en la misma raíz, y se exige que sean
    distintas. No comprueba la implementación contra sí misma (ST-d2.3): una implementación
    que duplique hace `_raiz_merkle([h1,h2,h3])` idéntica a `_raiz_merkle([h1,h2,h3,h3])` y
    este test falla.

    Entra por `_raiz_merkle` a propósito: [e1,e2,e3,e3] NO puede pasar por `anclar` —
    `verify_chain` lo mata en la puerta (seq != i+1). Sin este punto de entrada, el AC que más
    importa del delta sería inexpresable (DESIGN-TB3 §2).
    """
    h1, h2, h3 = (hashlib.sha256(x).hexdigest() for x in (b"e1", b"e2", b"e3"))
    assert anc._raiz_merkle([h1, h2, h3]) != anc._raiz_merkle([h1, h2, h3, h3])


def test_acd24_el_huerfano_sube_tal_cual():
    """La promoción, comprobada contra el árbol calculado a mano."""
    h1, h2, h3 = (hashlib.sha256(x).hexdigest() for x in (b"e1", b"e2", b"e3"))
    n12 = anc._par(h1, h2)
    assert anc._raiz_merkle([h1, h2, h3]) == anc._par(n12, h3)  # h3 sube sin hermano


def test_acd24_duplicar_hoja_impar_si_colisiona_control_negativo():
    """Control negativo: se implementa la versión DUPLICADORA aquí mismo y se muestra que sí
    colisiona. Es lo que prueba que el test de arriba tiene contenido y no pasa por vacuidad."""
    def raiz_duplicando(hojas):
        nivel = list(hojas)
        while len(nivel) > 1:
            if len(nivel) % 2 == 1:
                nivel = nivel + [nivel[-1]]  # el patrón de Bitcoin clásico
            nivel = [anc._par(nivel[i], nivel[i + 1]) for i in range(0, len(nivel), 2)]
        return nivel[0]

    h1, h2, h3 = (hashlib.sha256(x).hexdigest() for x in (b"e1", b"e2", b"e3"))
    assert raiz_duplicando([h1, h2, h3]) == raiz_duplicando([h1, h2, h3, h3])
    assert anc._raiz_merkle([h1, h2, h3]) != raiz_duplicando([h1, h2, h3])


# ===========================================================================
# AC-d2.5 — Cadena rota no se ancla (C-d2.2/F-d2.3)
# ===========================================================================
@pytest.mark.parametrize("campo,valor", [
    ("payload", {"n": 999}),
    ("ts", 424242),
    ("prev_hash", hashlib.sha256(b"falso").hexdigest()),
    ("hash", hashlib.sha256(b"falso").hexdigest()),
])
def test_acd25_cadena_rota_lanza_y_no_devuelve_raiz(campo, valor):
    events = cadena(5)
    assert anc.anclar(events, 1, 5)["raiz"]  # control positivo: intacta, sí ancla
    events[2][campo] = valor
    with pytest.raises(ValueError, match=r"payload|ts|prev_hash|hash|seq"):
        anc.anclar(events, 1, 5)


def test_acd25_tampoco_se_prueba_inclusion_sobre_cadena_rota():
    events = cadena(5)
    events[1]["payload"] = {"n": 999}
    with pytest.raises(ValueError, match=r"hash|prev_hash"):
        anc.prueba_de_inclusion(events, 1, 5, 3)


# ===========================================================================
# AC-d2.6 — Casos de borde del rango
# ===========================================================================
def test_acd26_un_solo_evento_la_raiz_es_la_hoja():
    events = cadena(1)
    r = anc.anclar(events, 1, 1)
    assert r["raiz"] == events[0]["hash"] == r["primer_hash"] == r["ultimo_hash"]
    assert r["n_eventos"] == 1
    assert anc.prueba_de_inclusion(events, 1, 1, 1) == []
    assert anc.verificar_inclusion(events[0]["hash"], [], r["raiz"]) is True


def test_acd26_rango_vacio_lanza():
    with pytest.raises(ValueError, match="rango"):
        anc.anclar([], 1, 1)


def test_acd26_desde_mayor_que_hasta_lanza():
    with pytest.raises(ValueError, match="rango"):
        anc.anclar(cadena(5), 4, 2)


def test_acd26_rango_fuera_de_los_seq_existentes_lanza():
    events = cadena(5)
    with pytest.raises(ValueError, match="rango"):
        anc.anclar(events, 3, 9)
    with pytest.raises(ValueError, match="rango"):
        anc.anclar(events, 0, 3)


def test_acd26_sublista_pre_recortada_lanza_via_verify_chain():
    """ST-d2.4: `anclar` recibe la lista COMPLETA. Sobre una sublista, la verificación sería
    del fragmento que el llamador eligió."""
    events = cadena(6)
    with pytest.raises(ValueError, match="seq"):
        anc.anclar(events[2:], 3, 6)


def test_acd26_rango_parcial_ancla_solo_su_periodo():
    events = cadena(8)
    r = anc.anclar(events, 3, 6)
    assert r["n_eventos"] == 4
    assert r["primer_hash"] == hoja_de(events, 3)
    assert r["ultimo_hash"] == hoja_de(events, 6)
    assert r["raiz"] == anc._raiz_merkle([hoja_de(events, s) for s in (3, 4, 5, 6)])
    assert r["raiz"] != anc.anclar(events, 1, 8)["raiz"]


def test_acd26_booleano_no_es_entero():
    with pytest.raises(ValueError, match="rango"):
        anc.anclar(cadena(5), True, 3)


# ===========================================================================
# AC-d2.7 — Propiedad: toda hoja del período es probable (hypothesis)
# ===========================================================================
@settings(max_examples=60, deadline=None)
@given(st.data())
def test_acd27_toda_hoja_del_periodo_es_probable(data):
    n = data.draw(st.integers(min_value=1, max_value=50))
    desde = data.draw(st.integers(min_value=1, max_value=n))
    hasta = data.draw(st.integers(min_value=desde, max_value=n))
    events = cadena(n)
    raiz = anc.anclar(events, desde, hasta)["raiz"]
    for seq in range(desde, hasta + 1):
        prueba = anc.prueba_de_inclusion(events, desde, hasta, seq)
        assert anc.verificar_inclusion(hoja_de(events, seq), prueba, raiz) is True, \
            "hoja %d de [%d,%d] (n=%d) no probable" % (seq, desde, hasta, n)


@settings(max_examples=40, deadline=None)
@given(st.data())
def test_acd27_ninguna_hoja_de_fuera_del_periodo_es_probable(data):
    n = data.draw(st.integers(min_value=2, max_value=30))
    desde = data.draw(st.integers(min_value=1, max_value=n))
    hasta = data.draw(st.integers(min_value=desde, max_value=n))
    fuera = [s for s in range(1, n + 1) if not (desde <= s <= hasta)]
    if not fuera:
        return
    events = cadena(n)
    raiz = anc.anclar(events, desde, hasta)["raiz"]
    for seq in fuera:
        with pytest.raises(ValueError, match="seq"):
            anc.prueba_de_inclusion(events, desde, hasta, seq)
        # Y ninguna prueba del período sostiene una hoja de fuera contra esa raíz.
        for otra in range(desde, hasta + 1):
            prueba = anc.prueba_de_inclusion(events, desde, hasta, otra)
            assert anc.verificar_inclusion(hoja_de(events, seq), prueba, raiz) is False


# ===========================================================================
# ADMISIÓN (AC-10) — un flujo REAL del ledger se ancla y su prueba verifica
# ===========================================================================
def test_admision_flujo_real():
    """Un `anclar` que lanzara siempre pasaría todos los tests de rechazo de arriba. Éste
    exige que la función haga su trabajo sobre eventos reales del ledger (célula USD, D1)."""
    _, events = flujo_real()
    assert [e["seq"] for e in events] == [1, 2, 3, 4]
    r = anc.anclar(events, 1, 4)
    assert r["n_eventos"] == 4 and len(r["raiz"]) == 64
    assert r["primer_hash"] == events[0]["hash"] and r["ultimo_hash"] == events[-1]["hash"]
    for seq in (1, 2, 3, 4):
        prueba = anc.prueba_de_inclusion(events, 1, 4, seq)
        assert anc.verificar_inclusion(hoja_de(events, seq), prueba, r["raiz"]) is True
    # La prueba es logarítmica: es lo que permite al árbitro comprobar un hecho sin el libro.
    assert len(anc.prueba_de_inclusion(events, 1, 4, 1)) == 2


def test_admision_prueba_logaritmica_no_lineal():
    """N7: si la prueba creciera con n, el árbitro acabaría recibiendo el libro."""
    events = cadena(64)
    anc.anclar(events, 1, 64)
    assert len(anc.prueba_de_inclusion(events, 1, 64, 1)) == 6  # log2(64)


# ===========================================================================
# AC-d2.8 — D2 es puramente aditivo
# ===========================================================================
def test_acd28_el_ledger_no_importa_el_anclaje():
    """La dependencia es de un solo sentido: `anclaje` → `ledger`, nunca al revés."""
    fuente = (_BASE / "src/ledger/mutual_credit_ledger.py").read_text(encoding="utf-8")
    assert "anclaje" not in fuente
    assert not hasattr(led, "anclar")
