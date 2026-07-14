"""Gobernanza sociocrática de la Capa 6 (consentimiento, no consenso) para el protocolo social Micorriza.

Este módulo implementa una resolución pura, determinista y sin efectos secundarios de UNA propuesta en
UN círculo local por CONSENTIMIENTO — la ausencia de una objeción primordial (razonada) — no por
consenso, y no por mayoría (brief §4 Capa 6; linaje: la Gran Ley de la Paz Haudenosaunee, la reunión
cuáquera, la sociocracia). Cada participante aporta exactamente UNA postura; la propuesta queda
`adoptada` si y solo si no persiste ninguna objeción primordial, o `revisar` con la RAZÓN de la
objeción expuesta — una pausa de forma de lista blanca que abre revisión, nunca una lista negra del
objetor.

Es DETERMINISTA, NO un LLM: sin núcleo estocástico, sin modelo inyectado, sin cliente de red — esa es
toda la diferencia con la Capa 3. Aplica el PROCEDIMIENTO del consentimiento; no puede fabricar la
voluntad de cooperar.

Cinco muros estructurales (spec.md):
 1. VOZ INDEPENDIENTE DE LA REPUTACIÓN (invariante 7, el movimiento definitorio): un token, una voz
    (deduplicado; un token duplicado se rechaza); la taxonomía VOTE_WEIGHT_KEY Y la taxonomía
    compartida FORBIDDEN_KEY rechazan cualquier entrada ponderada o portadora de reputación; las
    claves de postura están en lista blanca. La ponderación de vista-de-dios ni siquiera puede
    formularse.
 2. Consentimiento, no consenso, no mayoría: `adoptada` si y solo si no hay objeción primordial, si no
    `revisar`. El veredicto es CATEGÓRICO — nunca un porcentaje, nunca un recuento; un solo bloque
    razonado es decisivo.
 3. Una objeción es una PAUSA de forma de lista blanca (invariante 3): expone la RAZÓN y abre
    revisión; nunca marca al objetor. La salida lleva razones, nunca tokens del objetor.
 4. Los círculos son LOCALES y no se auto-propagan (invariantes 4/6): delimitados por circulo_id;
    posturas fuera del círculo se descartan; sin escalamiento a una autoridad padre/global.
 5. Olvido: expira_en por ronda; las posturas expiradas se descartan; sin expediente de quién objetó
    (invariante 5).

Ante cualquier brecha de ENVOLTORIO/FORMA/integridad (tipo incorrecto, clave fuera de lista blanca,
una clave FORBIDDEN o VOTE_WEIGHT, un token duplicado) el módulo LANZA ErrorDeBrechaGobernanza (nunca
repara, nunca despoja). El filtrado de ámbito de círculo y expiración DESCARTA-y-cuenta, nunca lanza.
El tiempo son cadenas ISO-8601 comparadas lexicográficamente (como en Capa 1/2/3); la Capa 6 no
necesita aritmética de tiempo transcurrido.

Especificación: workflows/micorriza-politica/capa6/spec.md

Procedencia: especificación redactada por Claude; se despachó un borrador de Mistral vía
multi-model-orchestration (vibe, sin interfaz) pero regresó vacío, así que este módulo fue
implementado directamente y revisado por Claude (un-token-una-voz aplicado por rechazo; puerta
VOTE_WEIGHT añadida al escáner FORBIDDEN compartido; tokens de objetor mantenidos fuera de toda
salida; veredicto mantenido categórico sin recuento).
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


class ErrorDeBrechaGobernanza(Exception):
    """Se lanza cuando una ronda de gobernanza incumple el envoltorio, un escaneo de forma o la
    integridad de la votación.

    La función rechaza la entrada de forma directa y nunca repara ni despoja campos. Las posturas
    fuera de círculo y expiradas se descartan-y-cuentan, no se lanzan como error.
    """
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


# Formas de peso de voto: el firewall anti-plutocracia (invariante 7). Ningún campo de
# peso/participación/poder-de-voto/recuento es una entrada representable, así que la reputación no
# puede ponderar una voz. Sesgado a sobre-rechazar (un rechazo falso es seguro; una admisión falsa es
# una fuga de plutocracia) — ver modelo de fallo ST1. (bilingüe)
VOTE_WEIGHT_KEYS = [
    'weight', 'peso', 'shares', 'acciones', 'voting_power', 'poder_de_voto',
    'vote_count', 'conteo', 'tally', 'recuento', 'majority', 'mayoria',
    'percent', 'porcentaje', 'proxy', 'seats', 'escanos', 'quorum', 'cuota',
]

_ALLOWED_DISPOSITIONS = ('consentir', 'objetar', 'abstenerse')
_DISPOSITION_KEYS = ('ficha', 'postura', 'objecion', 'circulo_id', 'expira_en')
_OBJECTION_KEYS = ('primordial', 'razon')


def _scan_keys(obj, taxonomy):
    """Escanea recursivamente las CLAVES de un dict (token/bigrama exacto, cualquier profundidad)
    contra una taxonomía, y cada VALOR de cadena en busca de un patrón de identidad venezolano.

    Devuelve (found, matching_key). Solo claves para la taxonomía — refleja las otras capas.
    """
    taxonomy = set(taxonomy)
    if isinstance(obj, dict):
        for key, value in obj.items():
            if _key_matches_taxonomy(key, taxonomy):
                return True, str(key)
            if _value_has_identity_shape(value):
                return True, str(key)
            found, coincidencia = _scan_keys(value, taxonomy)
            if found:
                return True, coincidencia
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            if _value_has_identity_shape(item):
                return True, str(item)
            found, coincidencia = _scan_keys(item, taxonomy)
            if found:
                return True, coincidencia
    return False, None


def _esta_expirada(expira_en, ahora):
    """Una postura está expirada si y solo si lleva un expira_en y expira_en <= ahora (lexicográfico)."""
    if expira_en is None:
        return False
    return expira_en <= ahora


def _validar_sobre(request):
    if not isinstance(request, dict):
        raise ErrorDeBrechaGobernanza("request debe ser un dict")

    circulo_id = request.get('circulo_id')
    if not isinstance(circulo_id, str) or circulo_id == '':
        raise ErrorDeBrechaGobernanza("circulo_id debe ser una cadena no vacía")

    propuesta_id = request.get('propuesta_id')
    if not isinstance(propuesta_id, str) or propuesta_id == '':
        raise ErrorDeBrechaGobernanza("propuesta_id debe ser una cadena no vacía")

    ahora = request.get('ahora')
    if not isinstance(ahora, str) or ahora == '':
        raise ErrorDeBrechaGobernanza("ahora debe ser una cadena ISO-8601 no vacía")

    expira_en = request.get('expira_en')
    if not isinstance(expira_en, str) or expira_en == '':
        raise ErrorDeBrechaGobernanza("expira_en debe ser una cadena ISO-8601 no vacía")

    posturas = request.get('posturas')
    if not isinstance(posturas, list):
        raise ErrorDeBrechaGobernanza("posturas debe ser una lista")

    for i, d in enumerate(posturas):
        if not isinstance(d, dict):
            raise ErrorDeBrechaGobernanza(f"posturas[{i}] debe ser un dict")
        for key in d:
            if key not in _DISPOSITION_KEYS:
                raise ErrorDeBrechaGobernanza(f"posturas[{i}] contiene una clave no permitida: {key!r}")

        token = d.get('ficha')
        if not isinstance(token, str) or token == '':
            raise ErrorDeBrechaGobernanza(f"posturas[{i}]['ficha'] debe ser una cadena no vacía")

        postura = d.get('postura')
        if postura not in _ALLOWED_DISPOSITIONS:
            raise ErrorDeBrechaGobernanza(
                f"posturas[{i}]['postura'] debe ser una de {_ALLOWED_DISPOSITIONS}; "
                f"se obtuvo {postura!r}"
            )

        d_circulo = d.get('circulo_id')
        if not isinstance(d_circulo, str) or d_circulo == '':
            raise ErrorDeBrechaGobernanza(f"posturas[{i}]['circulo_id'] debe ser una cadena no vacía")

        d_exp = d.get('expira_en')
        if d_exp is not None and (not isinstance(d_exp, str) or d_exp == ''):
            raise ErrorDeBrechaGobernanza(
                f"posturas[{i}]['expira_en'] debe ser una cadena no vacía o null"
            )

        objecion = d.get('objecion')
        if postura == 'objetar':
            if not isinstance(objecion, dict):
                raise ErrorDeBrechaGobernanza(
                    f"posturas[{i}]: una postura 'objetar' debe llevar un dict de objecion"
                )
            for key in objecion:
                if key not in _OBJECTION_KEYS:
                    raise ErrorDeBrechaGobernanza(
                        f"posturas[{i}]['objecion'] contiene una clave no permitida: {key!r}"
                    )
            primordial = objecion.get('primordial')
            if not isinstance(primordial, bool):
                raise ErrorDeBrechaGobernanza(
                    f"posturas[{i}]['objecion']['primordial'] debe ser un bool"
                )
            razon = objecion.get('razon')
            if not isinstance(razon, str) or razon == '':
                raise ErrorDeBrechaGobernanza(
                    f"posturas[{i}]['objecion']['razon'] debe ser una cadena no vacía"
                )
        else:
            if objecion is not None:
                raise ErrorDeBrechaGobernanza(
                    f"posturas[{i}]: solo una postura 'objetar' puede llevar una objecion"
                )


def decidir(request: dict) -> dict:
    """Resuelve una propuesta en un círculo por consentimiento (ausencia de una objeción primordial).

    Pura, determinista, sin efectos secundarios. Ante cualquier brecha de envoltorio/forma/integridad,
    lanza ErrorDeBrechaGobernanza; las posturas fuera de círculo y expiradas se descartan-y-cuentan
    (nunca se lanzan). No persiste nada. Devuelve el envoltorio de decisión especificado en
    capa6/spec.md.
    """
    # Área c: si el envelope trae `modo`, aplicar su calibración (rechazar, no recortar).
    if isinstance(request, dict) and 'modo' in request:
        try:
            validar_modo(request)
        except ErrorDeModo as _e:
            raise ErrorDeBrechaGobernanza(str(_e)) from _e

    # 1. Validar el envoltorio (rechazar, nunca reparar).
    _validar_sobre(request)

    circulo_id = request['circulo_id']
    propuesta_id = request['propuesta_id']
    ahora = request['ahora']
    expiracion_propuesta = request['expira_en']
    posturas = request['posturas']

    # 2. Escaneo de vigilancia + peso de voto sobre TODA la solicitud (claves, recursivo). Una
    #    violación de forma se rechaza ampliamente, antes de cualquier filtrado — como en cada capa.
    found, clave_coincidente = _scan_keys(request, FORBIDDEN_KEYS)
    if found:
        raise ErrorDeBrechaGobernanza(f"Forma de vigilancia detectada en la solicitud: clave {clave_coincidente!r}")
    found, clave_coincidente = _scan_keys(request, VOTE_WEIGHT_KEYS)
    if found:
        raise ErrorDeBrechaGobernanza(
            f"Forma de peso de voto detectada en la solicitud (la voz es independiente de la "
            f"reputación): clave {clave_coincidente!r}"
        )

    # 3. Ámbito de círculo + olvido (descartar-y-contar, nunca lanzar). Una postura fuera de círculo
    #    o expirada NO forma parte de la ronda de este círculo — se descarta, nunca es fatal.
    posturas_consideradas = len(posturas)
    descartadas_fuera_de_circulo = 0
    descartadas_expiradas = 0
    supervivientes = []
    for d in posturas:
        if d['circulo_id'] != circulo_id:              # local al círculo; sin voto cruzado
            descartadas_fuera_de_circulo += 1
            continue
        if _esta_expirada(d.get('expira_en'), ahora):  # olvido por ronda
            descartadas_expiradas += 1
            continue
        supervivientes.append(d)

    # 4. Un token, una voz — un invariante POR CÍRCULO (invariante 7; D-03). La unicidad se aplica
    #    solo entre las voces supervivientes (en círculo, no expiradas): un token repetido en una
    #    postura fuera de círculo o expirada ya fue descartado y no debe vetar esta ronda (eso
    #    permitiría que un rezagado delimitado a otro círculo bloquee una decisión legítima).
    tokens_vistos = set()
    for d in supervivientes:
        tok = d['ficha']
        if tok in tokens_vistos:
            raise ErrorDeBrechaGobernanza(
                f"un token, una voz: el token {tok!r} aparece en más de una "
                f"postura dentro del círculo"
            )
        tokens_vistos.add(tok)

    # 5. Resolver el consentimiento (categórico, SIN recuento) sobre las voces supervivientes.
    razones_primordiales = []
    razones_inquietud = []
    for d in supervivientes:
        if d['postura'] == 'objetar':
            objecion = d['objecion']
            if objecion['primordial']:
                razones_primordiales.append(objecion['razon'])
            else:
                razones_inquietud.append(objecion['razon'])

    # 6. Exponer razones, nunca personas. Orden canónico (determinista) por razón.
    objeciones_primordiales = [{'razon': r} for r in sorted(razones_primordiales)]
    inquietudes = [{'razon': r} for r in sorted(razones_inquietud)]

    # Consentimiento = la AUSENCIA de una objeción primordial. Un solo bloque razonado es decisivo;
    # mil consentimientos no lo superan en votos. Ningún recuento lo determina.
    veredicto = 'revisar' if objeciones_primordiales else 'adoptada'

    # 7. Ensamblar la salida. Delimitar al círculo; no propagar a ningún padre. No persistir nada.
    return {
        'circulo_id': circulo_id,
        'propuesta_id': propuesta_id,
        'veredicto': veredicto,
        'objeciones_primordiales': objeciones_primordiales,
        'inquietudes': inquietudes,
        'nota': ("El consentimiento es la ausencia de una objeción primordial, nunca una mayoría. "
                 "Una objeción es una pausa razonada que abre revisión, nunca una marca contra "
                 "nadie. Delimitada a este círculo; no se propaga."),
        'expira_en': expiracion_propuesta,
        'traza_auditoria': {
            'regla': ("adoptada si y solo si no hay objeción primordial; una ficha una voz; voz "
                      "independiente de la reputación; sin recuento, sin mayoría; local al "
                      "círculo; olvido por ronda"),
            'posturas_consideradas': posturas_consideradas,
            'descartadas_fuera_de_circulo': descartadas_fuera_de_circulo,
            'descartadas_expiradas': descartadas_expiradas,
            'objeciones_primordiales': len(objeciones_primordiales),
            'inquietudes': len(inquietudes),
        },
    }
