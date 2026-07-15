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

### Corrección a Fase 1 (el código volvió a mandar)

Al intentar apoyar D9 en el md5 del bloque firewall, TB.1 verificó los dos extremos:

- **Cierto:** el bloque `BEGIN…END` **es** byte-idéntico en las seis capas C2C-VE (3018 bytes,
  un solo grupo). La afirmación sustantiva de Fase 1 se sostiene.
- **Falso:** el md5 **no** es `5d693ec` sino **`758094a99054feffa153c869ecf17d5b`**; y
  `test_cross_layer_taxonomy` **no** fija los bytes — fija el conjunto `FORBIDDEN_KEYS`, la
  equivalencia de comportamiento del tokenizador y el descenso de los escáneres.

El valor equivocado sobrevivió TA.4→TA.8 propagándose por `DESIGN-TA4/5/6/7`,
`C2C-VE/README.md` y los comentarios de `membrana.py`/`aseguramiento.py` — **porque ningún test
lo calculaba**. Es un N10 en su forma pura: una garantía afirmada en prosa, sin mecanismo, que
solo se cayó cuando otro workstream intentó apoyarse en ella.

**Qué hace TB.1 con esto:** corrige el número en este sub-bundle y convierte la byte-identidad
en test (AC-d9.1, que calcula el md5 dentro del test). **Qué NO hace:** tocar los artefactos de
Fase 1 — sería alcance colado en un nodo de specs, sin gate. Va a Señalados (D10) y queda como
nodo pendiente de Fase 1.

## 4. Log de divergencia con upstream (E4/TP.2)

El fork no escribe upstream. Divergencias introducidas por Fase 2, para el día que haya que
mergear:

| Cambio | Archivo upstream afectado | Reversible |
|---|---|---|
| `turnover_eur_cents` → `turnover_cents` | `src/ledger/mutual_credit_ledger.py`, goldens, tests | sí (rename mecánico) |
| `moneda` obligatoria en `params` | idem | sí |
| `ratification_kinds` += `member_exited`, `bridge_paused`, `bridge_resumed` | idem | sí |
| Taxonomía FX rechazada (D1) | nuevo | aditivo |
