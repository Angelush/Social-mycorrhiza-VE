# Arquitectura — B2B-VE

> Extiende [`../micorriza/architecture.md`](../micorriza/architecture.md). La clasificación
> multi-especie **se mantiene íntegra**: sigue siendo un sistema que se clasifica por
> componente, jamás monolíticamente. Lo que sigue son los deltas.

## Clasificación por componente — corregida para VE

| Componente | Naturaleza | Cambio VE | Delta |
|---|---|---|---|
| Capa 0 — la célula | `[HUMANO]` | **La célula ES la cámara/gremio/asociación existente**, no una cooperativa registrada. Registrar = legibilidad ante un Estado parasitario + blanco de matraqueo. La formalidad es un **dial**, no un default (§3.6) | — |
| Capa 1 — solver de clearing | `[DETERMINISTA]` | **Sin cambio.** Intocable. Ni LLM ni smart contract en la ruta de liquidación | — |
| Ledger de crédito mutuo | `[DETERMINISTA]` | Unidad de cuenta USD; célula mono-moneda; cadena de hashes ascendida a evidencia anclable; saldos con scope | D1, D2, D3 |
| Capa 2 — matcher | `[ESTOCÁSTICO/LLM]` | **Fuera de Fase 2.** Sigue siendo Tool-assistant, jamás sobre valor | — |
| Capa 3 — federación | `[ESTÁNDAR]` | Etapa 3 (18+ meses). Reputación portable solo con consentimiento **y** si el modo vigente lo permite (U4) | — |
| Capa 4 — puente fiat | `[COMPLIANCE]` | **Se invierte:** de "EMT autorizada bajo MiCA" a **USDT + rieles alternos** (Zelle, efectivo, Pago Móvil), agnóstico de riel en los bordes. Y estrena botón de pausa | D6, D8 |
| Fondo de garantía | *(nuevo)* `[HUMANO + CRIPTO]` | **Multisig 2-de-3 / 3-de-5.** El escrow criptográfico sustituye al banco de confianza que no existe. El motor no custodia claves: solo verifica | D4 |
| Veteo / líneas | `[HUMANO]` | De estados financieros auditados a **veteo relacional**. Sigue sin score (N2) | D5 |
| Scoring de crédito | `[ESTOCÁSTICO assist]` | **Eliminado, no degradado.** El upstream lo dejaba como adviser con gate humano (RGPD Art. 22). Aquí no existe: el propio ledger es el expediente, visible solo al comité (§3.4) | D5 |

## Dónde cripto gana su sueldo (y dónde no)

El upstream minimizó cripto por razones **UE-contingentes** (MiCA cobra caro el token, la
banca funciona). En VE esos argumentos se invierten para los **rieles** y se mantienen para el
**token**. Cuatro usos, y solo cuatro:

1. **Puente de liquidación** (USDT): desequilibrios persistentes, salidas, entre células. D6.
2. **Reserva en multisig**: el escrow que reemplaza al banco de confianza. D4.
3. **Anclaje de hashes**: evidencia inviolable donde no hay juez. D2.
4. **Puente diáspora**: remesas → fondo/patrocinio. Sin análogo español. (Fuera de Fase 2.)

**Y nada más.** Cero tokens. El clearing sigue off-chain y determinista. Cripto como
fontanería, nunca como promesa.

## La frontera que no se mueve

El upstream la formula así: automatizar la capa combinatoria **sin destruir la relacional**.
En VE hay presión para cruzarla en la dirección contraria a la europea: como no hay
tribunales, es tentador que el motor arbitre. **No.** El motor produce evidencia que nadie
puede reescribir (D2) y la entrega a humanos que juzgan. Entorno más hostil ⇒ la frontera se
mueve **menos**, no más.

## Topología: dónde vive el código

Fase 1 creó el árbol `C2C-VE/` (copia de `C2C/{src,tests}`), dejando `C2C/` intacto como
referencia upstream (TA.2). **Fase 2 hace lo mismo:** TB.2 crea `B2B-VE/` a partir de
`B2B/{src,tests}` + goldens; `B2B/` queda intacto como referencia.

*Porque:* el bundle upstream `B2B/workflows/micorriza/` es la verdad heredada y su suite es el
piso de regresión (AC-1). Un fork que edita el árbol upstream in-place pierde la referencia
contra la que comparar, y con ella la capacidad de responder "¿esto lo rompimos nosotros?".

**Ojo con la asimetría respecto a Fase 1:** en C2C-VE el árbol nuevo se castellanizó entero
(TA.3). En B2B-VE **no** — E2 lo pospuso (`context.md` §2). `B2B-VE/` será un árbol bilingüe:
código heredado en inglés, APIs nuevas en castellano.

## El harness de construcción (cómo construimos ESTO)

Especie 1b — Coding Harness. Humano gestiona, el juicio es el gate. Revisor un tier por encima
del ejecutor. Concreción en este fork (heredada de TA.5–TA.8, 4/4 verdes):

- **Specs de invariantes y scoping M5 → modelo tope.** El eslabón más débil no es el código:
  es una spec de invariante mal leída. TB.1 se escribió íntegro sin fan-out por eso.
- **Tests mecánicos con contrato de firmas fijado → fan-out a modelos gratis**, con revisión
  del modelo tope. El contrato se fija ANTES de delegar.
- Cada nodo cierra con suite verde + commit (M2/M11).
