# C2C-VE — Micorriza social, fork Venezuela (workstream A)

> Árbol de trabajo del fork venezolano del protocolo **C2C** (`Comunidad-a-Comunidad`). El código
> upstream vive intacto en `../C2C/` como referencia; **todo el código del fork vive aquí**, en
> `C2C-VE/`. Las especificaciones (el *porqué* de cada decisión) viven en el sub-bundle
> `../C2C/workflows/micorriza-politica-ve/`; este README consolida, no reemplaza.

El protocolo original construye **infraestructura para que una sociedad alfabetizada se organice a
través de sus diferencias** — fertilidad, no eficiencia; jardinero, no ingeniero. El fork conserva
ese marco intacto y le añade **una calibración por grado de hostilidad del entorno**: coordinación
y ayuda mutua venezolana bajo represión.

**La recalibración del enemigo** (define todo lo demás): el ancla negativa del protocolo original
es el crédito social chino — vigilancia masiva con puntuación nacional. El enemigo estructural en
Venezuela **no es el mismo**: es la **represión *selectiva*** (un dossier sobre *un* organizador,
no un panóptico de 30 millones), la **captura política de la coordinación** (VenApp como
anti-patrón vivo), y el **punto único de fallo**. Sin tenedor central no hay trono que capturar
(invariante 5) — en represión selectiva eso deja de ser elegancia y pasa a ser supervivencia
operativa. Ver `../C2C/workflows/micorriza-politica-ve/intent.md`.

---

## Filosofía heredada — las seis capas

El pipeline conserva la naturaleza upstream (nombres castellanizados en Área b) y su orden fijo.
Cada capa es una función pura, sin estado global; nada se persiste (invariante 5). El patrón:

```
membrana → legibilidad → emparejador → aseguramiento → estigmergia → gobernanza
```

| # | Capa | Módulo (`src/…`) | Naturaleza (heredada) |
|---|---|---|---|
| 1 | **membrana** | `partition/membrana.py` | Firewall de *forma* en la frontera: rechaza escalares de persona, listas negra, patrones de identidad. No juzga semántica. |
| 2 | **legibilidad** | `legibility/legibilidad.py` | `consultante` obligatorio; el grafo es suministrado, *hop-bounded* y se descarta; la salida son caminos y hechos, **jamás un número** (invariante 3). |
| 3 | **emparejador** | `matcher/emparejador.py`, `matcher/emparejador_claude.py` | El LLM va inyectado, encajonado; su orden se descarta con *sort* canónico (invariante 6). Ninguna señal de *engagement* representable (invariante 7). |
| 4 | **aseguramiento** | `assurance/aseguramiento.py` | Campañas de compromiso; conservación exacta a escala de hiperinflación; **doble moneda sin conversión** (fork, Área e). |
| 5 | **estigmergia** | `stigmergy/estigmergia.py` | Señales *ambientales* sobre zonas y artefactos, nunca sobre personas; cortacircuitos anti-cascada; **convergencia en desastre** (fork, Área f). |
| 6 | **gobernanza** | `governance/gobernanza.py` | Un token, una voz; la ponderación por reputación no se puede ni escribir (invariante 4). El humano dispone (invariante 6). |

Transversal a las seis (fork VE, no upstream): **`modo/modo.py`** — la calibración por hostilidad.
Es una **hoja** del grafo de dependencias: las capas importan `modo`; `modo` no importa ninguna
capa (sin ciclos).

### Los diez invariantes (irrepresentables en los tres modos)

Contrato maestro completo en `lo-intocable.md`. **Ningún modo toca ninguno de estos.**

1. Ningún **escalar global de la persona** (score/reputación numérica): rechazado en entrada,
   inconstruible en salida, en las seis capas.
2. Ninguna **lista negra / veto / sanción** representable. Una ausencia es "sin información desde
   tu posición", nunca una marca.
3. **Vista de dios irrepresentable**: `consultante` obligatorio; salida = caminos y hechos.
4. **Voz independiente de la reputación**: un token, una voz; peso de voto no escribible.
5. **Sin tenedor central**: funciones puras, nada persistido, ningún trono que capturar.
6. **El agente propone, el humano dispone**: el LLM va inyectado, encajonado, su orden descartado.
7. **Ninguna señal de engagement** representable en el emparejador.
8. **Cortacircuitos anti-cascada** activos en toda propagación. *Los parámetros varían por modo;
   el mecanismo nunca se apaga.*
