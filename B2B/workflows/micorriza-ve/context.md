# Contexto — B2B-VE

> Lo que el bundle upstream asume y en Venezuela es falso, más las decisiones humanas
> fechadas que este sub-bundle NO puede tomar por su cuenta. Detalle completo del contexto
> verificado: [`../../micorriza-b2b-venezuela-adaptacion.md`](../../micorriza-b2b-venezuela-adaptacion.md) §2.

## 1. Lo que el bundle upstream da por supuesto (y aquí no se cumple)

El bundle `../micorriza/` es correcto **para España/UE**. Sus supuestos rotos en VE:

| Supuesto upstream | Dónde vive | Realidad VE | Delta que lo corrige |
|---|---|---|---|
| La unidad de cuenta es el euro | `spec-ledger.md` §1 título y `turnover_eur_cents` | Dolarización de facto; el VES pierde >70% desde oct. 2025 | D1 |
| MiCA es el marco vinculante | `constraints.md` N3 | MiCA no aplica; Sunacrip en limbo post-escándalo | (contexto; ningún delta lo "cumple") |
| RGPD Art. 22 justifica la puerta humana | `spec-ledger.md` §1, `architecture.md` | La puerta humana se mantiene, pero **su porqué cambia**: no es cumplimiento normativo, es que no hay tribunales que ejecuten contratos (§2.11) | (I3; refuerza M8) |
| La cadena de hashes es "audit-only, futuro punto de anclaje" | `spec-ledger.md` §5 | El anclaje deja de ser futuro: sustituye parcialmente al juez | D2 |
| Los saldos son visibles dentro de la célula | implícito: no hay scope en `member_statement` | Libro de saldos = mapa de matraqueo | D3 |
| Hay estados financieros auditables para fijar líneas | `spec-ledger.md` §1 (`turnover`) | No los hay → veteo relacional | D5 |
| Un miembro que se va es un caso de borde | no está | Éxodo continuo: se van a mitad de ciclo | D6 |

**Consecuencia de método:** cada delta debe decir explícitamente qué frase del bundle upstream
deroga. Un fork que solo añade, sin derogar, deja dos documentos afirmando cosas contrarias y
el siguiente lector cree al equivocado.

## 2. Decisiones humanas fechadas

### E2 (TP.3) — Alcance de la castellanización de B2B-VE — **2026-07-15**

**Decidido: el default de `constraints.md` §E2.**

- APIs **nuevas** y **docs**: castellano, ya. (`anclar`, `salida_con_saldo`, `puente_pausar`,
  `exportar_registros`, `referencias_comerciales`, `moneda`, `comite_credito`.)
- Identificadores **existentes** de B2B: se quedan en inglés. `mutual_credit_ledger.py`,
  `clearing_solver.py`, `state`, `members`, `obligations`, `debtor`, `creditor`,
  `balance_cents`, `ratified_by` — **no se renombran**.
- El renombrado total queda **pospuesto a decisión explícita**. No es "nunca": es "no ahora,
  y no por inercia".

*Porque:* B2B-VE no es C2C-VE. En Fase 1 el prompt §A ordenaba castellanización total y el
árbol era el fork entero (TA.3). Aquí el mandato no existe, y el renombrado tocaría los 5
archivos de test y los 4 goldens de un motor de **valor** cuya suite es el piso de regresión.
El coste es alto, el beneficio es estético, y el riesgo (un rename que cruce el scoping M5)
es exactamente el fallo que M5 existe para prevenir.

**Consecuencia aceptada, no ignorada:** el árbol queda bilingüe de forma permanente, y las
firmas nuevas mezclan los dos idiomas —
`salida_con_saldo(state, member_id, ratified_by, ts)`. Es feo y es deliberado. Queda en la
lista **Señalados** del README B2B-VE (D10/TB.9), no fake-resuelto en prosa (N10).

**Excepción que NO viola E2:** `turnover_eur_cents` → `turnover_cents` (ver D1). Sigue en
inglés; no es castellanización. Es una corrección de veracidad del esquema.

