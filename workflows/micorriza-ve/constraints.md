# Constraints — micorriza-ve

> Cada regla lleva su porqué: la razón permite aplicar juicio en el borde que la letra no
> cubre. IDs estables — `audit.md`, `evals/` y `tasks.md` referencian estos códigos.

## MUST (M)

- **M1 — Specs antes que código, por área/delta.** El sub-bundle correspondiente
  (`C2C/workflows/micorriza-politica-ve/`, extensión VE del bundle B2B) se escribe y aprueba
  ANTES de tocar `src/`. *Porque:* es el método del repo y el prompt §I.1 lo ordena; el coste
  de un invariante mal entendido se paga multiplicado en seis capas.
- **M2 — Suite completa verde antes de pasar de área, con salida pytest real citada en el
  gate.** *Porque:* el renombrado masivo hace trivial dejar medio árbol roto; la evidencia es
  el artefacto, jamás el auto-reporte.
- **M3 — Castellano total en C2C-VE** (identificadores públicos, claves, enums, mensajes,
  verdictos, docs, tests). Claves de esquema sin tildes; valores y mensajes con tildes.
  *Porque:* mandato del prompt; las claves sin tilde son robustez de transporte, los mensajes
  con tilde son respeto por el idioma de trabajo.
- **M4 — Enteros de unidad mínima en todo importe; float prohibido en rutas de valor;
  conservación exacta testeada a 15+ dígitos.** *Porque:* hiperinflación VES; los enteros de
  Python lo permiten y el test lo fija.
- **M5 — Alcance por sistema de las taxonomías.** C2C-VE hereda las cinco listas de §B
  completas; B2B-VE hereda SOLO vigilancia/identidad + la maquinaria de tokenización; jamás
  mercado/reciprocidad. *Porque:* `credito`, `saldo`, `deuda`, `moneda` son el vocabulario
  NUCLEAR del ledger B2B (ST1/C3) — un firewall copiado sin scoping mata al paciente.
- **M6 — Expansión de raíces al migrar substring→token-exacto.** Auditar cada entrada
  dependiente de raíz (`denominat`, `_cents`, …) y enumerar variantes morfológicas explícitas;
  la dirección de fallo sobre-rechazo se conserva — solo se eliminan las colisiones de
  dominio. *Porque:* CAL-1 upstream define el remedio y prohíbe relajar en silencio; las seis
  capas se mueven juntas vía AC-X.
- **M7 — Tabla de renombrado exhaustiva y versionada ANTES del cambio** (`mode`→`sala` y todo
  §A). *Porque:* F1/ST3 — la colisión semántica `mode`/`modo` es el error más barato de
  prevenir y el más caro de depurar a mitad de suite.
- **M8 — Toda operación de valor nueva en B2B-VE (`salida_con_saldo`, `puente.pausar`,
  `anclar`) pasa por el MISMO camino de ratificación humana que las existentes; ninguna
  helper directa sobre el ledger.** *Porque:* la puerta de un solo sentido (I3) no admite
  puertas laterales "por conveniencia" (ST6).
- **M9 — Verificación regulatoria/sanciones FECHADA en `docs/verificaciones/` antes de
  construir el puente (Fase 2, D4/D8 documentación operativa) y antes de cada Etapa de
  despliegue.** *Porque:* todo el §5 del anexo está EN FLUJO; el diseño exige re-verificar,
  no recordar.
- **M10 — El `modo` viaja en el envelope (`modo` + `celula_id` obligatorios); cada capa valida
  contra la tabla; rechazar, nunca recortar.** *Porque:* prompt §E; policéntrico sin estado
  global; reparar-en-silencio es la puerta de entrada del comportamiento no especificado.
- **M11 — Commits por área en castellano explicando el porqué; diff legible por área.**
  *Porque:* criterio global del prompt; el mensaje del commit es la memoria fiable del fork
  (lección heredada del upstream).
- **M12 — Los diez intocables C2C + las invariantes B2B originales verificables por test en
  los TRES modos.** *Porque:* criterio global; "verificable por test" es lo que separa
  invariante de eslogan.

## MUST-NOT (N)

- **N1 — Ningún token, moneda propia ni "puntos".** El crédito es compensación de
  obligaciones, no activo transferible fuera de la red. *Porque:* universal (plutocracia DAO,
  especulación vs. utilidad) + reforzado por Petro/Sunacrip: cualquier "moneda" nueva huele a
  estafa.
- **N2 — Ningún escalar global de persona** (score/reputación/solvencia numérica); en B2B-VE
  las `referencias_comerciales` son juicio del comité, sin score computado. *Porque:*
  intocable 1; delta 5; medir "solvencia" naive reconstruye el dossier.
- **N3 — FX irrepresentable en ambos motores**; conversión = decisión humana documentada
  fuera del protocolo; spreads de liquidación jamás hardcodeados. *Porque:* no existe "el"
  tipo de cambio (brecha BCV/paralelo viva); una tasa en código es una decisión política
  incrustada y un punto capturable.
- **N4 — Sin conversión ni mezcla automática USD/VES**; campañas y compromisos mono-moneda;
  mezcla → error de brecha. *Porque:* §D; dos campañas paralelas, jamás una mixta.
- **N5 — Ni LLM ni smart contract en la ruta de liquidación/clearing.** `anclar()` emite un
  hash; la publicación a cadena es del llamador. *Porque:* el solver determinista off-chain
  es intocable; gas+complejidad+apagones sin beneficio que lo justifique.
- **N6 — Sin integración con canales estatales de identidad o denuncia** (VenApp o
  equivalente); sin registro SUNACOOP como requisito de participación. *Porque:* el riesgo es
  la captura política de la coordinación, no solo la vigilancia (constraint 10 del prompt).