9. **Salida siempre disponible**: participación opt-in; el fork mismo prueba el derecho a bifurcar.
10. **Sin integración con canales estatales de identidad o denuncia** (VenApp o equivalente):
    constraint duro — el riesgo es la captura política de la coordinación, no solo la vigilancia.

Los diez son **verificables por test en los tres modos** (una forma prohibida rechaza idénticamente
en `paz`, `catastrofe_acotada` y `catastrofe_severa`).

---

## Los tres modos — calibración por hostilidad

`modo` viaja en el envelope de cada request (policéntrico, **por célula** — jamás estado global).
Un request que excede el límite de su modo se **rechaza** (`raise`), nunca se recorta. Lo que los
modos calibran, y **nada más**: retención, alcance (`max_hops`), tamaño de payload, y parámetros de
los cortacircuitos (velocidad, propuestas). Ningún modo toca un invariante.

> **Fuente única de los límites: [`src/modo/modo.py`](src/modo/modo.py)** (`LIMITES`,
> `TOPE_VELOCIDAD_MAX`). La tabla siguiente es una **instantánea al corte de TA.8** para lectura;
> el código manda. El *failure-model* prohíbe copiar esta tabla dentro de las capas — la consultan,
> no la re-teclean — precisamente para que no diverja.

| Dimensión (`LIMITES[…]`) | `paz` | `catastrofe_acotada` | `catastrofe_severa` |
|---|---|---|---|
| `retencion_max_dias` | 365 | 45 | 7 |
| `retencion_trazas_dias` | 90 | 14 | 3 (72 h) |
| `max_hops` | 4 | 3 | 2 |
| `max_payload_bytes` | 65 536 | 8 192 | 512 (SMS/LoRa) |
| `max_proposals` | 20 | 10 | 5 |
| `estrictez_velocidad` (ordinal) | 1 (laxo) | 2 (medio) | 3 (estricto) |
| `tope_velocidad_max` | 50 | 10 | 3 |

La transición entre modos es un **trinquete asimétrico** (Área d): la **escalada** (a mayor
hostilidad) es **unilateral e inmediata** — cualquier token la dispara; la **desescalada** exige una
decisión `adoptada` de Capa 6 sobre la propuesta `cambiar_modo` de *ese* círculo. Re-expandir
retención/alcance/payload es riesgo colectivo, no de un individuo. El código fuerza el
*procedimiento* del trinquete; jamás la buena fe ni el juicio de la crisis.

---

## Tres cláusulas que añade el fork

- **Moneda sin conversión** (Área e, Capa 4/1). Toda campaña declara `moneda: 'USD' | 'VES'` y
  **nunca** las mezcla; el tipo de cambio (BCV vs. paralelo) es *irrepresentable* dentro del motor —
  incrustar una tasa es incrustar una decisión política capturable. La diáspora que patrocina en USD
  junto a una acción local en VES crea **dos campañas paralelas mono-moneda**, jamás una mixta. La
  conservación exacta se mantiene a escala de hiperinflación (enteros de 15+ dígitos).
- **Calibración por modo** (Áreas c/d). Los tres modos por célula; el trinquete asimétrico. Alcance,
  no forma: ningún modo toca un invariante.
- **Firewall bilingüe con escaneo de valores** (Área a, las 6 capas a la vez). El firewall tokeniza
  y normaliza acentos (NFD), matchea por **token exacto** (no substring) y por **bigramas**, es
  bilingüe en las cinco taxonomías, y escanea **valores** por patrones de identidad venezolanos
  (cédula/RIF/teléfono) porque su presencia = forma de dossier. El bloque compartido es
  **byte-idéntico en las 6 capas** — md5 `5d693ecf1833fb760e173ee3db30a263` (span: bloque
  `BEGIN…END` completo, incluido su `\n` final = 3023 bytes) —, duplicado *a propósito* — no se factoriza para
  que ninguna capa pueda ser degradada en aislamiento.

### Convergencia en desastre (Área f, sobre Capa 5, sin capa nueva)

