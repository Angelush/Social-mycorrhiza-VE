# PROMPT — Fork Venezuela del protocolo C2C "Micorriza Política"

> Prompt ejecutable para un agente de ingeniería (Claude Code / Opus) con acceso al repositorio.
> Idioma de trabajo y de todo el artefacto resultante: **castellano**.

---

## ROL Y CONTEXTO

Eres un ingeniero de software senior trabajando sobre el repositorio `Angelush/Social-mycorrhiza`, directorio `C2C` (rama `master`). Ese directorio contiene una implementación spec-driven del protocolo social "Micorriza Política": seis capas puras, deterministas y sin efectos secundarios (`src/partition/membrane.py`, `src/legibility/legibility_query.py`, `src/matcher/matcher.py`, `src/assurance/assurance_engine.py`, `src/stigmergy/stigmergy.py`, `src/governance/governance.py`), un bundle de especificación por capa en `workflows/micorriza-politica/` (intent / context / architecture / spec / constraints / failure-model / evals), y ~293 tests (aceptación + propiedades + golden-set + cross-layer).

La filosofía del repo, que DEBES conservar:
- Los invariantes se fuerzan **estructuralmente** (formas irrepresentables), nunca como líneas de política ni flags.
- Funciones puras: estado suministrado por el llamador, escaneado y descartado; nada se persiste.
- "El agente propone, el humano dispone"; el único LLM (Capa 3) está encajonado e inyectado.
- Rechazar, nunca reparar (`raise` en breach de envelope/forma); contenido malo del modelo se descarta-y-cuenta, nunca crashea.
- **"Flagged, not fake-resolved":** lo que el código no puede resolver se declara abiertamente, no se finge.
- Método spec-driven: **las especificaciones se escriben ANTES que el código**, siguiendo la estructura de bundle existente.

## OBJETIVO DEL FORK

Crear la rama/fork **`venezuela`** (directorio `C2C-VE/` o repo `Social-mycorrhiza-VE`, a tu criterio documentado) que adapta el protocolo al contexto venezolano:

1. **Todo en castellano**: identificadores públicos, claves de esquema, mensajes de error, notas, verdictos, docs y tests.
2. **Doble moneda**: dólar estadounidense (USD) y bolívar (VES), sin conversión automática jamás.
3. **Tres modos de calibración por célula**: `paz`, `catastrofe_acotada`, `catastrofe_severa`, con transición en trinquete gobernada por Capa 6.
4. **Todas las correcciones de la auditoría**: taxonomías bilingües con matching por tokens y normalización de acentos, `cédula`/`RIF`, escaneo de valores para patrones de identidad, y regresiones de falsos positivos (`banco_de_tiempo`).
5. **Perfil de convergencia en desastre** reutilizando la Capa 5 (no construir una capa nueva).

---

## LO INTOCABLE — INVARIANTES QUE NINGÚN MODO TOCA

Estos siguen siendo **irrepresentables en los tres modos**. Si una tarea de este prompt parece pedirte relajarlos, la interpretación es errónea: detente y re-lee.

1. **Ningún escalar global de la persona** (score/puntuación/reputación numérica): la forma se rechaza en entrada y es inconstruible en salida, en las seis capas.
2. **Ninguna lista negra / veto / sanción representable**; whitelist-not-blacklist; una ausencia es "sin información desde tu posición", nunca una marca.
3. **Vista de dios irrepresentable**: `consultante` (asker) obligatorio en legibilidad; el grafo es suministrado, hop-bounded, y se descarta; la salida son caminos y hechos, jamás un número.
4. **Voz independiente de la reputación**: un token, una voz; la ponderación no se puede ni escribir (taxonomía de peso de voto rechazada).
5. **Sin tenedor central**: funciones puras; nada persistido; ningún trono que capturar.
6. **El agente propone, el humano dispone**; el LLM sigue inyectado, encajonado, y su orden se descarta con sort canónico.
7. **Ninguna señal de engagement representable** en el emparejador.
8. **Cortacircuitos anti-cascada** siguen activos en toda propagación (los parámetros varían por modo; el mecanismo nunca se apaga).
9. **Salida siempre disponible**: participación opt-in; el fork mismo es prueba del derecho a bifurcar.
10. **Sin integración con canales estatales de identidad o denuncia** (p. ej., VenApp o su equivalente): constraint duro con cláusula-porque en `constraints.md` — el riesgo es la captura política de la coordinación, no solo la vigilancia.

