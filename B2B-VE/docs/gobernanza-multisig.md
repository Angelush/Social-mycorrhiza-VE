# Gobernanza del multisig de reserva — célula B2B-VE

> **Entregable principal de D4 (nodo TB.8).** El código de `src/gobernanza/multisig.py` es lo
> accesorio: solo evita que se escriba mal un número aquí. **El multisig lo operan humanos.**
>
> **Este documento no tiene tests, y su verificación es que un humano lo lea** (ST-d4.3). Los
> helpers hacen ejecutable la parte aritmética (umbral, composición, distribución); el resto es
> gate humano. Se dice, en vez de fingir cobertura.
>
> **N8 aplicado, sin excepciones cómodas:** aquí hay **cargos y etiquetas opacas, jamás nombres,
> jamás ciudades**. El repo es público. Una lista de quién controla el fondo, con su ciudad, es
> una lista de objetivos.

---

## 0. LEA ESTO ANTES QUE NADA: los tres valores NO valen lo mismo

**La procedencia de cada valor es parte del valor.**

| Decisión | Valor | Procedencia | Estado |
|---|---|---|---|
| **Umbral** | **3 de 5** | **Propietario del fork, 2026-07-16** | ✅ **DECIDIDO** |
| Roles firmantes | los 5 cargos de §2 | **Relleno de Claude (Opus)** | ⚠️ **PROVISIONAL** |
| Rotación | 12 meses escalonada + disparadores (§4) | **Relleno de Claude (Opus)** | ⚠️ **PROVISIONAL** |

**Solo el umbral es una decisión de gobernanza.** Los otros dos los inventó Claude por
**instrucción explícita del propietario** el 2026-07-16 («inventa las demás para seguir con el
desarrollo»), para no dejar el nodo bloqueado. **No son decisiones: son andamios con forma de
decisión.**

**Qué hacer con ellos:**

- **NO se ascienden a decisión por inercia** — ni porque lleven meses en el archivo, ni porque
  la suite esté verde. **La suite verde no dice absolutamente nada sobre ellos:** el motor no
  custodia claves (N9), no los toca, y no puede tocarlos. Viven en prosa, y ahí se ven.
- **Se re-verifican con el propietario antes de la Etapa 0 de despliegue** y, en todo caso,
  **cuando exista una red real con miembros reales**. Solo se pueden calibrar contra una célula
  concreta: cuántos miembros tiene, dónde están, quién puede sostener un cargo. Hoy están
  elegidos contra una ficción.
- O el propietario los hace suyos, o los sustituye. **Lo que no puede pasar es que nadie
  recuerde que hubo que elegirlos.**

*Por qué este aviso ocupa el primer sitio del documento en vez de una nota al pie:* un valor
inventado y uno decidido son **indistinguibles dentro de seis meses** si nadie escribió cuál fue
cuál. Es el mismo fallo que las verificaciones fechadas de `docs/verificaciones/` existen para
prevenir, y la misma razón por la que la firma de `2026-07-15-sanciones.md` dice **cómo** se
produjo en vez de ser una firma limpia. Este es el documento con el que un comité decide dónde
pone su dinero: es exactamente el sitio donde un andamio se lee como decisión.

---

## 1. Umbral: 3 de 5 ✅ DECIDIDO

Tres firmas de cinco abren la reserva.

`verificar_umbral()` **no valida el número: valida la fórmula**, y sigue aceptando el 2-de-3 de
célula piloto (P-d4.1). Que el código solo aceptara 3-de-5 sería hornear una decisión de
gobernanza en el motor. **El helper valida; este documento registra la elección.**

Lo que el umbral **no** hace: **no protege contra la coerción — la reparte** (ST-d4.1). 3-de-5
significa que hay que presionar a tres personas, no a una. Es una mejora cuantitativa, no una
garantía. En un contexto de matraqueo (§6.2) esto hay que decirlo, y por eso existe el rol 5.

---

## 2. Los cinco cargos ⚠️ PROVISIONAL — relleno de Claude, no decisión

