# -*- coding: utf-8 -*-
"""Aceptación de D4 — multisig de reserva (TB.8).

AC-d4.0 (bloqueante) · AC-d4.1 · **AC-d4.2 (EL QUE IMPORTA)** · AC-d4.3 · AC-d4.4 · AC-d4.5 ·
AC-d4.6 · AC-d4.7.

LO QUE ESTE ARCHIVO NO PRUEBA, dicho primero: **nada sobre el umbral, los cargos o la
rotación**. El motor no custodia claves (N9), no los toca y no puede tocarlos: viven en
`docs/gobernanza-multisig.md`, en prosa, y su verificación es que un humano la lea (ST-d4.3).
Una suite verde aquí no dice que el 3-de-5 sea buena idea, ni que los cargos —que son relleno
de Opus marcado PROVISIONAL— estén decididos. Lo que cubre esta suite es la ARITMÉTICA.

Las direcciones de los fixtures son SINTÉTICAS: generadas por construcción (0x41 + sha256 de
una semilla literal + checksum sha256d), sin clave privada asociada, sin fondos y sin
correspondencia con ninguna dirección real. Nadie puede firmar con ellas porque nadie tiene —
ni tuvo nunca— la clave.
"""

import ast
import datetime
import importlib.util
import re
import sys
from pathlib import Path

import pytest

_BASE = Path(__file__).resolve().parent.parent
_RAIZ = _BASE.parent


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, _BASE / rel)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


ms = _load("multisig_d4", "src/gobernanza/multisig.py")

_DOC = _BASE / "docs" / "gobernanza-multisig.md"

# Sintéticas — ver el docstring del módulo.
_DIR = [
    "TAvEzRk9LX7iwR9EvakMSWyiMgG9J8zf5h",
    "TMWQbr8H1B3BqgK8Egp422x3aVUBPzB8KT",
    "TV7KoXDKerjpwXmDGENf5HtcmJGmK6MNZf",
    "TDMTfeAY54RVdwA8pLQDz3mMGTyUbm6kSY",
    "TBV72QXCMyGojKyNvSPW1otNMLf3U5eA4f",
    "TLL29f7Myt9Cx1BvpdhjMr9pLvPVTtjYn2",
]


def _firmante(i, rol, localidad, cargo=None):
    return {
        "alias": "firmante-%d" % i,
        "direccion": _DIR[i],
        "cadena": "TRC20",
        "rol": rol,
        "cargo": cargo or "cargo-%d" % i,
        "localidad": localidad,
    }


def _politica_3de5(**over):
    """La decisión del propietario: 3 de 5, máx 2 por localidad ⇒ 3 localidades."""
    p = {
        "umbral": 3,
        "total": 5,
        "cadena": "TRC20",
        "firmantes": [
            _firmante(0, "local", "L1"),
            _firmante(1, "local", "L1"),
            _firmante(2, "local", "L2"),
            _firmante(3, "local", "L2"),
            _firmante(4, "diaspora", "L3"),
        ],
    }
    p.update(over)
    return p


def _politica_2de3(**over):
    """El piloto de P-d4.1: 2 de 3 ⇒ máx 1 por localidad, 3 localidades."""
    p = {
        "umbral": 2,
        "total": 3,
        "cadena": "TRC20",
        "firmantes": [
            _firmante(0, "local", "L1"),
            _firmante(1, "local", "L2"),
            _firmante(2, "diaspora", "L3"),
        ],
    }
    p.update(over)
    return p


# ══ AC-d4.0 — M9 cumplido (BLOQUEANTE: se verifica primero) ════════════════════════════════

_VERIFICACIONES = _RAIZ / "docs" / "verificaciones"
_RE_CADUCA = re.compile(r"Caduca / re-verificar antes de:\*\*\s*\*\*(\d{4}-\d{2}-\d{2})\*\*")
_RE_VERIFICADO = re.compile(r"\*\*Verificado el:\*\*\s*(\d{4}-\d{2}-\d{2})")


