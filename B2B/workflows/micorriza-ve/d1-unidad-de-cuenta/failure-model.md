# Failure model — D1: unidad de cuenta

## Modos de fallo (F-d1#)

- **F-d1.1 — El campo `moneda` en la obligación.** El ejecutor lee «pista VES» (§3.1) como
  «las obligaciones llevan pista» y añade `moneda` a la obligación. A partir de ahí L1 hay que
  verificarla por partición, `to_clearing_input` tiene que filtrar, y el solver debe correr dos
  veces. *Y entonces alguien pregunta cuánto vale el neto total* — que solo se responde con una
  tasa. **Este es el camino por el que el FX vuelve a entrar**, y empieza con una decisión que
  parece de esquema. *Mitigación:* C-d1.1; §2 de la spec.
- **F-d1.2 — El default silencioso a USD.** `params.get("moneda", "USD")`. Una célula VES mal
  configurada contabiliza como USD; los saldos son correctos aritméticamente y falsos
  semánticamente. Ningún test lo ve porque los números cuadran. *Mitigación:* C-d1.2 —
  obligatoria, sin default. *Detección:* AC-d1.2.
- **F-d1.3 — La expiración "de verdad".** El ejecutor implementa `expira_en_dias` caducando
  obligaciones dentro del motor, con `ts`. Ahora una operación de valor (extinguir una deuda)
  ocurre **sin `ratified_by`**, disparada por el paso del tiempo. Es M8/I-VE5 rota, y disfrazada
  de feature pedida por la spec. *Mitigación:* N-d1.4; §3 de la spec. *Detección:* AC-d1.4.
- **F-d1.4 — La tasa "solo de referencia".** «Guardemos la tasa BCV del día en `params` para
  que los exportes la muestren; no la usamos para nada.» En cuanto está en el estado, alguien
  la lee, y el sistema tiene una opinión sobre el tipo de cambio. *Mitigación:* N-d1.1 +
  `_TASA_KEYS` sobre `params`. *Detección:* AC-d1.5.
- **F-d1.5 — El goldens regenerado a ciegas.** El rename `turnover_eur_cents` → `turnover_cents`
  rompe los 4 goldens; el ejecutor los regenera ejecutando el código nuevo y commiteando la
  salida. Si el código nuevo tiene un bug, el golden lo **consagra**. *Mitigación:* revisar que
  el diff del golden sea **solo el nombre del campo**; ningún importe cambia. Es la lección de
  TA.6. *Detección:* AC-d1.6.
- **F-d1.6 — El símbolo olvidado.** Se renombra `turnover_eur_cents` pero `_fmt_eur` sigue
  imprimiendo «€». El esquema dice la verdad y el extracto que lee el comité miente.
  *Mitigación:* C-d1.6. *Detección:* AC-d1.7.
- **F-d1.7 — El reflejo TA.6.** El ejecutor, que conoce Fase 1, copia `ErrorDeBrechaAseguramiento`
  + escaneo de mezcla + campo `moneda` por-compromiso. Más código, más superficie, y una
  garantía **más débil** que la geometría. *Mitigación:* §2 de la spec lo dice explícitamente.

## Hallazgos de estrés (ST-d1#)

- **ST-d1.1 — «Irrepresentable» solo aguanta si nadie añade el campo.** La garantía de §2 no
  es un invariante verificado en runtime: es una propiedad del **esquema**. Un delta futuro que
  añada `moneda` a la obligación la destruye sin romper ningún test existente.
  *Mitigación:* AC-d1.1 la fija como test explícito (la obligación rechaza claves desconocidas),
  de modo que el intento falle en el nodo que lo produzca.
- **ST-d1.2 — El clearing es indiferente a la moneda, y eso es correcto.** `clearing_solver`
  no sabe de `moneda` y no debe saber: opera sobre un grafo de una sola célula
  (`cell_id` único, N2 upstream). *Verificado en TB.1:* `_validate` exige `cell_id` y
  `apply_clearing` comprueba `proposal["cell_id"] == state["cell_id"]` — **la barrera
  entre células ya existe y es la misma barrera entre monedas.** D1 no añade defensa aquí;
  hereda la que hay.
- **ST-d1.3 — Dos células, un padrón.** El mismo miembro humano puede estar en la célula USD y
  en la VES. Sus dos saldos **no se suman jamás**, y ninguna vista los muestra juntos.
  *Señalado:* si un día alguien construye un panel que los muestre lado a lado, la tentación
  de un total aparece — y un total exige una tasa. No hay mecanismo que lo impida en el motor
  (está fuera de él). Va a Señalados (D10).
- **ST-d1.4 — Auto-confirmación en la conservación.** El ledger verifica su propia conservación
  con su propia aritmética. *Mitigación:* heredada — AC-L3 recomputa independientemente y
  AC1 upstream usa el oráculo `networkx`. D1 no toca la aritmética, así que la defensa
  heredada sigue siendo válida sin cambios.

## Abierto — no fake-resolver (N10)

- **El motor no puede impedir que una célula VES incumpla su propia expiración.** Es sin reloj
  por diseño. Lo declara y lo hace visible en `cell_metrics` y en los exportes (D7); ejecutarlo
  es del comité. Señalado en D10.
- **«Corto» no está definido.** `expira_en_dias` exige que exista, no cuánto vale. Cuánto es
  corto depende de la inflación del mes, que el motor no conoce y no debe conocer (sería otra
  tasa). Señalado.
- **El crédito USD no es un dólar.** Si los miembros empiezan a tratarlo como si lo fuera, el
  riesgo es reputacional y no técnico. El branding (D10) es la única mitigación, y es parcial.
