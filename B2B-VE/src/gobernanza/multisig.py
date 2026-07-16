"""Multisig de reserva (D4, fork VE) — helpers de VERIFICACIÓN, puros.

EL MOTOR NO CUSTODIA CLAVES, NO FIRMA, NO CONSULTA LA CADENA Y NO CRIBA CONTRA LA SDN
(N9/I-VE4/N-d4.1/N-d4.2). El entregable principal de D4 no es este archivo: es
`B2B-VE/docs/gobernanza-multisig.md`. Aquí solo vive lo que evita que se escriba mal un
número en aquel documento — el multisig lo operan humanos.

Por qué esto importa más de lo que parece: custodia en código = TRONO QUE CAPTURAR. El resto
de la arquitectura se esfuerza en no tener tronos (§4.6: sin tenedor central, células
federadas, ningún hub nacional). Las claves del fondo construirían el único que falta, y este
delta es el único sitio donde construirlo es tentador, porque aquí sí hay algo que custodiar.

POR QUÉ PAQUETE PROPIO Y NO `src/ledger/multisig.py` (a diferencia de `anclaje.py` y
`exportes.py`, que sí viven bajo `ledger/`): aquellos LEEN la cadena del ledger. Este no
importa el ledger y no lo toca. Vivir bajo `ledger/` invitaría a que un día alguien le pasara
el `state` «para cuadrar el fondo con el saldo del miembro-fondo» — que es ST-d4.4 con forma
de conveniencia, y N-d4.2 por la puerta de atrás.

UNA SUITE VERDE NO DICE NADA SOBRE EL UMBRAL, LOS ROLES NI LA ROTACIÓN. El motor no los toca:
viven en prosa, en el documento, y ahí se ven o no se ven. Lo que estos helpers cubren es la
aritmética. El resto lo cubre un humano leyendo (ST-d4.3), y se dice en vez de fingir
cobertura.

Señalados (N10 — no fake-resueltos):
  - El multisig NO protege contra la coerción: la REPARTE (ST-d4.1). 3-de-5 significa que hay
    que presionar a tres, no a uno. Es una mejora cuantitativa, no una garantía.
  - `localidad` es una etiqueta OPACA y el motor no puede saber si dos etiquetas distintas son
    dos lugares realmente descorrelacionados. Quien ponga L1/L2/L3 a tres barrios de la misma
    ciudad pasa estos tests y tiene un multisig de una sola ciudad (F-d4.4 intacto, con
    certificado). El motor comprueba la ARITMÉTICA; que las etiquetas correspondan a lugares
    que no caen juntos es del COMITÉ.
  - El escáner de identidad sobre `alias` es de FORMA, no de contenido (ST-d5.5): caza cédulas
    y RIF, no «el hermano del dueño de la ferretería de Chacao».
  - El fondo tiene dos vidas (ST-d4.4): en el ledger es un miembro con líneas; on-chain es un
    multisig. NADA garantiza que coincidan, no hay oráculo, y fingir uno sería peor.
  - El riesgo de contraparte Tether no es eliminable (§6.1): el fondo puede evaporarse sin que
    ninguna firma falle.
  - El motor no criba contra la lista SDN y NO DEBE (M9, hallazgo 5): diría «este firmante
    está limpio» sin poder sostenerlo. El cribado es del comité.
"""

# Shim de path para resolver `firewall.herencia` bajo carga standalone por ruta (mismo patrón
# que el del ledger, TB.2, y el de `modo` en C2C-VE, TA.4). `firewall.herencia` no importa
# nada de aquí: sin ciclos.
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from firewall.herencia import _value_has_identity_shape

import hashlib

# ── Esquema CERRADO ───────────────────────────────────────────────────────────────────────
#
# Lista blanca, reconstruida clave a clave (patrón `params` del ledger). Un campo
# `clave_privada` no se RECHAZA: NO ES REPRESENTABLE (I1 — forma irrepresentable antes que
# flag). La diferencia importa: un rechazo es una línea que alguien puede quitar.

CADENAS = ("TRC20", "ERC20")
ROLES = ("local", "diaspora")

_CLAVES_POLITICA = ("umbral", "total", "firmantes", "cadena")
_CLAVES_FIRMANTE = ("alias", "direccion", "cadena", "rol", "cargo", "localidad")

_TOTAL_MAX = 5
_UMBRAL_MIN = 2


