"""Consulta de legibilidad de confianza de la Capa-2 para el protocolo social Micorriza.

Este módulo implementa una consulta de legibilidad pura, determinista y sin efectos
secundarios que responde a una única pregunta: desde la posición del consultante, ¿la
gente en la que confío avala a X, aquí, ahora? Devuelve rutas de aval y hechos concretos
alcanzables desde el consultante dentro de la célula, o el veredicto neutral
sin_informacion_desde_tu_posicion cuando no hay ninguno alcanzable.

El componente es una consulta de red de confianza sobre un grafo local suministrado por
quien llama. No emite puntuación, ni rango, ni número de reputación, ni veredicto moral.
Clasifica la alcanzabilidad desde una posición; nunca califica a una persona. La
vista-de-dios se vuelve estructuralmente irrepresentable: el consultante es obligatorio,
el grafo lo suministra quien llama y se descarta, el recorrido está acotado por saltos, y
la salida son rutas/hechos, no un escalar.

Las formas de vigilancia (FORBIDDEN_KEYS) se rechazan de plano usando la taxonomía exacta
de Capa-1/Capa-4, escaneada recursivamente sobre toda la entrada (grafo incluido). El
cotejo de claves es por subcadena, sin distinguir mayúsculas/minúsculas, a cualquier
profundidad.

Especificación: workflows/micorriza-politica/capa2/spec.md

Procedencia: redactado por Mistral vía multi-model-orchestration, revisado por Claude.
"""
import re
import unicodedata


class ErrorDeBrechaLegibilidad(Exception):
    """Se lanza cuando una solicitud incumple las reglas de legibilidad (sobre o forma de vigilancia).

    La consulta rechaza la entrada de plano y nunca repara ni recorta campos.
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

# Cota superior sobre las rutas de aval concretas enumeradas a modo ilustrativo (D-02). Las
# respuestas significativas — alcanzable, saltos_minimos y avalado_por_gente_de_tu_confianza —
# se calculan de forma exacta mediante un BFS inverso lineal y NUNCA se recortan; sólo se acota
# la MUESTRA de rutas concretas, de modo que un grafo denso suministrado por quien llama ya no
# puede explotar en un número exponencial de rutas. Cuando se recorta la muestra,
# traza_auditoria.rutas_truncadas es True (la respuesta de alcanzabilidad sigue siendo completa).
_MAX_RUTAS_DE_AVAL = 256


def _contains_forbidden_key(obj, taxonomy):
    """Comprueba recursivamente si alguna clave de dict en obj coincide con una entrada
    de la taxonomía por token EXACTO (o bigrama adyacente / compuesto completo), y
    escanea cada VALOR de cadena en busca de un patrón de identidad venezolano
    (cedula/RIF/telefono).

    Args:
        obj: El objeto a escanear (dict, lista, tupla u otro).
        taxonomy: Iterable de tokens prohibidos normalizados (minúsculas, sin diacríticos).

    Devuelve:
        Tupla (found, clave_coincidente or None).
        Retorna en la primera coincidencia hallada (orden en profundidad).
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


def _no_expirado(expira_en, ahora):
    """Verifica si un elemento no ha expirado en `ahora`.

    No expirado = expira_en es None/ausente, O (cadena) expira_en > ahora
    por comparación lexicográfica simple.
    """
    if expira_en is None:
        return True
    return expira_en > ahora


