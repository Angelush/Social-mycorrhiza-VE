# Sub-bundle de especificación — `micorriza-politica-ve` (fork Venezuela)

> **Estado:** TA.1 — specs del fork. **Specs ANTES que código** (método spec-driven del repo).
> Este sub-bundle NO contiene código bajo `src/`; es el blueprint que las tareas TA.2–TA.8 del
> grafo (`workflows/micorriza-ve/tasks.md`) implementan, cada una con suite verde + commit + gate.

## Cómo leerlo

1. **`intent.md`** — el objetivo real recalibrado: represión *selectiva* (no vigilancia masiva),
   captura política y punto único de fallo como enemigo estructural.
2. **`context.md`** — data-room VE: doble moneda, diáspora, VenApp como anti-patrón, infraestructura
   frágil.
3. **`architecture.md`** — las seis capas (naturaleza conservada, nombres castellanos) + el nuevo
   módulo transversal `modo` `[DETERMINISTA]`.
4. **`lo-intocable.md`** — los diez invariantes en los tres modos + la lista consolidada
   **"Señalado, no falsamente resuelto"**. Contrato maestro: gana sobre cualquier área.
5. **Áreas** — una carpeta por unidad de construcción del grafo, cada una con
   `spec.md` · `constraints.md` (con cláusulas-porque) · `failure-model.md` · `evals/acceptance.md`.

## Mapa de áreas → tareas del grafo → §§ del prompt

| Carpeta | Tarea | Prompt | Contenido |
|---|---|---|---|
| `area-a-firewall-bilingue/` | TA.2 (área a) | §B + §C | tokenización, normalización NFD, matching token+bigrama, 5 taxonomías bilingües, escaneo de valores de identidad, auditoría de raíces |
| `area-b-castellanizacion/` | TA.3 (área b) | §A | tabla exhaustiva de renombrado; `mode`→`sala`; renombrado mecánico |
| `area-c-modo/` | TA.4 (área c) | §E | módulo `modo`, tabla de límites, `validar_modo`, `depurar` |
| `area-d-trinquete/` | TA.5 (área d) | §F | `validar_transicion` asimétrico, monotonía |
| `area-e-doble-moneda/` | TA.6 (área e) | §D | Capa 4 mono-moneda, FX irrepresentable, conservación a 15+ dígitos; taxonomía mercado Capa 1 |
| `area-f-convergencia/` | TA.7 (área f) | §G | perfil sobre Capa 5, `paso_maquinaria`, ejemplo La Guaira |

## Orden de construcción (del prompt §PROCESO y del grafo)

Maquinaria compartida primero y una sola vez: **área a (firewall)** y **área c (`modo`)**. Luego
área b (castellanización), área d (trinquete), área e (moneda), área f (convergencia). Tras cada
área: suite completa en verde antes de la siguiente.

## Convención de uso — doble moneda (área e, sin código)

Una campaña de aseguramiento es **mono-moneda**: declara `moneda: 'USD' | 'VES'` y todos sus
compromisos y su bono van en esa misma moneda (los importes, en enteros de unidad mínima —
centavos/céntimos). El motor **no convierte**: el tipo de cambio (BCV vs. paralelo) es irrepresentable
porque incrustar una tasa es incrustar una decisión política capturable.

**Patrón diáspora:** cuando la diáspora quiere patrocinar en USD junto a una acción local en VES, se
crean **dos campañas paralelas mono-moneda** (una USD, una VES), **jamás una campaña mixta**. La
comparación/conversión entre ambas es una decisión humana fuera del protocolo.

**Higiene inflacionaria (convención del llamador, no mecanismo):** para campañas VES conviene un
`expira_en` corto, porque el motor no modela inflación (sería otra tasa disputada). Señalado en
`lo-intocable.md`.

## Convención de uso — convergencia en desastre (área f, sin código)

El escenario: tras un **deslave en La Guaira / Caracas**, una ráfaga de voluntarios ("las motos
obstaculizando la maquinaria pesada") satura la coordinación de una zona. No hay capa nueva: se modela
sobre la **Capa 5** (estigmergia) existente y sus cortacircuitos.

- **Trazas sobre zonas, jamás sobre personas.** Una traza es `about: 'zona:la-guaira-01'` (artefacto).
  Ninguna señal *sobre una persona* (`about: 'persona:*'`) es representable — se rechaza. Una señal
  sobre persona sería un escalar/marca encubierta (invariantes 1/2).
- **`paso_maquinaria`** marca una zona reservada para paso de maquinaria pesada. Es señal ambiental de
  **zona**: solo válida sobre `zona:*`, y queda representable y visible. Nunca sobre una persona.
- **El cap de velocidad ES el amortiguador de estampida.** La ráfaga de `presencia` sobre una zona se
  throttlea por ventana. En `catastrofe_severa` el cap es **estricto** (cota ≤ 3 frente a ≤ 10 acotada
  y ≤ 50 paz, fuente única en `modo`): no se puede pedir un cap más laxo que el del modo. El mecanismo
  **nunca se apaga**; solo varían sus parámetros (invariante 8).
- **Contexto antes que juicio.** Una `bandera` (alerta) *sin contexto* se amortigua hasta que porte
  contexto — una alerta desnuda es el germen de una cascada de pánico o de una marca informal.
- **Alcance celular / cero-broadcast.** Una traza no sale de su célula.

La calibración concreta del cap no está validada en un desastre real (`failure-model.md`); el test
verifica el *mecanismo* (throttling, no-persona, amortiguación de alerta), no el número óptimo.

## Gate de esta tarea (TA.1)

- Sub-bundle completo, área por área, con cláusulas-porque en cada `constraints.md`.
- Los diez invariantes de `lo-intocable.md` verificables por test en los TRES modos.
- **Aprobación humana (M1) antes de escribir cualquier código de TA.2.**
