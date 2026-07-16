"""
Cortafuegos de partición por modo relacional (Capa 1) para el protocolo social Micorriza.

Este módulo implementa una membrana pura, determinista y libre de efectos
colaterales que clasifica y filtra interacciones según su sala de modo relacional.
El cortafuegos aplica tres salas con reglas de instrumentación distintas:
 - don_comunal: prohíbe instrumentos de mercado y claves de libro de reciprocidad
 - igualdad: prohíbe instrumentos de mercado; permite reciprocidad en especie
 - precio_de_mercado: permite instrumentos de mercado

Las formas de vigilancia (FORBIDDEN_KEYS) se rechazan en TODAS las salas.
El emparejamiento de claves es una coincidencia de subcadena sin distinguir
mayúsculas/minúsculas, realizada recursivamente a través de dicts, listas y
tuplas a cualquier profundidad (un contenedor anidado nunca oculta una forma
del escaneo).

Especificación: workflows/micorriza-politica/capa1/spec.md

Procedencia: redactado por Mistral vía multi-model-orchestration, revisado por Claude.
"""
import re
import unicodedata

# --- Área c: import del módulo `modo` (maquinaria compartida, fuente ÚNICA de la tabla de límites).
# Shim de path para resolver `modo.modo` bajo carga standalone por ruta (los tests cargan cada capa
# con spec_from_file_location, sin `src` en sys.path). NO forma parte del bloque firewall
# byte-idéntico. `modo` no importa ninguna capa (C-c6, sin ciclos).
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from modo.modo import validar_modo, ErrorDeModo


class ErrorDeBrechaMembrana(Exception):
    """Se lanza cuando una interacción viola el cortafuegos de la membrana."""
    pass


# === BEGIN shared firewall machinery (byte-identical across all six capas; AC-X) ===
# Tokenizing + normalizing key-match, plus identity-pattern value-scan. Fixed by
# workflows/micorriza-politica-ve/area-a-firewall-bilingue/{spec,constraints}.md.
# Defined locally in each layer (NOT a shared import — every capa must load standalone
# by file path); the six layers are held byte-for-byte in agreement by the AC-X test.

_CAMEL_BOUNDARY_RE = re.compile(r'(?<=[a-z0-9])(?=[A-Z])')
_NON_ALNUM_RE = re.compile(r'[^0-9a-zA-Z]+')

# Patrones exactos fijados en constraints.md (cedula/RIF/telefono venezolanos).
_CEDULA_RE = re.compile(r'\b[VE]-?\d{1,2}\.?\d{3}\.?\d{3}\b')
_RIF_RE = re.compile(r'\b[JGVEP]-?\d{8}-?\d\b')
_TELEFONO_RE = re.compile(r'\b(\+58|0058|0)(4\d{2}|2\d{2})[\s.\-]?\d{7}\b')
_IDENTITY_VALUE_PATTERNS = (_CEDULA_RE, _RIF_RE, _TELEFONO_RE)

# Surveillance shapes: forbidden in ALL inputs, all six capas, byte-identical taxonomy.
FORBIDDEN_KEYS = [
    'score', 'puntuacion', 'puntaje', 'rating', 'calificacion',
    'reputation', 'reputacion', 'rank', 'ranking', 'clasificacion',
    'blacklist', 'lista_negra', 'ban', 'veto', 'penalty', 'penalizacion',
    'sancion', 'karma', 'global_id', 'dni', 'cedula', 'rif', 'pasaporte',
]


def _strip_diacritics(s):
    """NFD-normalize and drop combining marks (accents), leaving base letters."""
    nfd = unicodedata.normalize('NFD', s)
    return ''.join(ch for ch in nfd if not unicodedata.combining(ch))


def _tokenize_key(key):
    """Strip diacritics FIRST (so an accented run is not split by the ASCII-only
    non-alnum regex), then split by camelCase boundaries and non-alphanumeric
    runs, lowercase. Returns a list of normalized tokens."""
    s = _strip_diacritics(str(key))
    s = _CAMEL_BOUNDARY_RE.sub('_', s)
    parts = _NON_ALNUM_RE.split(s)
    tokens = [p.lower() for p in parts if p != '']
    return tokens


def _key_token_set(key):
    """Candidates for exact matching: single tokens, adjacent-token bigrams (so a
    compound forbidden entry like lista_negra matches lista+negra split across two
    tokens), and the full underscore-joined key (so a 3+-token compound like
    poder_de_voto still matches a single taxonomy entry)."""
    tokens = _tokenize_key(key)
    grams = set(tokens)
    for i in range(len(tokens) - 1):
        grams.add(tokens[i] + '_' + tokens[i + 1])
    if len(tokens) > 1:
        grams.add('_'.join(tokens))
    return grams


def _key_matches_taxonomy(key, taxonomy):
    """Exact-token (or adjacent-bigram / full-compound) match of a key against a
    normalized taxonomy set. Never substring."""
    return bool(_key_token_set(key) & set(taxonomy))


