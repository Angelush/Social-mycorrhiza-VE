"""Motor determinista de contrato de aseguramiento / quorum de la Capa 4.

Micorriza Política (social C2C/B2C/C2B). Resuelve una ÚNICA campaña de acción
colectiva: ¿se comprometió suficiente gente distinta para que la acción se
active? Si no, cada comprometido queda íntegramente restituido (reembolso
total), y — para un contrato de aseguramiento *dominante* — el bono del
patrocinador se reparte exactamente entre los comprometidos.

Este es el componente `[DETERMINISTA]` del sistema social (brief §4 Capa 4):
- Sin LLM, sin proceso estocástico, sin aritmética de punto flotante sobre dinero.
- Función pura, sin efectos secundarios, SIN estado entre campañas: devuelve una
  *propuesta*; activar la acción / mover los reembolsos es un paso separado con
  compuerta humana (el agente propone, el humano dispone).
- Determinista byte a byte para una misma entrada (recorrido ordenado).
- Anti-vigilancia por forma (brief §1/§3/§6). DENTRO de una única resolución la
  salida es estructuralmente incapaz de portar un puntaje por persona, un rango,
  o un agregado entre campañas; los tokens de participante son opacos y por
  campaña; no hay mecanismo de exclusión/veto (lista blanca, no lista negra); y
  la entrada se rechaza (recursivamente, a cualquier profundidad) si porta un
  campo con forma de crédito social. ENTRE campañas, la no-vigilancia es una
  *convención* que esta función pura no puede vigilar — depende de que quien
  llama rote los tokens por campaña y de que el almacenamiento honre
  `expira_en`. La garantía estructural es por llamada; la propiedad entre
  llamadas se documenta aquí, no se impone aquí.
- Las violaciones de invariante interno (conservación de bono / no-pérdida)
  abortan con ErrorDeInvarianteAseguramiento — deliberadamente NO un
  ValueError, para que quien valida la entrada no pueda tragarse una señal de
  motor-roto (N7/E3).

Spec: workflows/micorriza-politica/spec.md  Restricciones: .../constraints.md
Aceptación: .../evals/acceptance.md (AC1-AC6).

Procedencia: redactado por Mistral devstral-small-latest vía
multi-model-orchestration, revisado y corregido por Claude (guarda de bono con
cero comprometidos + limpieza); endurecido después en una auditoría — bono en
campaña binaria rechazado (membrana + anti-Sybil), escaneo recursivo de claves
prohibidas, excepción de aborto distinta, alcance honesto por llamada.
Solo stdlib.
"""
from __future__ import annotations
import re
import unicodedata


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


class ErrorDeInvarianteAseguramiento(Exception):
    """El motor produjo un resultado que viola su propio invariante de
    no-pérdida / conservación. Este es un aborto interno (un error o una
    corrupción), NO una entrada de usuario incorrecta — deliberadamente no es
    un ValueError, para que quien valida la entrada (`except ValueError`) no
    pueda tragarse en silencio una señal de motor-roto.
    Restricciones N7/E3: ante tal violación, abortar y sacar a la superficie —
    nunca emitir."""


def _forbidden_key_path(obj) -> "str | None":
    # Recorre toda la estructura (dicts, listas, tuplas) y devuelve la primera clave
    # cuyos tokens normalizados coincidan con la taxonomía por token EXACTO (o
    # bigrama adyacente / compuesto completo), o la primera clave cuyo VALOR porte
    # un patrón de identidad venezolano (cédula/RIF/teléfono), si no None. Recursivo
    # (no solo el nivel superior) para que también se rechace un dossier anidado a
    # cualquier profundidad — esto coincide con el escaneo recursivo de salida que
    # exigen las pruebas, y honra la postura de "rechazar la forma, ampliamente".
    # Las propias claves del esquema no contienen ninguno de estos tokens, así que
    # no hay falsos positivos en entrada válida.
    taxonomy = set(FORBIDDEN_KEYS)
    if isinstance(obj, dict):
        for k, v in obj.items():
            if _key_matches_taxonomy(k, taxonomy):
                return k
            if _value_has_identity_shape(v):
                return k
            found = _forbidden_key_path(v)
            if found is not None:
                return found
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            if _value_has_identity_shape(v):
                return "<value>"
            found = _forbidden_key_path(v)
            if found is not None:
                return found
    return None


