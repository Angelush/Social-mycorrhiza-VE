# Constraints — D4: multisig

## MUST

- **C-d4.1 — M9: verificación regulatoria/sanciones FECHADA antes de construir el delta.**
  `docs/verificaciones/AAAA-MM-DD-*.md`. *Porque:* todo el §5 del anexo está EN FLUJO tras la
  transición de enero 2026; las licencias son revocables y la responsabilidad es estricta. El
  diseño exige **re-verificar, no recordar**: un dato de hace seis meses no es información, es
  una suposición con fecha.
- **C-d4.2 — Los helpers son puros: sin red, sin claves, sin firmar, sin consultar saldo.**
  *Porque:* N9/I-VE4. Consultar la cadena exige red, y un motor con red y conocimiento del
  fondo hace el fondo capturable **a través del motor**.
- **C-d4.3 — El entregable principal es el DOCUMENTO de gobernanza**, no el código. *Porque:*
  §8.4 lo dice así, y porque el multisig lo operan humanos; el código solo evita que se escriba
  mal un número.
- **C-d4.4 — Al menos un firmante `diaspora` y al menos uno `local`.** *Porque:* todos locales
  = un solo punto de presión física (§6.2, matraqueo); todos diáspora = la célula pierde el
  control de su propio fondo.
- **C-d4.5 — Umbral ≥ 2.** *Porque:* un multisig de umbral 1 es una wallet con pasos extra —
  toda la propiedad que se busca (que ningún individuo pueda mover el fondo solo) desaparece.
- **C-d4.6 — El documento dice explícitamente qué NO cubre el multisig.** *Porque:* N10 — el
  riesgo Tether no es eliminable (§6.1); el fondo puede evaporarse sin que ninguna firma falle.
  Un documento que solo enumere garantías miente por omisión.

## MUST-NOT

- **N-d4.1 — El motor jamás custodia claves ni direcciones operativas.** *Porque:* custodia en
  código = **trono que capturar**. El resto de la arquitectura se esfuerza en no tener tronos
  (§4.6: sin tenedor central, células federadas, ningún hub); las claves del fondo construirían
  el único que falta.
- **N-d4.2 — El motor no firma, no propone firmas y no avisa de umbrales.** *Porque:* cada una
  de esas features le da red y conocimiento del fondo (C-d4.2).
- **N-d4.3 — Jamás concentrar la reserva en una sola dirección ni en una sola cadena.**
  *Porque:* Tether congela direcciones a petición de OFAC (§3.2). Una dirección congelada con
  toda la reserva dentro es el fondo perdido de un plumazo.
- **N-d4.4 — Ni exchange ni custodio tercero.** Autocustodia. *Porque:* §3.2 — el custodio
  tercero es exactamente la figura de MiCA-landia que aquí no existe y no se echa de menos.
- **N-d4.5 — Sin datos personales en las verificaciones fechadas.** *Porque:* N8 — el repo es
  público; una lista de firmantes con nombres reales es una lista de objetivos.

## PREFERENCIAS

- **P-d4.1 —** 2-de-3 para célula piloto; 3-de-5 al madurar. *Porque:* §3.2 — el umbral escala
  con lo que hay que perder.

## ESCALADA

- **E-d4.1 —** Si alguien propone que el motor consulte el saldo del fondo «solo lectura» →
  E1. Es N-d4.2: la red es la puerta, y una vez abierta ya no importa que fuera de lectura.
- **E-d4.2 —** Snapback o cambio material del régimen de sanciones → E3: pausar la fase; y la
  verificación fechada se rehace, no se recuerda (C-d4.1).
- **E-d4.3 —** Si un firmante previsto aparece en la lista SDN → parada dura; decisión humana
  con asesoría, jamás una excepción en código.
