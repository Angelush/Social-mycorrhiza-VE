"""
Módulo `modo` — calibración por hostilidad para el protocolo social Micorriza (Área c).

`[DETERMINISTA]`, puro, sin estado global. Maquinaria compartida: se construye UNA vez y la
consultan las seis capas. `modo` NO importa ninguna capa (C-c6, sin ciclos): es una hoja del grafo
de dependencias; las capas importan `modo`.

El `modo` viaja en el envelope de cada request (policéntrico, por célula — jamás estado global:
C-c1). Valores: `paz`, `catastrofe_acotada`, `catastrofe_severa`. Cada capa aplica `validar_modo`
sobre su envelope antes de su lógica propia. Un request que excede el límite de su modo se
**rechaza** (`raise`), nunca se recorta (C-c2).

Alcance de este módulo (TA.4): tabla de límites + `validar_modo`. `depurar()` (evacuación pura tras
escalada) y `validar_transicion()` (trinquete asimétrico) pertenecen al Área d (TA.5) y se añaden
allí; no viven aquí todavía.

Los valores de la tabla son DEFAULTS ajustables por decisión de Capa 6, no dogma (C-c3). Los valores
de `velocity_cap` (ordinal `estrictez_velocidad` + cota `tope_velocidad_max`) son PROPUESTAS de
gobernanza para el hueco declarado por el prompt; el test verifica la *relación* de estrictez, no un
valor absoluto validado en campo.

Especificación: workflows/micorriza-politica-ve/area-c-modo/{spec,constraints,failure-model}.md
Diseño: workflows/micorriza-politica-ve/area-c-modo/DESIGN-TA4.md
"""
import json
from datetime import date


class ErrorDeModo(Exception):
    """Se lanza cuando un request viola el límite de su modo, o su modo es ausente/inválido."""
    pass


# Los tres modos de calibración por hostilidad. Ordenados de menor a mayor hostilidad.
MODOS = ('paz', 'catastrofe_acotada', 'catastrofe_severa')

# Tabla de límites por defecto (C-c3: defaults ajustables solo por decisión de Capa 6, NO dogma).
# Fuente ÚNICA: las capas la consultan, no la copian (failure-model: "deriva de límites entre capas").
LIMITES = {
    'paz': {
        'retencion_max_dias': 365,
        'retencion_trazas_dias': 90,
        'max_hops': 4,
        'max_payload_bytes': 64 * 1024,   # 65536
        'max_proposals': 20,
        'estrictez_velocidad': 1,         # laxo
        'tope_velocidad_max': 50,         # propuesto (hueco declarado)
    },
    'catastrofe_acotada': {
        'retencion_max_dias': 45,
        'retencion_trazas_dias': 14,
        'max_hops': 3,
        'max_payload_bytes': 8 * 1024,    # 8192
        'max_proposals': 10,
        'estrictez_velocidad': 2,         # medio
        'tope_velocidad_max': 10,         # propuesto
    },
    'catastrofe_severa': {
        'retencion_max_dias': 7,
        'retencion_trazas_dias': 3,       # 72 horas
        'max_hops': 2,
        'max_payload_bytes': 512,         # SMS/LoRa
        'max_proposals': 5,
        'estrictez_velocidad': 3,         # estricto
        'tope_velocidad_max': 3,          # propuesto
    },
}

# Vistas derivadas expuestas para los tests (AC-c5) y para lectores del módulo.
ESTRICTEZ_VELOCIDAD = {m: LIMITES[m]['estrictez_velocidad'] for m in MODOS}
TOPE_VELOCIDAD_MAX = {m: LIMITES[m]['tope_velocidad_max'] for m in MODOS}


def estrictez_velocidad(modo):
    """Ordinal de estrictez de `velocity_cap` para `modo` (1 laxo < 2 medio < 3 estricto).

    Satisface la *relación* AC-c5 (paz <= acotada <= severa), no un valor absoluto de campo.
    """
    if modo not in LIMITES:
        raise ErrorDeModo(f"modo inválido: {modo!r}; uno de {MODOS}")
    return LIMITES[modo]['estrictez_velocidad']


