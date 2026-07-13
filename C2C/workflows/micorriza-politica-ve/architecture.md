# Architecture — clasificación de especies + el nuevo módulo `modo`

> Hereda `../micorriza-politica/architecture.md`. Las seis capas conservan su naturaleza y su
> especie; el fork añade **un módulo transversal** (`modo`) y **endurece** la naturaleza del
> firewall compartido. Ninguna capa nueva se construye (invariante de reutilización).

## Diagnóstico (sin cambios de fondo)

- Ruta: **Deep.** El sistema sigue siendo multi-especie con especie dominante **HUMANA**.
- El cuello de botella sigue siendo **relación + claridad**, no ejecución. El fork sube las
  apuestas: el modo de fallo aquí no es solo una "jaula de vigilancia" sino la **captura política
  de una red bajo represión selectiva** (ver `intent.md`).

## Las seis capas (naturaleza conservada, nombres castellanizados)

| Capa | Módulo VE | Naturaleza | LLM | Cambio del fork |
|---|---|---|---|---|
| 0 — La célula / círculo | (humano) | `[HUMANO · LOCAL]` | no | El `modo` es **por célula** |
| 1 — Partición por sala relacional | `membrana.py` / `admitir()` | `[INVARIANTE ARQUITECTÓNICA]` | no | `mode`→`sala`; taxonomía de mercado bilingüe; valida `modo` del envelope |
| 2 — Legibilidad de la confianza | `legibilidad.py` / `consultar()` | `[EL FILO DE LA NAVAJA]` | no | `asker`→`consultante`; `max_hops` por modo |
| 3 — Emparejador (afordancia) | `emparejador.py` / `emparejar()` | `[ESTOCÁSTICO · LLM]` | **sí (inyectado)** | taxonomía engagement bilingüe; `max_proposals` por modo |
| 4 — Quórum / aseguramiento | `aseguramiento.py` | `[DETERMINISTA]` | no | doble moneda mono-moneda; FX irrepresentable |
| 5 — Estigmergia + cortacircuitos | `estigmergia.py` / `sentir()` | `[PROTOCOLO + CIRCUIT BREAKERS]` | no | señal `paso_maquinaria`; `velocity_cap` por modo; retención por modo |
| 6 — Gobernanza sociocrática | `gobernanza.py` / `decidir()` | `[HUMANO → CONSENT-NOT-CONSENSUS]` | no | resuelve la propuesta `cambiar_modo` (desescalada) |
| 7 — Sustrato simbólico | (humano) | `[HUMANO · PLURAL]` | no | — |

Todas reutilizan la **taxonomía de claves prohibidas compartida** (ahora bilingüe, byte-idéntica
en las seis — fijado por AC-X). Ninguna importa de otra ni de red; el LLM sigue inyectado.

## El nuevo módulo: `src/modo/modo.py` — `[DETERMINISTA]`

**No es una capa.** Es un módulo transversal, puro y sin estado, que las seis capas consultan.
Su razón de ser: la calibración por hostilidad es *ortogonal* a la lógica de cada capa, así que
vive en un solo sitio y se construye **una vez, con el tier más alto** (es maquinaria compartida,
M5 del grafo de tareas). Superficie:

| Función | Firma | Naturaleza |
|---|---|---|
| tabla de límites | constante | por defecto ajustable por Capa 6 (defaults, no dogma) |
| `validar_modo(request)` | request → válido \| `raise` | aplicada por cada capa; rechaza-no-recorta |
| `validar_transicion(actual, propuesto, decision_capa6=None)` | → bool | trinquete asimétrico (ver `area-d-trinquete/`) |
| `depurar(items, modo, ahora)` | → items | función pura determinista; convención del llamador |

**El modo viaja en el envelope** de cada request (`modo` obligatorio junto a `celula_id`). No hay
estado global de modo: es policéntrico por construcción. Cada capa valida sus propios límites
contra la tabla; un exceso de `expira_en`/`max_hops`/payload → **rechazo** (nunca recorte).

## La puerta anti-vigilancia (endurecida)

El peligro primario sigue siendo **la forma correcta en el sitio equivocado**: un escalar global
de persona, una lista negra, una vista de dios. El fork añade una segunda superficie de la misma
puerta: el **escaneo de valores** (patrones de identidad venezolanos) porque un valor string con
forma de cédula/RIF/teléfono es una forma de dossier aunque su clave sea inocente. Ver
`area-a-firewall-bilingue/`.

## El harness de construcción (cómo lo construimos NOSOTROS)

Especie 1b — Coding Harness (Project). Humano gestor, juicio como gate. Tareas a nivel de área,
revisor un escalón por encima del ejecutor, planificador→trabajador de dos niveles. El grafo de
tareas (`intent.md` del bundle raíz + `tasks.md`) cierra CADA nodo con suite verde + commit; los
nodos `alto` llevan además revisión humana del sub-bundle (M1). **La maquinaria compartida (el
firewall bilingüe y el módulo `modo`) se construye primero y una sola vez.**
