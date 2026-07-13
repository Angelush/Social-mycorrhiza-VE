# Arquitectura — especies y harness de construcción (micorriza-ve)

## El sistema en runtime (heredado; el fork NO añade agentes)

Clasificación por componente — hereda la del bundle C2C upstream; lo nuevo en negrita:

| Componente | Naturaleza | Nota VE |
|---|---|---|
| Solver de clearing B2B | `[DETERMINISTA]` — propone | Intocable; off-chain; jamás LLM ni contrato en la ruta de liquidación (N5) |
| Ledger de crédito mutuo | `[DETERMINISTA]` + puerta humana — dispone | Las ops nuevas (`salida_con_saldo`, `puente.pausar`, `anclar`) entran por la MISMA puerta de ratificación (M8) |
| Capas C2C 1–6 | `[DETERMINISTA]` puras, estado del llamador | Renombradas al castellano; límites por modo validados en el envelope (M10) |
| Emparejador Capa 3 | `[LLM ENCAJONADO]` inyectado | Sigue encajonado; su orden se descarta con sort canónico; señales de engagement irrepresentables |
| **Módulo `modo` (nuevo)** | **`[DETERMINISTA]` puro** | Tabla de límites + `validar_modo` + `validar_transicion` + `depurar`; por célula, sin estado global |
| Puente USDT / rieles | `[HUMANO]` — integración del llamador | El motor solo registra la obligación saldada; spreads y conversiones son decisión humana (N3) |
| Fondo multisig | `[HUMANO]` — gobernanza + helpers | El motor verifica direcciones/umbral; jamás custodia (N9) |
| Sim-VE (Fase 3) | `[AUTO-INVESTIGACIÓN acotada]` | El investigador jamás parchea el SUT (N11); Track-B descriptivo, sin escalar por persona |

## El harness de construcción (cómo SE CONSTRUYE esto)

**Especie 1b — harness de proyecto, dos niveles.** Planificador (el humano + la sesión que
enruta por fases de `tasks.md`) → ejecutores (una sesión por área/delta, con contexto mínimo:
su sub-bundle + la capa tocada) → juez (gates AC de `evals/` + revisión un nivel por encima
del ejecutor). Nunca tres o más capas de gestión; nunca enjambre plano.

## Puerta de piso de complejidad (el freno)

- El grueso del trabajo (castellanización, taxonomías) es transformación **mecánica**
  verificable por suite: peldaño bajo — una sesión por área con tabla previa (M7) y gate
  binario (M2). No amerita multi-agente.
- Lo **invariante-denso** (áreas c/d/e del prompt; deltas 2/3/6/8; oráculos de Sim-VE) exige
  el tier de modelo más alto + aprobación humana del sub-bundle ANTES del código (M1).
- El 10×: reutilizar 542 tests heredados y los bundles upstream ES la ventaja. No se
  reimplementa nada que el upstream ya pruebe; el fork solo toca lo que cambia de signo.

## Superficie de control humana

- **Observar:** salida pytest por gate (M2); diff legible por área (M11).
- **Aprobar:** sub-bundle de specs por área (M1); decisiones E1–E5.
- **Frenar:** conflicto con un intocable → parada dura y `audit.md` (E1); cambio regulatorio
  material → pausar la fase afectada (E3).

## Modos de ejecución de constraints

Tres modos, matriz completa en `constraints.md`: **Construcción** (Enforce), **Sim-VE
investigación** (oráculos Enforce — una violación para la campaña; métricas Measure-only),
**Docs** (n/a). El modo se fija al iniciar cada tarea, nunca a mitad de ejecución.
