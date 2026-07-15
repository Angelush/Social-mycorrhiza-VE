# Failure model — D4: multisig

## Modos de fallo (F-d4#)

- **F-d4.1 — El trono construido por conveniencia.** «Si el motor conoce la política, que
  guarde también la clave de vista / la semilla / una dirección de respaldo.» El sistema entero
  está diseñado sin tronos (§4.6); este delta es el único sitio donde construir uno es
  tentador, porque aquí sí hay algo que custodiar. *Mitigación:* N-d4.1/N9.
  *Detección:* AC-d4.2 (grep de material de clave + AST).
- **F-d4.2 — El helper que consulta.** `verificar_direccion` que hace una llamada RPC «para
  comprobar que existe». Ahora el motor tiene red: se cae en apagones, necesita un endpoint
  (capturable), y filtra qué direcciones le interesan a quien observe el tráfico.
  *Mitigación:* C-d4.2. *Detección:* AC-d4.3 (pureza con `socket` parcheado).
- **F-d4.3 — El umbral 1.** `verificar_umbral` acepta `{"umbral": 1, "total": 3}` porque
  `1 <= 3`. Un multisig de umbral 1 es una wallet: cualquier firmante mueve el fondo solo.
  Toda la propiedad buscada desaparece y el documento sigue diciendo «multisig».
  *Mitigación:* C-d4.5. *Detección:* AC-d4.1.
- **F-d4.4 — El multisig de una sola ciudad.** Tres firmantes, los tres en Valencia. Un solo
  operativo de presión los alcanza a los tres en una tarde (§6.2). El umbral no protege contra
  coerción correlacionada. *Mitigación:* C-d4.4. *Detección:* AC-d4.1.
- **F-d4.5 — La reserva en una dirección.** Todo el fondo en una TRC-20. Tether la congela a
  petición de OFAC y el fondo desaparece **sin que ninguna firma haya fallado** — la
  criptografía funcionó perfectamente y el dinero no está. *Mitigación:* N-d4.3 + el documento.
- **F-d4.6 — M9 saltado.** «La verificación de sanciones la hacemos al desplegar.» Se construye
  el delta sobre un régimen que puede haber cambiado; el fideicomisario US-person opera bajo
  una GL revocada. *Mitigación:* C-d4.1 — es **bloqueante**, no un checklist.
  *Detección:* AC-d4.5.
- **F-d4.7 — Los nombres reales en el repo.** El documento de gobernanza lista a los firmantes
  con nombre y apellido «para que quede claro». El repo es público: acaba de publicarse una
  lista de tres personas que controlan un fondo, con su ciudad. *Mitigación:* N-d4.5/N8 —
  alias y roles, jamás identidades. *Detección:* AC-d4.4.

## Hallazgos de estrés (ST-d4#)

- **ST-d4.1 — El multisig no protege contra la coerción, la reparte.** 2-de-3 significa que hay
  que presionar a dos, no a uno. Es una mejora cuantitativa, no una garantía. En un contexto de
  matraqueo (§6.2) esto importa decirlo: el fideicomisario de la diáspora es el firmante que
  está **fuera de alcance físico**, y por eso C-d4.4 lo exige. **Señalado.**
- **ST-d4.2 — La rotación es el punto débil operativo.** Rotar direcciones exige coordinar
  firmantes en un país con conectividad intermitente (§2.9). Un procedimiento que solo funcione
  con todos en línea a la vez fallará cuando se necesite. El documento debe contemplar rotación
  asíncrona. **Señalado**: es diseño operativo, no de código.
- **ST-d4.3 — Auto-confirmación del documento.** Un documento de gobernanza no tiene tests. Su
  «verificación» es que un humano lo lea. *Mitigación:* los helpers hacen ejecutable la parte
  aritmética (umbral/composición); el resto es gate humano (M1) — y se dice, en vez de fingir
  cobertura.
- **ST-d4.4 — El fondo como miembro tiene dos vidas.** En el ledger es un miembro con líneas
  (D6/ST-d68.1); on-chain es un multisig. **Nada garantiza que coincidan.** El ledger dice que
  el fondo absorbió −5000; que el USDT se moviera es fe en el comité. *Sin oráculo*, y fingir
  uno sería peor (mismo Señalado que D6). **Señalado.**

## Abierto — no fake-resolver (N10)

- Riesgo de contraparte Tether: no eliminable. Autocustodia, rotación y multi-riel lo mitigan
  parcialmente (§6.1).
- Congelamiento de direcciones a petición de OFAC: mitigado por no concentrar; no evitado.
- El multisig reparte la coerción, no la elimina (ST-d4.1).
- El saldo del ledger y el saldo on-chain pueden divergir; no hay oráculo (ST-d4.4).
- El documento de gobernanza se verifica leyéndolo (ST-d4.3).
