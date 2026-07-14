"""
Módulo `modo` — calibración por hostilidad para el protocolo social Micorriza (Área c).

`[DETERMINISTA]`, puro, sin estado global. Maquinaria compartida: se construye UNA vez y la
consultan las seis capas. `modo` NO importa ninguna capa (C-c6, sin ciclos): es una hoja del grafo
de dependencias; las capas importan `modo`.

El `modo` viaja en el envelope de cada request (policéntrico, por célula — jamás estado global:
C-c1). Valores: `paz`, `catastrofe_acotada`, `catastrofe_severa`. Cada capa aplica `validar_modo`
sobre su envelope antes de su lógica propia. Un request que excede el límite de su modo se
**rechaza** (`raise`), nunca se recorta (C-c2).

Alcance del módulo: tabla de límites + `validar_modo` (Área c, TA.4); `validar_transicion` (trinquete
asimétrico), `depurar` (evacuación pura tras escalada) y el helper de convención `tras_escalada`
(Área d, TA.5). Todo puro y determinista; `modo` sigue sin importar ninguna capa.

Los valores de la tabla son DEFAULTS ajustables por decisión de Capa 6, no dogma (C-c3). Los valores
de `velocity_cap` (ordinal `estrictez_velocidad` + cota `tope_velocidad_max`) son PROPUESTAS de
gobernanza para el hueco declarado por el prompt; el test verifica la *relación* de estrictez, no un
valor absoluto validado en campo.

Especificación: workflows/micorriza-politica-ve/area-c-modo/{spec,constraints,failure-model}.md
Diseño: workflows/micorriza-politica-ve/area-c-modo/DESIGN-TA4.md
"""
import json
from datetime import date, timedelta


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


# ==================================================================== Área d · TA.5
# El trinquete asimétrico y la evacuación pura. Ver DESIGN-TA5.md y area-d-trinquete/{spec,
# constraints,failure-model}.md. Todo puro; `modo` no importa ninguna capa (C-c6).

def _indice_modo(m):
    """Índice de estrictez de `m` en MODOS (paz=0 < acotada=1 < severa=2). `raise` si inválido."""
    if m not in MODOS:
        raise ErrorDeModo(f"modo inválido: {m!r}; uno de {MODOS}")
    return MODOS.index(m)


def _autoriza_desescalada(decision, propuesto):
    """¿`decision` (veredicto de `gobernanza.decidir`) autoriza la desescalada a `propuesto`?

    La correspondencia "esa propuesta `cambiar_modo` / ese círculo" (C-d2) es auto-contenida en la
    decisión, porque la firma de `validar_transicion` es de tres argumentos y no lleva círculo.
    Convención del `propuesta_id` de una propuesta de cambio de modo:

        cambiar_modo:{circulo_id}:{modo_destino}

    Autoriza iff la decisión es `adoptada` Y su `propuesta_id` codifica exactamente un cambio a
    `propuesto` **ligado a su propio círculo**. Así:
      - otra propuesta → `propuesta_id` no codifica `cambiar_modo…:{propuesto}` → no autoriza;
      - otro círculo → `propuesta_id` nombra un círculo distinto del `circulo_id` de la decisión
        (una decisión adoptada de B no puede autorizar la propuesta de A) → no autoriza;
      - veredicto `revisar` → no autoriza.

    Se consume el veredicto tal cual; NO se reimplementa gobernanza (C-d5). La clave es `veredicto`
    (con e), la que devuelve `gobernanza.decidir` — la fuente de verdad, aunque la prosa del spec
    escriba `verdicto`.
    """
    if not isinstance(decision, dict):
        return False
    if decision.get('veredicto') != 'adoptada':
        return False
    circulo_id = decision.get('circulo_id')
    if not isinstance(circulo_id, str) or circulo_id == '':
        return False
    esperado = f"cambiar_modo:{circulo_id}:{propuesto}"
    return decision.get('propuesta_id') == esperado