def _archivos_de_verificacion():
    """Por GLOB, no por nombre literal.

    La spec (§5, AC-d4.0) pedía `AAAA-MM-DD-sanciones-multisig.md`. M9 produjo dos archivos
    —`2026-07-15-sanciones.md` y `2026-07-15-cripto.md`— y están FIRMADOS por el propietario.
    Manda el artefacto real: renombrar un documento firmado para que cuadre con un glob sería
    tocar la firma. El artefacto es el hecho; el AC es la descripción.

    Y el reparto en dos es MEJOR que el nombre único de la spec: AC-d4.0 exige cubrir
    sanciones Y marco cripto Y marco fiscal, y son cosas que envejecen a ritmos distintos
    (caducan 10-15 y 09-15). Un archivo único tendría una sola fecha para tres hechos.
    """
    return sorted(_VERIFICACIONES.glob("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*.md"))


def test_acd40_verificaciones_presentes_y_fechadas():
    """AC-d4.0 — sin M9 fechado, TB.8 no empieza (C-d4.1, bloqueante)."""
    archivos = _archivos_de_verificacion()
    temas = {a.name.split("-", 3)[3].replace(".md", "") for a in archivos}
    assert {"sanciones", "cripto"} <= temas, (
        "AC-d4.0: faltan verificaciones fechadas en docs/verificaciones/. Encontradas: %s. "
        "Sin ellas TB.8 NO EMPIEZA (C-d4.1)." % sorted(temas))
    for a in archivos:
        texto = a.read_text(encoding="utf-8")
        assert _RE_VERIFICADO.search(texto), "%s: sin fecha de verificación parseable" % a.name
        assert _RE_CADUCA.search(texto), "%s: sin fecha de caducidad parseable" % a.name
        assert "## 5. Firma" in texto, "%s: sin sección de firma" % a.name


def test_acd40_las_verificaciones_no_estan_caducadas():
    """AC-d4.0 endurecido — **este test se pondrá ROJO por el calendario**, y es el diseño.

    C-d4.1 dice «re-verificar, no recordar: un dato de hace seis meses no es información, es
    una suposición con fecha». Un test que solo comprobara que la fecha se parsea dejaría a
    M9 en folclore — el archivo está, luego el requisito está cumplido, para siempre. Y uno
    que siguiera verde en 2027 sobre una verificación de 2026 sería el fake-resolve que M9
    existe para prevenir, con formato de cobertura.

    El riesgo, dicho: cuando esto se ponga rojo, alguien puede poner un `skip` en vez de
    re-verificar. Desde el test no se puede impedir; lo que sí se puede es decir qué hacer.
    """
    hoy = datetime.date.today()
    for a in _archivos_de_verificacion():
        m = _RE_CADUCA.search(a.read_text(encoding="utf-8"))
        caduca = datetime.date.fromisoformat(m.group(1))
        assert hoy <= caduca, (
            "VERIFICACIÓN CADUCADA: %s caducó el %s (hoy %s).\n"
            "RE-VERIFICA, NO BORRES EL TEST NI LE PONGAS SKIP. El régimen de sanciones se ha "
            "movido en los DOS sentidos en los últimos 6 meses; las licencias generales se "
            "revocan con un anuncio. Rehacer M9 para este archivo es lo que desbloquea D4/D8 "
            "otra vez — construir sobre él caducado es exactamente lo que C-d4.1 prohíbe."
            % (a.name, caduca, hoy))


def test_acd40_las_verificaciones_no_llevan_datos_personales():
    """AC-d4.0 / N8 — el repo es público. Escáner HEREDADO, no uno nuevo."""
    for a in _archivos_de_verificacion():
        for i, linea in enumerate(a.read_text(encoding="utf-8").splitlines(), 1):
            assert not ms._value_has_identity_shape(linea), (
                "%s:%d tiene forma de identidad (N8): %r" % (a.name, i, linea))


# ══ AC-d4.1 — `verificar_umbral` rechaza lo incoherente ════════════════════════════════════

def test_acd41_acepta_las_dos_politicas_coherentes():
    """La tabla de AC-d4.1, filas ✅. Las DOS: `verificar_umbral` valida la fórmula, no el
    número elegido. Que solo aceptara 3-de-5 (lo que decidió el propietario) sería hornear una
    decisión de gobernanza en el motor — N9 por la puerta de atrás."""
    assert ms.verificar_umbral(_politica_3de5()) is None
    assert ms.verificar_umbral(_politica_2de3()) is None


