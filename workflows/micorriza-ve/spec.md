# Especificación — fork Venezuela (consolidación ejecutable)

> Los documentos fundacionales SON la especificación de detalle; este archivo es el contrato
> que los une: entradas, salidas, dependencias, capa de significado y semántica de
> operaciones. Detalle C2C-VE: [`../../C2C/prompt-fork-venezuela.md`](../../C2C/prompt-fork-venezuela.md)
> (áreas §A–§I). Detalle B2B-VE: [`../../B2B/micorriza-b2b-venezuela-adaptacion.md`](../../B2B/micorriza-b2b-venezuela-adaptacion.md)
> (§3 arquitectura, §8 deltas 1–10).

## Problema autocontenido

- **ENTRADAS:** el árbol del fork en HEAD (B2B 128 verdes, C2C 293, Sim 121); los dos
  documentos fundacionales; los bundles upstream (incl. CAL-1); las decisiones E2/E5 cuando
  el humano las tome.
- **SALIDAS:** (Fase 1) C2C-VE en castellano con modos + trinquete + doble moneda +
  convergencia, suite equivalente + nuevos AC verdes; (Fase 2) B2B-VE con los deltas 1–10;
  (Fase 3) Sim-VE sobre los contratos nuevos; READMEs con la lista Señalados; un sub-bundle
  de specs por área ANTES de su código.
- **FORMATO:** Python stdlib + pytest/hypothesis (networkx solo en Sim); docs markdown en
  castellano; claves de esquema sin tildes, valores y mensajes con tildes (M3).
- **DEPENDENCIAS:** venv propio del fork; tests deterministas y offline (sin red, sin reloj).
- **SUPUESTOS:** el comportamiento upstream es la verdad heredada; sus tests son el piso de
  regresión (AC-1). Las seis capas C2C siguen puras (estado del llamador, nada persiste).
- **LÍMITES DE ALCANCE:** los bordes de `intent.md` (transporte, UI, despliegue, custodia,
  asesoría legal, upstream).

## Workstreams

### Fase 1 — C2C-VE (prompt §A–§I, en el orden de §PROCESO)

| Área | Qué | Ancla |
|---|---|---|
| a | Tokenización de claves (límites no-alfanuméricos + camelCase), normalización NFD, matching por token exacto + bigramas para claves compuestas, cinco taxonomías bilingües byte-idénticas donde aplica, escaneo de VALORES string (cédula/RIF/teléfono) — las 6 capas a la vez, AC-X actualizado | §B, §C, M6, C1 |
| b | Castellanización completa: módulos, funciones, claves, enums, mensajes, verdictos, tests, docs; `mode`→`sala` resuelve la colisión con el nuevo `modo` | §A, M7, ST3 |
| c | Módulo `modo` (`src/modo/modo.py`): tabla de límites, `validar_modo` aplicado por cada capa vía envelope (`modo` + `celula_id` obligatorios), rechazar-no-recortar | §E, M10 |
| d | Trinquete asimétrico: escalada unilateral e inmediata; desescalada solo con decisión `adoptada` de Capa 6; `depurar(items, modo, ahora)` pura y determinista | §F, ST4 |
| e | Doble moneda en Capa 4 (campañas mono-moneda `USD`/`VES`, mezcla → `ErrorDeBrechaAseguramiento`) + taxonomía de mercado en Capa 1; conservación exacta con importes de 15+ dígitos | §D, M4, N4 |
| f | Perfil de convergencia SOBRE la Capa 5 (señal `paso_maquinaria` en whitelist; señal de ZONA, jamás de persona; `velocity_cap` estricto en severa) | §G, P4 |

Gate por área: suite completa verde + los AC del área + commit con porqué (M2, M11).

### Fase 2 — B2B-VE (anexo §8; arranca tras el área (a) para heredar la maquinaria — M5)

| Delta | Qué | Ancla |
|---|---|---|
| D1 | Unidad de cuenta `USD` por defecto; pista `VES` opcional con `expira_en` corto OBLIGATORIO; enteros de unidad mínima; FX irrepresentable (taxonomía `tasa_de_cambio, tipo_de_cambio, exchange_rate, fx, bcv, paralelo`) | §8.1, N3, M4 |
| D2 | Ledger append-only + hash-encadenado + `anclar()` pura que emite el hash raíz del período (la publicación a cadena es integración del llamador, documentada) | §8.2, N5 |
| D3 | Visibilidad de saldos con scope `comite_credito`; toda exportación pública seudonimizada; test: ningún punto de consulta público expone saldo+identidad | §8.3, N7 |
| D4 | Multisig del fondo de garantía: documento de gobernanza (umbral, firmantes, rotación de direcciones) + helpers de verificación; el motor JAMÁS custodia claves | §8.4, N9 |
| D5 | Esquema `referencias_comerciales` (quién avala, relación declarada, antigüedad) como input del comité — SIN score numérico | §8.5, N2 |
| D6 | `salida_con_saldo`: positivo → liquidación vía puente; negativo → plan de pago o absorción por avalista. Especificada y testeada desde el día 1 (riesgo éxodo) | §8.6, M8 |
| D7 | `exportar_registros(miembro, periodo)` → CSV/JSON limpio por empresa; el sistema no declara por nadie (compliance-READY, no -DEPENDENT) | §8.7 |
| D8 | `puente.pausar()` reversible, activable por el comité, que NO detiene el crédito interno (sobrevivir a "USDT deja de ser viable" y al *snapback*) | §8.8, M8 |
| D9 | Herencia C2C con alcance M5: maquinaria de matching + listas de vigilancia/identidad; JAMÁS las de mercado/reciprocidad (vocabulario nuclear B2B) | §8.9, ST1 |
| D10 | Branding: "circuito de crédito comercial"; nada de moneda/coin/token/petro/comunal | §8.10, P2 |