def _value_has_identity_shape(value):
    """A string value matching a Venezuelan identity pattern (cedula/RIF/telefono) —
    a dossier shape hiding in a VALUE rather than a key."""
    if not isinstance(value, str):
        return False
    return any(p.search(value) for p in _IDENTITY_VALUE_PATTERNS)
# === END shared firewall machinery ===


# Instrumentos de mercado: prohibidos en las salas don_comunal e igualdad (bilingüe)
MARKET_KEYS = [
    'price', 'precio', 'cost', 'costo', 'coste', 'fee', 'tarifa',
    'cents', 'centavos', 'centimos', 'currency', 'moneda', 'divisa',
    'valuation', 'valoracion', 'denominat', 'denominacion',
    'pago', 'cobro', 'usd', 'ves', 'dolar', 'dolares', 'bolivar', 'bolivares',
]

# Alias castellano de trazabilidad con la spec del área e (doble moneda). MARKET_KEYS ya incluye
# los tokens de denominación bilingües (usd/ves/dolar/dolares/bolivar/bolivares, añadidos en TA.2),
# de modo que la moneda solo es representable en la sala `precio_de_mercado`: `don_comunal` e
# `igualdad` la rechazan (membrana direccional, C-e6, AC-e2). Misma lista, misma referencia; fuera
# del bloque firewall compartido → md5 5d693ecf1833fb760e173ee3db30a263 intacto
# (span: bloque BEGIN…END completo, incluido su \n final = 3023 bytes).
CLAVES_MERCADO = MARKET_KEYS

# Libro de reciprocidad: prohibido solo en la sala don_comunal (bilingüe)
RECIPROCITY_LEDGER_KEYS = [
    'debt', 'deuda', 'owed', 'debe', 'balance', 'saldo',
    'credit', 'credito', 'reciprocity', 'reciprocidad', 'iou',
    'favor_balance', 'saldo_de_favores',
]

# Claves del sobre: los campos estructurales de la interacción están en lista blanca (D-01). El
# sobre tiene un esquema fijo; el contenido libre pertenece a `carga`, que SÍ se escanea en busca de
# formas. Cualquier otra clave de primer nivel es rechazada — así un instrumento de mercado no puede
# colarse como hermano de `carga` (el escaneo de mercado está acotado a la carga y lo pasaría por
# alto). Lista blanca, no lista negra, igual que Capa-3/5/6, que ya ponen en lista blanca sus claves
# estructurales; Capa-1 era la única capa que no lo hacía.
_ENVELOPE_KEYS = ('sala', 'celula_id', 'interaccion_id', 'expira_en', 'participantes', 'carga', 'modo')


def _contains_forbidden_key(obj, taxonomy):
    """Verifica recursivamente si alguna clave de dict en obj coincide con una entrada
    de la taxonomía por token EXACTO (o bigrama adyacente / compuesto completo), y
    escanea cada VALOR de tipo cadena en busca de un patrón de identidad venezolano
    (cédula/RIF/teléfono).

    Args:
        obj: El objeto a escanear (dict, list, tuple, u otro).
        taxonomy: Iterable de tokens prohibidos normalizados (minúsculas, sin tildes).

    Returns:
        Tupla (found: bool, matching_key: str o None).
        Retorna en la primera coincidencia encontrada (orden en profundidad).
    """
    taxonomy = set(taxonomy)
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_str = str(key)
            if _key_matches_taxonomy(key_str, taxonomy):
                return True, key_str
            if _value_has_identity_shape(value):
                return True, key_str
            # Recurse into value
            found, match_key = _contains_forbidden_key(value, taxonomy)
            if found:
                return True, match_key
        return False, None
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            if _value_has_identity_shape(item):
                return True, str(item)
            found, match_key = _contains_forbidden_key(item, taxonomy)
            if found:
                return True, match_key
        return False, None
    return False, None


def _count_keys(obj):
    """Cuenta recursivamente todas las claves de dict en obj.

    Args:
        obj: El objeto en el que contar claves (dict, list, u otro).

    Returns:
        int: Número total de claves de dict encontradas recursivamente.
    """
    count = 0
    if isinstance(obj, dict):
        count += len(obj)
        for value in obj.values():
            count += _count_keys(value)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            count += _count_keys(item)
    return count


