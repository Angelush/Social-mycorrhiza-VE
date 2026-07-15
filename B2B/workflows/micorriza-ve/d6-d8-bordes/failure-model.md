# Failure model — D6+D8: bordes

## Modos de fallo (F-d68#)

- **F-d68.1 — La helper cómoda (el fallo que M8 nombra).** `def salida_con_saldo(state, ...):`
  que muta `state["members"][mid]["balance_cents"] = 0` y devuelve. Es la implementación más
  corta y **se salta de una vez** `ratified_by`, `ts` monótono, el check de `paused`, el
  encadenado de hashes y los post-asserts L1/L2. Ningún test heredado la caza porque los tests
  heredados no la conocen. *Mitigación:* C-d68.1. *Detección:* AC-d68.1 (la operación emite
  evento encadenado y `replay` la reconstruye — imposible si no pasó por `_apply`).
- **F-d68.2 — El saldo que se evapora.** `liquidacion_puente` pone el saldo a 0 y no mueve la
  contrapartida a ningún sitio. `sum(balance_cents) != 0`: **L1 rota, valor destruido en
  silencio**. *Mitigación:* C-d68.2 + los post-asserts heredados, que ya lanzan.
  *Detección:* AC-d68.2.
- **F-d68.3 — El emigrante marcado como moroso.** Se reutiliza `expelled` para las salidas
  «porque ya es terminal». La cadena registra para siempre que a quien se mudó a Bogotá lo
  **expulsaron**, y eso viaja a cualquier federación futura. *Mitigación:* C-d68.3 (`exited`
  fuera de la escalera). *Detección:* AC-d68.4.
- **F-d68.4 — El puente que mata la red (el fallo que I-VE7 nombra).** `puente_pausar` reutiliza
  `params["paused"]`. Al pausar el puente por un snapback, la célula entera deja de registrar
  obligaciones — **el crédito interno muere justo cuando más falta hace**. El sistema falla
  exactamente en el escenario para el que se diseñó. *Mitigación:* C-d68.4.
  *Detección:* AC-d68.5, que ejerce el flujo completo con el puente pausado.
- **F-d68.5 — El avalista atropellado.** `absorcion_avalista` empuja al avalista fuera de sus
  líneas y el código lo recorta o lo ignora. Contagio silencioso, y el impago es contagioso
  (U2). *Mitigación:* C-d68.5 + L2 heredada. *Detección:* AC-d68.3.
- **F-d68.6 — El motor que liquida.** «`liquidacion_puente` debería mandar el USDT.» Ahora el
  motor tiene claves, red y una dirección que congelar. *Mitigación:* N-d68.2/N9.
  *Detección:* AC-d68.7 (pureza + sin red).
- **F-d68.7 — La resolución deducida.** «Si el saldo es positivo, obviamente es liquidación.»
  El motor decide, sin comité, algo que afecta al fondo o a un avalista. *Mitigación:* C-d68.6.
- **F-d68.8 — El plan de pago que mueve el saldo.** `plan_de_pago` «reserva» o «provisiona» el
  saldo negativo. No: el plan de pago es un acuerdo **fuera** del motor; el saldo negativo sigue
  ahí porque **esa es la verdad**. *Mitigación:* §2 de la spec. *Detección:* AC-d68.2.

## Hallazgos de estrés (ST-d68#)

- **ST-d68.1 — El fondo es un miembro.** Para que `liquidacion_puente` conserve L1, la
  contrapartida tiene que ir a **alguien**. Ese alguien es el fondo de garantía, modelado como
  un miembro más de la célula con sus propias líneas. *Consecuencia no obvia:* el fondo puede
  quedarse sin línea, y entonces la salida se rechaza. **Correcto**: es la verdad (el fondo no
  da abasto), y lo que hay que hacer es capitalizarlo, no recortar el check. Se fija en
  AC-d68.6.
- **ST-d68.2 — Salidas en cascada.** Se van tres miembros a la vez, cada uno absorbido por el
  siguiente. Cada operación es válida por separado; el orden importa. *Mitigación:* ninguna en
  el motor — cada salida se ratifica por separado y L1/L2 se verifican en cada una. Es el
  comité quien ve la cascada. **Señalado.**
- **ST-d68.3 — El puente pausado y el fondo lleno.** Con el puente pausado, un saldo positivo
  no puede salir. El miembro se va igual (se muda), y su saldo positivo se queda vivo en una
  célula donde ya no opera. *Sin mecanismo:* es la realidad del snapback. El comité decide si
  usa `plan_de_pago` inverso o espera. **Señalado.**
- **ST-d68.4 — `exited` y el clearing.** `to_clearing_input` incluye a todos los miembros. Un
  `exited` con obligaciones abiertas debe seguir apareciendo (sus deudas se compensan), pero no
  puede recibir obligaciones nuevas. *Verificado en TB.1:* el filtro de estado ya vive en
  `record_obligation` (`status not in {"active","warned","line_reduced"}` → raise), así que
  `exited` queda excluido **automáticamente** al añadirlo fuera de ese conjunto. Cero código
  nuevo; se documenta para que nadie lo «arregle».

## Abierto — no fake-resolver (N10)

- Salidas en cascada: válidas una a una, el efecto conjunto lo ve el comité (ST-d68.2).
- Puente pausado + saldo positivo atrapado: es la realidad del snapback (ST-d68.3).
- El motor registra la liquidación; que el USDT se haya movido de verdad es fe en el comité.
  **No hay oráculo**, y fingir uno sería peor.
- Riesgo Tether no eliminable (§6.1): autocustodia, rotación y multi-riel lo mitigan
  parcialmente. La pausa es la respuesta estructural, no la solución.
