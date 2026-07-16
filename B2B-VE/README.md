# B2B-VE — Circuito de crédito comercial, fork Venezuela (workstream B)

> Árbol de trabajo del fork venezolano del sistema **B2B** de crédito mutuo empresarial. El
> código upstream vive intacto en [`../B2B/`](../B2B/) como referencia; **todo el código del
> fork vive aquí**, en `B2B-VE/`. Las especificaciones (el *porqué* de cada decisión) viven en
> el sub-bundle [`../B2B/workflows/micorriza-ve/`](../B2B/workflows/micorriza-ve/); este README
> consolida, no reemplaza.

## Qué es — y qué no es

**Es un circuito de crédito comercial** de la cámara o gremio que lo opere: un registro de
compensación de obligaciones entre negocios que ya comercian entre sí. Cuando la ferretería le
debe a la distribuidora y la distribuidora al transportista, el sistema encuentra los ciclos y
los cancela — sin que se mueva un centavo de efectivo escaso.

**No es una moneda.** No es un activo criptográfico transferible. No es una inversión, no rinde
intereses, no es un banco y no custodia dinero de nadie. Un saldo aquí es crédito comercial
entre miembros que se conocen, dentro de la red y solo dentro de ella. Quien pida que el saldo
«salga» de la red está pidiendo otro producto — uno que este sistema se niega a ser por diseño
([N1, upstream](../B2B/workflows/micorriza/constraints.md)).

*Por qué la insistencia:* la criptomoneda estatal fallida (2018–2024) y el escándalo de su
regulador (Sunacrip, ~$3.000M desaparecidos) dejaron cicatrices — en Venezuela
cualquier «moneda nueva» huele a estafa, y con razón. El vocabulario de este repo es la primera
línea de defensa de esa frontera: si los documentos nunca prometen un activo, la petición de
convertirlo en uno llega más tarde y con menos legitimidad. Es una mitigación parcial y honesta:
la calle llamará a esto como quiera (Señalado №23).

## Filosofía heredada

Clearing determinista off-chain + crédito mutuo + confianza relacional + gestión activa. Las
invariantes del motor (L1–L6) y las institucionales (I1–I5) están definidas en el bundle
upstream — [`spec-ledger.md`](../B2B/workflows/micorriza/spec-ledger.md) y
[`constraints.md`](../B2B/workflows/micorriza/constraints.md) — y **aquí se referencian, no se
re-teclean** (una tabla copiada diverge, y la copia es la que se lee). La que gobierna todo:
**L1, `sum(balance_cents) == 0`** — la definición de crédito mutuo, verificada tras cada
operación y probada a escala de hiperinflación en
[`tests/test_conservacion_hiperinflacion.py`](tests/test_conservacion_hiperinflacion.py).

Los **modos de calibración C2C** (paz/tensión/desastre) son herencia **documentada, no
integrada**: el B2B opera típicamente en `paz` y ningún nodo de Fase 2 los exige
([D9 §1](../B2B/workflows/micorriza-ve/d9-herencia-scoping/spec.md)).

## Los deltas VE (D1–D10)

Qué asume el upstream que en Venezuela es falso, y qué delta lo corrige:
[`context.md` §1](../B2B/workflows/micorriza-ve/context.md). Cada delta tiene su directorio con
`spec / constraints / failure-model / acceptance` y el `DESIGN-TB*.md` del nodo que lo ejecutó:

