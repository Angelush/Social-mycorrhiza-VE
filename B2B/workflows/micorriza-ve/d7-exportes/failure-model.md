# Failure model — D7: exportes

## Modos de fallo (F-d7#)

- **F-d7.1 — El exporte servicial.** «Ya que exportamos, calculemos el IGTF (3%) y marquemos
  qué es gravable.» El motor acaba de clasificar fiscalmente al miembro bajo un marco ambiguo
  (§5) y un enforcement arbitrario. Si la interpretación es incorrecta, el sistema **le creó**
  el problema. *Mitigación:* N-d7.1. *Detección:* AC-d7.4.
- **F-d7.2 — El float que vuelve.** `importe = cents / 100` «para que quede bonito en el CSV».
  Reintroduce el float exactamente en el punto donde el número sale del sistema y entra en una
  hoja de cálculo — que es donde el redondeo se vuelve dinero. *Mitigación:* C-d7.6.
  *Detección:* AC-d7.3.
- **F-d7.3 — La columna moneda por línea.** Parece más informativo; sugiere que puede variar, y
  la pregunta siguiente es la tasa. **El formato del exporte hace representable el FX** aunque
  el motor no lo represente. *Mitigación:* C-d7.5. *Detección:* AC-d7.5.
- **F-d7.4 — El exporte que escribe.** `exportar_registros(..., ruta="/tmp/x.csv")`. El motor
  toca disco; el test se vuelve dependiente del entorno (N12) y el motor deja de ser puro.
  *Mitigación:* C-d7.1. *Detección:* AC-d7.2.
- **F-d7.5 — El scope duplicado.** D7 se escribe un control de acceso propio «porque el exporte
  es distinto». Dos controles divergen: se arregla uno, el otro se queda con el agujero.
  *Mitigación:* C-d7.3. *Detección:* AC-7 de D3 (por enumeración) cubre `exportar_registros`
  automáticamente — **por eso está escrito por enumeración**.
- **F-d7.6 — El exporte público con identidad.** «El exporte del miembro es suyo, que lleve su
  nombre» — y alguien lo publica. *Mitigación:* C-d7.4 + el scope. El motor seudonimiza en
  `publico`; que el miembro comparta el suyo es su decisión, y es correcto que pueda.
- **F-d7.7 — El exporte desde el estado.** Se deriva de `state` en vez de `events`: el exporte
  del período de marzo refleja los saldos de julio. Cuadra consigo mismo y es falso.
  *Mitigación:* C-d7.2. *Detección:* AC-d7.6.

## Hallazgos de estrés (ST-d7#)

- **ST-d7.1 — El exporte es la superficie de fuga más probable.** No por un bug: porque **su
  propósito es salir del sistema**. El scope protege lo que el motor devuelve; lo que el
  miembro haga con su CSV está fuera. Es correcto y es irreducible. **Señalado.**
- **ST-d7.2 — La verificabilidad depende de que la raíz esté publicada.** `hash_evento` +
  `raiz_ancla` solo valen ante un tercero si la raíz se publicó (D2/ST-d2.1), que es del
  llamador. Un exporte con `raiz_ancla` de un período no anclado da falsa sensación de prueba.
  *Mitigación:* el campo se omite si no hay ancla — no se rellena con la raíz calculada al
  vuelo. Fijado en AC-d7.7.
- **ST-d7.3 — Un exporte de una célula de dos miembros identifica al otro.** La contraparte de
  cada línea es el otro. Aritmética, no bug (igual que ST-d3.3). Otra razón por la que la
  Etapa 0 son 30–50 pymes.
- **ST-d7.4 — CSV e inyección.** Un `member_id` que empiece por `=` o `+` se ejecuta como
  fórmula al abrir el CSV en Excel. *Mitigación:* escapar el prefijo en el formato CSV. No es
  paranoia: los `member_id` los eligen humanos.

## Abierto — no fake-resolver (N10)

- El sistema no promete neutralidad fiscal; el tratamiento del crédito mutuo es ambiguo y una
  reclasificación agresiva del SENIAT es un escenario real (§6.7). **Asesoría local antes de
  escalar**, no una interpretación en el código.
- Lo que el miembro haga con su exporte está fuera del motor (ST-d7.1).
- La verificabilidad ante terceros depende de una publicación que el motor no hace (ST-d7.2).