### D1 — Dónde vive `moneda` — **2026-07-15**

**Decidido: mono-moneda por CÉLULA; `turnover_eur_cents` → `turnover_cents`.**

- `moneda` ∈ {`USD`, `VES`} es parámetro de `create_cell`, no campo de la obligación.
- **`USD` es el default y la unidad de cuenta del sistema. `VES` no es su igual.**
- Las obligaciones y los saldos **no llevan moneda** → una obligación mixta es
  **irrepresentable**, no rechazada.
- La "pista VES" del anexo §3.1 = una **célula VES aparte** (§3.1 dice, literalmente,
  "contabilidad separada").
- Célula `VES` ⇒ `expira_en_dias` obligatorio (D1/H4).

**Por qué USD y no simetría entre las dos (decisión humana, 2026-07-15):** el VES **no sirve
como depósito de valor**. Las tres funciones del dinero se separan en Venezuela y hay que
tratarlas por separado: el VES sigue siendo medio de pago y unidad de cuenta para menudeo y
obligaciones estatales (§2.1), pero pierde >70% de su valor desde oct. 2025. Un **saldo** de
crédito mutuo es, por definición, valor sostenido en el tiempo — exactamente la función que
el VES no cumple. De ahí que la asimetría sea estructural y no una preferencia:

- El USD es la unidad de cuenta **porque** el crédito mutuo denominado en USD da contabilidad
  a prueba de devaluación **sin necesitar los dólares físicos escasos** (el truco WIR
  aplicado a la sequía de divisas, §1.2).
- `expira_en_dias` en las células VES **no es una precaución**: es lo que impide que el motor
  finja que un saldo VES almacena valor. Una pista VES sin expiración es un pasivo
  inflacionario (H4) — el motor estaría mintiendo sobre lo que guarda.
- Un motor que modelara la pérdida de valor del VES necesitaría una tasa. Eso es N3. La
  expiración es la única respuesta a la inflación que **no** requiere representar el FX.

*Porque:* el invariante L1 del ledger (`sum(balance_cents) == 0`) **es** la definición de
crédito mutuo, y solo significa algo dentro de una unidad de cuenta: sumar centavos USD con
centavos VES no da cero, da basura. Poner `moneda` en la obligación obligaría a verificar L1
por partición y abriría la puerta a que alguien "resuelva" la partición con una tasa — que es
precisamente N3/I5. Sacando la moneda de la obligación, el FX no tiene dónde escribirse.

*Por qué esto NO copia el patrón de TA.6:* en C2C-VE (área e) la mezcla se rechaza con
`ErrorDeBrechaAseguramiento` porque varias campañas conviven en un motor y el sobre lleva la
moneda. Aquí no hace falta un check: la forma no existe. **I1 pide irrepresentable antes que
flag**, y aquí se puede pagar ese precio. Copiar el check de TA.6 sería más código para una
garantía más débil.

*Coste aceptado:* `turnover_cents` toca fixtures y los 4 goldens JSON
(`evals/golden-set/{test_A,test_B,test_C,ledger_flow}.json`) — misma clase de regresión que
TA.6 y con el mismo remedio: actualizar conservando la semántica, no el byte.

### D4 — Multisig de reserva: umbral, roles, rotación — **2026-07-16**

> **LA PROCEDENCIA DE CADA VALOR ES PARTE DEL VALOR.** Solo el umbral es del propietario. Los
> otros dos los rellenó Opus **por instrucción explícita del propietario** («inventa las demás
> para seguir con el desarrollo»), para no dejar TB.8 bloqueado. **No son decisiones de
> gobernanza: son andamios con forma de decisión.** Se marcan aquí porque un valor inventado y
> uno decidido son indistinguibles dentro de seis meses si nadie escribe cuál fue cuál — el
> mismo fallo que M9 previene en las verificaciones, y la misma razón por la que la firma de
> `2026-07-15-sanciones.md` dice cómo se produjo.

