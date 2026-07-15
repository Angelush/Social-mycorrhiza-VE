# DESIGN — TA.7 · Área f · Perfil de convergencia en desastre (sobre Capa 5)

> Opus diseña e implementa; los tests mecánicos van por fan-out a un modelo gratis
> con contrato de firmas fijado aquí. **Reutiliza Capa 5 (`estigmergia.py`); NO
> construye capa nueva** (C-f1). Gate TA.7: AC-6; suite verde.

## 0. Reconciliación spec ↔ código (como en TA.6)

El sketch de spec/prompt nombra las señales castellanizadas como
`presencia/camino/alerta/contribucion/respaldo`. **El código real de TA.3 usa otros
lemas** y manda el código, no el sketch:

```
ALLOWED_SIGNALS = ('contribucion', 'ruta', 'respaldo', 'presencia', 'bandera')
JUDGMENT_SIGNALS = ('bandera',)   # la única señal con forma de juicio
```

`ruta` (no `camino`) y `bandera` (no `alerta`) son los lemas vigentes. `bandera` ES
la "alerta" del sketch: es la señal de juicio sujeta al cortacircuito
contexto-antes-que-juicio (AC-f1). No se renombra nada en TA.7.

## 1. Alcance (una sola capa)

Solo `src/stigmergy/estigmergia.py` (Capa 5) + lectura de la fuente única de
`src/modo/modo.py` (tabla de límites, TA.4). No toca aseguramiento, membrana ni
gobernanza (C-f1, "Alcance" de constraints). Los cortacircuitos heredados
(fricción/velocity-cap por cubeta-ventana, contexto-antes-que-juicio, alcance
celular/cero-broadcast) YA están y **no se tocan**; TA.7 solo suma dos reglas y
cablea el cap por modo.

## 2. Tabla de cambios

| # | Dónde | Cambio | AC | Firewall |
|---|-------|--------|-----|----------|
| 1 | `ALLOWED_SIGNALS` | añadir `'paso_maquinaria'` | AC-f4, AC-C1 | taxonomía PRIVADA de capa (fuera del bloque md5 5d693ec) → intacto |
| 2 | loop de validación por traza | rechazar toda traza con `about` de espacio `persona:` (regla traza-ambiental, invariantes 1/2) | AC-C1, AC-f4 | privada |
| 3 | loop de validación por traza | `paso_maquinaria` **solo** válida sobre `zona:*` (namespace obligatorio) | AC-f4, AC-C1 | privada |
| 4 | tras `validar_modo`, antes de aplicar el cap | si viene `modo`: rechazar si `tope_velocidad > TOPE_VELOCIDAD_MAX[modo]` (cap severo estricto; fuente única modo.py, NO se duplica) | AC-f2, AC-C1, AC-c5 | n/a |

### Detalle de cada cambio

**Cambio 1 — whitelist.** `paso_maquinaria` es señal ambiental sobre una ZONA
(artefacto). Se suma a la lista blanca privada de la capa. NO es señal de juicio →
NO entra en `JUDGMENT_SIGNALS` (no la amortigua el cortacircuito de contexto; es una
marca de zona representable y visible, C-f2/AC-C1). Como `ALLOWED_SIGNALS` ya vive
DESPUÉS de `# === END shared firewall machinery ===`, es taxonomía de dominio privada
igual que `MARKET_KEYS`/`TASA_KEYS` (patrón TA.6) → **md5 firewall
`5d693ecf1833fb760e173ee3db30a263` (span: bloque `BEGIN…END` completo, incluido su `\n` final
= 3023 bytes) intacto en las 6, `test_cross_layer_taxonomy` sin tocar.**

**Cambios 2+3 — regla traza-ambiental (no-sobre-persona).** Constantes privadas:

```python
_NS_PERSONA = 'persona:'   # jamás sujeto de una traza (invariantes 1/2)
_NS_ZONA = 'zona:'         # espacio de artefacto para señales de zona
_SENALES_SOLO_ZONA = ('paso_maquinaria',)  # señal ambiental de zona
```

En el loop `for i, trace in enumerate(trazas)`, tras validar que `about` es cadena no
vacía y ANTES/junto a la validación de `senal`:

- **Universal (cambio 2):** si `about` empieza por `_NS_PERSONA` → `raise
  ErrorDeBrechaEstigmergia`. Ninguna traza —de cualquier señal— puede ser *sobre una
  persona*. Es un rechazo de sobre (envelope breach), no un descarte-y-cuenta: una
  traza sobre persona es una marca encubierta, se rechaza duro (convención: brechas de
  forma-de-vigilancia lanzan; ver el `_scan_forbidden` que ya lanza).
- **Específico de la señal (cambio 3):** si `senal in _SENALES_SOLO_ZONA` y `about` NO
  empieza por `_NS_ZONA` → `raise`. `paso_maquinaria` es válida *solo* sobre `zona:*`.

Orden: validar `senal ∈ ALLOWED_SIGNALS` primero (ya existe), luego el chequeo
`_SENALES_SOLO_ZONA`. El chequeo persona va junto a la validación de `about`.

Por qué `raise` y no descartar-y-contar: los descartes-y-cuenta de Capa 5
(fuera-de-célula, futura, bandera-sin-contexto, sobre-el-tope, evaporada) son
contenido *bien-formado* que el ambiente amortigua. Una traza *sobre persona* está
mal-formada respecto de la regla traza-ambiental — misma categoría que una clave de
vigilancia detectada por `_scan_forbidden`, que lanza. AC-C1 dice "rechazado", no
"amortiguada". → `raise ErrorDeBrechaEstigmergia`.

