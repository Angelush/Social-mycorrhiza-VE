# Failure model — D9: herencia con alcance

> Revisión hostil de la spec de D9. Lo que un ejecutor competente, leyendo el anexo §8.9 de
> buena fe, haría mal.

## Modos de fallo (F-d9#)

- **F-d9.1 — El paciente muerto (el modo de fallo principal).** El ejecutor lee §8.9
  («reutilizar verbatim las taxonomías bilingües»), copia las cinco listas a B2B-VE y aplica
  `_contains_forbidden_key` a los payloads del ledger. Resultado: `moneda` (D1), `saldo`,
  `credito` y `deuda` quedan **prohibidos en el motor de crédito mutuo**. El sistema no puede
  representar su propio dominio. *Detección:* AC-10 (las claves nucleares deben ser
  ADMITIDAS). *Mitigación:* M5, C-d9.2, §1 de la spec.
  **Este fallo es "verde" hasta que se prueba el caso positivo:** un firewall que rechaza todo
  pasa cualquier test que solo compruebe rechazos. Por eso AC-10 prueba la ADMISIÓN, no el
  rechazo. Un test suite que solo verifique «X se rechaza» es exactamente la forma que este
  fallo tiene de sobrevivir.
- **F-d9.2 — La colisión dormida.** D5 introduce `referencias_comerciales` y alguien nombra
  una clave `veto_del_comite` o `sancion_aplicada`. `FORBIDDEN_KEYS` contiene `veto` y
  `sancion`, el matching es token-exacto, y la clave se rechaza — en el delta cuyo propósito
  **es** el veteo. *Detección:* AC-d9.4. *Mitigación:* C-d9.5 (auditar antes de fijar),
  N-d9.1 (se renombra la clave, jamás la taxonomía).
- **F-d9.3 — La taxonomía metida dentro del bloque.** El ejecutor necesita una taxonomía B2B
  nueva (p. ej. la FX de D1) y la mete dentro del bloque compartido «porque ahí están las otras
  listas». *Detección:* **AC-d9.1, y solo AC-d9.1.** Verificado en TB.1: nada más lo cazaría —
  `test_cross_layer_taxonomy` comprueba el conjunto `FORBIDDEN_KEYS` y el comportamiento del
  tokenizador, no los bytes; una lista **extra** dentro del bloque los deja a ambos intactos.
  *Mitigación:* C-d9.3 — patrón establecido en TA.6/TA.7.
- **F-d9.4 — La relajación local.** Colisiona `sancion`, y el ejecutor "arregla" quitando
  `sancion` de `FORBIDDEN_KEYS` en la copia B2B-VE. Ahora hay dos taxonomías de vigilancia
  divergentes, el md5 miente, y C2C-VE tiene un agujero que nadie introdujo allí.
  *Mitigación:* N-d9.1 + C-d9.1.
- **F-d9.5 — El firewall decorativo.** Se hereda el bloque, se deja el módulo importado y no
  se llama desde ningún sitio. Todos los tests pasan (no rechaza nada porque no corre) y el
  repo aparenta una defensa que no existe. *Detección:* AC-d9.5 exige que D5 demuestre el
  rechazo end-to-end sobre su superficie real. *Mitigación:* C-d9.4 nombra la superficie.
- **F-d9.6 — La herencia por analogía.** «Ya que heredamos el firewall, heredemos también los
  modos, que §8.9 los nombra.» Añade un eje de configuración entero a un motor que opera en
  `paz` y que ningún nodo del grafo pidió. *Mitigación:* §1 punto 2; va a Señalados (D10).

## Hallazgos de estrés (ST-d9#)

- **ST-d9.1 — Las dos mitades de M5 no son simétricas.** La formulación de M5
  («hereda vigilancia/identidad; jamás mercado/reciprocidad») invita a leer que la primera
  mitad es segura. No lo es: `veto`/`sancion`/`penalizacion` son vigilancia en C2C y
  gobernanza en B2B. *Hueco encontrado en TB.1 → cerrado* en `spec.md` §3 con la distinción
  computado-vs-ratificado, y en C-d9.5.
- **ST-d9.2 — El scoping por taxonomía es insuficiente; hace falta scoping por superficie.**
  Aun con las listas correctas, aplicar el escáner al sitio equivocado (esquemas cerrados)
  solo puede hacer daño. *Hueco encontrado en TB.1 → cerrado* en C-d9.4.
- **ST-d9.3 — Auto-confirmación.** El test del md5 lo escribe quien copia el bloque; si copia
  mal y calcula el md5 de su propia copia, coincide consigo mismo. *Mitigación:* AC-d9.1 fija el
  literal `5d693ecf1833fb760e173ee3db30a263` **verificado sobre las seis capas C2C-VE**, no un
  md5 recalculado aquí. El valor esperado es un dato de entrada, jamás una salida del propio
  nodo — **y el span tampoco**.
- **ST-d9.6 — Ajustar la convención hasta que cuadre (ya pasó, en TB.1).** Un md5 sin span
  declarado admite dos respuestas honestas: con `\n` final da `5d693ec…`, con `.strip()` da
  `758094a9…`. TB.1 extrajo con la segunda, no encontró el número de Fase 1, y concluyó que
  Fase 1 mentía — casi hace reescribir siete artefactos correctos. *Mitigación:* el span es
  parte de la constante (C-d9.1) y AC-d9.1 comprueba el byte-count además del md5, para que un
  cambio de convención falle distinto que un cambio de contenido. **La forma general del fallo:
  cuando el mecanismo y la afirmación discrepan, el sospechoso por defecto es el mecanismo
  nuevo, no el artefacto que lleva cinco nodos en pie.**
- **ST-d9.4 — Deriva futura.** Alguien edita el bloque en C2C-VE (siete copias ahora) y
  actualiza seis. La séptima queda huérfana y B2B-VE diverge en silencio. *Mitigación:* AC-d9.1
  corre en la suite B2B-VE contra el literal; el fallo aparece en el nodo que lo produjo.
  *Asimetría a decir en voz alta:* B2B-VE tendrá el test de md5 y **las seis capas C2C-VE no**
  — allí la byte-identidad sigue siendo prosa. La séptima copia está mejor defendida que las
  seis originales.
  *Señalado:* no hay test que corra **a la vez** sobre los dos árboles — las suites son
  independientes (`cd C2C-VE && pytest` / `cd B2B && pytest`). El acoplamiento es por
  constante literal y revisión humana. **No fake-resuelto** (N10): va a Señalados en D10.

## Abierto — no fake-resolver (N10)

- **La séptima copia.** El md5 compartido entre dos árboles de fork con suites independientes
  es una convención sostenida por una constante y por quien revise. Un test cross-árbol exigiría
  que una suite conozca la ruta de la otra — que es N12 (fijar topología del entorno). Se acepta
  el acoplamiento débil y se señala.
- **La colisión `veto`/`sancion` no está resuelta: está evitada.** Mientras E2 mantenga los
  identificadores en inglés y D5 elija claves que no colisionen, no duele. El día que se
  decida el renombrado total de B2B (E2 pospuesto, no cerrado), esta colisión es lo primero
  que hay que re-derivar — `status` → `estado` no colisiona, pero `sancion` sí, y la escalera
  de AC-L9 se llama «graduated sanctions» en el bundle upstream.