**Cargos, jamás nombres.** La regla no distingue aunque las designaciones sean públicas.

1. **Coordinación del comité de crédito**
2. **Tesorería de la célula**
3. **Auditoría interna** — miembro **fuera** del comité de crédito
4. **Representación de miembros** — elegida por asamblea, **fuera** del comité
5. **Custodia externa** — fuera de la operación diaria y **fuera del país** (rol `diaspora`)

*El razonamiento, para que quien los sustituya sepa qué no perder:* con 3 de 5, tres firmas
abren la reserva. Si los cinco cargos fueran capturables por la misma vía —todos del comité,
todos de la misma directiva— el umbral sería **decorativo**: quien capture esa vía tiene tres
firmas. Los cargos 3, 4 y 5 existen para que **ninguna captura de una sola función alcance el
quórum**. `verificar_umbral()` rechaza cargos duplicados por esa razón: dos firmantes con el
mismo cargo son una sola función con dos firmas.

**Requisito que M9 manda a este documento** (`2026-07-15-sanciones.md`, hallazgos 1 y 5 —
**esto no es relleno y no se negocia**): **ningún firmante puede estar designado en la lista
SDN**, y **esa comprobación es del comité, no del motor**. El motor no criba contra la SDN y no
debe: diría «este firmante está limpio» sin poder sostenerlo, que es un juicio de cumplimiento
con firma de software. El cargo 5 es probablemente *US person* → responsabilidad estricta, nada
que toque GoV/PdVSA/designados. Eso no lo resuelve el código.

---

## 3. Distribución geográfica — **esta parte NO es opinión**

Sale de la aritmética del umbral, no del criterio de nadie. **Si se rehacen los cargos de §2,
esto se conserva.**

```
máx. firmantes por localidad ≤ umbral − 1        ninguna localidad concentra el quórum
total − máx. por localidad   ≥ umbral            perder una localidad no deja bajo el quórum
```

- **3-de-5 → máximo 2 por localidad, mínimo 3 localidades.**
- (2-de-3 → máximo 1 por localidad, mínimo 3 localidades.)

Hacen falta **las dos** condiciones, porque son **fallos simétricos**:

| Fallo | Qué lo causa | Lo cubre |
|---|---|---|
| La reserva **se abre** sin quórum legítimo | una redada, una detención o un allanamiento alcanzan a tres firmantes en una tarde | máx. por localidad ≤ umbral − 1 |
| La reserva queda **INACCESIBLE** | un apagón, una emigración en bloque, un cierre de frontera | total − máx. ≥ umbral |

**El segundo es el más probable** (§6.5, éxodo continuo) y el que siempre se olvida, porque
«perder el fondo» suena a robo y no a que nadie contesta el teléfono. Que los dos umbrales caigan
de la misma fórmula es la señal de que la restricción no es una preferencia.

**`localidad` es una etiqueta OPACA** (`L1`, `L2`, `L3`), sin semántica geográfica. El comité
sabe qué es L1; este repo no, y no le hace falta para la aritmética.

> **Señalado — el límite de lo anterior, dicho:** el motor **no puede saber** que dos etiquetas
> distintas son dos lugares realmente descorrelacionados. Quien ponga `L1/L2/L3` a tres barrios
> de Caracas pasa la verificación en verde y tiene un multisig de una sola ciudad. **El motor
> comprueba la aritmética; que las etiquetas correspondan a lugares que no caen juntos es del
> comité.** Un test verde aquí no es una garantía: es una condición necesaria.

---

## 4. Rotación ⚠️ PROVISIONAL — relleno de Claude, no decisión

- **Periódica: cada 12 meses, escalonada — nunca más de 1 de los 5 en un mismo acto.** Rotar el
  quórum entero de golpe es el momento exacto en que nadie sabe qué clave es válida.
- **Disparada por evento** (sin esperar al plazo): cese o cambio del titular del cargo · salida
  del titular de la célula (`exited`, el mismo hecho que registra D6) · sospecha o constancia de
  compromiso de una clave · **designación del titular en la lista SDN** (verificada por el
  comité) · revocación de la licencia general que ampara el riel.