**Regresión:** los abouts de los fixtures existentes son `"a"/"b"/"c"/"d"/"f"/
"flg"/"hot"` — ninguno con prefijo `persona:` ni son `paso_maquinaria` → **cero
regresión** sobre los 429. No hace falta tocar fixtures (a diferencia de TA.6).

**Cambio 4 — cap severo estricto vía `modo` (fuente única).** Hoy `sentir` llama
`validar_modo(request)` solo para validar, y luego usa `tope_velocidad` del request
tal cual. TA.7 cablea la cota del modo: la estrictez del `velocity_cap` por modo es
`TOPE_VELOCIDAD_MAX = {'paz': 50, 'catastrofe_acotada': 10, 'catastrofe_severa': 3}`
(fuente ÚNICA en `modo.py`, TA.4). Estrictez severa(3) ≤ acotada(10) ≤ paz(50) →
severa es el cap más estricto (AC-c5/AC-f2).

Regla (patrón "rechaza, no recorta" del fork, igual que `validar_modo`): **si viene
`modo` y `tope_velocidad > TOPE_VELOCIDAD_MAX[modo]` → `raise
ErrorDeBrechaEstigmergia`.** No se puede pedir un cap más laxo que la cota estricta del
modo. El mecanismo del velocity-cap **nunca se apaga** (C-f3/invariante 8): un
`tope_velocidad` válido siempre debe ser `>= 1` (ya validado) y `<= cota del modo`; la
cota más estricta (severa=3) sigue siendo un cap activo, no un apagado.

Import: se reutiliza `TOPE_VELOCIDAD_MAX` de `modo.modo` (ya hay shim de path
`__file__`-relativo y el import guardado `if 'modo' in request`, patrón TA.4). **NO se
duplica la tabla de límites** (el failure-model lo prohíbe; distinto del firewall que
sí se duplica a propósito). Se añade `TOPE_VELOCIDAD_MAX` al import existente
`from modo.modo import validar_modo, ErrorDeModo`.

Ubicación: dentro del bloque `if 'modo' in request:`, tras `validar_modo(request)` y
tras leer/validar `velocity_cap` como int>0. Como `velocity_cap` se lee más abajo,
el chequeo del cap va DESPUÉS de esa validación (reordenar: mover el chequeo del cap
severo a después de la validación de `tope_velocidad`, guardado por `if 'modo' in
request`).

## 3. Contrato de firmas para el fan-out (tests)

El modelo gratis escribe `C2C-VE/tests/test_area_f_convergencia.py` contra ESTAS
firmas fijas (no las cambia):

- `from stigmergy.estigmergia import sentir, ErrorDeBrechaEstigmergia, ALLOWED_SIGNALS`
- `sentir(request: dict) -> dict`. Request keys: `celula_id:str`, `ahora:int`,
  `ventana:int>0`, `tope_velocidad:int>0`, `vida_media:int>0`, `fuerza_min:number>=0`,
  `trazas:list[dict]`, opcional `modo:str`.
- Cada traza: keys exactas de `_TRACE_KEYS` = `about, senal, fuerza, creado_en,
  celula_id, contexto`. `about:str no vacío`; `senal ∈ ALLOWED_SIGNALS`; `fuerza:
  number>0`; `creado_en:int`; `celula_id:str no vacío`; `contexto:str|None`.
- Salida: `{'celula_id','ahora','sentidas':[{about,senal,celula_id,fuerza_efectiva,
  contexto}],'veredicto': 'senales_sentidas'|'silencio_desde_tu_celula','nota',
  'traza_auditoria': {..., 'amortiguadas_velocidad', 'amortiguadas_sin_contexto',
  'descartadas_fuera_de_celula', 'tope_velocidad', ...}}`.
- `modo ∈ ('paz','catastrofe_acotada','catastrofe_severa')`; cotas de cap
  `{50,10,3}`.

AC a cubrir:
- **AC-C1 / AC-f4**: ráfaga de `presencia` sobre `zona:X` con `tope_velocidad`
  chico → `amortiguadas_velocidad>0` (throttled); una traza `paso_maquinaria` sobre
  `zona:X` es válida y sentida (aparece en `sentidas`); una traza con `about`
  `persona:*` → `raise ErrorDeBrechaEstigmergia`; `paso_maquinaria` sobre `persona:*`
  o sobre un about no-`zona:` → `raise`.
- **AC-f1**: una `bandera` sin `contexto` (None o '') → amortiguada
  (`amortiguadas_sin_contexto>0`, no aparece en `sentidas`); con contexto → pasa.
- **AC-f2**: velocity-cap activo en los tres modos; con `modo` presente,
  `tope_velocidad` mayor que la cota del modo → `raise`; cota severa(3) ≤ acotada(10)
  ≤ paz(50). Ningún modo apaga el cap (con `tope_velocidad` dentro de cota, siempre se
  throttlea una ráfaga que lo supere).
- **AC-f3**: alcance celular — una traza con `celula_id` ≠ el `celula_id` del request
  no aparece en `sentidas` (`descartadas_fuera_de_celula>0`).

Piso: la suite debe quedar **429 + nuevos** verdes.