**Nada de esto entra en `src/`.** N9: el motor no custodia claves, no firma y no verifica
quórums de gobernanza. D4 es un **documento** + helpers de verificación. Que estos valores sean
provisionales no contamina el motor: contamina el documento, y ahí se ve.

| Decisión | Valor | Procedencia | Estado |
|---|---|---|---|
| **Umbral** | **3 de 5** | **Propietario, 2026-07-16** | **DECIDIDO** |
| Roles firmantes | los 5 de abajo | **Opus (relleno)** | **PROVISIONAL** |
| Rotación | 12 meses escalonada + disparadores | **Opus (relleno)** | **PROVISIONAL** |

**Requisito que M9 manda al documento** (`2026-07-15-sanciones.md`, hallazgos 1 y 5): **ningún
firmante puede estar designado en la lista SDN**, y esa comprobación **es del comité, no del
motor**. El motor no criba contra la SDN y no debe: diría «este firmante está limpio» sin poder
sostenerlo.

**Roles (PROVISIONAL — cargos, JAMÁS nombres, N8):**

1. Coordinación del comité de crédito
2. Tesorería de la célula
3. Auditoría interna — miembro **fuera** del comité de crédito
4. Representación de miembros — elegida por asamblea, **fuera** del comité
5. Custodia externa — fuera de la operación diaria y **fuera del país**

*Por qué cinco cargos distintos y no cinco personas de confianza:* con 3 de 5, tres firmas
abren la reserva. Si los cinco cargos fueran capturables por la misma vía (todos del comité,
todos en la misma ciudad), el umbral sería decorativo — quien capture esa vía tiene tres firmas.
Los roles 3, 4 y 5 existen para que **ninguna captura de una sola función alcance el quórum**.

**Restricción geográfica derivada del umbral (esta NO es opinión: sale de la aritmética de
3-de-5, y es la parte de este bloque que más se sostiene):**

- **Ningún lugar puede concentrar 3 firmantes** → una redada, una detención o un allanamiento en
  un solo sitio no abre la reserva.
- **Perder un lugar no puede dejar menos de 3** → un apagón, una emigración en bloque o un cierre
  de frontera no deja la reserva **inaccesible**, que es el fallo simétrico y el que más
  probablemente ocurra (§6.5, éxodo continuo).
- Con 5 firmantes y umbral 3: **máximo 2 por localidad ⇒ mínimo 3 localidades**, y el rol 5
  fuera del país. Es lo que hace que ambas condiciones se cumplan a la vez.

**Rotación (PROVISIONAL):**

- **Periódica:** cada **12 meses**, **escalonada — nunca más de 1 de los 5 en un mismo acto**.
  Rotar el quórum entero de golpe es el momento exacto en que nadie sabe qué clave es válida.
- **Disparada por evento** (cualquiera de estos, sin esperar al plazo): cese o cambio del titular
  del cargo · **salida del titular de la célula** (`exited` — el mismo hecho que registra D6) ·
  sospecha o constancia de compromiso de una clave · **designación del titular en la lista SDN**
  (verificada por el comité) · revocación de la licencia general que ampara el riel.
- **Rotar es generar clave nueva, JAMÁS traspasar la vieja al sucesor.** Una clave que se hereda
  con el cargo deja firmando a quien ya se fue, y eso no aparece en ningún registro: el sucesor
  cree que tiene una clave y en realidad tiene dos titulares. Es la forma de ST-d5.8 (el aval que
  no caduca) aplicada a una firma.

**Caducidad — se re-verifica cuando el sistema esté terminado (instrucción del propietario,
2026-07-16):** los tres valores se revisan **antes de la Etapa 0 de despliegue** y, en todo caso,
**cuando Fases 1–3 estén cerradas y exista una red real con miembros reales**. *Porque:* el
umbral y los roles solo se pueden calibrar contra una célula concreta — cuántos miembros tiene,
dónde están y quién puede sostener un cargo. Elegirlos hoy contra una red que no existe es
elegirlos contra una ficción. **Los `PROVISIONAL` de arriba se convierten en decisión del
propietario, o se sustituyen; no se ascienden por inercia ni porque «llevan meses ahí».**

