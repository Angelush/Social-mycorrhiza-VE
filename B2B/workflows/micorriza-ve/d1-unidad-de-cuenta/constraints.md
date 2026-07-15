# Constraints — D1: unidad de cuenta

## MUST

- **C-d1.1 — `moneda` es parámetro de la célula, jamás de la obligación ni del saldo.**
  *Porque:* L1 (`sum(balance_cents)==0`) solo significa algo dentro de una unidad de cuenta.
  Poner moneda en la obligación obligaría a verificar L1 por partición y abriría la puerta a
  que alguien "resuelva" la partición con una tasa (N3).
- **C-d1.2 — `moneda` obligatoria, sin default implícito.** `params` sin `moneda` →
  `ValueError`. *Porque:* M10 heredado en espíritu — «rechazar, nunca recortar». Un default
  silencioso a USD haría que una célula VES mal configurada contabilizara como USD, que es
  destrucción de valor invisible.
- **C-d1.3 — `expira_en_dias` obligatorio ⇔ `moneda == "VES"`**, entero > 0; prohibido en
  células USD. *Porque:* el VES no es depósito de valor; una pista VES sin expiración es un
  pasivo inflacionario (H4). Y una célula USD que declara expiración está confundida sobre qué
  es — el error se rechaza, no se ignora.
- **C-d1.4 — Enteros de unidad mínima en todo importe; float prohibido.** *Porque:* M4 (ya
  heredado como M1/I3 upstream). D1 no cambia la aritmética; solo la etiqueta.
- **C-d1.5 — La taxonomía FX va en lista PRIVADA de d1, fuera del bloque compartido.**
  *Porque:* C-d9.3 — el patrón de TA.6/TA.7. Meterla en el bloque rompe el md5 `758094a9` y con
  él AC-10 y las seis capas C2C-VE.
- **C-d1.6 — El símbolo de moneda se deriva de `params["moneda"]`.** *Porque:* `render_statement`
  y `render_report` los lee un humano; un extracto con «€» en una célula USD es una mentira que
  el comité usará para decidir.

## MUST-NOT

- **N-d1.1 — Ninguna tasa de cambio en el motor, en ninguna forma**: ni campo, ni constante,
  ni parámetro, ni «solo de referencia», ni un spread por defecto. *Porque:* N3/I-VE1. No
  existe «el» tipo de cambio (brecha BCV/paralelo ~16,5%, viva y disputada); una tasa en
  código es una decisión política incrustada y un punto capturable.
- **N-d1.2 — Ninguna conversión ni mezcla automática USD/VES.** *Porque:* N4. Y aquí ni
  siquiera hace falta prohibirla: no hay forma de expresarla (§2 de la spec). La prohibición
  es el cinturón; la geometría son los tirantes.
- **N-d1.3 — El motor no modela inflación.** Ni indexación, ni ajuste, ni decay de saldos.
  *Porque:* P3 — modelarla exige una tasa, y eso es N-d1.1. La expiración es la única
  respuesta a la inflación que no representa el FX.
- **N-d1.4 — El motor no caduca nada automáticamente.** *Porque:* es puro y sin reloj (`ts` es
  entrada). Un tick que caduque obligaciones sería una operación de valor sin puerta humana
  (M8/I-VE5). Se declara y se hace visible; lo ejecuta el comité.
- **N-d1.5 — El motor jamás asume 1 USDT = 1 USD.** *Porque:* §2.4 del anexo — primas P2P de
  hasta ~40% en pánico. Los spreads de liquidación son decisión humana, jamás hardcodeados.

## PREFERENCIAS

- **P-d1.1 —** `expira_en` corto en células VES (convención documentada; el motor exige que
  exista, no cuánto vale). *Porque:* P3 — cuánto es corto depende de la inflación del mes, y
  el motor no la conoce.

## ESCALADA

- **E-d1.1 —** Si un delta futuro parece necesitar dos monedas en la misma célula → **parar**.
  Es I-VE2 y la respuesta es dos células (§3.1: «contabilidad separada»). Si persiste, E1.
- **E-d1.2 —** Reclasificación fiscal que obligue a representar la tasa (p. ej. SENIAT tratando
  cada compensación como pago en divisa gravable) → E3: pausar la fase, no incrustar la tasa.