**Lo que los modos SÍ calibran:** retención (ventanas de expiración), alcance (max_hops, portabilidad entre células), tamaño de payload, y parámetros de los cortacircuitos. **Nada más.**

---

## ESPECIFICACIONES POR ÁREA

### A. Castellanización (renombrado completo y consistente)

Renombra módulos, funciones públicas, claves de esquema, valores enumerados, mensajes y verdictos. Mapa principal (complétalo con una tabla exhaustiva en el spec bundle; consistencia total en código+tests+docs):

| Original | Castellano |
|---|---|
| `membrane.py` / `admit()` | `membrana.py` / `admitir()` |
| `legibility_query.py` / `query()` | `legibilidad.py` / `consultar()` |
| `matcher.py` / `match()` | `emparejador.py` / `emparejar()` |
| `assurance_engine.py` | `aseguramiento.py` |
| `stigmergy.py` / `sense()` | `estigmergia.py` / `sentir()` |
| `governance.py` / `decide()` | `gobernanza.py` / `decidir()` |
| `mode` (Capa 1, sala relacional) | **`sala`** — valores: `don_comunal`, `igualdad`, `precio_de_mercado` |
| *(nuevo)* modo de calibración | **`modo`** — valores: `paz`, `catastrofe_acotada`, `catastrofe_severa` |
| `cell_id` / `circle_id` | `celula_id` / `circulo_id` |
| `asker` / `target` | `consultante` / `objetivo` |
| `now` / `expires_at` | `ahora` / `expira_en` |
| `vouches` / `facts` / `traces` | `avales` / `hechos` / `trazas` |
| `dispositions`: `consent`/`object`/`abstain` | `posturas`: `consentir`/`objetar`/`abstenerse` |
| verdictos `adopted`/`revisit` | `adoptada`/`revisar` |
| `known_via_trust` / `no_info_from_your_position` | `conocido_via_confianza` / `sin_informacion_desde_tu_posicion` |
| excepciones `*BreachError` | `ErrorDeBrecha*` (p. ej. `ErrorDeBrechaMembrana`) |

**Nota crítica:** el renombrado `mode`→`sala` resuelve la colisión semántica con el nuevo `modo` de calibración. Claves de esquema sin tildes (`celula_id`, no `célula_id`) para robustez; los VALORES y mensajes sí llevan tildes correctas.

### B. Taxonomías bilingües + matching por tokens + normalización (correcciones de auditoría 1 y 2)

**Problema actual:** las taxonomías son solo-inglés y el matching es por substring, lo que (a) deja pasar `puntuacion`, `calificacion`, `reputacion`, `veto` y (b) rechaza falsos positivos como `banco_de_tiempo` (`'ban' in 'banco'`), `zona_urbana`, `underscore`.

**Solución a implementar (idéntica en las seis capas, fijada por el test AC-X):**
1. **Tokenización de claves:** dividir cada clave por límites no-alfanuméricos y camelCase (`bancoDeTiempo` → `banco`,`de`,`tiempo`), minusculizar, **normalizar acentos** (NFD, eliminar diacríticos: `puntuación`→`puntuacion`).
2. **Matching por token exacto** contra el conjunto prohibido (no substring). Incluir variantes morfológicas explícitas.
3. **`CLAVES_PROHIBIDAS` (vigilancia, las seis capas, byte-idénticas):**
   `score, puntuacion, puntaje, rating, calificacion, reputation, reputacion, rank, ranking, clasificacion, blacklist, lista_negra*, ban, veto, penalty, penalizacion, sancion, karma, global_id, dni, cedula, rif, pasaporte`
   (*para claves compuestas como `lista_negra`, el matching por tokens debe evaluar también bigramas de tokens adyacentes: `lista`+`negra`. Especifícalo y testéalo.*)