## 3. Reconciliación spec↔código pendiente (manda el código)

Ya cazadas en TB.0; cada una se resuelve en su delta, por escrito:

- **§8.9 del anexo dice "reutilizar verbatim las taxonomías bilingües".** `constraints.md` M5
  y el rechazo codificado R3 dicen lo contrario, y tienen razón. **Manda M5.** La palabra
  "verbatim" del §8.9 es un error de lectura adversarial ya diagnosticado en R3. Se deroga
  explícitamente en `d9-herencia-scoping/spec.md`.
- **§8.9 dice "y los modos de calibración".** El anexo §3.7 lo matiza: el B2B opera
  típicamente en `paz`. Los modos son herencia **documentada**, no integración obligatoria
  en Fase 2; ningún nodo TB.* los exige. Va a Señalados (D10), no a `src/`.
- **`spec-ledger.md` §5 lista "no on-chain anchoring" como límite de alcance.** D2 lo deroga
  parcialmente: `anclar()` **emite un hash**; la publicación sigue fuera (N5). El límite
  upstream sigue vigente en su parte real (nada de smart contracts en la ruta de liquidación).

### El md5 del bloque firewall (TB.1 se equivocó; TB.2 lo deshace)

Al intentar apoyar D9 en el md5 del bloque firewall, TB.1 concluyó que el `5d693ec` de Fase 1
era falso y que el real era `758094a9…`. **Eso era un error de TB.1**, verificado y deshecho en
TB.2 (2026-07-15):

- **Cierto:** el bloque `BEGIN…END` **es** byte-idéntico en las seis capas C2C-VE (un solo
  grupo). La afirmación sustantiva de Fase 1 se sostiene.
- **Cierto también:** `test_cross_layer_taxonomy` **no** fija los bytes — fija el conjunto
  `FORBIDDEN_KEYS`, la equivalencia de comportamiento del tokenizador y el descenso de los
  escáneres. Ningún test calcula el md5. El N10 es real.
- **Falso — lo que TB.1 llamó «corrección»:** los dos md5 son **el mismo bloque** con distinto
  span. `5d693ecf1833fb760e173ee3db30a263` = bloque completo con el `\n` final (3023 bytes);
  `758094a99054feffa153c869ecf17d5b` = el mismo bloque con `.strip()` (3022 bytes). `5d693ec`
  es el prefijo de 7 caracteres del primero: **Fase 1 lo calculó bien.** El «3018 bytes» de
  TB.1 no corresponde a ninguna de las dos medidas.

**Canon (decisión humana, 2026-07-15):** el span es el bloque **completo, con el `\n` final** —
3023 bytes, md5 `5d693ecf1833fb760e173ee3db30a263`. Es el número que Fase 1 ya publicó, así que
**los artefactos de Fase 1 son correctos y no se tocan**.

**La lección, que sí se conserva:** el defecto no era el número, era que **un md5 publicado sin
declarar su span no es verificable** — dos lectores honestos del mismo bloque sacan dos números
y cada uno cree que el otro miente. Eso es lo que costó un nodo entero. Por eso AC-d9.1 fija el
span además del literal, y por eso el Señalado de Fase 1 pasa a ser «declarar el span junto al
número + añadir el test de byte-identidad a las seis capas», no «arreglar el número».

## 4. Log de divergencia con upstream (E4/TP.2)

El fork no escribe upstream. Divergencias introducidas por Fase 2, para el día que haya que
mergear:

| Cambio | Archivo upstream afectado | Reversible |
|---|---|---|
| `turnover_eur_cents` → `turnover_cents` | `src/ledger/mutual_credit_ledger.py`, goldens, tests | sí (rename mecánico) |
| `moneda` obligatoria en `params` | idem | sí |
| `ratification_kinds` += `member_exited`, `bridge_paused`, `bridge_resumed` | idem | sí |
| Taxonomía FX rechazada (D1) | nuevo | aditivo |
