"""Capa-5 coordinación estigmérgica + cortacircuitos anti-cascada para el protocolo social Micorriza.

Este módulo implementa una lectura pura, determinista y sin efectos secundarios de las trazas
ambientales visibles desde UNA célula — historiales de contribución, rutas, artefactos, señales — de
la forma en que FOSS, Wikipedia o los precios de Hayek coordinan sin un comandante (brief §4 Capa 5,
§5 estigmergia). Aplica EVAPORACIÓN de feromona (olvido) y los CORTACIRCUITOS anti-cascada
(invariante 9) para que el mismo mecanismo que coordina no pueda producir tampoco el "molino de
hormigas" (espiral de muerte), la cascada de información o la turba.

Es DETERMINISTA, NO un LLM: sin núcleo estocástico, sin modelo inyectado, sin cliente de red — esa es
toda la diferencia con la Capa 3.

Cuatro muros estructurales (spec.md):
 1. Las trazas son AMBIENTALES, nunca un escalar-de-persona. `about` es una ficha de
    artefacto/ruta/contribución; la taxonomía compartida FORBIDDEN_KEY rechaza una traza de
    puntuación/rango/reputación/lista-negra; la `signal` está en lista blanca a tipos
    positivos/ambientales para que ninguna señal de veto/desconfianza sea representable
    (invariantes 2/3, suma positiva).
 2. El olvido es ESTRUCTURAL — evaporación de feromona: efectiva = fuerza * 0.5^(transcurrido/vida_media);
    una traza desvanecida se descarta antes de sentir. La evaporación es el mecanismo, no un sello
    (invariante 5).
 3. Cortacircuitos anti-cascada (invariante 9), cada uno estructural: (a/c) un TOPE DE VELOCIDAD
    frena una ráfaga por artefacto por ventana (fricción/límite-de-velocidad); (b) una `flag` sin
    contexto se AMORTIGUA (contexto antes que juicio); (d) una traza fuera de célula se descarta
    (CERO difusión global, invariante 4).
 4. Con alcance de célula, provista por quien llama, escaneada y descartada: pura sobre el estado
    local provisto; nada persiste; sin depósito central; determinista byte a byte (invariantes 4/6).

Ante cualquier brecha de SOBRE/FORMA (tipo incorrecto, clave/señal fuera de lista blanca, una clave
PROHIBIDA) el módulo LANZA ErrorDeBrechaEstigmergia (nunca repara, nunca despoja). El CONTENIDO con
forma de cascada (fuera de célula, futura, bandera desnuda, sobre-el-tope, evaporada) se DESCARTA-Y-
CUENTA, nunca se lanza — el cortacircuito no debe poder ser derribado por una turba. El tiempo son
ticks lógicos enteros (ahora/creado_en) porque la evaporación necesita aritmética de tiempo
transcurrido; esto mantiene el módulo solo-stdlib sin dependencia de datetime.

Especificación: workflows/micorriza-politica/capa5/spec.md

Procedencia: redactado por Mistral vía multi-model-orchestration (vibe, headless), revisado y
corregido por Claude (se eliminó el import de defaultdict para paridad solo-stdlib con las capas
hermanas; docstring y traza de auditoría finalizados; modelo de tiempo y taxonomía de
descarte/amortiguación confirmados contra la spec).
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


class ErrorDeBrechaEstigmergia(Exception):
    """Se lanza cuando una solicitud de sentir viola el sobre o el escaneo de forma-de-vigilancia.

    La función rechaza la entrada de plano y nunca repara ni despoja campos. El CONTENIDO con forma
    de cascada (trazas fuera-de-célula/futuras/bandera-desnuda/sobre-el-tope/evaporadas) se descarta-
    y-cuenta, no se lanza.
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

# Lista blanca de señales de suma positiva: solo tipos de traza ambiental. Ninguna señal de
# veto/desconfianza/condena es representable (invariante 3). `bandera` es la única señal con forma
# de juicio — sobre un ARTEFACTO, controlada por el cortacircuito de contexto-antes-que-juicio.
ALLOWED_SIGNALS = ('contribucion', 'ruta', 'respaldo', 'presencia', 'bandera')
JUDGMENT_SIGNALS = ('bandera',)

# Las claves de traza están en lista blanca para que ningún escalar-de-persona / contador de
# interacción / veto pueda entrar por un campo.
_TRACE_KEYS = ('about', 'senal', 'fuerza', 'creado_en', 'celula_id', 'contexto')


def _scan_forbidden(obj):
    """Escanea recursivamente las CLAVES de un dict (token/bigrama exacto, cualquier profundidad)
    en busca de una forma prohibida, y cada VALOR de tipo cadena en busca de un patrón de identidad
    venezolano.

    Devuelve (encontrado, clave_coincidente). Refleja las otras capas.
    """
    taxonomy = set(FORBIDDEN_KEYS)
    if isinstance(obj, dict):
        for key, value in obj.items():
            if _key_matches_taxonomy(key, taxonomy):
                return True, str(key)
            if _value_has_identity_shape(value):
                return True, str(key)
            found, coincidencia = _scan_forbidden(value)
            if found:
                return True, coincidencia
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            if _value_has_identity_shape(item):
                return True, str(item)
            found, coincidencia = _scan_forbidden(item)
            if found:
                return True, coincidencia
    return False, None