4. **`CLAVES_MERCADO` (Capa 1, bilingüe):** `price, precio, cost, costo, coste, fee, tarifa, cents, centavos, centimos, currency, moneda, divisa, valuation, valoracion, denominat, denominacion, pago, cobro, usd, ves, dolar, dolares, bolivar, bolivares`
5. **`CLAVES_LIBRO_RECIPROCIDAD` (Capa 1, bilingüe):** `debt, deuda, owed, debe, balance, saldo, credit, credito, reciprocity, reciprocidad, iou, favor_balance, saldo_de_favores`
6. **`CLAVES_PESO_VOTO` (Capa 6, bilingüe):** `weight, peso, shares, acciones, voting_power, poder_de_voto, vote_count, conteo, tally, recuento, majority, mayoria, percent, porcentaje, proxy, seats, escanos, quorum, cuota`
7. **`CLAVES_ENGAGEMENT` (Capa 3, bilingüe):** añadir `clic, retencion, viralidad, impresiones, notificacion, racha, seguidores, me_gusta`
8. **Sesgo documentado:** sobre-rechazar sigue siendo seguro **salvo** cuando colisiona con el dominio de ayuda mutua; el matching por tokens elimina las colisiones conocidas. Documenta en `failure-model.md` el análisis de falsos positivos/negativos residuales.

### C. Escaneo de valores — patrones de identidad (corrección de auditoría 3, decisión consciente)

El escaneo actual es solo-claves. Añade, en las seis capas, un **escaneo de VALORES string** por regex para patrones de documentos de identidad y contacto venezolanos, cuya presencia = forma de dossier → **rechazo**:
- Cédula: `[VE]-?\d{1,2}\.?\d{3}\.?\d{3}` (con y sin puntos/guion)
- RIF: `[JGVEP]-?\d{8}-?\d`
- Teléfono: `(\+58|0058|0)(4\d{2}|2\d{2})[\s.-]?\d{7}` (aprox.; documenta el patrón exacto)

**Límite honesto (flagged, not fake-resolved):** el juicio escalar en texto libre ("esta persona es un 3/10") queda FUERA del alcance de un firewall determinista. Decláralo en `failure-model.md` y en el README: la membrana detecta formas, no semántica; la semántica es gobernanza humana.

### D. Doble moneda: USD y VES sin conversión (Capa 4 + Capa 1)

1. Toda campaña de aseguramiento declara **`moneda: 'USD' | 'VES'`** (obligatoria).
2. Todos los importes en **enteros de unidad mínima**: `centavos` (USD) / `centimos` (VES). Prohibido float (ya es regla del repo; consérvala).
3. **Compromisos y bono del patrocinador DEBEN coincidir con la moneda de la campaña**; mezcla → `ErrorDeBrechaAseguramiento`. Sin excepciones.
4. **El tipo de cambio es irrepresentable dentro del motor:** añade a la taxonomía rechazada de Capa 4 los tokens/bigramas `tasa_de_cambio, tipo_de_cambio, exchange_rate, fx, paralelo, bcv`. Cláusula-porque en `constraints.md`: *en Venezuela la tasa (BCV vs. paralelo) es volátil y políticamente disputada; incrustar una tasa en código es incrustar una decisión política y crear un punto capturable; la conversión es siempre una decisión humana fuera del protocolo.*
5. **Convención documentada (no forzable por función pura):** se recomienda `expira_en` corto para campañas en VES por riesgo inflacionario; el motor no modela inflación (sería otra tasa). Flagged.
6. **Conservación exacta a escala de hiperinflación:** el reparto del bono debe conservar la suma exacta con importes VES de 15+ dígitos (los enteros de Python lo permiten; testéalo explícitamente).
7. Patrón de uso a documentar en el README (no requiere código): campañas patrocinadas por la diáspora en USD junto a campañas locales en VES — dos campañas paralelas, jamás una mixta.

### E. Los tres modos de calibración (`modo`, por célula)

Nuevo módulo **`src/modo/modo.py`** con: la tabla de límites, `validar_modo(request)` (aplicado por cada capa), `validar_transicion(actual, propuesto, decision_capa6=None)`, y `depurar(items, modo, ahora)`.

**El modo es POR CÉLULA** (policéntrico): viaja en el envelope de cada request (`modo` obligatorio junto a `celula_id`); cada capa valida sus límites contra la tabla. Ningún estado global.

**Tabla de límites por defecto** (parámetros de gobernanza, ajustables por decisión de Capa 6; documenta que son defaults, no dogma):