def consultar(request: dict) -> dict:
    """Consulta única de legibilidad de confianza de un consultante sobre un único objetivo.

    Función pura, determinista y sin efectos secundarios. Ante cualquier brecha,
    lanza ErrorDeBrechaLegibilidad. Nunca repara, nunca devuelve resultados parciales.

    Args:
        request: dict con:
            - consultante: str no vacío (REQUERIDO)
            - objetivo: un único str no vacío; list/dict/None/"*"/"" -> se rechaza
            - celula_id: str no vacío
            - ahora: str no vacío (ISO-8601)
            - saltos_max: int > 0 (rechaza bool, <= 0, no-int)
            - grafo: dict con:
                - avales: lista de dicts, cada uno {"de": str, "a": str, "celula_id": str, "expira_en": str|null}
                - hechos: lista de dicts, cada uno {"sobre": str, "afirmacion": str, "celula_id": str, "expira_en": str|null}

    Returns:
        dict con la forma de salida exacta especificada en spec.md:
            - consultante, objetivo, celula_id ecoados de la entrada
            - desde_tu_posicion: dict con alcanzable, saltos_minimos, rutas_de_aval, avalado_por_gente_de_tu_confianza, hechos
            - veredicto: "conocido_via_confianza" o "sin_informacion_desde_tu_posicion"
            - nota: cadena fija
            - traza_auditoria: dict con regla, avales_considerados, hechos_considerados, saltos_max

    Raises:
        ErrorDeBrechaLegibilidad: Ante cualquier error de validación del sobre o brecha de forma de vigilancia.
    """
    # 1. Validar el sobre completo; rechazar (lanzar), nunca reparar
    if not isinstance(request, dict):
        raise ErrorDeBrechaLegibilidad("request debe ser un dict")

    # Validar consultante
    consultante = request.get('consultante')
    if not isinstance(consultante, str) or consultante == '':
        raise ErrorDeBrechaLegibilidad("consultante debe ser una cadena no vacía")

    # Validar objetivo — debe ser un único str no vacío; se rechaza list/dict/None/*/vacío
    objetivo = request.get('objetivo')
    if objetivo is None:
        raise ErrorDeBrechaLegibilidad("objetivo es requerido y debe ser una cadena no vacía")
    if isinstance(objetivo, bool):
        raise ErrorDeBrechaLegibilidad("objetivo debe ser una cadena no vacía; se recibió bool")
    if not isinstance(objetivo, str):
        raise ErrorDeBrechaLegibilidad(
            f"objetivo debe ser una única cadena no vacía; se recibió {type(objetivo).__name__}"
        )
    if objetivo == '':
        raise ErrorDeBrechaLegibilidad(
            "objetivo debe ser una cadena no vacía; se recibió cadena vacía"
        )
    if objetivo == '*':
        raise ErrorDeBrechaLegibilidad(
            "objetivo debe ser un único token concreto; el comodín '*' no está permitido"
        )

    # Validar celula_id
    celula_id = request.get('celula_id')
    if not isinstance(celula_id, str) or celula_id == '':
        raise ErrorDeBrechaLegibilidad("celula_id debe ser una cadena no vacía")

    # Validar ahora
    ahora = request.get('ahora')
    if not isinstance(ahora, str) or ahora == '':
        raise ErrorDeBrechaLegibilidad("ahora debe ser una cadena ISO-8601 no vacía")

    # Validar saltos_max — debe ser int > 0, rechaza bool, rechaza <= 0, rechaza no-int
    saltos_max = request.get('saltos_max')
    if isinstance(saltos_max, bool):
        raise ErrorDeBrechaLegibilidad("saltos_max debe ser un int > 0; se recibió bool")
    if not isinstance(saltos_max, int):
        raise ErrorDeBrechaLegibilidad("saltos_max debe ser un int > 0")
    if saltos_max <= 0:
        raise ErrorDeBrechaLegibilidad("saltos_max debe ser un int > 0")

    # Validar grafo
    grafo = request.get('grafo')
    if not isinstance(grafo, dict):
        raise ErrorDeBrechaLegibilidad("grafo debe ser un dict")

    # Validar avales
    avales = grafo.get('avales')
    if not isinstance(avales, list):
        raise ErrorDeBrechaLegibilidad("grafo['avales'] debe ser una lista")
    for i, v in enumerate(avales):
        if not isinstance(v, dict):
            raise ErrorDeBrechaLegibilidad(f"grafo['avales'][{i}] debe ser un dict")
        for field in ('de', 'a', 'celula_id'):
            val = v.get(field)
            if not isinstance(val, str) or val == '':
                raise ErrorDeBrechaLegibilidad(
                    f"grafo['avales'][{i}]['{field}'] debe ser una cadena no vacía"
                )
        # expira_en es opcional, puede ser str o None
        expira_en = v.get('expira_en')
        if expira_en is not None and not isinstance(expira_en, str):
            raise ErrorDeBrechaLegibilidad(
                f"grafo['avales'][{i}]['expira_en'] debe ser una cadena o null"
            )

    # Validar hechos
    hechos = grafo.get('hechos')
    if not isinstance(hechos, list):
        raise ErrorDeBrechaLegibilidad("grafo['hechos'] debe ser una lista")
    for i, f in enumerate(hechos):
        if not isinstance(f, dict):
            raise ErrorDeBrechaLegibilidad(f"grafo['hechos'][{i}] debe ser un dict")
        for field in ('sobre', 'celula_id'):
            val = f.get(field)
            if not isinstance(val, str) or val == '':
                raise ErrorDeBrechaLegibilidad(
                    f"grafo['hechos'][{i}]['{field}'] debe ser una cadena no vacía"
                )
        afirmacion = f.get('afirmacion')
        if not isinstance(afirmacion, str) or afirmacion == '':
            raise ErrorDeBrechaLegibilidad(
                f"grafo['hechos'][{i}]['afirmacion'] debe ser una cadena no vacía"
            )
        # expira_en es opcional, puede ser str o None
        expira_en = f.get('expira_en')
        if expira_en is not None and not isinstance(expira_en, str):
            raise ErrorDeBrechaLegibilidad(
                f"grafo['hechos'][{i}]['expira_en'] debe ser una cadena o null"
            )

    # 2. Escaneo de formas de vigilancia sobre TODA la solicitud (grafo incluido), recursivo
    found, match_key = _contains_forbidden_key(request, FORBIDDEN_KEYS)
    if found:
        raise ErrorDeBrechaLegibilidad(
            f"Forma de vigilancia detectada en la solicitud: clave {match_key!r}"
        )

    # 3. Filtrar: conservar sólo avales/hechos cuyo cell_id == celula_id Y no expirados en ahora
    # Aplicar ANTES del recorrido
    avales_filtrados = [
        v for v in avales
        if v['celula_id'] == celula_id and _no_expirado(v.get('expira_en'), ahora)
    ]
    hechos_filtrados = [
        f for f in hechos
        if f['celula_id'] == celula_id and _no_expirado(f.get('expira_en'), ahora)
    ]
    avales_considerados = len(avales_filtrados)
    hechos_considerados = len(hechos_filtrados)

    # 4. Recorrer las aristas de aval sobrevivientes dentro de la célula desde la posición del consultante.
    # Construir adyacencia deduplicada (D-05: aristas idénticas no deben producir rutas duplicadas
    # idénticas). `adj` es directa (de -> a's únicos ordenados); `radj` es inversa (a -> {de's}),
    # usada para calcular distancias HASTA el objetivo sin enumerar ninguna ruta.
    adj = {}
    radj = {}
    for v in avales_filtrados:
        fr = v['de']
        to = v['a']
        adj.setdefault(fr, set()).add(to)
        radj.setdefault(to, set()).add(fr)
    adj = {k: sorted(tos) for k, tos in adj.items()}

    rutas_truncadas = False

    # Caso especial: consultante == objetivo no produce ruta (auto-aval no es legibilidad).
    if consultante == objetivo:
        rutas_de_aval = []
        saltos_minimos = None
        avalado_por_gente_de_tu_confianza = []
    else:
        # (a) Un BFS inverso desde el objetivo sobre las aristas invertidas da dist_to_target[nodo]
        # para cada nodo dentro de saltos_max — LINEAL en el grafo, sin enumeración de rutas. Esto
        # produce la alcanzabilidad, saltos_minimos y (abajo) el conjunto exacto de avaladores
        # directos en alguna ruta más corta, nada de lo cual puede explotar en un grafo denso
        # (D-02). Una ruta más corta es inherentemente simple, así que no hace falta guardia de ciclos.
        dist_to_target = {objetivo: 0}
        frontier = [objetivo]
        for hop in range(1, saltos_max + 1):
            next_frontier = []
            for node in frontier:
                for pred in radj.get(node, ()):        # nodos con una arista HACIA `node`
                    if pred not in dist_to_target:
                        dist_to_target[pred] = hop
                        next_frontier.append(pred)
            if not next_frontier:
                break
            frontier = next_frontier

        saltos_minimos = dist_to_target.get(consultante)
        if saltos_minimos is None or saltos_minimos > saltos_max:
            saltos_minimos = None
            rutas_de_aval = []
            avalado_por_gente_de_tu_confianza = []
        else:
            # (b) Avaladores directos del consultante en ALGUNA ruta más corta — EXACTO y completo
            # (nunca se recorta): un vecino n califica sii dist_to_target[n] == saltos_minimos - 1.
            avalado_por_gente_de_tu_confianza = sorted(
                n for n in adj.get(consultante, ())
                if dist_to_target.get(n) == saltos_minimos - 1
            )
            # (c) Una muestra DETERMINISTA y ACOTADA de rutas más cortas concretas. Recorremos sólo
            # aristas de distancia decreciente (dist_to_target baja estrictamente en 1 en cada paso,
            # así que toda rama llega al objetivo — sin callejones sin salida) y nos detenemos en
            # _MAX_RUTAS_DE_AVAL. Sólo el objetivo lleva dist 0, así que `dist == 0` es exactamente
            # el objetivo. El orden de descubrimiento es determinista; el ordenamiento final hace
            # la salida canónica de todos modos.
            rutas_de_aval = []
            stack = [[consultante]]
            while stack and not rutas_truncadas:
                path = stack.pop()
                remaining = saltos_minimos - (len(path) - 1)   # aristas aún necesarias para llegar al objetivo
                for nb in sorted(adj.get(path[-1], ()), reverse=True):  # reverse: pop() produce orden asc
                    if dist_to_target.get(nb) != remaining - 1:
                        continue                              # fuera del frente de ruta más corta
                    new_path = path + [nb]
                    if nb == objetivo:
                        rutas_de_aval.append(new_path)
                        if len(rutas_de_aval) >= _MAX_RUTAS_DE_AVAL:
                            rutas_truncadas = True
                            break
                    else:
                        stack.append(new_path)
            rutas_de_aval.sort()

    # 5. Recopilar hechos sobrevivientes dentro de la célula cuyo about == objetivo, ordenados deterministamente
    hechos_objetivo = [
        f for f in hechos_filtrados
        if f['sobre'] == objetivo
    ]
    hechos_objetivo.sort(key=lambda x: x['afirmacion'])

    # 6. Construir la salida
    alcanzable = saltos_minimos is not None   # exacto (del BFS inverso), no la muestra acotada
    tiene_hechos = len(hechos_objetivo) > 0
    veredicto = "conocido_via_confianza" if (alcanzable or tiene_hechos) else "sin_informacion_desde_tu_posicion"

    return {
        'consultante': consultante,
        'objetivo': objetivo,
        'celula_id': celula_id,
        'desde_tu_posicion': {
            'alcanzable': alcanzable,
            'saltos_minimos': saltos_minimos,
            'rutas_de_aval': rutas_de_aval,
            'avalado_por_gente_de_tu_confianza': avalado_por_gente_de_tu_confianza,
            'hechos': [
                {
                    'afirmacion': f['afirmacion'],
                    'celula_id': f['celula_id'],
                    'expira_en': f.get('expira_en')
                }
                for f in hechos_objetivo
            ]
        },
        'veredicto': veredicto,
        'nota': "La ausencia de una ruta es 'sin información desde donde estás', nunca una marca en contra de nadie.",
        'traza_auditoria': {
            'regla': "rutas de aval dentro de la célula, no expiradas, desde el consultante dentro de saltos_max; hechos sobre el objetivo",
            'avales_considerados': avales_considerados,
            'hechos_considerados': hechos_considerados,
            'saltos_max': saltos_max,
            'rutas_de_aval_max': _MAX_RUTAS_DE_AVAL,
            'rutas_truncadas': rutas_truncadas
        }
    }