@pytest.mark.parametrize("over, patron", [
    ({"umbral": 1}, r"umbral: minimo"),
    ({"umbral": 6, "total": 5}, r"umbral: mayor que total"),
    ({"umbral": 4, "total": 3}, r"umbral: mayor que total"),
])
def test_acd41_umbral_incoherente(over, patron):
    with pytest.raises(ValueError, match=patron):
        ms.verificar_umbral(_politica_3de5(**over))


def test_acd41_umbral_1_es_una_sola_firma():
    """F-d4.3 — `1 <= 3` es cierto y no basta. Un multisig de umbral 1 es una firma única con pasos
    extra: cualquier firmante mueve el fondo solo, toda la propiedad buscada desaparece, y el
    documento sigue diciendo «multisig»."""
    with pytest.raises(ValueError, match=r"umbral: minimo 2 \(umbral 1 es una sola firma\)"):
        ms.verificar_umbral(_politica_2de3(umbral=1))


def test_acd41_total_mayor_que_5():
    p = _politica_3de5(umbral=2, total=6)
    p["firmantes"] = p["firmantes"] + [_firmante(5, "diaspora", "L3", cargo="cargo-5")]
    with pytest.raises(ValueError, match=r"total: maximo 5"):
        ms.verificar_umbral(p)


def test_acd41_len_firmantes_distinto_de_total():
    p = _politica_3de5()
    p["firmantes"] = p["firmantes"][:4]
    with pytest.raises(ValueError, match=r"firmantes: len != total"):
        ms.verificar_umbral(p)


def test_acd41_direcciones_duplicadas():
    p = _politica_3de5()
    p["firmantes"][1]["direccion"] = p["firmantes"][0]["direccion"]
    with pytest.raises(ValueError, match=r"firmantes: direcciones duplicadas"):
        ms.verificar_umbral(p)


def test_acd41_alias_duplicados():
    p = _politica_3de5()
    p["firmantes"][1]["alias"] = p["firmantes"][0]["alias"]
    with pytest.raises(ValueError, match=r"firmantes: alias duplicados"):
        ms.verificar_umbral(p)


def test_acd41_cargos_duplicados():
    """Dos firmantes con el mismo cargo son UNA función con dos firmas. Los cargos 3/4/5 del
    documento existen para que ninguna captura de una sola función alcance el quórum; si el
    cargo se repite, el umbral vuelve a ser decorativo por esa vía."""
    p = _politica_3de5()
    p["firmantes"][1]["cargo"] = p["firmantes"][0]["cargo"]
    with pytest.raises(ValueError, match=r"firmantes: cargos duplicados"):
        ms.verificar_umbral(p)


def test_acd41_cero_diaspora():
    """F-d4.4/ST-d4.1 — todos locales = un solo punto de presión física (§6.2, matraqueo)."""
    p = _politica_3de5()
    p["firmantes"][4]["rol"] = "local"
    with pytest.raises(ValueError, match=r"firmantes: sin diaspora"):
        ms.verificar_umbral(p)


def test_acd41_cero_local():
    """La célula perdería el control de su propio fondo."""
    p = _politica_3de5()
    for f in p["firmantes"]:
        f["rol"] = "diaspora"
    with pytest.raises(ValueError, match=r"firmantes: sin local"):
        ms.verificar_umbral(p)


def test_acd41_esquema_cerrado_no_admite_clave_privada():
    """N-d4.1 — no se RECHAZA la clave privada: NO ES REPRESENTABLE (I1). La diferencia
    importa: un rechazo es una línea que alguien puede quitar «temporalmente»."""
    p = _politica_3de5()
    p["firmantes"][0]["clave_privada"] = "L1aW4Xv8oTU3zvHqPu6nVoQ8k9J2wR7yT4bC5dE6fG7hJ8kL9mN0"
    with pytest.raises(ValueError, match=r"firmante: clave desconocida \['clave_privada'\]"):
        ms.verificar_umbral(p)
    p2 = _politica_3de5()
    p2["semilla"] = "abandon abandon abandon"
    with pytest.raises(ValueError, match=r"politica: clave desconocida \['semilla'\]"):
        ms.verificar_umbral(p2)


def test_acd41_direccion_invalida_del_firmante():
    p = _politica_3de5()
    p["firmantes"][0]["direccion"] = _DIR[0][:-1] + "2"
    with pytest.raises(ValueError, match=r"firmante: direccion invalida"):
        ms.verificar_umbral(p)