- **N7 — Saldos jamás públicos con identidad.** Scope `comite_credito`; todo export público
  seudonimizado (hashes/compromisos), nunca identidad+monto en claro. *Porque:* un libro
  público de saldos es un mapa de matraqueo (lista de objetivos de extorsión).
- **N8 — El repo público jamás contiene datos reales de personas o células** — ni en
  fixtures, ni en goldens, ni en las verificaciones fechadas. Los vectores con forma de
  identidad (cédulas/RIF/teléfonos de test) son sintéticos y están marcados como tales.
  *Porque:* el repo es protocolo, no despliegue; la seguridad personal no es negociable.
- **N9 — El motor jamás custodia claves ni direcciones.** Multisig = documento de gobernanza
  + helpers de verificación. *Porque:* delta 4; custodia en código = trono que capturar.
- **N10 — Ningún problema abierto "resuelto" en prosa sin mecanismo.** Sin test que lo fije,
  va a la lista Señalados. *Porque:* filosofía heredada — flagged, not fake-resolved.
- **N11 — El harness/investigador de Sim-VE jamás parchea el SUT dentro del loop.** *Porque:*
  la puerta de un solo sentido del harness upstream; un investigador que "arregla" el sistema
  bajo prueba no investiga nada.
- **N12 — Ningún test que fije topología del entorno** (rutas absolutas, existencia de
  `.git`, nombre del repo) como si fuera invariante del sistema. *Porque:* rechazo codificado
  R1 (el bootstrap ya pagó este error).

## PREFERENCIAS (P)

- **P1 —** El sobre-rechazo sigue siendo la dirección de fallo elegida, SALVO colisión con el
  dominio de ayuda mutua; documentar FP/FN residual en el failure-model del área.
- **P2 —** Branding: "circuito de crédito comercial" de la cámara/gremio; jamás
  moneda/coin/token/petro/comunal.
- **P3 —** `expira_en` corto recomendado en campañas VES (convención documentada — el motor
  no modela inflación: sería otra tasa).
- **P4 —** Reutilizar capas existentes antes que crear nuevas (convergencia sobre Capa 5;
  trinquete sobre Capa 6; gobernanza de célula B2B reutiliza Capa 6 C2C).

## ESCALADA (E)

- **E1 —** Conflicto entre una instrucción y LO INTOCABLE → parar, documentar en el
  `audit.md` del sub-bundle, decisión humana. Gana lo intocable.
- **E2 —** Alcance de la castellanización de B2B-VE (¿también identificadores?) → decisión
  humana antes de TB.2. Default propuesto: APIs nuevas y docs en castellano ya; renombrado
  total de identificadores B2B pospuesto a decisión explícita.
- **E3 —** Cambio material del contexto regulatorio (snapback, reclasificación IGTF del
  crédito mutuo) → pausar la fase afectada; el diseño ya exige sobrevivir sin puente.
- **E4 —** Cualquier cambio que requiera tocar el repo upstream → humano decide; el fork no
  escribe upstream.
- **E5 —** Si un modo parece exigir relajar un intocable → re-leer el prompt (la
  interpretación es errónea); si persiste, E1.

## Matriz constraint × modo de ejecución

| Constraint | Construcción | Sim-VE (investigación) | Docs |
|---|---|---|---|
| I1–I5, N1–N9 | Enforce (test rojo = parada) | Enforce vía oráculos Track-A (violación = alto de campaña, jamás promediada) | n/a |
| Métricas de bienestar (Track-B) | n/a | **Measure-only** — distribuciones descriptivas; el TIPO de salida hace irrepresentable el escalar por persona | n/a |
| M2 (suite verde) | Enforce | Skip (las campañas no re-corren la suite) | Skip |
| M9 (verificación fechada) | Enforce al llegar a D4/D8 | Skip | Enforce antes de publicar guías de despliegue |
| N8, N12 | Enforce | Enforce | Enforce |

El modo se fija al iniciar la tarea; no cambia a mitad de ejecución.

## Rechazos codificados (QUÉ ESTUVO MAL → POR QUÉ IMPORTA → CONSTRAINT → EJEMPLO CORRECTO)

- **R1 (bootstrap, commit `a50f7d2`).** Dos tests del harness afirmaban la topología del
  entorno original (B2B repo propio / C2C sin repo) como si fuera propiedad del sistema → al
  cambiar el entorno (monorepo del fork) ningún código podía satisfacer ambos → **N12** →
  ejemplo: probar "sin repo envolvente → pin None" en un `tmp_path` hermético, no exigir que
  un directorio del árbol real carezca de `.git`.
- **R2 (auditoría fundacional, §B).** Taxonomías solo-inglés con matching substring dejaban
  pasar `puntuacion`/`reputacion` y rechazaban `banco_de_tiempo`/`zona_urbana` (`ban` ⊂
  `urbana`) → un firewall que mata el dominio que protege se desinstala solo → **M6 + P1 +
  AC-2/AC-3** → ejemplo: `bancoDeTiempo` → tokens `banco,de,tiempo` → admitida;
  `lista_negra_local` → bigrama `lista+negra` → rechazada; `descripción_del_score_musical` →
  token `score` → SIGUE rechazada (dirección de fallo conservada).
- **R3 (anexo delta 9, lectura adversarial).** "Reutilizar verbatim las taxonomías" aplicado
  a B2B habría prohibido su vocabulario nuclear → la herramienta de un dominio aplicada a
  otro sin scoping invierte su función → **M5 + AC-10** → ejemplo: `{"saldo": …}` admitido en
  el ledger B2B; rechazado en C2C Capa 1 sala `don_comunal` (CLAVES_LIBRO_RECIPROCIDAD).