def resolver(campana: dict) -> dict:
    # 1. Validar (rechazar, nunca reparar) ------------------------------------
    if not isinstance(campana, dict):
        raise ValueError("campana debe ser un dict")
    bad_key = _forbidden_key_path(campana)
    if bad_key is not None:
        raise ValueError(
            f"campana contiene una clave prohibida (con forma de vigilancia): {bad_key!r}")

    for key in ("campana_id", "celula_id"):
        val = campana.get(key)
        if not isinstance(val, str) or not val.strip():
            raise ValueError(f"{key} debe ser un str no vacío")

    tipo = campana.get("tipo")
    if tipo not in ("binario", "monetario"):
        raise ValueError("tipo debe ser 'binario' o 'monetario'")

    umbral = campana.get("umbral")
    if not isinstance(umbral, int) or isinstance(umbral, bool) or umbral <= 0:
        raise ValueError("umbral debe ser int > 0")

    bono_patrocinador_centavos = campana.get("bono_patrocinador_centavos", 0)
    if (not isinstance(bono_patrocinador_centavos, int) or isinstance(bono_patrocinador_centavos, bool)
            or bono_patrocinador_centavos < 0):
        raise ValueError("bono_patrocinador_centavos debe ser int >= 0")
    if tipo == "binario" and bono_patrocinador_centavos > 0:
        # Un bono de garantía dominante es un instrumento monetario/de mercado. Una
        # campaña binaria es un conteo de cabezas en una sala de igualdad/regalo sin
        # apuesta, así que un bono aquí (a) rompe la membrana mercado/igualdad
        # (invariante 1, N5) y (b) sin nada que compensar, convierte el pago de
        # fracaso en un grifo Sybil de costo cero (drenar el bono con tokens
        # desechables, §6.2).
        raise ValueError(
            "una campana binaria debe tener bono_patrocinador_centavos == 0 "
            "(sin instrumento de mercado en una sala de igualdad; anti-Sybil)")

    expira_en = campana.get("expira_en")
    if not isinstance(expira_en, str) or not expira_en.strip():
        raise ValueError("expira_en debe ser un str ISO-8601")

    compromisos = campana.get("compromisos", [])
    if not isinstance(compromisos, list):
        raise ValueError("compromisos debe ser una lista")

    seen_compromiso_ids: set[str] = set()
    for p in compromisos:
        if not isinstance(p, dict):
            raise ValueError("cada compromiso debe ser un dict")
        # el chequeo de clave prohibida ya corrió una vez, recursivamente, sobre toda la campana
        pid = p.get("compromiso_id")
        if not isinstance(pid, str) or not pid.strip():
            raise ValueError("compromiso_id debe ser un str no vacío")
        if pid in seen_compromiso_ids:
            raise ValueError(f"compromiso_id duplicado: {pid}")
        seen_compromiso_ids.add(pid)

        token = p.get("ficha_participante")
        if not isinstance(token, str) or not token.strip():
            raise ValueError("ficha_participante debe ser un str no vacío")

        amount = p.get("monto_centavos", 0)
        if tipo == "monetario":
            if "monto_centavos" not in p:
                raise ValueError("un compromiso monetario requiere monto_centavos")
            if not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
                raise ValueError("monto_centavos de un compromiso monetario debe ser int >= 0")
        else:  # binario: el precio de mercado NO debe filtrarse a una sala de igualdad (invariante 1)
            # Aceptar solo un no-precio explícito: ausente, None, o un int ESTRICTO 0. Rechazar bool y
            # float para que `False`/`0.0` no se cuelen por la coerción `==` de Python (D-06), y
            # cualquier precio distinto de cero sigue siendo brecha de membrana — la estrictez de
            # tipo ahora coincide con el camino monetario.
            if "monto_centavos" in p and amount is not None and not (
                    isinstance(amount, int) and not isinstance(amount, bool) and amount == 0):
                raise ValueError("un compromiso binario no debe portar precio (brecha de membrana)")

    # 2. Deduplicar comprometidos (una persona -> un peso; invariante 7) ------
    comprometidos = sorted({p["ficha_participante"] for p in compromisos})
    distinct = len(comprometidos)

    # 3. Decidir ---------------------------------------------------------------
    estado = "se_activa" if distinct >= umbral else "reembolsa"

    if estado == "se_activa":
        # 4. se_activa: total en garantía (0 para binario); no se paga bono.
        total_comprometido = sum(p.get("monto_centavos", 0) or 0 for p in compromisos)
        resolucion = {"se_activa": {"total_comprometido_centavos": total_comprometido}, "reembolsos": []}
    else:
        # 5. reembolsa: restitución completa por comprometido + reparto exacto del bono.
        comprometido_por_token: dict[str, int] = {}
        for p in compromisos:
            comprometido_por_token[p["ficha_participante"]] = (
                comprometido_por_token.get(p["ficha_participante"], 0)
                + (p.get("monto_centavos", 0) or 0)
            )

        reembolsos = []
        if distinct == 0:
            # Sin comprometidos: nadie a quien reembolsar o pagar. El bono no se
            # distribuye (vuelve al patrocinador); ningún comprometido queda peor.
            # Sin división por cero.
            bonus_total = 0
        else:
            base, rem = divmod(bono_patrocinador_centavos, distinct)
            bonus_total = 0
            for i, token in enumerate(comprometidos):  # orden ascendente de token
                bonus = base + 1 if i < rem else base
                reembolsos.append({
                    "ficha_participante": token,
                    "reembolso_centavos": comprometido_por_token.get(token, 0),
                    "bono_centavos": bonus,
                })
                bonus_total += bonus

        # 6. Guardas de conservación (invariantes internos; abortar, nunca emitir — N7/E3).
        expected_bonus = bono_patrocinador_centavos if distinct > 0 else 0
        if bonus_total != expected_bonus:
            raise ErrorDeInvarianteAseguramiento(
                "la distribución del bono no conserva bono_patrocinador_centavos")
        if sum(r["reembolso_centavos"] for r in reembolsos) != sum(comprometido_por_token.values()):
            raise ErrorDeInvarianteAseguramiento(
                "los reembolsos no conservan los montos comprometidos (se violó no-pérdida)")

        resolucion = {"se_activa": None, "reembolsos": reembolsos}

    return {
        "campana_id": campana["campana_id"],
        "celula_id": campana["celula_id"],
        "estado": estado,
        "comprometidos_distintos": distinct,
        "umbral": umbral,
        "expira_en": expira_en,
        "resolucion": resolucion,
        "traza_auditoria": {
            "regla": "comprometidos_distintos >= umbral",
            "deduplicado_de_compromisos": len(compromisos),
        },
    }