| Delta | Qué cambió | Nodo | Especificación |
|---|---|---|---|
| D1 | Unidad de cuenta: mono-moneda por célula (`USD`/`VES`), mezcla **irrepresentable**; `expira_en_dias` bicondicional con VES; símbolo derivado, jamás `€` | TB.2 + TB.8b | [`d1-unidad-de-cuenta/`](../B2B/workflows/micorriza-ve/d1-unidad-de-cuenta/) |
| D2 | `anclar()`: raíz Merkle de un rango de eventos; prueba de inclusión para un árbitro sin entregarle el libro | TB.3 | [`d2-anclaje/`](../B2B/workflows/micorriza-ve/d2-anclaje/) |
| D3 | `scope` obligatorio en las vistas (`comite_credito`/`miembro`/`publico`); seudónimo estable con sal por célula | TB.4 | [`d3-visibilidad/`](../B2B/workflows/micorriza-ve/d3-visibilidad/) |
| D4 | Gobernanza del multisig de reserva: **documento** + helpers aritméticos; el motor no custodia claves | TB.8 | [`d4-multisig/`](../B2B/workflows/micorriza-ve/d4-multisig/) |
| D5 | `referencias_comerciales`: veteo relacional en esquema cerrado, sin puntuación posible | TB.5 | [`d5-referencias-comerciales/`](../B2B/workflows/micorriza-ve/d5-referencias-comerciales/) |
| D6 | `salida_con_saldo`: emigrar no es sanción; estado `exited` terminal, 4 resoluciones ratificadas | TB.6 | [`d6-d8-bordes/`](../B2B/workflows/micorriza-ve/d6-d8-bordes/) |
| D7 | `exportar_registros`: exporte contable limpio por miembro — la herramienta **defensiva** del miembro ante el fisco (declarar es la mejor defensa legal publicada) | TB.7 | [`d7-exportes/`](../B2B/workflows/micorriza-ve/d7-exportes/) |
| D8 | `puente_pausar()/puente_reanudar()`: la pausa del puente **no** detiene el crédito interno | TB.6b | [`d6-d8-bordes/`](../B2B/workflows/micorriza-ve/d6-d8-bordes/) |
| D9 | Herencia del firewall C2C: 7ª copia byte-idéntica del bloque compartido (md5 `5d693ecf1833fb760e173ee3db30a263`, 3023 bytes con `\n` final) | TB.2 | [`d9-herencia-scoping/`](../B2B/workflows/micorriza-ve/d9-herencia-scoping/) |
| D10 | Este README, el vocabulario y los property tests de cierre | TB.9 | [`d10-branding/`](../B2B/workflows/micorriza-ve/d10-branding/) |

**Unidad de cuenta:** la fuente única es
[`context.md` §2 «D1»](../B2B/workflows/micorriza-ve/context.md) y
[`d1-unidad-de-cuenta/spec.md`](../B2B/workflows/micorriza-ve/d1-unidad-de-cuenta/spec.md). Lo
esencial: USD es la unidad de cuenta del sistema (el VES no sirve como depósito de valor y un
saldo ES valor sostenido); una «pista VES» es una **célula aparte** con expiración obligatoria;
**el FX es irrepresentable en el motor** — no hay dónde escribir una tasa. La brecha cambiaria
del momento vive en la verificación fechada
([`docs/verificaciones/2026-07-15-cripto.md`](../docs/verificaciones/2026-07-15-cripto.md),
hallazgo 5), nunca en el código.

## Procedencia por módulo

| Módulo | Procedencia | Qué área lo tocó |
|---|---|---|
| `src/ledger/mutual_credit_ledger.py` | **Upstream modificado** | D1 (moneda, rename, `_fmt_cents`), D3 (scope/sal), D5 (walker de forma libre), D6 (`exited`), D8 (`puente_pausado`), TB.8b (puerta `proposal_moneda`) |
| `src/clearing/clearing_solver.py` | **Upstream modificado** | D1/TB.8b (`moneda` obligatoria en el input; símbolo derivado en `render_report`) |
| `src/ledger/anclaje.py` | **100% fork** | D2 (Merkle; no toca el ledger — `git diff` del ledger quedó vacío en TB.3) |
| `src/ledger/exportes.py` | **100% fork** | D7 (CSV/JSON del miembro; aditivo puro) |
| `src/gobernanza/multisig.py` | **100% fork** | D4 (keccak-256 propio, validación EIP-55/TRC-20, fórmula geográfica; **no importa el ledger**) |
| `src/firewall/herencia.py` | **Bloque C2C heredado byte a byte** + cabecera propia | D9 (el bloque es la 7ª copia; imports fuera del bloque) |
| `tests/`, `workflows/micorriza/evals/golden-set/` | Upstream extendido | cada nodo añadió los suyos; los 4 goldens son el piso de regresión |

## El seam bilingüe (E2) — dicho sin disimulo

Por decisión fechada ([`context.md` §2 «E2», 2026-07-15](../B2B/workflows/micorriza-ve/context.md)):
las API **nuevas** y los docs están en castellano; los identificadores B2B **existentes** quedan
en inglés (`state`, `debtor`, `balance_cents`, `ratified_by`, …). El resultado es un árbol
bilingüe permanente con firmas mixtas — `salida_con_saldo(state, member_id, ...)`. **Es feo y es
deliberado**: renombrar tocaría el piso de regresión de un motor de valor para un beneficio
estético, y un rename que cruce el scoping M5 es exactamente el fallo que M5 previene. El
renombrado total queda pospuesto a decisión explícita — «no ahora, y no por inercia».

## Señalados — lo que este sistema NO garantiza

