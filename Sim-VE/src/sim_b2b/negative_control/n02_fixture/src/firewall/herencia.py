"""Herencia del firewall C2C-VE, con alcance (D9 / M5).

Séptima copia del bloque compartido que las seis capas C2C-VE mantienen byte a byte
en acuerdo. Copiado verbatim; NADA de fuera del bloque se hereda — ni MARKET_KEYS, ni
RECIPROCITY_LEDGER_KEYS, ni TASA_KEYS, ni _ENVELOPE_KEYS, ni _contains_forbidden_key.
Esas son taxonomías de DOMINIO, y `credito`/`saldo`/`deuda`/`moneda` son el vocabulario
nuclear del ledger B2B: heredarlas sería un firewall que mata al paciente (M5, R3, AC-10).

El corte no lo hace este archivo: lo hace la geometría del original. TA.6 ya sacó las
taxonomías de dominio fuera del bloque compartido, precisamente por ser de dominio.

DÓNDE SE APLICA: solo en superficies de entrada de FORMA LIBRE que introduzcan los deltas
nuevos. NO sobre los esquemas cerrados heredados del ledger (`allowed_keys`), que ya están
protegidos por algo más fuerte: la lista blanca. En Fase 2 la única superficie de forma libre
es `referencias_comerciales` (D5/TB.5).

EL BLOQUE Y SU md5 — el span es parte de la constante:
    span   = desde la línea marcadora BEGIN hasta la línea marcadora END, INCLUIDO el
             '\n' final de esta última
    bytes  = 3023
    md5    = 5d693ecf1833fb760e173ee3db30a263   (= el '5d693ec' publicado en Fase 1, correcto)
Un md5 sin span declarado no es verificable: el mismo bloque con .strip() da 3022 bytes y
758094a99054feffa153c869ecf17d5b. TB.1 confundió ese cambio de convención con un número
falso. Si AC-d9.1 falla, se arregla la copia — jamás el literal ni el span (ST-d9.3/ST-d9.6).

Hay SIETE copias ahora (6 capas C2C-VE + esta). Si el bloque cambia, cambian las siete o no
cambia ninguna (C-d9.1). Es otro árbol a propósito: importar de C2C-VE cruzaría los dos forks
y acoplaría sus ciclos de vida.

Spec: B2B/workflows/micorriza-ve/d9-herencia-scoping/spec.md
Acceptance: idem, evals/acceptance.md (AC-10, AC-d9.1..d9.6).
Provenance: bloque copiado por programa desde C2C-VE/src/partition/membrana.py en TB.2.
stdlib only.
"""
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