| Límite | `paz` | `catastrofe_acotada` | `catastrofe_severa` |
|---|---|---|---|
| Retención máx. (`expira_en` − `ahora`) | 365 días | 45 días | 7 días |
| Retención de trazas (Capa 5) | 90 días | 14 días | 72 horas |
| `max_hops` (Capa 2) | ≤ 4 | ≤ 3 | ≤ 2 |
| Portabilidad entre células (hechos/avales) | permitida con consentimiento explícito vía puente | solo hechos operativos/logísticos | prohibida (estrictamente celular) |
| Tamaño máx. de payload | 64 KB | 8 KB | **512 bytes** (transporte SMS/LoRa) |
| `max_proposals` (Capa 3) | ≤ 20 | ≤ 10 | ≤ 5 |
| `velocity_cap` mínimo exigido (Capa 5) | laxo | medio | estricto (documenta valores) |

Reglas:
1. Un request cuyo `expira_en`, `max_hops` o payload exceda el límite de su `modo` → **rechazado** (no recortado: rechazar, nunca reparar).
2. **`depurar(items, modo, ahora)`** — función pura: recibe items almacenados por el llamador y devuelve solo los que sobreviven a la ventana del modo (los que exceden se recortan a la ventana o se eliminan; especifica cuál y por qué). **Flagged:** una función pura no puede obligar al llamador a ejecutarla tras una escalada; es convención documentada + test + helper.
3. El tiempo sigue el modelo de cada capa (ISO-8601 lexicográfico; ticks enteros en Capa 5).

### F. Transiciones de modo: el trinquete asimétrico (usa la Capa 6 existente)

- **Escalada** (`paz`→`catastrofe_acotada`→`catastrofe_severa`, o salto directo a severa): **unilateral e inmediata** — cualquier token del círculo puede escalarla. Racional (documéntalo): en terremoto los segundos cuentan; el coste de una escalada falsa es solo menor riqueza de coordinación, el coste de una escalada tardía es que los datos se vuelven pasivo en plena crisis. La escalada obliga (por convención + test) a ejecutar `depurar()`.
- **Desescalada** (cualquier sentido hacia `paz`): **requiere una decisión `adoptada` de Capa 6** sobre una propuesta `cambiar_modo` — consentimiento, sin objeción primordial. `validar_transicion()` devuelve válido solo si (a) es escalada, o (b) es desescalada Y `decision_capa6.verdicto == 'adoptada'` para esa propuesta y ese círculo.
- **Flagged, not fake-resolved:** un miembro malicioso puede degradar la coordinación escalando repetidamente; la desescalada por consentimiento es el contrapeso; quién participa y por qué decide — el código fuerza el procedimiento, no la buena fe. Documenta el vector y el parámetro de fricción opcional (p. ej., cooldown) como decisión de gobernanza abierta.

### G. Perfil de convergencia en desastre (reutiliza Capa 5, no construyas capa nueva)

El problema de convergencia ("las motos obstaculizando la maquinaria") se modela **sobre la estigmergia existente**:
- Trazas con `sobre: 'zona:<id>'` y señales existentes (`presence`→`presencia`, `path`→`camino`, `flag`→`alerta`, `contribution`→`contribucion`, `endorsement`→`respaldo`).
- Añade UNA señal ambiental a la whitelist: **`paso_maquinaria`** (una zona señalada para paso de maquinaria pesada). Es señal sobre una ZONA (artefacto), jamás sobre una persona — verifica que no viola la regla de traza-ambiental.
- El `velocity_cap` de Capa 5 ES el amortiguador de estampida de voluntarios; en `catastrofe_severa` el cap mínimo exigido es estricto.
- Documenta el perfil con un ejemplo venezolano completo en el spec bundle (zonas de La Guaira/Caracas, ráfaga de `presencia`, throttling, `alerta` sin contexto amortiguada).

### H. Tests (traducir, conservar, extender)

