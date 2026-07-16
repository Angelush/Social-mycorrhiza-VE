# Hoja de ruta — grafo de tareas (micorriza-ve)

> Cada nodo: atómico (una sesión de agente con gate humano), con entradas/salidas definidas y
> verificación independiente (máquina donde se pueda). "Fase" = construcción de software; las
> "Etapas" del anexo §7 son despliegue de la red real y NO viven en este grafo (C2).
>
> **Cómo leerlo:** ejecutar en orden de fase; dentro de una fase, las dependencias mandan.
> Tier = capacidad mínima del ejecutor: `alto` (modelo tope + revisión humana del sub-bundle),
> `medio` (transformación mecánica con gate), `humano` (decisión que el código no toma).

## Fase 0 — Fundación del fork ✅ (hecha en la sesión del 2026-07-13)

| ID | Tarea | Verificación | Estado |
|---|---|---|---|
| T0.1 | Fork como repo propio FUERA del árbol upstream, historia completa, remotos `origin` (fork) + `upstream` | `git remote -v`; historia sobre `76519ab` | ✅ |
| T0.2 | Vendorizar `B2B/` y `Sim/` como árboles regulares (upstream los publicó como gitlinks rotos: un clon recibía solo C2C) | `git ls-files B2B/ Sim/` > 0; commit `3a22f51` | ✅ |
| T0.3 | Reconciliar el pin de procedencia con la topología monorepo (R1/N12) | Sim 121/121; commit `a50f7d2` | ✅ |
| T0.4 | Documentos fundacionales en su sitio (`C2C/prompt-fork-venezuela.md`, `B2B/micorriza-b2b-venezuela-adaptacion.md`) | commit `c39955c` | ✅ |
| T0.5 | Este bundle (`workflows/micorriza-ve/`) — la hoja de ruta | presente | ✅ |
| T0.6 | README raíz del fork en castellano | presente | ✅ |
| T0.7 | Publicación en GitHub (`Angelush/Social-mycorrhiza-VE`) | `git push` exitoso; repo visible | ✅ |
| T0.8 | Piso de regresión: B2B 128 · C2C 293 · Sim 121, todas verdes en el fork | salidas pytest en los mensajes de commit | ✅ |

## Fase 1 — C2C-VE (workstream A; prompt §A–§I en el orden §PROCESO)

| ID | Tarea | Entrada | Salida | Deps | Tier | Verificación |
|---|---|---|---|---|---|---|
| TA.0 | Leer TODO el código y bundle C2C; correr la suite como gate de comprensión | `C2C/` | nada (gate) | — | medio | 293 verdes reproducidos |
| TA.1 | Sub-bundle de specs del fork C2C (`C2C/workflows/micorriza-politica-ve/`): intent/context/architecture actualizados + spec/constraints/failure-model/evals POR ÁREA, con cláusulas-porque | prompt §A–§I + este bundle | sub-bundle aprobado | TA.0 | alto + humano | M1: aprobación humana antes de código |
| TA.2 | **Área a** — tokenización (límites no-alfanum + camelCase), normalización NFD, matching token-exacto + bigramas, 5 taxonomías bilingües, escaneo de valores de identidad (cédula/RIF/teléfono; fijar patrón exacto). Incluye **auditoría de expansión de raíces** (M6: `denominat`, `_cents`, …). Las 6 capas A LA VEZ; AC-X actualizado | TA.1 specs área a | 6 capas con firewall bilingüe | TA.1 | **alto** | AC-2, AC-3, AC-X; goldens `casos.json`; suite verde |
| TA.3 | **Área b** — castellanización completa: tabla exhaustiva PRIMERO (M7), luego renombrado mecánico (módulos, funciones, claves, enums, mensajes, verdictos, excepciones `ErrorDeBrecha*`), tests traducidos | TA.2 | árbol C2C-VE castellano | TA.2 | medio | 293 equivalentes verdes; `mode`→`sala` sin residuos (grep) |
| TA.4 | **Área c** — módulo `modo` (`src/modo/modo.py`): tabla de límites, `validar_modo` por capa vía envelope, rechazar-no-recortar; proponer valores de `velocity_cap` (hueco declarado) | TA.3 | módulo + integración 6 capas | TA.3 | **alto** | AC-5 (parte M1); suite verde |
| TA.5 | **Área d** — trinquete asimétrico: `validar_transicion` (escalada unilateral / desescalada solo `adoptada` Capa 6) + `depurar()` pura determinista | TA.4 | trinquete testeado | TA.4 | **alto** | AC-5 completo; monotonía (hypothesis) |
| TA.6 | **Área e** — doble moneda Capa 4 (mono-moneda, mezcla → `ErrorDeBrechaAseguramiento`) + taxonomía mercado Capa 1; conservación exacta 15+ dígitos (hypothesis) | TA.5 | Capa 4/1 VE | TA.5 | **alto** | AC-4; suite verde |
| TA.7 | **Área f** — perfil de convergencia sobre Capa 5: `paso_maquinaria` (señal de ZONA), ejemplo venezolano completo en el sub-bundle, cap estricto en severa | TA.6 | perfil documentado+testeado | TA.6 | medio | AC-6; suite verde |
| TA.8 | README C2C-VE castellano: filosofía heredada, tabla de modos, tabla de renombrado, lista **Señalados** consolidada; property tests finales; notas de procedencia por módulo | TA.7 | C2C-VE completo | TA.7 | medio | AC-9; suite completa verde |