### Fase 3 — Sim-VE (tras Fases 1–2)

Adaptadores del harness a los contratos VE (el SUT real se importa, jamás se reimplementa —
N11); oráculos Track-A nuevos: `fx_irrepresentable`, `moneda_unica_por_campana`,
`visibilidad_saldos`, `puerta_humana_ops_nuevas`; un control negativo con planta SILENCIOSA
por invariante nueva (el SUT roto debe burlar sus propios guards, si no el test prueba la
autodefensa del SUT y no el oráculo); campañas descriptivas (Track-B sin escalar por
persona — el muro es el TIPO de salida).

## Capa de significado (lo que un ejecutor no puede inferir)

**INVARIANTES** (romper una = parada dura, no un test rojo más):
- I1 — Los 10 intocables del prompt: forma irrepresentable, nunca política ni flag.
- I2 — Conservación exacta de valor en enteros de unidad mínima, a escala de hiperinflación.
- I3 — La puerta de un solo sentido sobre valor: el solver/agente propone, el humano dispone.
- I4 — Determinismo offline: mismo input → mismo byte en cualquier nodo (los apagones no
  rompen el clearing; cualquier nodo de la célula puede correrlo).
- I5 — FX irrepresentable en ambos motores: "no existe EL tipo de cambio" es un hecho del
  dominio (brecha ~16,5% políticamente disputada), no una opinión de diseño.

**PELIGROS** (prevención activa):
- H1 — El escalar de persona con nombre benigno (`fertilidad`, `alcance`): el muro real es el
  TIPO de salida y el cierre de esquema; la lista de claves es lint secundario.
- H2 — Sobre-rechazo que mata el dominio de ayuda mutua (`banco_de_tiempo`): la única
  relajación permitida es la de CAL-1 (token-exacto con expansión de raíces, M6); jamás
  cobertura efectiva menor que la actual.
- H3 — Libro de saldos público = mapa de matraqueo (N7): la visibilidad restringida ENDURECE
  el diseño respecto a España.
- H4 — Pista VES sin expiración = pasivo inflacionario (`expira_en` obligatorio en D1).
- H5 — Branding con olor a moneda estatal (P2): Petro, Sunacrip y el trueke comunal dejaron
  cicatrices simbólicas; el producto es un registro de compensación de la cámara/gremio.

**RESTRICCIONES NO ESCRITAS** (obvias para el experto, exactamente lo que un ejecutor viola):
- U1 — Una ausencia informativa es `sin_informacion_desde_tu_posicion`, jamás una marca.
- U2 — El impago es contagioso: B2B sigue *permissioned* con veteo relacional. El C2C tiene
  salas sin barrera. NO cruzar las lógicas de admisión.
- U3 — La asimetría del trinquete es deliberada: borrar rápido (escalada unilateral),
  re-acumular despacio (desescalada por consentimiento). En crisis los datos son pasivo.
- U4 — La reputación no viaja entre células sin consentimiento explícito Y sin que el modo
  vigente lo permita (en `catastrofe_severa` está prohibida aunque haya consentimiento).

## Semántica de operaciones consecuentes

| Operación | Tipo | Dueño | ¿Reversible? | Radio | Regla |
|---|---|---|---|---|---|
| aplicar clearing | write | puerta humana | no (asientos) | célula | heredada; intocable |
| `salida_con_saldo` | write | comité, vía puerta | no | célula + avalista | M8; día 1 (éxodo a mitad de ciclo) |
| `puente.pausar/reanudar` | write | comité | sí (dos vías) | bordes | M8; el crédito interno sigue vivo (AC-7) |
| `anclar()` | read/emit | cualquiera | n/a (pura) | ninguno | emite hash raíz; publicar a cadena es del llamador |
| `exportar_registros` | read | miembro | n/a | un miembro | seudonimizar si el destino es público (N7) |
| escalada de modo | write | cualquier token del círculo | sí (vía desescalada gobernada) | círculo | unilateral inmediata + `depurar()` por convención+test |
| desescalada de modo | write | Capa 6 (`adoptada`) | sí | círculo | jamás unilateral (U3) |
| alta/líneas de miembro | write | comité | sí | miembro | veteo relacional D5; sin score (N2) |

## Chequeo de eco

**ENTREGABLE:** fork operativo en castellano con los invariantes testeados en los tres modos ·
**INCLUSIÓN CLAVE:** intocables 1–10 + deltas 1–10, cada uno con su AC · **RESTRICCIÓN DURA:**
nada irrepresentable se vuelve representable, y nada abierto se "resuelve" en prosa (N10).