def _es_entero(x):
    """int verdadero (no bool, que es subclase de int)."""
    return isinstance(x, int) and not isinstance(x, bool)


def _tamano_payload_bytes(request):
    """Tamaño del envelope COMPLETO en JSON canónico determinista (bytes UTF-8).

    El límite de payload (p.ej. 512 B en severa) modela el canal SMS/LoRa: lo que debe caber es el
    mensaje entero, no un sub-campo. Serialización canónica → medida reproducible y estable.
    """
    serial = json.dumps(request, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return len(serial.encode('utf-8'))


def _fecha_iso(s):
    """`date` a partir de los primeros 10 caracteres YYYY-MM-DD de una cadena ISO-8601, o None si
    no parsea (granularidad de días; la retención de la tabla está en días)."""
    if not isinstance(s, str) or len(s) < 10:
        return None
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        return None


def validar_modo(request):
    """Aplica los límites del modo del `request` a su envelope. Rechaza (`raise ErrorDeModo`), nunca
    recorta (C-c2).

    El `modo` es obligatorio en el request y debe ser uno de MODOS; ausente o inválido → `raise`
    (nunca un default silencioso: escondería la ausencia de una decisión de gobernanza — AC-c2).

    Límites aplicados (cada uno solo si su dato está presente, salvo el payload que es universal):
      - payload: tamaño del envelope serializado > `max_payload_bytes` → raise (AC-c1).
      - retención: `expira_en - ahora` (días de calendario) > `retencion_max_dias` → raise; solo si
        `expira_en` y `ahora` son ambos cadenas ISO (en Capa 5 `ahora` es tick int → se omite aquí;
        la ventana de trazas la gobierna `depurar()` en TA.5).
      - `max_hops` (Capa 2), `max_proposals` (Capa 3), `tope_velocidad` (Capa 5): si la clave existe
        y excede la cota del modo → raise.

    Returns:
        str: el `modo` validado.

    Raises:
        ErrorDeModo: modo ausente/inválido, o cualquier límite excedido.
    """
    if not isinstance(request, dict):
        raise ErrorDeModo("request debe ser un dict")

    modo = request.get('modo')
    if modo not in LIMITES:
        raise ErrorDeModo(
            f"modo ausente o inválido: {modo!r}; debe ser uno de {MODOS} (sin default silencioso)"
        )
    lim = LIMITES[modo]

    # Payload (universal a las 6 capas).
    tam = _tamano_payload_bytes(request)
    if tam > lim['max_payload_bytes']:
        raise ErrorDeModo(
            f"payload de {tam} bytes excede el límite de {modo}: {lim['max_payload_bytes']} bytes"
        )

    # Retención por tiempo de calendario (solo con expira_en y ahora ISO).
    expira_en = request.get('expira_en')
    ahora = request.get('ahora')
    if expira_en is not None:
        d_expira = _fecha_iso(expira_en)
        d_ahora = _fecha_iso(ahora)
        if d_expira is not None and d_ahora is not None:
            dias = (d_expira - d_ahora).days
            if dias > lim['retencion_max_dias']:
                raise ErrorDeModo(
                    f"retención de {dias} días excede el límite de {modo}: "
                    f"{lim['retencion_max_dias']} días (rechazo, no recorte)"
                )

    # max_hops (Capa 2).
    if 'max_hops' in request:
        h = request['max_hops']
        if _es_entero(h) and h > lim['max_hops']:
            raise ErrorDeModo(f"max_hops={h} excede el límite de {modo}: {lim['max_hops']}")

    # max_proposals (Capa 3).
    if 'max_proposals' in request:
        p = request['max_proposals']
        if _es_entero(p) and p > lim['max_proposals']:
            raise ErrorDeModo(
                f"max_proposals={p} excede el límite de {modo}: {lim['max_proposals']}"
            )

    # tope_velocidad (Capa 5): menor = más estricto; el modo impone una cota superior.
    if 'tope_velocidad' in request:
        t = request['tope_velocidad']
        if _es_entero(t) and t > lim['tope_velocidad_max']:
            raise ErrorDeModo(
                f"tope_velocidad={t} excede el límite de {modo}: {lim['tope_velocidad_max']}"
            )

    return modo