## Fase 2 — B2B-VE (workstream B; anexo §8 — arranca tras TA.2, paralelo con TA.3+)

| ID | Tarea | Entrada | Salida | Deps | Tier | Verificación |
|---|---|---|---|---|---|---|
| TB.0 | Leer código+bundle B2B; correr suite | `B2B/` | gate | — | medio | 128 verdes |
| TB.1 | Sub-bundle specs B2B-VE (extensión VE del bundle B2B, con porqués); resolver **E2** (alcance castellanización) con el humano | anexo §3/§8 | sub-bundle aprobado | TB.0, TA.2, **E2** | alto + humano | M1 |
| TB.2 | **D1** — unidad de cuenta USD; pista VES con `expira_en` obligatorio; FX irrepresentable (con scoping M5: maquinaria + vigilancia/identidad, sin mercado/reciprocidad) | TB.1 | núcleo monetario VE | TB.1 | **alto** | AC-4 (B2B), AC-10; 128+ verdes |
| TB.3 | **D2** — ledger append-only hash-encadenado + `anclar()` pura | TB.2 | evidencia inviolable | TB.2 | **alto** | AC-7 (anclar determinista); suite |
| TB.4 | **D3** — scope `comite_credito` en consultas de saldo; seudonimización de exportes; test de no-exposición saldo+identidad | TB.3 | visibilidad restringida | TB.3 | **alto** | AC-7; suite |
| TB.5 | **D5** — esquema `referencias_comerciales` (sin score) como input del comité | TB.2 | veteo relacional | TB.2 | medio | AC-8 (N2); suite |
| TB.6 | **D6** — `salida_con_saldo` por la puerta de ratificación existente (M8); `exited` fuera de la escalera sancionadora | TB.3 | salida de borde segura | TB.3 | **alto** | AC-7; suite |
| TB.6b | **D8** — `puente.pausar()` reversible por la misma puerta (M8); la pausa no detiene el crédito interno (I-VE7); **M9**: verificación regulatoria fechada previa | TB.6, M9 | pausa del puente | TB.6, **M9** | alto + humano | AC-d68.5/d68.9; suite |
| TB.7 | **D7** — `exportar_registros(miembro, periodo)` → CSV/JSON limpio | TB.4 | exportes fiscales | TB.4 | medio | AC-7 (seudonimización si público); suite |
| TB.8 | **D4** — multisig: documento de gobernanza (umbral, firmantes, rotación) + helpers de verificación; **M9**: verificación regulatoria fechada previa | TB.1, M9 | gobernanza de reserva | TB.1 | alto + humano | doc presente; helpers testeados; motor sin claves (N9) |
| TB.8b | **Correctivo D1** (decisión humana 2026-07-16, antes de TB.9): `render_report` imprimía `€` hardcodeado — defecto hallado por TB.8; completa AC-d1.7 (`moneda` viaja en `to_clearing_input`, el solver la exige sin default, puerta `proposal_moneda` en M8). Ver `d1-unidad-de-cuenta/DESIGN-TB8b.md` | TB.8 | AC-d1.7 completo | TB.8 | medio | AC-d1.7 los 3 puntos; goldens regenerados por construcción; suite |
| TB.9 | **D10** — branding + README B2B-VE + test de conservación a escala de hiperinflación | TB.2–TB.8b (incl. TB.6b) | B2B-VE completo | TB.2–TB.8b, TB.6b | medio | AC-4, AC-9; suite completa |