Consolidado de los failure-models de D1–D9 más los hallazgos de ejecución (N10: se señala, no se
fake-resuelve; **nada de esta lista está resuelto**, y un Señalado «resuelto» en prosa sería
peor que uno abierto). Ordenados por **quién paga el fallo**, no por delta.

### Lo paga el miembro (el comerciante)

1. **El motor no autentica.** El `scope` es un contrato con quien llama, no un guardia: quien
   consiga invocar la vista con `comite_credito` ve todo. (F-d3.6)
2. **Tras la puerta del scope está el mapa de la red.** Saldos + referencias = el mapa del
   matraqueo si la puerta cae. El scope acota la salida; no cifra nada. (ST-d5.6)
3. **`member_statement` bajo `publico` es un oráculo de pertenencia:** preguntar por un miembro
   y recibir seudónimo confirma que está dentro. (ST-d3.5)
4. **Correlación entre salidas por seudónimo estable:** el seudónimo no cambia entre anclas —
   ésa es su función para el árbitro, y también su costo. (ST-d3.1)
5. **La agregación no anonimiza en células diminutas.** Con 5 miembros, «el total» ya señala.
   (ST-d3.3)
6. **Reclasificación fiscal del crédito mutuo.** El sistema es compliance-READY, no
   compliance-dependent: **no declara por nadie**, no calcula IGTF, no marca `gravable` — si el
   tratamiento cambia, la exposición es del miembro y su contador. La pregunta de fondo (¿la
   compensación sin transferencia de divisa es hecho imponible?) **no tiene respuesta pública
   hoy** (H1 de la verificación fechada). (§6.7, D7)
7. **Salida con obligaciones en vuelo — PREGUNTA ABIERTA (ST-d68.7):** la resolución de una
   salida es una **foto del saldo**, y lo que está en vuelo no es saldo todavía. Una salida
   `simple` ratificada con 3000 en vuelo deja al `exited` en −3000 **sin plan, sin avalista y
   sin ratificación** — y L1/L2 se conservan, así que la suite queda verde y nadie lo ve. Las
   dos salidas obvias están descartadas (prohibir salir con obligaciones abiertas lo veta
   AC-d68.10; que el aval cubra liquidaciones futuras sería una garantía permanente que nadie
   ratificó). **Es una decisión de spec pendiente del humano, no un descuido.** Está fijado en
   test para que sea decisión y no accidente.
8. **El aval no caduca.** `antiguedad_meses` es una foto del alta; un avalista que emigró sigue
   avalando. Caducarlo sería una operación de valor sin puerta humana (M8). (ST-d5.8)
9. **Puente pausado + saldo positivo = valor atrapado** hasta que el comité reanude o resuelva
   la salida por otra vía. La pausa protege a la red, no al que quería salir esa semana. (ST-d68.3)

### Lo paga el comité

10. **El comité de crédito es presionable; el multisig reparte la coerción, no la elimina.**
    3-de-5 sube el costo del ataque de una persona a tres — no lo baja a cero. (§6.2, ST-d4.1)
11. **Riesgo Tether: contraparte + congelamiento OFAC.** No eliminable desde este repo; la
    reserva puente vive en un activo que un tercero puede congelar. (§6.1, D4)
12. **Las etiquetas de localidad son opacas a propósito (L1/L2/L3)** — el motor comprueba la
    **forma** de la distribución de firmantes; que las etiquetas correspondan a lugares de
    verdad distintos y descorrelacionados **lo verifica el comité**, no el código. Tres barrios
    de Caracas etiquetados L1/L2/L3 pasan verde. (TB.8)
13. **Roles y rotación del multisig son PROVISIONALES — deuda de GOBERNANZA, no técnica.** Solo
    el umbral (3-de-5) es decisión del propietario; los cargos y la rotación son relleno
    declarado, y **una suite verde no dice nada sobre ellos** (el motor no los toca). No se
    presentan aquí como decididos porque no lo están: ver
    [`docs/gobernanza-multisig.md` §0](docs/gobernanza-multisig.md). (TB.8)
14. **El motor NO criba contra la lista SDN y no debe hacerlo** — diría «este firmante está
    limpio» sin poder sostenerlo. El cribado es del comité, con la lista del día. (M9)
15. **Referencias no verificadas:** un anillo de avales mutuos pasa limpio. El firewall de
    valores es de **forma, no de contenido** — «el hermano del dueño de la panadería de Chacao»
    es texto válido. (ST-d5.2, ST-d5.5)