Tras un **deslave en La Guaira / Caracas**, una ráfaga de voluntarios ("las motos obstaculizando la
maquinaria pesada") satura la coordinación de una zona. Se modela sobre la estigmergia existente:

- **Trazas sobre zonas, jamás sobre personas.** `about: 'zona:la-guaira-01'` sí; `about: 'persona:*'`
  se **rechaza** (sería un escalar/marca encubierta — invariantes 1/2).
- **`paso_maquinaria`** marca una zona reservada para paso de maquinaria pesada: señal ambiental de
  **zona**, solo válida sobre `zona:*`, nunca sobre una persona.
- **El cap de velocidad ES el amortiguador de estampida.** En `catastrofe_severa` el cap es
  **estricto** (≤ 3, fuente única en `modo`): no se puede pedir un cap más laxo que el del modo. El
  mecanismo **nunca se apaga**; solo varían sus parámetros (invariante 8).
- **Contexto antes que juicio.** Una `bandera` (alerta) sin contexto se amortigua hasta que porte
  contexto — una alerta desnuda es el germen de una cascada de pánico o una marca informal.

---

## Tabla de renombrado (procedencia inglés → castellano)

Tabla exhaustiva (M7) en
[`area-b-castellanizacion/rename-table.md`](../C2C/workflows/micorriza-politica-ve/area-b-castellanizacion/rename-table.md).
Resumen: los **archivos `.py`** se castellanizaron; los **directorios de paquete NO** (acota el
radio del cambio: no son clave de esquema/valor/verdicto).

| Concepto | Antes (upstream) | Después (fork) |
|---|---|---|
| Capa 1 | `partition/membrane.py` | `partition/membrana.py` |
| Capa 2 | `legibility/legibility_query.py` | `legibility/legibilidad.py` |
| Capa 3 | `matcher/matcher.py`, `matcher/claude_matcher.py` | `matcher/emparejador.py`, `matcher/emparejador_claude.py` |
| Capa 4 | `assurance/assurance_engine.py` | `assurance/aseguramiento.py` |
| Capa 5 | `stigmergy/stigmergy.py` | `stigmergy/estigmergia.py` |
| Capa 6 | `governance/governance.py` | `governance/gobernanza.py` |
| Clave de dominio | `mode` | `sala` |
| Clave de dominio | `token` | `ficha` |
| Excepciones de brecha | `*BreachError` | `ErrorDeBrecha*` |

> **Nota de colisión deliberada:** `mode`→`sala` (la clave de dominio "sala/espacio") es distinta de
> `modo` (el módulo de calibración por hostilidad del fork). No confundir: `sala` es un espacio de
> intercambio; `modo` es `paz | catastrofe_acotada | catastrofe_severa`.

**Convenciones de excepción fijadas** (no derivables de la tabla): cada capa re-lanza como su propio
`ErrorDeBrecha*`; **Capa 4 conserva `ValueError`** para la validación de entrada (deliberadamente
distinto del abort interno). En `modo.py`, `ErrorDeModo`. Cuidado con dos excepciones cercanas de
aseguramiento: `ErrorDeBrechaAseguramiento` **es** `ValueError` (rechazo de sobre); mientras que
`ErrorDeInvarianteAseguramiento` **no** lo es (abort interno).

---

## Procedencia por módulo (upstream vs. fork VE)

| Módulo | Origen | Qué es del fork |
|---|---|---|
| `partition/membrana.py` | upstream + Área a/b | firewall bilingüe (tokenización, NFD, bigramas, escaneo de identidad); taxonomía de mercado con `usd/ves/dolar/bolivar`; integración `modo`. |
| `legibility/legibilidad.py` | upstream + Área b | castellanización; integración `modo`. |
| `matcher/emparejador*.py` | upstream + Área b | castellanización; integración `modo`. `emparejador_claude.py` conserva keywords JSON-schema/API en inglés (contrato externo). |
| `assurance/aseguramiento.py` | upstream + Área e | doble moneda mono-moneda (`MONEDAS`, `bono_moneda`); taxonomía privada `TASA_KEYS` (FX irrepresentable); conservación 15+ dígitos. |
| `stigmergy/estigmergia.py` | upstream + Área f | `paso_maquinaria` (señal de zona); rechazo de trazas `persona:*`; cap severo estricto vía `modo`. |
| `governance/gobernanza.py` | upstream + Área b | castellanización; devuelve `veredicto` (`adoptada`/`revisar`), consumido por el trinquete. |
| **`modo/modo.py`** | **100% fork VE** | módulo nuevo: `LIMITES`, `validar_modo`, `validar_transicion` (trinquete), `depurar`, `tras_escalada`. Puro, hoja del grafo. |

> Las taxonomías **de dominio** (moneda, FX, señales de zona) viven en taxonomías **privadas de cada
> capa**, fuera del bloque compartido del firewall — por eso el md5 `5d693ec…` sigue intacto en las 6
> y `test_cross_layer_taxonomy` no se toca.

---

## Señalado, no falsamente resuelto (lista consolidada)

Lo que el código **no** puede resolver se declara aquí abiertamente; ninguno se "resuelve" en prosa
sin mecanismo. Si no hay test que lo fije, vive en esta lista (contrato maestro: `lo-intocable.md`).

- **Sybil / person-binding.** Un token, una voz; ligar token↔persona está **fuera de alcance**
  (heredado). El motor cuenta tokens distintos, no personas.
- **Juicio escalar en texto libre.** "Esta persona es un 3/10" en prosa: la membrana detecta
  **formas** (claves, patrones de valor), no **semántica**. La semántica es gobernanza humana.
- **`depurar()` como convención del llamador.** Una función pura no puede obligar al llamador a
  ejecutarla tras una escalada; es convención documentada + test + helper (`tras_escalada`), **no
  garantía**.
- **Escalada abusiva del modo.** Un miembro malicioso puede degradar la coordinación escalando en
  bucle; la desescalada por consentimiento (Capa 6) es el contrapeso; el cooldown/fricción es una
  decisión de gobernanza abierta, **no** un mecanismo impuesto.
- **Transporte / malla fuera del núcleo.** SMS/LoRa en `catastrofe_severa` es el motivo del límite
  de 512 bytes, pero el transporte en sí **no lo modela** el núcleo puro.
- **Parámetros de modo como decisión de gobernanza.** La tabla de `LIMITES` son *defaults*
  ajustables por Capa 6, **no dogma incrustado**; y no están validados en un desastre real.
- **Mandatoriedad de `modo` como postura de despliegue.** El motor engancha `modo` solo si viene en
  el envelope (`if 'modo' in env`); exigirlo *siempre* es una decisión de despliegue, no del motor.
- **Inflación no modelada.** El motor no modela inflación (sería otra tasa disputada); `expira_en`
  corto en VES es **convención documentada** del llamador, no mecanismo.
- **Correlación entre salidas.** Una función pura olvida por diseño; correlacionar salidas
  almacenadas es preocupación de gobernanza/almacenamiento (rotación de tokens, `expira_en`), no algo
  que la función pueda cerrar.
- **Homoglifos de otros alfabetos.** El firewall normaliza diacríticos latinos (NFD) pero **no**
  homoglifos cirílicos/griegos. Señalado; sin mitigación determinista.

---

## Correr la suite

Desde `C2C-VE/` (venv con `pytest` + `hypothesis`, gitignored en la raíz):

```bash
cd C2C-VE && ../.venv-ve/bin/python -m pytest -q
```

**Property tests (hypothesis)** que fijan los invariantes globales del fork, además de las
propiedades heredadas por capa (`test_*_properties.py`):

| Test | Fija |
|---|---|
| `test_area_c_modo.py` (PB-c*) | `validar_modo` rechaza-no-recorta; monotonía de `LIMITES` y `TOPE_VELOCIDAD_MAX` (severa ≤ acotada ≤ paz). |
| `test_area_d_trinquete.py` (PB-d1) | monotonía del trinquete (escalada unilateral / desescalada solo consentida); `depurar` idempotente. |
| `test_area_e_doble_moneda.py` (PB-e1) | conservación exacta del bono patrocinador en reembolso, a alta precisión. |
| `test_area_f_convergencia.py` (PB-f1) | señales sentidas acotadas por el cap del modo para cualquier ráfaga; ninguna traza `persona:*` pasa. |

## Estado

**Fase 1 (C2C-VE) — cerrada en TA.8.** Grafo de tareas y presupuesto de fiabilidad en
`../workflows/micorriza-ve/tasks.md`. Fases 2 (B2B-VE) y 3 (Sim-VE) parten de aquí (`TS.1` importa
estos contratos; el SUT real jamás se reimplementa).
</content>
</invoke>