## Fase 3 — Sim-VE (tras Fases 1 y 2)

| ID | Tarea | Deps | Tier | Verificación |
|---|---|---|---|---|
| TS.1 | Adaptadores del harness a los contratos VE (nombres castellanos, envelope con `modo`); el SUT real se importa, jamás se reimplementa (N11) | TA.8, TB.9 | alto | adaptador pass-through; suite Sim verde |
| TS.2 | Oráculos Track-A nuevos: `fx_irrepresentable`, `moneda_unica_por_campana`, `visibilidad_saldos`, `puerta_humana_ops_nuevas` (independientes: no importan el SUT) | TS.1 | **alto** | AC-8; AST-check de independencia |
| TS.3 | Control negativo por invariante nueva: planta SILENCIOSA (el SUT roto burla sus propios guards; si se auto-detecta, el test prueba la autodefensa del SUT, no el oráculo) | TS.2 | **alto** | el gate del harness upstream (ST6-vacuidad) replicado para cada oráculo nuevo |
| TS.4 | Campañas descriptivas VE (poblaciones buena/neutra/mala; Track-B distribucional) | TS.3 | medio | campaña end-to-end reproducible byte a byte |

## Fase 4 — Continuas (no bloquean, no caducan)

| ID | Tarea | Regla |
|---|---|---|
| TP.1 | `docs/verificaciones/AAAA-MM-DD-*.md` — re-verificación fechada de sanciones/fiscal/cripto ANTES de D4/D8 y de toda Etapa de despliegue | M9; sin datos personales (N8). **Tensión M9/D8 zanjada por el humano el 2026-07-15:** `tasks.md` ponía D8 en TB.6 con deps solo `TB.3` y TP.1 lo exigía tras M9 — spec contra spec, así que no la zanjaba el ejecutor. **D8 sale a TB.6b con dep `M9` explícita**; TB.6 queda solo-D6 y arranca sin M9 (emigrar no es un evento sancionador). Ver `B2B/workflows/micorriza-ve/d6-d8-bordes/DESIGN-TB6.md` §0. |
| TP.2 | Sincronización con upstream: `git fetch upstream && git merge` documentado; divergencias al log de conflictos de `context.md` | E4: el fork no escribe upstream |
| TP.3 | Resolver E2 (alcance castellanización B2B) — bloquea TB.1 | humano |
| TP.4 | Castellanizar meta-docs heredados (CONTRIBUTING, plantillas .github) | medio; no bloquea Fases 1–3 |

## Presupuesto de fiabilidad

Cadena crítica Fase 1: TA.1→TA.8 son 8 nodos secuenciales. La fiabilidad end-to-end decae
multiplicativamente (~0,95⁸ ≈ 0,66 sin gates), y por eso CADA nodo cierra con suite verde +
commit: el fallo se detecta en el nodo que lo produjo y el retroceso cuesta un `git revert`,
no una arqueología. Los nodos `alto` llevan además revisión humana del sub-bundle (M1) — el
eslabón más débil no es el código sino una spec de invariante mal leída. Fase 2 corre en
paralelo desde TA.2: las dos cadenas solo se tocan en la maquinaria compartida (M5), que por
eso se construye UNA vez, primero, y con el tier más alto.

## Qué NO está en este grafo (a propósito)

Las Etapas de despliegue 0–3 del anexo §7 (validar → piloto → reservas/puente → federación),
la operación del multisig, el reclutamiento de células y la asesoría legal/fiscal: son
trabajo de humanos con la herramienta ya construida. El grafo termina donde empieza la
gobernanza (I3: el humano dispone).
