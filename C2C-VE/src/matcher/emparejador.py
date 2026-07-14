"""Emparejador de affordance prosocial de Capa-3 ("el emparejador") para el protocolo social Micorriza.

Este módulo es el resguardo determinista envuelto alrededor del PRIMER LLM de la pila. El
modelo estocástico *propone* candidatos de emparejamiento; este envoltorio puro y determinista
*valida, acota y da forma* a esas propuestas; un humano *dispone*. El modelo se inyecta detrás
de un callable `proponer` y NUNCA se confía en él ciegamente: todo lo que devuelve se valida
contra un esquema estricto y se DESCARTA si está fuera de esquema, fuera de célula, corresponde
a una ficha inelegible (no consintiente / expirada / fuera de célula / desconocida), tiene forma
de vigilancia, o tiene forma de engagement.

El problema de diseño completo es que este es el primer LLM, y la atracción gravitacional de
todo recomendador es la optimización de engagement (invariante 8, el pecado original de la
plataforma). La respuesta es estructural, no una línea de política: la señal de engagement se
hace IRREPRESENTABLE — las claves de declaración están en lista blanca, se rechaza una taxonomía
ENGAGEMENT_KEY, y no hay entrada de feedback/resultado. El objetivo es la cooperación iniciada
porque el sistema no puede ver nada más.

Cinco muros estructurales (spec.md):
 1. Engagement irrepresentable (lista blanca + escaneo ENGAGEMENT_KEYS; sólo offers/needs/goals
    declarados).
 2. Sin escalar de persona (escaneo FORBIDDEN_KEYS sobre la entrada y la salida del modelo; una
    propuesta con forma de vigilancia se descarta, no se limpia; cita un hecho de Capa-2, nunca
    sintetices una calificación).
 3. El LLM no puede rankear personas (se descarta el orden del modelo; se impone un orden
    canónico (tipo, ficha, razón) — el orden con carnada de engagement se destruye por
    construcción).
 4. Puente de traducción delgado, acotado a célula (empareja sólo dentro de las células propias
    declaradas por el consultante).
 5. Olvido + sin expediente (declaraciones expiradas se descartan; las propuestas llevan
    expira_en; puro).

El cliente LLM se INYECTA vía `proponer`; nada al inicio del módulo toca la red, así que este
módulo permanece importable y toda la suite de tests corre offline con un stub.

Especificación: workflows/micorriza-politica/capa3/spec.md

Procedencia: redactado por Mistral vía multi-model-orchestration (vibe, headless), revisado y
corregido por Claude (ausencia de consentimiento hecha inelegible en vez de fatal; campos de
lista de declaración hechos indulgentes; coincidencia verbatim de hechos citados completada;
traza de auditoría finalizada).
"""
import re
import unicodedata