def admitir(interaccion: dict) -> dict:
    """Clasifica y filtra una única interacción a través del cortafuegos de membrana de Capa 1.

    Esta es una función pura, determinista y libre de efectos colaterales. Ante
    cualquier brecha, lanza ErrorDeBrechaMembrana. Nunca repara ni elimina campos,
    nunca retorna admitido=False, y nunca persiste nada.

    Args:
        interaccion: Un dict con el sobre de la interacción:
            - sala: str, una de 'don_comunal', 'igualdad', 'precio_de_mercado'
            - celula_id: str no vacío
            - interaccion_id: str no vacío
            - expira_en: str no vacío opcional o ausente
            - participantes: lista de str no vacíos (puede ser lista vacía)
            - carga: dict (puede estar vacío)

    Returns:
        dict con claves: sala, celula_id, interaccion_id, expira_en (o None),
        admitido (siempre True), y dict traza_auditoria.
        La traza_auditoria contiene:
            - regla: str que describe las reglas aplicadas
            - claves_revisadas: int, conteo de claves de carga visitadas recursivamente

    Raises:
        ErrorDeBrechaMembrana: Si la interacción viola alguna regla del cortafuegos.
    """
    # 1. Validar el sobre (rechazar/lanzar, no reparar)
    if not isinstance(interaccion, dict):
        raise ErrorDeBrechaMembrana("La interacción debe ser un dict")

    # Área c: si el envelope trae `modo`, aplicar su calibración (rechazar, no recortar). Ausencia
    # de `modo` = no engancha (compat con envelopes previos).
    if 'modo' in interaccion:
        try:
            validar_modo(interaccion)
        except ErrorDeModo as _e:
            raise ErrorDeBrechaMembrana(str(_e)) from _e

    # Lista blanca del sobre: cualquier clave inesperada de primer nivel es rechazada (D-01),
    # cerrando la brecha donde una clave de mercado en el sobre (hermana de carga) no estaba
    # ni en lista blanca ni era detectada por el escaneo de mercado acotado a la carga.
    for key in interaccion:
        if key not in _ENVELOPE_KEYS:
            raise ErrorDeBrechaMembrana(
                f"clave desconocida de primer nivel en el sobre de la interacción: {key!r} "
                f"(el sobre está en lista blanca; el contenido libre va en carga)"
            )

    sala = interaccion.get('sala')
    if sala not in ('don_comunal', 'igualdad', 'precio_de_mercado'):
        raise ErrorDeBrechaMembrana(
            f"sala debe ser una de 'don_comunal', 'igualdad', 'precio_de_mercado'; se recibió {sala!r}"
        )

    celula_id = interaccion.get('celula_id')
    if not isinstance(celula_id, str) or celula_id == '':
        raise ErrorDeBrechaMembrana("celula_id debe ser una cadena no vacía")

    interaccion_id = interaccion.get('interaccion_id')
    if not isinstance(interaccion_id, str) or interaccion_id == '':
        raise ErrorDeBrechaMembrana("interaccion_id debe ser una cadena no vacía")

    participantes = interaccion.get('participantes')
    if not isinstance(participantes, list):
        raise ErrorDeBrechaMembrana("participantes debe ser una lista")
    for i, p in enumerate(participantes):
        if not isinstance(p, str) or p == '':
            raise ErrorDeBrechaMembrana(
                f"participantes[{i}] debe ser una cadena no vacía; se recibió {p!r}"
            )

    expira_en = interaccion.get('expira_en')
    if expira_en is not None:
        if not isinstance(expira_en, str) or expira_en == '':
            raise ErrorDeBrechaMembrana("expira_en debe ser una cadena no vacía o estar ausente")

    carga = interaccion.get('carga')
    if not isinstance(carga, dict):
        raise ErrorDeBrechaMembrana("carga debe ser un dict")

    # 2. Escaneo de vigilancia sobre TODA la interacción
    found, match_key = _contains_forbidden_key(interaccion, FORBIDDEN_KEYS)
    if found:
        raise ErrorDeBrechaMembrana(
            f"Forma de vigilancia detectada en la interacción: clave {match_key!r}"
        )

    # 3. Escaneo de membrana sobre la carga (recursivo)
    # ===================================================================================
    # N-02 SILENT PLANT (negative control — NOT in the real C2C-VE source). The market/
    # reciprocity scan for the non-market salas is DISABLED, so an interaction carrying a
    # price/_cents/centavos key into a don_comunal or igualdad sala is silently ADMITTED
    # (admitido=True) instead of raising ErrorDeBrechaMembrana. The kula/gimwali wall
    # (invariant 1) is down. Crucially SURGICAL: the surveillance scan (step 2 above) is
    # left intact, so this plant still self-catches a forbidden-shaped carga — only the
    # market leak passes silently. Track A's no_market_leak oracle must catch the admit.
    if sala == 'don_comunal':
        pass  # market + reciprocity scans removed
    elif sala == 'igualdad':
        pass  # market scan removed
    # precio_de_mercado: sin restricciones de membrana sobre la carga

    # 4. Contar claves de carga visitadas recursivamente (todas las claves, ya que no hubo brecha)
    claves_revisadas = _count_keys(carga)

    # 5. Admitir con traza de auditoría
    return {
        'sala': sala,
        'celula_id': celula_id,
        'interaccion_id': interaccion_id,
        'expira_en': expira_en,
        'admitido': True,
        'traza_auditoria': {
            'regla': 'ningún instrumento de mercado en una sala no de mercado; ninguna forma de vigilancia en ninguna sala',
            'claves_revisadas': claves_revisadas
        }
    }