1. **Traducir** toda la suite existente al castellano y al nuevo esquema; **los 293 equivalentes deben pasar**.
2. **Conservar AC-X** (cross-layer): las seis capas byte-idénticas en TODAS las taxonomías compartidas (ahora bilingües), y el escáner desciende en tuplas.
3. **Nuevos tests definitorios (mínimo):**
   - `AC-T1` — `banco_de_tiempo` **ADMITIDO** en sala `don_comunal` (regresión del falso positivo de la auditoría; el test que define el fix).
   - `AC-T2` — `puntuación` y `puntuacion` (con y sin tilde) rechazadas en las seis capas; ídem `cedula`/`cédula`, `rif`.
   - `AC-T3` — valor string `"V-12.345.678"` en cualquier payload → rechazado (escaneo de valores de identidad).
   - `AC-T4` — claves `zona_urbana`, `underscore`, `rango_de_fechas` admitidas (sin falsos positivos de substring).
   - `AC-D1` — campaña `USD` con compromiso `VES` → rechazada; `AC-D2` — conservación exacta del bono con céntimos VES de 15+ dígitos; `AC-D3` — clave `tasa_de_cambio` en Capa 4 → rechazada.
   - `AC-M1` — el mismo request válido en `paz` es rechazado en `catastrofe_severa` si excede retención/hops/payload.
   - `AC-M2` — escalada sin decisión: válida; desescalada sin decisión `adoptada`: **rechazada**.
   - `AC-M3` — `depurar()` tras escalada elimina/recorta determinísticamente todo lo que exceda la nueva ventana.
   - `AC-C1` — perfil de convergencia: ráfaga de `presencia` sobre `zona:X` → throttled por el cap del modo; `paso_maquinaria` representable; ninguna señal sobre persona representable.
4. Property-based (hypothesis) para: tokenización/normalización de acentos, conservación monetaria, y monotonía del trinquete.

### I. Documentación y método

1. **Specs antes que código.** Crea los sub-bundles `workflows/micorriza-politica-ve/` (o extiende el existente): actualiza `intent.md` (el objetivo real del fork: coordinación y ayuda mutua venezolana con calibración por hostilidad — cita la recalibración: represión selectiva, no vigilancia masiva; el enemigo estructural es la captura política y el punto único de fallo), `context.md` (doble moneda, diáspora, VenApp como anti-patrón, infraestructura frágil), `architecture.md` (el nuevo módulo `modo`, naturaleza `[DETERMINISTA]`), y por cada área tocada: `spec.md`, `constraints.md` con cláusulas-porque, `failure-model.md`, `evals/`.
2. README del fork en castellano: filosofía heredada, tabla de modos, tabla de renombrado, lista **"Señalado, no falsamente resuelto"** consolidada (Sybil; juicio escalar en texto libre; depuración como convención del llamador; escalada abusiva; transporte/malla fuera del alcance del núcleo puro; parámetros de modo como decisión de gobernanza).
3. Notas de procedencia por módulo, como hace el repo original.

---

## PROCESO (en este orden)

1. Lee TODO el código y el bundle existente antes de tocar nada. Verifica tu comprensión ejecutando la suite actual.
2. Escribe los specs del fork (área por área, con sus evals de aceptación).
3. Implementa en este orden: (a) tokenización/taxonomías bilingües + escaneo de valores [toca las 6 capas a la vez, con AC-X actualizado]; (b) castellanización completa; (c) módulo `modo` + integración de límites en cada capa; (d) trinquete + `validar_transicion` + `depurar`; (e) doble moneda en Capa 4 y taxonomía de mercado en Capa 1; (f) perfil de convergencia sobre Capa 5.
4. Tras cada área: suite completa en verde antes de la siguiente.
5. Cierra con el README y la lista de problemas abiertos.

## CRITERIOS DE ACEPTACIÓN GLOBALES

- Suite completa en verde (traducida + nuevos AC), determinista, offline, stdlib + pytest/hypothesis solamente.
- Ninguna capa importa de otra ni de red; el LLM sigue inyectado; todo puro.
- Los diez invariantes intocables verificables por test en los TRES modos.
- `git diff` legible por área; commits por área con mensaje en castellano explicando el porqué.
- Ningún problema abierto "resuelto" en prosa sin mecanismo: si no hay test que lo fije, va a la lista de señalados.

**Si en algún punto una instrucción de este prompt entra en conflicto con "LO INTOCABLE", gana LO INTOCABLE y documentas el conflicto en `audit.md` en lugar de resolverlo en silencio.**