16. **El score no necesita un campo nuevo:** basta inflar uno que ya existe (`credit_max` ×
    referencias). La defensa es el rastreo por AST en los tests — y la vigilancia humana en la
    revisión. (ST-d5.7)
17. **Salidas en cascada:** válidas una a una; solo el comité ve el conjunto. (ST-d68.2)
18. **El evento registra lo PEDIDO; el estado, lo DECIDIDO.** El payload de un evento conserva
    lo que el llamador pasó (verbatim, y `replay` lo preserva); el estado refleja lo que el
    motor aceptó. **Un auditor que lea solo payloads puede leer una pausa que nunca existió.**
    (TB.6b, hallazgo 2)

### Lo paga la red

19. **Cooptación política de una célula.** El cortafuegos es que no arrastre a las demás
    (células independientes); no hay defensa interna contra la captura de una. (§6.3)
20. **Cold-start con confianza erosionada por el éxodo.** El sistema presupone comerciantes que
    se conocen; el éxodo se llevó parte de ese tejido. (§6.4, ST-d5.3)
21. **La voluntad de cooperar no se fabrica.** Ningún mecanismo de este repo la produce. (§6.8)
22. **La marca temporal del ancla depende de una publicación externa.** La raíz prueba QUÉ,
    no CUÁNDO: el cuándo lo da publicarla en un medio fechado, fuera del motor. (ST-d2.1)
23. **El anclaje no impide el doble libro** — lo hace detectable si alguien compara. (ST-d2.2)
24. **Ledger y on-chain pueden divergir; no hay oráculo** que los reconcilie. (ST-d4.4, D6)
25. **El motor no puede impedir que una célula VES incumpla su expiración** operando fuera del
    registro. (ST-d1)
26. **«Corto» no está definido para `expira_en_dias`** — 30, 60, 90: decisión del comité, sin
    ancla empírica todavía. (D1 §3)
27. **Dos células (USD/VES), un padrón:** un panel que las sume exigiría una tasa — y eso es
    exactamente lo que no se puede escribir. No hay vista consolidada, a propósito. (ST-d1.3)
28. **El branding no sobrevive al contacto con la calle.** La gente llamará a esto «los dólares
    de la cámara». Lo que el vocabulario del repo controla es qué peticiones ganan legitimidad,
    no cómo habla la gente. (ST-d10.1)
29. **El seam bilingüe de E2** — permanente, pospuesto, no cerrado (ver arriba).
30. **Los modos C2C: herencia documentada, no integrada.** (D9 §1)
31. **La séptima copia del bloque firewall está acoplada por constante, sin test cross-árbol**
    (B2B-VE y C2C-VE son raíces pytest distintas que fijan el mismo literal/span/byte-count —
    la identidad entre árboles es por transitividad, no por un test que los cruce). (ST-d9.4)
32. **La colisión `veto`/`sancion` (M5) está evitada, no resuelta:** si una clave castellana
    nueva colisiona con la taxonomía heredada, se renombra la clave, jamás la taxonomía. (D9 §3)
33. **El md5 de Fase 1 (`5d693ec`) es correcto, pero se publicó sin declarar su span** — y eso
    hizo que un nodo entero lo declarara falso y propusiera reescribir 7 artefactos sanos. Un
    hash sin span no es verificable. Corregido declarando el span (bloque completo con `\n`
    final, 3023 bytes); las 6 capas C2C-VE tienen su test de byte-identidad desde TA.9.
    (ST-d9.6, ST-d9.4)
34. **La verificación regulatoria CADUCA por diseño:** los tests de D4 se pondrán rojos el
    **2026-09-15** (cripto) y el **2026-10-15** (sanciones). Cuando ocurra: **se re-verifica con
    fuentes primarias y firma del propietario** (`docs/verificaciones/`), no se le pone skip ni
    se borra el test. (C-d4.1, M9)

## Cómo correr la suite

```
cd B2B-VE && ../.venv-ve/bin/python -m pytest -q
```

Los 3 `skipped` del árbol upstream (`B2B/tests/test_clearing_solver.py`, cross-check contra
`networkx`, ausente a propósito en `.venv-ve`) **no son regresión y no se «arreglan»**.

## Verificación humana pendiente (AC-9)

Este README está sujeto al **gate humano AC-9**
([checklist](../B2B/workflows/micorriza-ve/d10-branding/evals/acceptance.md)): un humano lo lee
frase por frase y confirma que no promete nada que el código no haga. Es el único AC sin
máquina, y se dice en vez de fingir cobertura automática (ST-d10.3).
