# Workflow: micorriza-ve — hoja de ruta del fork Venezuela

> Un **paquete de especificación** (spec bundle). El activo durable es el *hábito* — tarea +
> contexto + patrón de interacción + gate de revisión — no un prompt suelto. Clónalo,
> re-córrelo, compártelo.

## La tarea

Convertir los dos documentos fundacionales del fork —
[`C2C/prompt-fork-venezuela.md`](../../C2C/prompt-fork-venezuela.md) (protocolo social en
castellano, doble moneda, tres modos de calibración) y
[`B2B/micorriza-b2b-venezuela-adaptacion.md`](../../B2B/micorriza-b2b-venezuela-adaptacion.md)
(crédito mutuo re-anclado a la realidad venezolana) — en un plan de construcción ejecutable
por fases, sin ceder ninguno de los invariantes heredados: cero tokens, cero escalares de
persona, FX irrepresentable, el humano dispone.

## Cómo correrlo

1. Carga `context.md` (el cuarto de datos: fuentes, conflictos resueltos, huecos declarados,
   qué es VOLÁTIL y caduca).
2. Toma el siguiente nodo de `tasks.md` (las deps mandan; Fase 0 ya está hecha).
3. El prompt de producción del nodo ES el documento fundacional en su sección ancla
   (spec.md la nombra), leído junto a `constraints.md`.
4. Gate: suite completa verde con salida pytest citada + los AC del área
   (`evals/acceptance.md`) + commit en castellano con su porqué.
5. Re-corre `evals/golden-set/casos.json` ante cualquier cambio de taxonomía o de modelo.

## El patrón de interacción (lo que de verdad transfiere)

Las tres correcciones que este fork repite hasta que duelan:

1. **"¿Esto es universal o era contexto europeo?"** — la pregunta del anexo §1. Antes de
   conservar o cambiar cualquier decisión heredada, clasificarla.
2. **"Esto no puede volverse un score"** — heredada intacta: al primer olor de escalar por
   persona, lista negra o señal de engagement, parar y rediseñar la FORMA.
3. **"Señalado, no falsamente resuelto"** — lo que no tiene mecanismo va a la lista con su
   porqué; prosa que "resuelve" = defecto.

## El gate de revisión

Humano + máquina, un nivel por encima del ejecutor. Las dos cosas con más probabilidad de
estar mal: (1) la **forma anti-vigilancia** rota por la migración bilingüe — un stem sin
expandir (M6) o una colisión de dominio sin regresión (AC-2/AC-3); (2) **dinero** — una
conversión implícita USD/VES/USDT o una conservación rota por resto mal repartido (AC-4).

## Estado del build

- [x] Fase 0 — fundación del fork (repo propio, árboles B2B/Sim reparados, 542 tests verdes,
      publicado)
- [ ] Fase 1 — C2C-VE (áreas a→f del prompt, TA.0–TA.8)
- [ ] Fase 2 — B2B-VE (deltas 1–10, TB.0–TB.9; requiere E2 resuelta)
- [ ] Fase 3 — Sim-VE (adaptadores + oráculos nuevos + control negativo, TS.1–TS.4)
- [ ] Continuas — verificaciones fechadas, sync upstream, meta-docs (TP.1–TP.4)

## Qué hay en este bundle

| Archivo | Qué es |
|---|---|
| `intent.md` | el objetivo real, la auditoría de marco y el contrato de corrección |
| `context.md` | cuarto de datos: fuentes, conflictos (C1–C5), huecos, estabilidad, terminología |
| `architecture.md` | naturaleza de cada componente + el harness de construcción de dos niveles |
| `spec.md` | el contrato que une los dos documentos fundacionales: fases, capa de significado, semántica de operaciones |
| `constraints.md` | M/N/P/E con porqués + matriz por modo + rechazos codificados (R1–R3) |
| `tasks.md` | el grafo de tareas por fases con gates, tiers y presupuesto de fiabilidad |
| `evals/` | criterios de aceptación (AC-1..10), suite A/B/C, golden set canónico |
| `failure-model.md` | fallos previstos (F1–F6) + hallazgos adversariales (ST1–ST10) |
| `simulation.md` | tres líneas de tiempo con sus pivotes + protocolo de recuperación |
| `audit.md` | prueba de que cada hallazgo es un requisito exigible — cero GAP |
| `.specsmith.json` | procedencia |