def test_acd41_umbral_booleano_no_cuela():
    """`True == 1` en Python: sin el check de `bool`, `umbral=True` sería un umbral 1 con
    forma de otra cosa."""
    with pytest.raises(ValueError, match=r"umbral: no es un entero"):
        ms.verificar_umbral(_politica_2de3(umbral=True))


# ══ AC-d4.1 (§4 del DESIGN) — la distribución: la fórmula, no el número ════════════════════

def test_distribucion_ninguna_localidad_concentra_el_quorum():
    """Fallo 1 — la redada. 3 de 5 en L1 con umbral 3: un allanamiento en un solo sitio abre
    la reserva. Y hay 3 localidades, así que la regla ingenua «mínimo 3 localidades» lo deja
    pasar en verde."""
    p = _politica_3de5()
    loc = ["L1", "L1", "L1", "L2", "L3"]
    for f, l in zip(p["firmantes"], loc):
        f["localidad"] = l
    with pytest.raises(ValueError, match=r"localidad: concentra el quorum \(3 en una, maximo 2 con umbral 3\)"):
        ms.verificar_umbral(p)


def test_distribucion_perder_una_localidad_no_deja_bajo_el_quorum():
    """Fallo 2 — **el simétrico, y el MÁS PROBABLE** (§6.5, éxodo continuo): el apagón, la
    emigración en bloque, el cierre de frontera. La reserva no se roba: se vuelve
    INACCESIBLE. Aquí máx=2 cumple la primera condición y aun así perder L1 deja 3 < 4.
    Se olvida siempre porque «perder el fondo» suena a robo y no a que nadie contesta."""
    p = _politica_3de5(umbral=4)
    loc = ["L1", "L1", "L2", "L2", "L3"]
    for f, l in zip(p["firmantes"], loc):
        f["localidad"] = l
    with pytest.raises(ValueError, match=r"localidad: perder una deja bajo el quorum \(5 - 2 < 4\)"):
        ms.verificar_umbral(p)


def test_distribucion_la_formula_generaliza_a_los_dos_umbrales():
    """Que 3-de-5 y 2-de-3 caigan de la MISMA fórmula es la evidencia de que la restricción
    geográfica no es una opinión de Opus: sale de la aritmética del umbral. Si algún día se
    rehacen los cargos (que son PROVISIONALES), esto se conserva."""
    # 2-de-3 → máx 1 por localidad: dos en L1 ya concentra el quórum.
    p = _politica_2de3()
    p["firmantes"][1]["localidad"] = "L1"
    with pytest.raises(ValueError, match=r"localidad: concentra el quorum \(2 en una, maximo 1 con umbral 2\)"):
        ms.verificar_umbral(p)
    # …y con 3 localidades distintas, pasa.
    p["firmantes"][1]["localidad"] = "L2"
    assert ms.verificar_umbral(p) is None


def test_distribucion_localidad_es_obligatoria():
    """Opcional = F-d4.4 pasa en silencio para toda política que la omita, y el campo que
    existe para cazarlo solo lo caza en quien se molesta en rellenarlo."""
    p = _politica_3de5()
    del p["firmantes"][0]["localidad"]
    with pytest.raises(ValueError, match=r"firmante: falta clave \['localidad'\]"):
        ms.verificar_umbral(p)


def test_distribucion_la_etiqueta_opaca_no_sabe_geografia():
    """**Control negativo del Señalado, no una garantía.** Tres barrios de la misma ciudad con
    etiquetas distintas PASAN en verde: el motor comprueba la aritmética, no el territorio.
    Se fija en test para que el límite sea una decisión visible y no un descubrimiento
    incómodo dentro de seis meses. Que L1/L2/L3 sean lugares que no caen juntos es del
    COMITÉ."""
    p = _politica_3de5()
    assert ms.verificar_umbral(p) is None  # L1/L2/L3 podrían ser tres esquinas de Chacao


# ══ AC-d4.2 — EL QUE IMPORTA: el motor no custodia ═════════════════════════════════════════

_SRC = _BASE / "src"