class ErrorDeBrechaEmparejador(Exception):
    """Se lanza cuando una SOLICITUD de emparejamiento rompe el envoltorio (sobre o forma de
    vigilancia/engagement).

    Nota: una mala salida del *modelo* nunca lanza excepción — se descarta y se cuenta. El
    resguardo no debe poder ser tumbado por un modelo malo (o con inyección de prompt). Sólo una
    solicitud malformada lanza excepción.
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


# Formas de engagement: el pecado original de la plataforma (invariante 8). Ninguna señal de
# click/permanencia/resultado/viralidad es una entrada representable para el emparejador, y
# ninguna forma así puede volver del modelo. Sesgado hacia sobre-rechazar (un falso rechazo es
# seguro; un falso admitido es una fuga de engagement) — ver ST1.
ENGAGEMENT_KEYS = [
    'click', 'clic', 'dwell', 'engagement', 'viral', 'viralidad', 'watch_time',
    'impression', 'impresiones', 'ctr', 'feed', 'time_in_app', 'notification',
    'notificacion', 'streak', 'racha', 'like_count', 'me_gusta', 'follower', 'seguidores',
    'retencion',
]

_ALLOWED_KINDS = ('oferta_cubre_necesidad', 'meta_compartida', 'traduccion')
_SELF_KEYS = ('ofertas', 'necesidades', 'metas')
_CANDIDATE_KEYS = ('ficha', 'celula_id', 'ofertas', 'necesidades', 'metas', 'consentimiento', 'hechos', 'expira_en')


def _scan_forbidden(obj):
    """Recursively scan dict KEYS (exact token/bigram, any depth) for a forbidden or
    engagement shape, and every string VALUE for a Venezuelan identity pattern.
    Returns (found, matching_key)."""
    taxonomy = set(FORBIDDEN_KEYS) | set(ENGAGEMENT_KEYS)
    if isinstance(obj, dict):
        for key, value in obj.items():
            if _key_matches_taxonomy(key, taxonomy):
                return True, str(key)
            if _value_has_identity_shape(value):
                return True, str(key)
            found, mk = _scan_forbidden(value)
            if found:
                return True, mk
        return False, None
    if isinstance(obj, (list, tuple)):
        for item in obj:
            if _value_has_identity_shape(item):
                return True, str(item)
            found, mk = _scan_forbidden(item)
            if found:
                return True, mk
        return False, None
    return False, None


def _validar_lista_str(value, label):
    if not isinstance(value, list):
        raise ErrorDeBrechaEmparejador(f"{label} must be a list")
    for item in value:
        if not isinstance(item, str):
            raise ErrorDeBrechaEmparejador(f"{label} must contain only strings")


def _validar_listas_declaracion(obj, allowed_keys, label):
    """Aplica lista blanca de claves y valida tipos de las listas ofertas/necesidades/metas de
    una declaración (propio/candidato).

    Los campos de lista de declaración son OPCIONALES (por defecto vacíos); cualquier clave
    fuera de `allowed_keys` se rechaza (no hay campo por el cual pueda entrar una señal de
    engagement/resultado — spec M3)."""
    for key in obj:
        if key not in allowed_keys:
            raise ErrorDeBrechaEmparejador(f"{label} contains disallowed key: {key!r}")
    for key in _SELF_KEYS:
        if key in obj:
            _validar_lista_str(obj[key], f"{label}.{key}")


def _validar_solicitud(request):
    if not isinstance(request, dict):
        raise ErrorDeBrechaEmparejador("request must be a dict")

    consultante = request.get('consultante')
    if not isinstance(consultante, str) or consultante == '':
        raise ErrorDeBrechaEmparejador("consultante must be a non-empty string")

    celulas_ids = request.get('celulas_ids')
    if not isinstance(celulas_ids, list) or len(celulas_ids) == 0:
        raise ErrorDeBrechaEmparejador("celulas_ids must be a non-empty list")
    for cid in celulas_ids:
        if not isinstance(cid, str) or cid == '':
            raise ErrorDeBrechaEmparejador("each celula_id must be a non-empty string")

    ahora = request.get('ahora')
    if not isinstance(ahora, str) or ahora == '':
        raise ErrorDeBrechaEmparejador("ahora must be a non-empty string")

    expira_en = request.get('expira_en')
    if not isinstance(expira_en, str) or expira_en == '':
        raise ErrorDeBrechaEmparejador("expira_en must be a non-empty string")

    propuestas_max = request.get('propuestas_max')
    if isinstance(propuestas_max, bool) or not isinstance(propuestas_max, int):
        raise ErrorDeBrechaEmparejador("propuestas_max must be an int > 0")
    if propuestas_max <= 0:
        raise ErrorDeBrechaEmparejador("propuestas_max must be an int > 0")

    self_data = request.get('propio')
    if not isinstance(self_data, dict):
        raise ErrorDeBrechaEmparejador("propio must be a dict")
    _validar_listas_declaracion(self_data, set(_SELF_KEYS), "propio")

    candidatos = request.get('candidatos')
    if not isinstance(candidatos, list):
        raise ErrorDeBrechaEmparejador("candidatos must be a list")
    for cand in candidatos:
        if not isinstance(cand, dict):
            raise ErrorDeBrechaEmparejador("each candidato must be a dict")
        _validar_listas_declaracion(cand, set(_CANDIDATE_KEYS), "candidato")
        for key in ('ficha', 'celula_id'):
            val = cand.get(key)
            if not isinstance(val, str) or val == '':
                raise ErrorDeBrechaEmparejador(f"candidato {key} must be a non-empty string")
        consentimiento = cand.get('consentimiento')
        if consentimiento is not None and not isinstance(consentimiento, dict):
            raise ErrorDeBrechaEmparejador("candidato consentimiento must be a dict when present")
        hechos = cand.get('hechos')
        if hechos is not None:
            if not isinstance(hechos, list):
                raise ErrorDeBrechaEmparejador("candidato hechos must be a list")
            for fact in hechos:
                if not isinstance(fact, dict):
                    raise ErrorDeBrechaEmparejador("each hecho must be a dict")
                for fk in ('afirmacion', 'celula_id'):
                    if not isinstance(fact.get(fk), str) or fact.get(fk) == '':
                        raise ErrorDeBrechaEmparejador(f"hecho {fk} must be a non-empty string")
                fexp = fact.get('expira_en')
                if fexp is not None and not isinstance(fexp, str):
                    raise ErrorDeBrechaEmparejador("hecho expira_en must be a string or null")
        cexp = cand.get('expira_en')
        if cexp is not None and not isinstance(cexp, str):
            raise ErrorDeBrechaEmparejador("candidato expira_en must be a string or null")


def _is_unexpired(expira_en, ahora):
    if expira_en is None:
        return True
    return expira_en > ahora


def emparejar(solicitud: dict, proponer) -> dict:
    """Muestra una lista acotada y efímera de candidatos de emparejamiento para
    `solicitud['consultante']`.

    Pura, determinista, sin efectos secundarios. `proponer(context) -> list[dict]` es el modelo
    estocástico INYECTADO; nunca se confía en él. Ante cualquier SOLICITUD malformada, lanza
    ErrorDeBrechaEmparejador; una mala salida del modelo se descarta y se cuenta (nunca se lanza
    excepción). No persiste nada.

    Devuelve el sobre de propuestas especificado en capa3/spec.md.
    """
    if not callable(proponer):
        raise ErrorDeBrechaEmparejador("proponer must be a callable")

    # 1. Validar el sobre (rechazar, nunca reparar).
    _validar_solicitud(solicitud)

    # 2. Escaneo de vigilancia + engagement sobre TODA la solicitud (claves, recursivo).
    found, mk = _scan_forbidden(solicitud)
    if found:
        raise ErrorDeBrechaEmparejador(f"Surveillance/engagement shape detected in request: key {mk!r}")

    ahora = solicitud['ahora']
    celulas_ids = set(solicitud['celulas_ids'])
    propuestas_max = solicitud['propuestas_max']
    proposal_expiry = solicitud['expira_en']

    # 3. Filtro de elegibilidad (ANTES de que el modelo vea nada): en célula, consintiente,
    # sin expirar.
    eligible = {}  # ficha -> candidato (se preserva el orden de inserción)
    eligible_context = []
    for cand in solicitud['candidatos']:
        consentimiento = cand.get('consentimiento') or {}
        in_cell = cand['celula_id'] in celulas_ids
        consenting = consentimiento.get('mostrable') is True
        unexpired = _is_unexpired(cand.get('expira_en'), ahora)
        if in_cell and consenting and unexpired:
            eligible[cand['ficha']] = cand
            eligible_context.append(cand)

    # 4. Construir el contexto sanitizado y llamar al proponente inyectado.
    context = {
        'consultante': solicitud['consultante'],
        'propio': solicitud['propio'],
        'candidatos': eligible_context,
    }
    raw = proponer(context)
    if not isinstance(raw, list):
        raw = []

    # 5. Validar cada propuesta; DESCARTAR (nunca confiar en) las malas, contando cada descarte.
    descartadas_fuera_de_esquema = 0
    descartadas_ficha_desconocida = 0
    descartadas_forma_vigilancia = 0
    survivors = []
    for p in raw:
        if not isinstance(p, dict):
            descartadas_fuera_de_esquema += 1
            continue
        ficha = p.get('ficha')
        razon = p.get('razon')
        tipo = p.get('tipo')
        if (not isinstance(ficha, str) or ficha == ''
                or not isinstance(razon, str) or razon == ''
                or tipo not in _ALLOWED_KINDS):
            descartadas_fuera_de_esquema += 1
            continue
        if ficha not in eligible:
            # ficha desconocida / alucinada — también captura a alguien fuera de célula o no
            # consintiente, que nunca fue elegible y por tanto nunca está en este conjunto
            # (spec F5/F6/F7).
            descartadas_ficha_desconocida += 1
            continue
        found, _mk = _scan_forbidden(p)
        if found:
            # forma de vigilancia/engagement del modelo: descarta la propuesta ENTERA, nunca la
            # limpies.
            descartadas_forma_vigilancia += 1
            continue

        cand = eligible[ficha]
        # citar_hechos se aceptan sólo si coinciden exactamente con un hecho declarado en ese
        # candidato (cita verbatim, sin síntesis — spec M4/N9). Un citar_hechos que no es lista es
        # basura del modelo: se descarta cada cita, la propuesta sobrevive — el resguardo no debe
        # poder ser tumbado (F7).
        declared_facts = cand.get('hechos') or []
        raw_cites = p.get('citar_hechos')
        if not isinstance(raw_cites, list):
            raw_cites = []
        cited = [f for f in raw_cites if f in declared_facts]
        survivors.append({
            'ficha': ficha,
            'celula_id': cand['celula_id'],
            'tipo': tipo,
            'razon': razon,
            'hechos_citados': cited,
            'expira_en': proposal_expiry,
        })

    # 6. Descartar el orden del modelo: orden canónico, deduplicar por (ficha, tipo), acotar a
    # propuestas_max.
    survivors.sort(key=lambda x: (x['tipo'], x['ficha'], x['razon']))
    deduped = []
    seen = set()
    for s in survivors:
        key = (s['ficha'], s['tipo'])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(s)
    emitidas = deduped[:propuestas_max]

    # 7. Ensamblar la salida. No comprometer nada; no persistir nada.
    veredicto = 'propuestas_mostradas' if emitidas else 'sin_coincidencias_desde_tu_posicion'
    return {
        'consultante': solicitud['consultante'],
        'celulas_ids': list(solicitud['celulas_ids']),
        'propuestas': emitidas,
        'veredicto': veredicto,
        'nota': ("Propuestas para mostrar, nunca acciones tomadas. Un humano resuelve si "
                 "contactar. El orden es canónico, no un ranking de personas."),
        'traza_auditoria': {
            'regla': ("candidatos en célula, consintientes, sin expirar; propuestas del LLM "
                      "validadas/acotadas/ordenadas canónicamente; sin escalar, sin señal de "
                      "engagement"),
            'candidatos_elegibles': len(eligible),
            'propuestas_del_modelo': len(raw),
            'descartadas_fuera_de_esquema': descartadas_fuera_de_esquema,
            'descartadas_fuera_de_celula': 0,
            'descartadas_no_consintientes': 0,
            'descartadas_forma_vigilancia': descartadas_forma_vigilancia,
            'descartadas_ficha_desconocida': descartadas_ficha_desconocida,
            'emitidas': len(emitidas),
            'propuestas_max': propuestas_max,
        },
    }