# ── keccak-256, puro ──────────────────────────────────────────────────────────────────────
#
# NO es `hashlib.sha3_256`. Misma permutación, distinto padding (0x01 frente a 0x06), y por
# eso `sha3_256` devuelve otro digest: EIP-55 se calcula con keccak, el de antes de que SHA-3
# se estandarizara. Sustituir uno por otro se lee idéntico y rompe el checksum en silencio.
#
# Un hash NO es custodia. AC-d4.2 prohíbe librerías de FIRMA (ecdsa, eth_account, nacl); esto
# es una función de resumen sin estado, sin claves y sin red — la misma clase que `hashlib`,
# que el ledger usa desde upstream. El motor tiene primitivas de hash y no puede firmar con
# ellas.
#
# Fijado por los vectores publicados en AC-d4.5, incluidas las 4 direcciones del propio EIP-55.

_RC = (
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
    0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
    0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
    0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
    0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
)
_ROT = (
    (0, 36, 3, 41, 18),
    (1, 44, 10, 45, 2),
    (62, 6, 43, 15, 61),
    (28, 55, 25, 21, 56),
    (27, 20, 39, 8, 14),
)
_MASK64 = (1 << 64) - 1
_RATE = 136  # 1600 - 2*256 bits, en bytes


def _rotl64(x, n):
    if n == 0:
        return x
    return ((x << n) | (x >> (64 - n))) & _MASK64


def _keccak_f1600(a):
    for rnd in range(24):
        c = [a[x][0] ^ a[x][1] ^ a[x][2] ^ a[x][3] ^ a[x][4] for x in range(5)]
        d = [c[(x - 1) % 5] ^ _rotl64(c[(x + 1) % 5], 1) for x in range(5)]
        for x in range(5):
            for y in range(5):
                a[x][y] ^= d[x]
        b = [[0] * 5 for _ in range(5)]
        for x in range(5):
            for y in range(5):
                b[y][(2 * x + 3 * y) % 5] = _rotl64(a[x][y], _ROT[x][y])
        for x in range(5):
            for y in range(5):
                a[x][y] = b[x][y] ^ ((~b[(x + 1) % 5][y] & _MASK64) & b[(x + 2) % 5][y])
        a[0][0] ^= _RC[rnd]
    return a