- **Rotar es generar clave nueva, JAMÁS traspasar la vieja al sucesor.** Una clave que se hereda
  con el cargo deja firmando a quien ya se fue, y eso **no aparece en ningún registro**: el
  sucesor cree que tiene una clave y en realidad tiene dos titulares. Es ST-d5.8 (el aval que no
  caduca) aplicado a una firma.

> **Señalado (ST-d4.2) — la rotación es el punto débil operativo.** Rotar exige coordinar
> firmantes en un país con conectividad intermitente (§2.9). **Un procedimiento que solo funcione
> con los cinco en línea a la vez fallará justo cuando se necesite.** La rotación tiene que poder
> hacerse **asíncrona**. Esto es diseño operativo, no de código, y está sin resolver.

---

## 5. Custodia y reparto de la reserva

- **Autocustodia. Ni exchange, ni custodio tercero** (N-d4.4). El custodio tercero es
  exactamente la figura de MiCA-landia que aquí no existe — el escrow criptográfico **sustituye
  al banco de confianza que no hay** (§3.2).
- **Jamás toda la reserva en una sola dirección ni en una sola cadena** (N-d4.3). Tether congela
  direcciones a petición de OFAC: una dirección congelada con todo el fondo dentro es el fondo
  entero perdido de un plumazo, **sin que ninguna firma haya fallado**.
- El motor **no consulta la cadena y no tiene red**. `verificar_formato_direccion()` comprueba el
  checksum (TRC-20 base58check, ERC-20 EIP-55) y **nada más**: no afirma que la dirección exista
  ni que tenga saldo. Comprobarlo exigiría red, y un motor con red y conocimiento del fondo hace
  el fondo capturable **a través del motor**.

---

## 6. Qué NO cubre este multisig

Un documento que solo enumere garantías **miente por omisión** (C-d4.6/N10), y este es el
documento con el que un comité decide dónde pone su dinero.

- **El riesgo de contraparte Tether no es eliminable** (§6.1). El fondo puede evaporarse **sin
  que ninguna firma falle**: la criptografía funcionó perfectamente y el dinero no está.
  Autocustodia, rotación y multi-riel lo mitigan **parcialmente**. No lo evitan.
- **El congelamiento de direcciones a petición de OFAC** está mitigado por no concentrar. **No
  está evitado.**
- **La coerción está repartida, no eliminada** (ST-d4.1).
- **El saldo del ledger y el saldo on-chain pueden divergir, y no hay oráculo** (ST-d4.4). En el
  ledger el fondo es un miembro con líneas; on-chain es un multisig. **Nada garantiza que
  coincidan.** El ledger dice que el fondo absorbió −5000; que el USDT se moviera de verdad es
  **fe en el comité**. Fingir un oráculo sería peor que no tenerlo.
- **El motor no criba contra la lista SDN** (M9, hallazgo 5). Es una decisión, no un olvido.
- **La distribución geográfica se verifica en la forma, no en el territorio** (§3).
- **Este documento se verifica leyéndolo** (ST-d4.3).
- **Dos de sus tres valores son provisionales** (§0). No es deuda técnica: es **deuda de
  gobernanza**.

---

## 7. Procedencia

- **Umbral 3 de 5:** propietario del fork, 2026-07-16.
- **Cargos y rotación:** Claude (Opus), 2026-07-16, por instrucción del propietario. Ver §0.
- **Marco de sanciones:** `docs/verificaciones/2026-07-15-sanciones.md` — **caduca 2026-10-15**.
- **Marco cripto/fiscal:** `docs/verificaciones/2026-07-15-cripto.md` — **caduca 2026-09-15**.

**Las verificaciones caducan de verdad, no de boca:** `test_d4_multisig.py::test_acd40_*` **se
pone rojo** cuando pasa la fecha. Si eso ocurre, **se re-verifica; no se borra el test**. Un dato
de hace seis meses no es información: es una suposición con fecha.
