# Contexto — cuarto de datos del fork (micorriza-ve)

> Inventario revisado ANTES de construir. Cada afirmación de abajo fue verificada contra el
> árbol del fork en su Fase 0 (2026-07-13), no asumida.

## Inventario de fuentes

| Fuente | Qué manda | Estado |
|---|---|---|
| `C2C/prompt-fork-venezuela.md` | El prompt de producción del workstream C2C-VE: rol, intocables 1–10, áreas §A–§I, proceso y criterios globales | Fundacional |
| `B2B/micorriza-b2b-venezuela-adaptacion.md` | Auditoría UE→VE decisión por decisión (§1), contexto operativo verificado jul-2026 (§2), arquitectura corregida (§3), realidad regulatoria (§5), riesgos (§6), secuenciación de despliegue (§7), deltas accionables 1–10 (§8) | Fundacional |
| `C2C/workflows/micorriza-politica/` | Bundle upstream C2C: specs por capa, constraints (incl. **CAL-1**), failure-model, evals + golden sets | Heredado |
| `B2B/workflows/micorriza/` | Bundle upstream B2B: spec del solver/ledger, invariantes, evals | Heredado |
| Código SUT | B2B: solver de clearing + ledger de crédito mutuo (single-cell, `ts` entero, determinista; **128 tests**). C2C: seis capas puras sin estado (**293 tests**). Sim: motor + 3 sims contra los SUT reales (**121 tests** en el fork) | Heredado, verde en Fase 0 |
| Commit upstream `76519ab` (CAL-1) | El escaneo substring sobre claves es calibración deliberada, CON disparador de revisión definido | Heredado — ver conflicto C1 |

## Log de conflictos (resueltos aquí, no en silencio)

- **C1 — CAL-1 vs. §B del prompt.** Upstream documenta el substring sobre-amplio como decisión
  (`descripción_del_score_musical` se rechaza y está bien); §B lo corrige a token-exacto. NO es
  contradicción: CAL-1 define su propio disparador ("cuando llegue contenido en lenguaje
  natural… word-boundary matching o allowlist revisada, las 6 capas a la vez vía AC-X, nunca
  relajado en silencio"). El castellano dispara la revisión ANTES de lo previsto
  (`banco_de_tiempo` contiene `ban`; `zona_urbana` contiene `ban`): **§B ES la ejecución del
  remedio que CAL-1 dejó especificado.** Obligaciones que CAL-1 impone al fork: M6 (expansión
  de raíces: `denominat`/`_cents` solo funcionaban como substring → enumerar variantes
  morfológicas explícitas) y conservar la dirección de fallo sobre-rechazo (P1) —
  `descripción_del_score_musical` SIGUE rechazada bajo tokens (contiene el token `score`).
- **C2 — "Etapa" vs. "Fase".** Las Etapas del anexo §7 (0 validar → 3 federación) son de
  DESPLIEGUE de la red real; las Fases de `tasks.md` son de CONSTRUCCIÓN del software. Nombres
  distintos a propósito.
- **C3 — delta 9 leído literalmente.** "Reutilizar verbatim las taxonomías bilingües" aplicado
  a B2B prohibiría su vocabulario nuclear (`credito`, `saldo`, `deuda`, `moneda`). Resolución
  ST1→M5: B2B hereda la MAQUINARIA (tokenización, normalización, bigramas) + las listas de
  vigilancia/identidad; jamás las de mercado/reciprocidad.
- **C4 — ubicación del fork.** El prompt ofrecía "directorio `C2C-VE/` o repo
  `Social-mycorrhiza-VE`, a tu criterio documentado". Decisión: **repo separado**. Porqués: el
  fork abarca B2B+C2C+Sim (no solo C2C); el upstream publicado queda limpio; el renombrado
  total dentro de un subdirectorio duplicaría el árbol; y "el fork mismo es prueba del derecho
  a bifurcar" (intocable 9) se ejerce de verdad. La carpeta anidada original (`Vzla Fork/`
  dentro del repo upstream, sin trackear) no era un fork y quedó como puntero.
- **C5 — números de suite.** El prompt dice "~293 tests" (exacto: 293 ✓). El README upstream
  dice Sim 120; aquí son 121 (Fase 0 añadió un test hermético del pin — ver R1 en
  constraints.md).

## Contexto faltante (se declara, no se inventa)

| Hueco | Dueño | Cuándo se cierra |
|---|---|---|
| Valores concretos de `velocity_cap` por modo ("documenta valores") | spec de área c/f | TA.4 / TA.7 (defaults propuestos + nota de gobernanza) |
| Fricción/cooldown contra escalada abusiva | gobernanza humana | Señalados (ST4); parámetro abierto a decisión de célula |
| Alcance de la castellanización de B2B (¿identificadores también?) | humano (E2) | antes de TB.2 |
| Patrón exacto de teléfono VE (el prompt da una aproximación) | spec TA.2 | TA.2, con goldens que fijen los casos |
| Jurisdicción del wrapper offshore | asesoría externa | fuera del código (bordes de intent.md) |
| Tratamiento fiscal del crédito mutuo (¿compensación gravable con IGTF?) | asesoría local | antes de despliegue; el código solo garantiza exportes limpios (TB.7) |

## Estabilidad del contexto

- **PERENNE:** intocables 1–10; invariantes B2B (conservación, puerta humana, permissioned);
  pureza/determinismo offline; enteros de unidad mínima; licencias copyleft.
- **EVOLUTIVO:** tabla de límites por modo (defaults, no dogma); líneas iniciales
  conservadoras; banda Sardex ~25–50% como sensibilidad reportada, no gate.
- **VOLÁTIL** (re-verificar y FECHAR antes de construir el puente y antes de toda etapa de
  despliegue — M9): brecha BCV/paralelo (~16,5% jul-2026); IGTF 3%; ofensiva SENIAT sobre
  USDT; GLs y sanciones (~150–200 SDN activos; *snapback* posible); primas P2P de pánico
  (~40% ene-2026); predominio TRC-20.

## Exclusiones (qué NO cargar al construir)

- Contexto mínimo por tarea: el sub-bundle del área + los archivos de la capa tocada. No todo
  el repo, no este bundle entero, no transcritos de diseño.
- Nada de material del harness de especificación ni de su base de conocimiento en el repo
  público (convención heredada del upstream).
- Cachés (`.venv`, `.pytest_cache`, `.hypothesis`, `__pycache__`) jamás se versionan.

## Terminología (mapa mínimo compartido)

- **sala** (ex-`mode` relacional de Capa 1: `don_comunal` / `igualdad` / `precio_de_mercado`)
  ≠ **modo** (calibración por célula: `paz` / `catastrofe_acotada` / `catastrofe_severa`).
- **crédito** (unidad de cuenta interna; 1 crédito = 1 USD de valor) ≠ **USD físico** ≠
  **USDT** (activo puente de bordes; JAMÁS se asume 1:1 en pánico — spreads humanos).
- **célula** = cámara/gremio/asociación existente usando la herramienta (no una cooperativa
  nueva registrada ante SUNACOOP — eso es N6/anti-patrón).
- **gitlink** = puntero de submódulo sin `.gitmodules` (el defecto de publicación upstream que
  la Fase 0 corrigió vendorizando B2B y Sim).
- **Etapa** (despliegue, anexo §7) vs. **Fase** (construcción, tasks.md).