_PATRONES_CLAVE = [
    (re.compile(r"\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b"), "WIF (clave privada Bitcoin)"),
    (re.compile(r"\b0x[0-9a-fA-F]{64}\b"), "clave privada hex de 32 bytes"),
    (re.compile(r"\bxprv[0-9A-Za-z]{50,}\b"), "clave extendida BIP-32"),
]
# BIP-39: 12+ palabras del diccionario seguidas. Se buscan las 4 primeras, que bastan para
# que la línea sea sospechosa sin arrastrar las 2048.
_RE_MNEMONICO = re.compile(
    r"\b(abandon|ability|able|about|above|absent|absorb|abstract)\b"
    r"(\s+[a-z]{3,8}\b){11,}", re.I)

_LIBRERIAS_DE_FIRMA = {
    "ecdsa", "eth_account", "eth_keys", "bitcoinlib", "nacl", "secp256k1", "coincurve",
    "cryptography", "Crypto", "tronpy", "web3", "bip32", "mnemonic", "bip_utils",
}


def _fuentes():
    return sorted(_SRC.rglob("*.py"))


def test_acd42_ningun_literal_con_forma_de_clave_en_src():
    """AC-d4.2 — grep sobre TODO `src/`, no solo el módulo nuevo. Un test que solo mirase
    `multisig.py` cazaría al que guarda la clave donde se espera."""
    for f in _fuentes():
        texto = f.read_text(encoding="utf-8")
        for i, linea in enumerate(texto.splitlines(), 1):
            for patron, que in _PATRONES_CLAVE:
                assert not patron.search(linea), (
                    "%s:%d parece contener %s. El motor NO custodia claves (N9): custodia en "
                    "código = trono que capturar." % (f.relative_to(_BASE), i, que))
        assert not _RE_MNEMONICO.search(texto), (
            "%s parece contener un mnemónico BIP-39 (N9)." % f.relative_to(_BASE))


def test_acd42_control_negativo_el_grep_no_pasa_por_vacuidad():
    """Sin esto, los patrones podrían no casar NADA nunca y el test de arriba sería verde por
    no mirar. Es la lección de TB.7: un test verde sobre texto puede estar pasando por
    vacuidad."""
    juguetes = [
        "clave = '5KYZdUEo39z3FPrtuX2QbbwGnNP5zTd7yyr2SC1j299sBCnWjss'",
        "clave = '0x4c0883a69102937d6231471b5dbb6204fe5129617082792ae468d01a3f362318'",
        "clave = 'xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TGtRBeJgk33yuGBxrMPHi'",
    ]
    for j in juguetes:
        assert any(p.search(j) for p, _ in _PATRONES_CLAVE), "el grep no caza %r" % j
    assert _RE_MNEMONICO.search(
        "semilla = 'abandon abandon abandon abandon abandon abandon abandon abandon "
        "abandon abandon abandon about'")