def sentir(request: dict) -> dict:
    """Siente las trazas ambientales evaporadas y estranguladas visibles desde una célula.

    Pura, determinista, sin efectos secundarios. Ante cualquier brecha de sobre/forma, lanza
    ErrorDeBrechaEstigmergia; el contenido con forma de cascada se descarta-y-cuenta (nunca se
    lanza). No persiste nada. Devuelve el sobre de sentir especificado en capa5/spec.md.
    """
    # 1. Validar el sobre (rechazar, nunca reparar).
    if not isinstance(request, dict):
        raise ErrorDeBrechaEstigmergia("request debe ser un dict")

    # Área c: si el envelope trae `modo`, aplicar su calibración (rechazar, no recortar). En Capa 5
    # `ahora` es un tick entero: la retención por tiempo la gobierna `depurar()` (TA.5), no aquí.
    if 'modo' in request:
        try:
            validar_modo(request)
        except ErrorDeModo as _e:
            raise ErrorDeBrechaEstigmergia(str(_e)) from _e

    cell_id = request.get('celula_id')
    if not isinstance(cell_id, str) or cell_id == '':
        raise ErrorDeBrechaEstigmergia("celula_id debe ser una cadena no vacía")

    now = request.get('ahora')
    if not isinstance(now, int) or isinstance(now, bool):
        raise ErrorDeBrechaEstigmergia("ahora debe ser un int (tick lógico)")

    window = request.get('ventana')
    if not isinstance(window, int) or isinstance(window, bool) or window <= 0:
        raise ErrorDeBrechaEstigmergia("ventana debe ser un int > 0")

    velocity_cap = request.get('tope_velocidad')
    if not isinstance(velocity_cap, int) or isinstance(velocity_cap, bool) or velocity_cap <= 0:
        raise ErrorDeBrechaEstigmergia("tope_velocidad debe ser un int > 0")

    half_life = request.get('vida_media')
    if not isinstance(half_life, int) or isinstance(half_life, bool) or half_life <= 0:
        raise ErrorDeBrechaEstigmergia("vida_media debe ser un int > 0")

    min_strength = request.get('fuerza_min')
    if isinstance(min_strength, bool) or not isinstance(min_strength, (int, float)):
        raise ErrorDeBrechaEstigmergia("fuerza_min debe ser un número")
    if min_strength < 0:
        raise ErrorDeBrechaEstigmergia("fuerza_min debe ser >= 0")

    trazas = request.get('trazas')
    if not isinstance(trazas, list):
        raise ErrorDeBrechaEstigmergia("trazas debe ser una lista")

    for i, trace in enumerate(trazas):
        if not isinstance(trace, dict):
            raise ErrorDeBrechaEstigmergia(f"trazas[{i}] debe ser un dict")
        for key in trace:
            if key not in _TRACE_KEYS:
                raise ErrorDeBrechaEstigmergia(f"trazas[{i}] contiene una clave no permitida: {key!r}")
        about = trace.get('about')
        if not isinstance(about, str) or about == '':
            raise ErrorDeBrechaEstigmergia(f"trazas[{i}]['about'] debe ser una cadena no vacía")
        signal = trace.get('senal')
        if signal not in ALLOWED_SIGNALS:
            raise ErrorDeBrechaEstigmergia(
                f"trazas[{i}]['senal'] debe ser una de {ALLOWED_SIGNALS}; se recibió {signal!r}"
            )
        strength = trace.get('fuerza')
        if isinstance(strength, bool) or not isinstance(strength, (int, float)):
            raise ErrorDeBrechaEstigmergia(f"trazas[{i}]['fuerza'] debe ser un número")
        if strength <= 0:
            raise ErrorDeBrechaEstigmergia(f"trazas[{i}]['fuerza'] debe ser > 0")
        created_at = trace.get('creado_en')
        if not isinstance(created_at, int) or isinstance(created_at, bool):
            raise ErrorDeBrechaEstigmergia(f"trazas[{i}]['creado_en'] debe ser un int (tick lógico)")
        trace_cell_id = trace.get('celula_id')
        if not isinstance(trace_cell_id, str) or trace_cell_id == '':
            raise ErrorDeBrechaEstigmergia(f"trazas[{i}]['celula_id'] debe ser una cadena no vacía")
        context = trace.get('contexto')
        if context is not None and not isinstance(context, str):
            raise ErrorDeBrechaEstigmergia(f"trazas[{i}]['contexto'] debe ser una cadena o null")

    # 2. Escaneo de vigilancia sobre TODA la solicitud (claves, recursivo).
    found, matching_key = _scan_forbidden(request)
    if found:
        raise ErrorDeBrechaEstigmergia(f"Forma de vigilancia detectada en request: clave {matching_key!r}")

    # 3. Amortiguación por traza (descartar-y-contar, nunca lanzar): alcance de célula, futuro,
    #    contexto-antes-que-juicio.
    considered_traces = len(trazas)
    dropped_off_cell = 0
    dropped_future = 0
    damped_no_context = 0
    damped_velocity = 0
    evaporated = 0

    candidates = []
    for trace in trazas:
        if trace['celula_id'] != cell_id:            # muro 3(d): cero difusión global
            dropped_off_cell += 1
            continue
        if trace['creado_en'] > now:                 # traza futura
            dropped_future += 1
            continue
        if trace['senal'] in JUDGMENT_SIGNALS:        # muro 3(b): contexto antes que juicio
            ctx = trace.get('contexto')
            if ctx is None or ctx == '':
                damped_no_context += 1
                continue
        candidates.append(trace)

    # 4. Estrangulamiento de velocidad (fricción / límite-de-velocidad, muros 3(a)/(c)). El tope
    #    se aplica por artefacto POR CUBETA-DE-VENTANA, no solo la ventana actual (D-04). Una
    #    ráfaga es una ráfaga sin importar a qué tick esté fechada, así que una ráfaga
    #    retro-fechada apenas fuera de la ventana ya no puede escapar del estrangulamiento
    #    mientras una vida_media grande la deja apenas evaporada. La cubeta 0 es la ventana
    #    actual — el intervalo cerrado [ahora - ventana, ahora], preservando ST3 — y cada
    #    ventana más antigua es su propia cubeta, así que la coordinación sostenida genuina
    #    (trazas repartidas en muchas ventanas) sigue pasando: cada cubeta bajo el tope sobrevive.
    def _cubeta_ventana(created_at):
        elapsed = now - created_at            # >= 0 aquí (el futuro ya se descartó)
        if elapsed <= window:                 # ventana actual, intervalo cerrado (ST3)
            return 0
        return 1 + (elapsed - window - 1) // window

    groups = {}  # (about, cubeta) -> [trazas] (dict simple; las capas hermanas no importan nada)
    for t in candidates:
        groups.setdefault((t['about'], _cubeta_ventana(t['creado_en'])), []).append(t)

    all_survivors = []
    for key in groups:
        group = groups[key]
        if len(group) > velocity_cap:
            group_sorted = sorted(
                group, key=lambda x: (x['creado_en'], x['about'], x['senal'], x['fuerza'])
            )
            all_survivors.extend(group_sorted[:velocity_cap])  # conserva el más temprano hasta el tope por cubeta
            damped_velocity += len(group) - velocity_cap
        else:
            all_survivors.extend(group)

    # 5. Evaporación (decaimiento de feromona, muro 2): se desvanece por vida media; se descarta
    #    bajo el piso.
    sensed = []
    for t in all_survivors:
        elapsed = now - t['creado_en']              # >= 0 aquí (el futuro ya se descartó)
        effective = round(t['fuerza'] * (0.5 ** (elapsed / half_life)), 6)
        if effective < min_strength:
            evaporated += 1
            continue
        sensed.append({
            'about': t['about'],
            'senal': t['senal'],
            'celula_id': t['celula_id'],
            'fuerza_efectiva': effective,
            'contexto': t.get('contexto'),
        })

    # 6. Orden canónico (una lectura ambiental determinista, no un ranking de personas).
    sensed.sort(key=lambda x: (x['about'], x['senal'], -x['fuerza_efectiva'], str(x['contexto'])))

    # 7. Ensamblar la salida. No confirma nada; no persiste nada.
    verdict = 'senales_sentidas' if sensed else 'silencio_desde_tu_celula'
    return {
        'celula_id': cell_id,
        'ahora': now,
        'sentidas': sensed,
        'veredicto': verdict,
        'nota': ("Trazas sentidas desde tu célula, evaporándose y estranguladas; la ausencia es "
                 "silencio, nunca una marca en contra de nadie."),
        'traza_auditoria': {
            'regla': ("solo trazas ambientales; evaporación por vida media; con alcance de célula; "
                      "contexto-antes-que-juicio; con tope de velocidad por ventana; sin escalar-de-persona"),
            'trazas_consideradas': considered_traces,
            'descartadas_fuera_de_celula': dropped_off_cell,
            'descartadas_futuras': dropped_future,
            'amortiguadas_sin_contexto': damped_no_context,
            'amortiguadas_velocidad': damped_velocity,
            'evaporadas': evaporated,
            'sentidas': len(sensed),
            'ventana': window,
            'tope_velocidad': velocity_cap,
            'vida_media': half_life,
            'fuerza_min': min_strength,
        },
    }