def _keccak256(data):
    """keccak-256 (el de Ethereum), no SHA3-256. Ver el comentario de arriba."""
    a = [[0] * 5 for _ in range(5)]
    buf = bytearray(data)
    buf.append(0x01)
    while len(buf) % _RATE != 0:
        buf.append(0x00)
    buf[-1] |= 0x80
    for off in range(0, len(buf), _RATE):
        blk = buf[off:off + _RATE]
        for i in range(_RATE // 8):
            a[i % 5][i // 5] ^= int.from_bytes(blk[i * 8:i * 8 + 8], "little")
        a = _keccak_f1600(a)
    out = bytearray()
    for i in range(4):
        out += a[i % 5][i // 5].to_bytes(8, "little")
    return bytes(out)


# ── base58check (TRC-20) ──────────────────────────────────────────────────────────────────

_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_B58_INDICE = {c: i for i, c in enumerate(_B58)}


def _b58decode(s):
    """Devuelve los bytes, o `None` si hay un carácter fuera del alfabeto base58."""
    n = 0
    for ch in s:
        if ch not in _B58_INDICE:
            return None
        n = n * 58 + _B58_INDICE[ch]
    cuerpo = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    ceros = len(s) - len(s.lstrip("1"))
    return b"\x00" * ceros + cuerpo


def _direccion_trc20_valida(direccion):
    if len(direccion) != 34 or not direccion.startswith("T"):
        return False
    crudo = _b58decode(direccion)
    if crudo is None or len(crudo) != 25:
        return False
    if crudo[0] != 0x41:
        return False
    esperado = hashlib.sha256(hashlib.sha256(crudo[:21]).digest()).digest()[:4]
    return crudo[21:] == esperado


def _direccion_erc20_valida(direccion):
    if len(direccion) != 42 or not direccion.startswith("0x"):
        return False
    cuerpo = direccion[2:]
    if any(c not in "0123456789abcdefABCDEF" for c in cuerpo):
        return False
    if cuerpo == cuerpo.lower() or cuerpo == cuerpo.upper():
        # Todo-minúsculas o todo-mayúsculas: EIP-55 no lleva checksum que comprobar.
        # Se acepta la forma, y `describir_politica` no puede decir más de lo que sabe.
        return True
    h = _keccak256(cuerpo.lower().encode("ascii")).hex()
    for i, c in enumerate(cuerpo):
        if not c.isalpha():
            continue
        mayus = int(h[i], 16) >= 8
        if (c.isupper()) != mayus:
            return False
    return True


def verificar_formato_direccion(direccion, cadena):
    """FORMATO, y SOLO formato. Devuelve `True`/`False`, jamás lanza.

    **NO afirma que la dirección exista, ni que tenga saldo, ni que sea del firmante que
    dice serlo.** Comprobar cualquiera de esas cosas exige RED (F-d4.2), y un motor con red
    y conocimiento del fondo hace el fondo capturable A TRAVÉS DEL MOTOR: se cae en los
    apagones, necesita un endpoint (que es capturable) y filtra qué direcciones le interesan
    a quien observe el tráfico. Un checksum mal tecleado es un error caro y barato de cazar;
    todo lo demás es del comité.

    TRC-20: base58check (prefijo 0x41, 25 bytes, checksum sha256d).
    ERC-20: EIP-55 sobre keccak-256. Una dirección todo-minúsculas o todo-mayúsculas no
    lleva checksum: se acepta su forma y no se promete más.
    """
    if not isinstance(direccion, str) or not isinstance(cadena, str):
        return False
    if cadena == "TRC20":
        return _direccion_trc20_valida(direccion)
    if cadena == "ERC20":
        return _direccion_erc20_valida(direccion)
    return False


# ── verificar_umbral ──────────────────────────────────────────────────────────────────────

def _max_por_localidad(umbral):
    """Ninguna localidad concentra el quórum."""
    return umbral - 1


def verificar_umbral(politica):
    """Lanza `ValueError` si la política es incoherente. No devuelve nada, no muta nada.

    Valida la FÓRMULA, no el número elegido. Que este helper solo aceptara 3-de-5 (la
    decisión del propietario del 2026-07-16) sería hornear una decisión de gobernanza en el
    motor — N9 por la puerta de atrás. El helper valida; el DOCUMENTO registra la elección.
    """
    if not isinstance(politica, dict):
        raise ValueError("politica: no es un dict")

    desconocidas = set(politica) - set(_CLAVES_POLITICA)
    if desconocidas:
        raise ValueError("politica: clave desconocida %s" % sorted(desconocidas))
    faltan = set(_CLAVES_POLITICA) - set(politica)
    if faltan:
        raise ValueError("politica: falta clave %s" % sorted(faltan))

    umbral, total = politica["umbral"], politica["total"]
    if not isinstance(umbral, int) or isinstance(umbral, bool):
        raise ValueError("umbral: no es un entero")
    if not isinstance(total, int) or isinstance(total, bool):
        raise ValueError("total: no es un entero")

    if umbral < _UMBRAL_MIN:
        # F-d4.3: un multisig de umbral 1 es una firma única con pasos extra. Cualquier firmante
        # mueve el fondo solo, toda la propiedad buscada desaparece, y el documento sigue
        # diciendo «multisig».
        raise ValueError("umbral: minimo %d (umbral 1 es una sola firma)" % _UMBRAL_MIN)
    if umbral > total:
        raise ValueError("umbral: mayor que total")
    if total > _TOTAL_MAX:
        raise ValueError("total: maximo %d" % _TOTAL_MAX)

    if politica["cadena"] not in CADENAS:
        raise ValueError("cadena: desconocida")

    firmantes = politica["firmantes"]
    if not isinstance(firmantes, list):
        raise ValueError("firmantes: no es una lista")
    if len(firmantes) != total:
        raise ValueError("firmantes: len != total")

    for f in firmantes:
        if not isinstance(f, dict):
            raise ValueError("firmantes: entrada no es un dict")
        desc = set(f) - set(_CLAVES_FIRMANTE)
        if desc:
            # El esquema es CERRADO: `clave_privada` no es representable (N-d4.1).
            raise ValueError("firmante: clave desconocida %s" % sorted(desc))
        falta = set(_CLAVES_FIRMANTE) - set(f)
        if falta:
            raise ValueError("firmante: falta clave %s" % sorted(falta))
        if f["rol"] not in ROLES:
            raise ValueError("firmante: rol desconocido")
        if f["cadena"] not in CADENAS:
            raise ValueError("firmante: cadena desconocida")
        for campo in ("alias", "cargo", "localidad"):
            if not isinstance(f[campo], str) or not f[campo].strip():
                raise ValueError("firmante: %s vacio" % campo)
        # N8: el repo es público. Una lista de quién controla el fondo, con su cédula, es una
        # lista de objetivos. El escáner es el HEREDADO (D5 hizo lo mismo con
        # `referencias_comerciales`): no se inventa un segundo formato de identidad.
        for campo in ("alias", "cargo", "localidad"):
            if _value_has_identity_shape(f[campo]):
                raise ValueError("firmante: %s con forma de identidad" % campo)
        if not verificar_formato_direccion(f["direccion"], f["cadena"]):
            raise ValueError("firmante: direccion invalida")

    alias = [f["alias"] for f in firmantes]
    if len(set(alias)) != len(alias):
        raise ValueError("firmantes: alias duplicados")
    direcciones = [f["direccion"] for f in firmantes]
    if len(set(direcciones)) != len(direcciones):
        raise ValueError("firmantes: direcciones duplicadas")
    cargos = [f["cargo"] for f in firmantes]
    if len(set(cargos)) != len(cargos):
        # Dos firmantes con el mismo cargo = una sola función con dos firmas. Los roles 3/4/5
        # del documento existen para que ninguna captura de UNA función alcance el quórum.
        raise ValueError("firmantes: cargos duplicados")

    roles = [f["rol"] for f in firmantes]
    if "diaspora" not in roles:
        # F-d4.4/ST-d4.1: todos locales = un solo punto de presión física (§6.2, matraqueo).
        # El firmante de la diáspora es el que está FUERA DE ALCANCE físico.
        raise ValueError("firmantes: sin diaspora")
    if "local" not in roles:
        # La célula perdería el control de su propio fondo.
        raise ValueError("firmantes: sin local")

    _verificar_distribucion(umbral, total, firmantes)


def _verificar_distribucion(umbral, total, firmantes):
    """La restricción geográfica. NO es opinión: sale de la aritmética del umbral.

    Dos condiciones, y hacen falta LAS DOS porque son fallos simétricos:

      max_por_localidad <= umbral - 1      ninguna localidad concentra el quórum
      total - max_por_localidad >= umbral  perder una localidad no deja bajo el quórum

    La primera: una redada, una detención o un allanamiento en un solo sitio no abre la
    reserva. La segunda: un apagón, una emigración en bloque o un cierre de frontera no deja
    la reserva INACCESIBLE — y ese es el fallo MÁS PROBABLE en este contexto (§6.5, éxodo
    continuo), además del que siempre se olvida, porque «perder el fondo» suena a robo y no a
    que nadie contesta el teléfono.

    Generaliza, y por eso aquí hay una fórmula y no un número:
      3-de-5 → máx 2 por localidad, mín 3 localidades  (lo que decidió el propietario)
      2-de-3 → máx 1 por localidad, mín 3 localidades  (el piloto de P-d4.1)
    """
    por_localidad = {}
    for f in firmantes:
        por_localidad[f["localidad"]] = por_localidad.get(f["localidad"], 0) + 1
    mayor = max(por_localidad.values())

    if mayor > _max_por_localidad(umbral):
        raise ValueError(
            "localidad: concentra el quorum (%d en una, maximo %d con umbral %d)"
            % (mayor, _max_por_localidad(umbral), umbral))
    if total - mayor < umbral:
        raise ValueError(
            "localidad: perder una deja bajo el quorum (%d - %d < %d)" % (total, mayor, umbral))


# ── describir_politica ────────────────────────────────────────────────────────────────────

def _truncar(direccion):
    return direccion[:6] + "…" + direccion[-4:]


def describir_politica(politica):
    """Markdown legible para el comité. No dice nada que no estuviera en la política.

    Direcciones TRUNCADAS: el documento y todo lo que sale de aquí puede acabar en un repo
    público (N8/N-d4.5). Verifica primero — describir una política incoherente en markdown
    bonito es darle formato de decisión a un error.

    NO lleva las advertencias del documento de gobernanza (riesgo Tether, coerción repartida,
    el motor no criba contra la SDN): las APUNTA. Copiarlas aquí sería duplicar prosa que
    envejece por separado — al cabo de un año el render y el documento dirían cosas distintas
    y nadie sabría cuál manda. Es el mismo motivo por el que el bundle apunta a las
    verificaciones fechadas en vez de copiarlas.
    """
    verificar_umbral(politica)
    lineas = [
        "# Política multisig del fondo de garantía",
        "",
        "- **Umbral:** %d de %d" % (politica["umbral"], politica["total"]),
        "- **Cadena:** %s" % politica["cadena"],
        "- **Localidades distintas:** %d"
        % len({f["localidad"] for f in politica["firmantes"]}),
        "",
        "| Alias | Cargo | Rol | Localidad | Dirección |",
        "|---|---|---|---|---|",
    ]
    for f in politica["firmantes"]:
        lineas.append("| %s | %s | %s | %s | `%s` |" % (
            f["alias"], f["cargo"], f["rol"], f["localidad"], _truncar(f["direccion"])))
    lineas += [
        "",
        "> Qué cubre y qué NO cubre esta política: `docs/gobernanza-multisig.md`.",
    ]
    return "\n".join(lineas)