def test_acd42_sin_imports_de_libreria_de_firma():
    """AST, no grep: `import ecdsa` dentro de una función o un `from x import y` los ve el
    árbol y no una lista de líneas.

    keccak-256 vive en `multisig.py` implementado a mano y NO es una excepción a esta regla:
    un hash es una función de resumen sin estado, sin claves y sin red — la misma clase que
    `hashlib`, que el ledger usa desde upstream. El motor tiene primitivas de hash y NO PUEDE
    FIRMAR con ellas. Lo que esta regla prohíbe es la capacidad de firmar.
    """
    for f in _fuentes():
        arbol = ast.parse(f.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            nombres = []
            if isinstance(nodo, ast.Import):
                nombres = [a.name for a in nodo.names]
            elif isinstance(nodo, ast.ImportFrom) and nodo.module:
                nombres = [nodo.module]
            for n in nombres:
                raiz = n.split(".")[0]
                assert raiz not in _LIBRERIAS_DE_FIRMA, (
                    "%s importa %r: el motor no firma (N-d4.2). Si hace falta verificar algo "
                    "de una cadena, se verifica el FORMATO — comprobar existencia exige red, "
                    "y con red el fondo es capturable a través del motor."
                    % (f.relative_to(_BASE), n))


def test_acd42_ninguna_funcion_publica_recibe_ni_devuelve_material_de_clave():
    """AST — el esquema cerrado ya lo hace irrepresentable, pero una firma nueva podría
    saltárselo. Esto se pone rojo el día que alguien lo escriba."""
    sospechosos = re.compile(
        r"clave_privada|private_key|privkey|seed_phrase|semilla|mnemonic|mnemonico|"
        r"secreto|secret_key|keystore|wif|xprv", re.I)
    for f in _fuentes():
        arbol = ast.parse(f.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for arg in nodo.args.args + nodo.args.kwonlyargs:
                    assert not sospechosos.search(arg.arg), (
                        "%s: %s(%s) recibe material de clave (N9)."
                        % (f.relative_to(_BASE), nodo.name, arg.arg))


# ══ AC-d4.3 — los helpers son puros ════════════════════════════════════════════════════════

def test_acd43_los_helpers_no_tienen_red_ni_disco(monkeypatch):
    """F-d4.2 — el helper que consulta. Un `verificar_direccion` que hace una llamada RPC
    «solo para comprobar que existe» le da red al motor: se cae en los apagones, necesita un
    endpoint (capturable) y filtra qué direcciones le interesan a quien mire el tráfico.

    `open` NO se parchea: `_load` ya cargó el módulo y pytest necesita leer archivos para
    reportar. Se parchea lo que importa —la RED— y se dice por qué, en vez de un parche
    decorativo que no prueba nada."""
    import socket

    def _prohibido(*a, **k):
        raise AssertionError("el motor NO tiene red (C-d4.2/N-d4.2)")

    monkeypatch.setattr(socket, "socket", _prohibido)
    monkeypatch.setattr(socket, "create_connection", _prohibido)
    monkeypatch.setattr(socket, "getaddrinfo", _prohibido)

    p = _politica_3de5()
    assert ms.verificar_umbral(p) is None
    assert ms.verificar_formato_direccion(_DIR[0], "TRC20") is True
    assert "Umbral" in ms.describir_politica(p)


def test_acd43_no_mutan_la_entrada():
    import copy
    p = _politica_3de5()
    antes = copy.deepcopy(p)
    ms.verificar_umbral(p)
    ms.describir_politica(p)
    assert p == antes


def test_acd43_deterministas():
    p = _politica_3de5()
    assert ms.describir_politica(p) == ms.describir_politica(_politica_3de5())
    assert ms._keccak256(b"micorriza") == ms._keccak256(b"micorriza")


# ══ AC-d4.4 — sin identidades en el documento ni en los fixtures ═══════════════════════════

def test_acd44_el_documento_de_gobernanza_no_lleva_identidades():
    """N-d4.5/N8 — el repo es público; una lista de quién controla el fondo es una lista de
    objetivos. Escáner HEREDADO (`_value_has_identity_shape`), como D5 con
    `referencias_comerciales`: no se inventa un segundo formato de identidad."""
    assert _DOC.exists(), "AC-d4.6/C-d4.3: falta docs/gobernanza-multisig.md, que ES el delta"
    for i, linea in enumerate(_DOC.read_text(encoding="utf-8").splitlines(), 1):
        assert not ms._value_has_identity_shape(linea), (
            "gobernanza-multisig.md:%d tiene forma de identidad (N8): %r" % (i, linea))


def test_acd44_los_fixtures_no_llevan_identidades():
    for f in _politica_3de5()["firmantes"]:
        for campo in ("alias", "cargo", "localidad", "direccion"):
            assert not ms._value_has_identity_shape(f[campo])


def test_acd44_el_escaner_rechaza_un_alias_con_cedula():
    """`alias` es la segunda superficie de texto libre de Fase 2 (la primera fue
    `referencias_comerciales`, D5) y va en un repo público."""
    p = _politica_3de5()
    p["firmantes"][0]["alias"] = "V-12.345.678"
    with pytest.raises(ValueError, match=r"firmante: alias con forma de identidad"):
        ms.verificar_umbral(p)
    p2 = _politica_3de5()
    p2["firmantes"][2]["cargo"] = "tesoreria J-30684267-5"
    with pytest.raises(ValueError, match=r"firmante: cargo con forma de identidad"):
        ms.verificar_umbral(p2)


def test_acd44_control_negativo_el_escaner_no_confunde_una_direccion_con_una_cedula():
    """Verificado, no supuesto: `_CEDULA_RE` es `\\b[VE]-?\\d{1,2}\\.?\\d{3}\\.?\\d{3}\\b` y
    una base58 de 34 caracteres es UNA tirada alfanumérica — dentro de ella no hay `\\b`, así
    que un tramo tipo `V12345678` incrustado no puede casar. Si alguien «endureciera» el
    escáner quitando los límites de palabra, este test cae y avisa de que acaba de romper las
    direcciones, no de que las haya protegido mejor."""
    for d in _DIR:
        assert not ms._value_has_identity_shape(d)
    # …y el escáner SÍ caza la misma forma cuando está aislada: no pasa por vacuidad.
    assert ms._value_has_identity_shape("V-12.345.678")
    assert ms._value_has_identity_shape("E12345678")


def test_acd44_señalado_el_escaner_es_de_forma_no_de_contenido():
    """ST-d5.5 otra vez, fijado para que sea decisión y no descubrimiento: un alias que
    identifica a una persona sin usar ni un dígito PASA LIMPIO. El escáner caza cédulas y
    RIF, no descripciones. **Señalado → README de TB.9.**"""
    p = _politica_3de5()
    p["firmantes"][0]["alias"] = "el hermano del dueño de la ferreteria de Chacao"
    assert ms.verificar_umbral(p) is None


# ══ AC-d4.5 — formato, y SOLO formato ══════════════════════════════════════════════════════

def test_acd45_trc20_valida():
    for d in _DIR:
        assert ms.verificar_formato_direccion(d, "TRC20") is True


def test_acd45_trc20_checksum_roto():
    roto = _DIR[0][:-1] + "2"
    assert ms.verificar_formato_direccion(roto, "TRC20") is False


@pytest.mark.parametrize("basura", [
    "", None, 42, b"TAvEzRk9LX7iwR9EvakMSWyiMgG9J8zf5h", [],
    "T" + "0" * 33,            # '0' no está en el alfabeto base58
    _DIR[0][:-1],              # 33 caracteres
    "X" + _DIR[0][1:],         # sin prefijo T
])
def test_acd45_trc20_basura(basura):
    assert ms.verificar_formato_direccion(basura, "TRC20") is False


def test_acd45_cadena_desconocida():
    assert ms.verificar_formato_direccion(_DIR[0], "BEP20") is False
    assert ms.verificar_formato_direccion(_DIR[0], None) is False


def test_acd45_keccak_no_es_sha3():
    """**La mutación plausible de verdad**: la línea se lee idéntica y `hashlib` la ofrece.
    Vectores publicados de keccak-256 — si esto cae, EIP-55 devuelve `False` sobre
    direcciones válidas, que es «un error caro» con firma de software: exactamente lo que el
    helper existe para evitar."""
    import hashlib as _h
    assert ms._keccak256(b"").hex() == (
        "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470")
    assert ms._keccak256(b"abc").hex() == (
        "4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45")
    assert ms._keccak256(b"testing").hex() == (
        "5f16f4c7f149ac4f9510d9cf8cf384038ad348b3bcdc01915f95de12df9d1b02")
    # …y no es SHA3-256, que es lo que se colaría sin que nadie lo notase.
    assert ms._keccak256(b"") != _h.sha3_256(b"").digest()


@pytest.mark.parametrize("direccion", [
    # Los 4 vectores oficiales del propio EIP-55.
    "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed",
    "0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359",
    "0xdbF03B407c01E7cD3CBea99509d93f8DDDC8C6FB",
    "0xD1220A0cf47c7B9Be7A2E6BA89F429762e7b9aDb",
])
def test_acd45_erc20_eip55_valida(direccion):
    assert ms.verificar_formato_direccion(direccion, "ERC20") is True


def test_acd45_erc20_eip55_checksum_roto():
    """Una sola letra cambiada de caja: el checksum EIP-55 lo caza y nada más lo haría."""
    v = "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"
    roto = "0x5AAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"
    assert ms.verificar_formato_direccion(v, "ERC20") is True
    assert ms.verificar_formato_direccion(roto, "ERC20") is False


def test_acd45_erc20_sin_caja_mixta_no_lleva_checksum():
    """Todo-minúsculas: EIP-55 no tiene checksum que comprobar. Se acepta la FORMA y no se
    promete más — decir `False` sería rechazar direcciones válidas."""
    v = "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"
    assert ms.verificar_formato_direccion(v.lower(), "ERC20") is True
    assert ms.verificar_formato_direccion("0x" + v[2:].upper(), "ERC20") is True
    assert ms.verificar_formato_direccion("0x" + "g" * 40, "ERC20") is False
    assert ms.verificar_formato_direccion(v[:-1], "ERC20") is False


def test_acd45_el_docstring_dice_que_no_afirma_existencia():
    """AC-d4.5 exige que la función DIGA lo que no sabe. Un helper que devuelve `True` sin
    decir qué significa ese `True` invita a leerlo como «la dirección es buena»."""
    doc = ms.verificar_formato_direccion.__doc__
    assert "NO afirma que la dirección exista" in doc
    assert "saldo" in doc
    assert "RED" in doc or "red" in doc


# ══ AC-d4.6 — el documento dice qué NO cubre ═══════════════════════════════════════════════

def test_acd46_el_documento_enumera_sus_limites():
    """C-d4.6/N10 — un documento que solo enumere garantías miente por omisión, y es el
    documento con el que un comité decide dónde pone su dinero. Presencia por máquina; que
    los límites sean los correctos y estén bien dichos es gate humano (M1)."""
    texto = _DOC.read_text(encoding="utf-8")
    for exigido in [
        "Tether",            # riesgo de contraparte no eliminable (§6.1)
        "OFAC",              # congelamiento mitigado, no evitado
        "coerción",          # repartida, no eliminada (ST-d4.1)
        "oráculo",           # ledger y on-chain pueden divergir (ST-d4.4)
        "SDN",               # el motor no criba (M9, hallazgo 5)
    ]:
        assert exigido in texto, "gobernanza-multisig.md no dice nada de %r" % exigido


def test_acd46_el_documento_marca_los_valores_provisionales():
    """**El test de este nodo que más importa de los que se pueden escribir**, y aun así solo
    comprueba que las palabras están: que el documento los marque NO garantiza que nadie los
    ascienda por inercia. Si TB.8 escribiera los cargos y la rotación con el mismo tono que el
    umbral, habría fake-resuelto una decisión de gobernanza (N10) con formato de entregable.
    """
    texto = _DOC.read_text(encoding="utf-8")
    assert "PROVISIONAL" in texto
    assert "3 de 5" in texto and "Propietario del fork, 2026-07-16" in texto
    assert "Relleno de Claude (Opus)" in texto
    # El umbral está DECIDIDO y los otros dos no: si alguien borra la distinción, esto cae.
    assert texto.count("PROVISIONAL") >= 3, (
        "los DOS valores provisionales (cargos y rotación) tienen que verse como tales, y el "
        "aviso de §0 con ellos")
    assert "no dice absolutamente nada sobre ellos" in texto, (
        "el documento tiene que decir que la suite verde no los avala: el motor no los toca")


def test_acd46_el_documento_no_promete_que_el_motor_criba():
    texto = _DOC.read_text(encoding="utf-8")
    assert "El motor no criba contra la lista SDN" in texto
    assert "es del comité, no del motor" in texto


# ══ AC-d4.7 — `describir_politica` es legible y no filtra ══════════════════════════════════

def test_acd47_describe_lo_que_hay():
    md = ms.describir_politica(_politica_3de5())
    assert "**Umbral:** 3 de 5" in md
    assert "**Cadena:** TRC20" in md
    assert "**Localidades distintas:** 3" in md
    for f in _politica_3de5()["firmantes"]:
        assert f["alias"] in md
        assert f["cargo"] in md


def test_acd47_no_saca_direcciones_completas():
    """N8 — lo que sale de aquí puede acabar en un repo público."""
    md = ms.describir_politica(_politica_3de5())
    for d in _DIR[:5]:
        assert d not in md, "la dirección completa %s sale en el markdown" % d
        assert d[:6] in md, "la dirección truncada tiene que verse para poder cotejarla"


def test_acd47_no_inventa_nada_que_no_estuviera_en_la_politica():
    """No hay saldo, no hay estado on-chain, no hay juicio sobre nadie: el motor no lo sabe."""
    md = ms.describir_politica(_politica_3de5()).lower()
    for prohibido in ["saldo", "balance", "usdt", "limpio", "sdn", "clave"]:
        assert prohibido not in md, "describir_politica dice %r, que no está en la política" % prohibido


def test_acd47_verifica_antes_de_describir():
    """Describir una política incoherente en markdown bonito es darle formato de decisión a un
    error — y este markdown va a un documento de gobernanza."""
    with pytest.raises(ValueError, match=r"umbral: minimo"):
        ms.describir_politica(_politica_2de3(umbral=1))