def validar_transicion(actual, propuesto, decision_capa6=None):
    """Trinquete asimétrico de modos. Función pura; devuelve un ESTADO, nunca recorta (§F, área d).

    - **Escalada** (a mayor hostilidad, `idx(propuesto) > idx(actual)`): **unilateral e inmediata**;
      cualquier token la dispara, `decision_capa6` es irrelevante (C-d1). Devuelve `'escalada'`.
    - **Desescalada** (a menor hostilidad): válida SOLO con una decisión `adoptada` de Capa 6 sobre
      la propuesta `cambiar_modo` de ese círculo (`_autoriza_desescalada`). Devuelve `'desescalada'`.
      Re-expandir retención/alcance/payload es riesgo colectivo, no de un individuo (C-d1).
    - `actual == propuesto`: **no es transición**; devuelve `'no_op'` (explícito, sin error — AC-d3).

    Fuerza el PROCEDIMIENTO, no la buena fe (C-d3): no impide escaladas abusivas en bucle; solo
    garantiza que desescalar exija consentimiento. El cooldown es decisión de gobernanza abierta,
    NO se incrusta aquí (failure-model).

    Returns:
        str: `'escalada'`, `'desescalada'` o `'no_op'`.

    Raises:
        ErrorDeModo: modo inválido, o desescalada sin decisión `adoptada` correspondiente (rechazo).
    """
    ia, ip = _indice_modo(actual), _indice_modo(propuesto)
    if ip == ia:
        return 'no_op'
    if ip > ia:
        return 'escalada'
    # Desescalada: exige consentimiento de Capa 6 para esa propuesta y ese círculo.
    if _autoriza_desescalada(decision_capa6, propuesto):
        return 'desescalada'
    raise ErrorDeModo(
        f"desescalada {actual}→{propuesto} rechazada: requiere una decisión 'adoptada' de Capa 6 "
        f"sobre la propuesta 'cambiar_modo' de ese círculo (sin auto-propagación)"
    )


def depurar(items, modo, ahora):
    """Evacuación pura determinista: aplica la ventana de retención de `modo` a `items` almacenados.

    `ahora` es una fecha ISO (granularidad de días, coherente con `validar_modo`). Por tipo de item
    (clave `tipo`, con `creado_en` ISO):

      - `traza`: se **RECORTA** su TTL a la ventana `retencion_trazas_dias` — `expira_en ←
        min(expira_en, creado_en + ventana)` — y se **conserva** (nunca se elimina: es el "salvo" del
        spec). El recorte es idempotente (AC-M3).
      - resto (`dato`, …): se **ELIMINA** si `edad = ahora − creado_en` excede `retencion_max_dias`;
        si no, se conserva sin cambios.

    Un item con `creado_en` no parseable se descarta (evacuación conservadora: sin fecha no se puede
    probar que está dentro de ventana ni recortar su TTL). **Señalado.**

    NO muta las entradas (las trazas recortadas son copias). La EJECUCIÓN de `depurar` tras una
    escalada es convención del llamador (una función pura no puede forzarse): ver `tras_escalada`,
    el test que la fija, y C-d4/C-c5.

    Returns:
        list: los items que sobreviven (datos dentro de ventana + trazas con TTL recortado).

    Raises:
        ErrorDeModo: `modo` inválido, o `ahora` no es una fecha ISO.
    """
    if modo not in LIMITES:
        raise ErrorDeModo(f"modo inválido: {modo!r}; uno de {MODOS}")
    lim = LIMITES[modo]
    d_ahora = _fecha_iso(ahora)
    if d_ahora is None:
        raise ErrorDeModo(f"ahora debe ser una fecha ISO (YYYY-MM-DD…): {ahora!r}")

    supervivientes = []
    for item in items:
        creado = _fecha_iso(item.get('creado_en') if isinstance(item, dict) else None)
        if creado is None:
            continue  # malformado: no verificable → se descarta (conservador)
        if item.get('tipo') == 'traza':
            tope = creado + timedelta(days=lim['retencion_trazas_dias'])
            exp = _fecha_iso(item.get('expira_en'))
            nuevo = tope if exp is None else min(exp, tope)
            recortada = dict(item)
            recortada['expira_en'] = nuevo.isoformat()
            supervivientes.append(recortada)
        else:
            edad = (d_ahora - creado).days
            if edad <= lim['retencion_max_dias']:
                supervivientes.append(item)
    return supervivientes


def tras_escalada(items, actual, propuesto, ahora):
    """Helper de CONVENCIÓN (C-d4) que acopla escalada→depuración; NO es un efecto forzado.

    Valida que `actual→propuesto` sea una escalada y devuelve `depurar(items, propuesto, ahora)`, de
    modo que los items que exceden la nueva ventana más estricta se eliminen/recorten. El
    acoplamiento se fija con este helper + un test + la convención documentada; una función pura no
    puede obligar al llamador a invocarlo (C-d4, C-c5/failure-model). NO se finge la garantía.

    Raises:
        ErrorDeModo: si `actual→propuesto` no es una escalada (o algún modo es inválido).
    """
    if validar_transicion(actual, propuesto) != 'escalada':
        raise ErrorDeModo(
            f"tras_escalada solo aplica a una escalada; {actual}→{propuesto} no lo es"
        )
    return depurar(items, propuesto, ahora)
