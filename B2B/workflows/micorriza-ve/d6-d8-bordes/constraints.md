# Constraints — D6+D8: bordes

## MUST

- **C-d68.1 — Las tres operaciones nuevas pasan por `_apply` y por `ratification_kinds`.**
  *Porque:* M8/I-VE5/I3. Una helper que mute el estado directamente se salta de una vez
  `ratified_by`, la monotonía de `ts`, el check de `paused`, el encadenado de hashes y los
  post-asserts L1/L2. La puerta de un solo sentido no admite puertas laterales.
- **C-d68.2 — L1 se conserva en toda salida.** `sum(balance_cents) == 0` después.
  *Porque:* es la definición de crédito mutuo. Un saldo que «desaparece» al irse su dueño es
  valor destruido en silencio — el fallo que M2/N4 existen para impedir.
- **C-d68.3 — `exited` es un estado terminal FUERA de la escalera sancionadora.** *Porque:*
  `expelled` es el último peldaño de las sanciones graduadas (inv. 5). Emigrar no es una
  sanción; confundirlos **marca a un emigrante como moroso**, y esa marca queda en la cadena y
  viaja (U1: jamás una marca).
- **C-d68.4 — `puente_pausado` es un campo distinto de `paused`.** *Porque:* `paused` mata toda
  mutación (inv. 8); el puente pausado no debe matar nada del crédito interno (I-VE7).
  Reutilizar el campo es la colisión semántica barata de prevenir y cara de depurar (F1/M7).
- **C-d68.5 — `absorcion_avalista` respeta las líneas del avalista (L2).** No cabe → rechazo.
  *Porque:* M6 heredada — flag/reject, jamás clamp. Un avalista empujado fuera de sus líneas
  «porque alguien se fue» es contagio, y el impago es contagioso (U2).
- **C-d68.6 — La `resolucion` es explícita, provista por el comité.** *Porque:* deducirla del
  signo del saldo sería que el motor decide cómo se resuelve una salida — con consecuencias
  sobre un avalista que no está en la sala.

## MUST-NOT

- **N-d68.1 — La pausa del puente NO detiene el crédito interno.** *Porque:* I-VE7/§8.8. USDT
  puede morir de un plumazo (§6.1, §6.6); si la pausa parara el crédito, el sistema habría
  acoplado su supervivencia a su pieza más frágil.
- **N-d68.2 — El motor no mueve USDT, ni toca rieles, ni direcciones, ni claves.** *Porque:*
  N9/I-VE4 + §3.2 («el núcleo solo registra la obligación saldada»). `liquidacion_puente`
  **registra** que se liquidó; no liquida.
- **N-d68.3 — Ningún spread ni tasa hardcodeados.** *Porque:* N-d1.1/§2.4 — ni USDT es un dólar
  perfecto (primas P2P de hasta ~40% en pánico); los spreads son decisión humana.
- **N-d68.4 — Un miembro `exited` no registra obligaciones nuevas, pero sus obligaciones
  abiertas SÍ se liquidan.** *Porque:* herencia literal — «sanctions never trap debt; paying
  what you owe is always legal».
- **N-d68.5 — `salida_con_saldo` no es reversible y no se le añade un `undo`.** *Porque:* mueve
  valor. Se corrige con asientos nuevos, como los asientos — no borrando la historia de una
  cadena append-only.

## PREFERENCIAS

- **P-d68.1 —** Reutilizar la maquinaria de `pause_cell`/`resume_cell` como plantilla del par
  del puente (P4: reutilizar antes que crear), **sin** reutilizar su campo (C-d68.4).

## ESCALADA

- **E-d68.1 —** Si la pausa del puente parece requerir detener algo del crédito interno →
  **parar**. Es I-VE7 y la interpretación es errónea (E5). Si persiste, E1.
- **E-d68.2 —** Snapback de sanciones o reclasificación que afecte al puente → E3: se pausa el
  puente (que para eso existe), no se pausa la red.
