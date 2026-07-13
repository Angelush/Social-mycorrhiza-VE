# Modelo de fallos — micorriza-ve

> Enumeración hostil ANTES de construir: primero se listan los fallos (sin arreglarlos aquí —
> eso es sesgo del defensor), luego `audit.md` prueba que cada uno vive como constraint, AC o
> tarea. F# = modos de fallo previstos; ST# = hallazgos de la lectura adversarial de los dos
> documentos fundacionales y del bootstrap.

## Modos de fallo previstos (F)

- **F1 — Deriva de especificación en el renombrado masivo.** A mitad del área b el árbol
  queda medio traducido (`sala` en tres capas, `mode` en tres) y la suite "pasa" porque los
  tests también quedaron a medias. *Mitigación:* tabla exhaustiva ANTES (M7), renombrado
  mecánico, grep de residuos como parte del gate, suite equivalente completa (AC-1).
- **F2 — Degradación de contexto en sesiones largas.** El ejecutor de un área tardía "olvida"
  un intocable y lo negocia. *Mitigación:* episodios acotados por área con contexto mínimo
  (el sub-bundle del área, no el transcript), estado externo = repo + bundle
  (`simulation.md`), constraints con porqué (el juicio sobrevive al resumen).
- **F3 — Alucinación de completitud.** "Todas las suites verdes" sin correr pytest, o
  corriendo solo el paquete tocado. *Mitigación:* M2 exige la SALIDA pytest real citada en el
  gate; AC-1 lista los tres números esperados; verificar artefactos, no reportes.
- **F4 — El firewall bilingüe mata el dominio.** Sobre-rechazo mal calibrado: la ayuda mutua
  venezolana habla de bancos de tiempo, zonas urbanas y rangos de fechas. *Mitigación:* M6 +
  P1 + AC-2; el análisis FP/FN residual queda en el failure-model del sub-bundle del área a.
- **F5 — Fallos de cola.** Los casos raros y caros: céntimos VES de 15+ dígitos, payload 512
  B en severa, *snapback* a mitad de Fase 2, éxodo del avalista. *Mitigación:* niveles B/C de
  `tests.md` son de cola por diseño; AC-4/5/7; E3 pausa la fase; D6 especifica salida desde
  el día 1.
- **F6 — Goodhart en Sim-VE.** El investigador optimiza una métrica de bienestar y
  reconstruye el dios-vista o degrada la calidad real para subir el número. *Mitigación:*
  Track-B es Measure-only y distribucional (matriz de constraints); el muro es el TIPO de
  salida; N11 (jamás parchear el SUT); los oráculos Track-A paran la campaña, no promedian.

## Hallazgos adversariales (ST)

- **ST1 — "Verbatim" que se vuelve veneno.** El delta 9 dice reutilizar las taxonomías
  bilingües "verbatim"; aplicado literalmente a B2B, `CLAVES_LIBRO_RECIPROCIDAD` y
  `CLAVES_MERCADO` prohíben `credito`, `saldo`, `deuda`, `moneda` — el vocabulario NUCLEAR
  del ledger. El hueco entre lo que el autor quiso (reusar la maquinaria) y lo que la letra
  permite (importar las listas) contiene un sistema muerto. → M5, AC-10, R3.
- **ST2 — La migración token-exacto rompe los stems.** `denominat` y `_cents` solo capturan
  por substring; con tokens exactos, `denominacion`/`centavos` pasarían de largo si nadie
  expande las variantes. CAL-1 lo advierte ("nunca relajado en silencio"). → M6, golden
  `denominacion`, AC-3.
- **ST3 — Colisión `mode`→`sala` vs. nuevo `modo`.** Si el área b corre antes que la a (o el
  módulo c antes que la b), la mitad de la suite interpreta `modo` como sala relacional. El
  orden a→b→c del prompt §PROCESO no es estético: es anti-colisión. → orden fijado en
  `tasks.md` (deps duras), M7.
- **ST4 — Escalada abusiva y `depurar()` no ejecutable.** Una función pura no puede obligar
  al llamador a depurar tras escalar; un miembro malicioso puede ciclar escaladas. El código
  fuerza el procedimiento, no la buena fe. NO se inventa un cooldown en silencio: es
  parámetro de gobernanza abierto. → convención + helper + test (AC-5), Señalados (AC-9),
  N10.
- **ST5 — Confundir la unidad de cuenta con el activo puente.** "1 crédito = 1 USD de valor"
  ≠ "1 USDT = 1 USD" (primas de pánico ~40%). Si el motor asume la paridad en los bordes,
  incrusta la tasa que N3 prohíbe. → N3, spreads humanos documentados, test de que el motor
  no representa tasa alguna (AC-4).
- **ST6 — Puertas laterales en las ops nuevas.** `salida_con_saldo`, `puente.pausar` y
  `anclar` podrían implementarse como helpers directos del ledger "porque es más simple",
  saltándose la ratificación. → M8, AC-7 (el caso C: el camino lateral NO existe en la API).
- **ST7 — Datos con forma de identidad en el repo.** Los goldens del área a NECESITAN
  cédulas/RIF/teléfonos de prueba; si alguien pega uno real, el repo público lo distribuye
  para siempre. → N8: sintéticos marcados; revisión en cada gate que toque goldens.
- **ST8 — El defecto de publicación heredado.** Upstream publicó B2B y Sim como gitlinks
  rotos (un clon recibía solo C2C, con un README que promete 128+120 tests invisibles) y los
  `.git` anidados fueron borrados localmente — la historia pre-publicación de B2B/Sim ya no
  existe. El fork lo corrigió (T0.2/T0.3); el arreglo upstream es decisión del humano (E4).
- **ST9 — Los hechos VE caducan.** Brecha ~16,5%, IGTF 3%, GLs revocables, primas de pánico:
  todo fechado jul-2026 y EN FLUJO. Construir D4/D8 (o desplegar) sobre hechos vencidos
  incrusta un mundo que ya no existe. → etiquetas VOLÁTIL en `context.md`, M9 (verificación
  fechada como gate), E3.
- **ST10 — Tests que fijan el entorno, no el sistema.** El bootstrap encontró dos (pin de
  B2B/C2C atado a la topología de repos del autor). El fork los pagó una vez; no dos. → N12,
  R1.

## Límite honesto (heredado, no resuelto aquí)

El juicio escalar en TEXTO LIBRE ("esta persona es un 3/10") queda fuera del alcance de un
firewall determinista: la membrana detecta FORMAS, no semántica; la semántica es gobernanza
humana. Vive en Señalados (AC-9) y en el README — declararlo es la mitigación.
