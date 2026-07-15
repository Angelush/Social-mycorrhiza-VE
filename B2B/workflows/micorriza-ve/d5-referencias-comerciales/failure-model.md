# Failure model — D5: referencias comerciales

## Modos de fallo (F-d5#)

- **F-d5.1 — El score que se cuela por la puerta de servicio.** El ejecutor añade
  `len(referencias_comerciales)` a la salida del extracto, o un `antiguedad_media`, «que no es
  un score, es un dato». Lo es: es un número derivado, comparable entre solicitantes, sobre una
  persona jurídica. *Mitigación:* C-d5.1/N-d5.1. *Detección:* AC-d5.1, que prueba el TIPO de
  salida, no una lista de nombres.
- **F-d5.2 — La sugerencia amable.** `linea_sugerida = turnover * f(referencias)`. El comité la
  acepta por defecto porque está ahí, y la capa relacional queda automatizada sin que nadie lo
  decidiera. *Mitigación:* N-d5.2. *Detección:* AC-d5.1 (ninguna función deriva números).
- **F-d5.3 — La cédula en la nota.** El comité escribe «Pedro, V-12.345.678, lleva 3 años
  vendiéndonos». El dossier entra por el campo de texto libre, que es precisamente el que nadie
  valida. *Mitigación:* C-d5.2 — `_value_has_identity_shape` escanea **también** la `nota`.
  *Detección:* AC-d5.3.
- **F-d5.4 — El firewall no cableado.** D9 heredó el bloque, D5 define el esquema, y nadie
  llama al escáner. Todo verde, defensa inexistente (F-d9.5). *Mitigación:* C-d5.2.
  *Detección:* AC-d5.3 corre sobre la operación real (`add_member`), no sobre el escáner.
- **F-d5.5 — La colisión que despierta.** Alguien nombra el campo `veto_del_comite` o
  `sancion_previa` — nombres naturales para este dominio. `FORBIDDEN_KEYS` los rechaza y el
  delta del veteo no puede expresar el veteo. *Mitigación:* C-d5.4 + §4 de la spec (se eligió
  `avalista` a propósito). *Detección:* AC-d9.4.
- **F-d5.6 — El campo obligatorio.** «Si es el mecanismo de veteo, que sea obligatorio.»
  Resultado: el comité inventa referencias para poder dar de alta a alguien que conoce de toda
  la vida. El campo pasa de informar el juicio a **sustituirlo con teatro**.
  *Mitigación:* P-d5.1.
- **F-d5.7 — El grafo de avales público.** Las referencias se filtran a un exporte «porque no
  llevan importes». Pero «quién avala a quién» **es** el mapa de la red: a quién presionar para
  llegar a quién. *Mitigación:* C-d5.5. *Detección:* AC-d5.4.

## Hallazgos de estrés (ST-d5#)

- **ST-d5.1 — El conteo es un score aunque nadie lo compute.** Con la lista visible, el comité
  **puede** contar avalistas y ordenar solicitantes mentalmente. Y debe poder: es su juicio.
  La línea que N2 traza no es «que nadie compare nunca» sino «que el **sistema** no compute ni
  compare». Un comité que juzga usando los datos es el diseño; un motor que juzga es el fallo.
  *Se documenta para que nadie intente «arreglar» lo que no está roto.*
- **ST-d5.2 — El aval no se verifica.** Que el avalista diga la verdad es social. Un anillo de
  tres empresas avalándose mutuamente pasa todos los checks. *Mitigación:* ninguna en el motor
  — N-d5.4 solo impide el auto-aval trivial. El anillo lo caza el comité, que conoce a la
  gente. **Señalado.**
- **ST-d5.3 — El cold-start VE es peor que el español y esto no lo arregla.** §6.4: el dolor es
  permanente (ventaja) pero la confianza está erosionada por el éxodo y la informalidad
  dificulta el veteo (desventaja). D5 da el formato del juicio, no el sustrato. **Señalado.**
- **ST-d5.4 — Auto-confirmación del firewall.** El test del escáner lo escribe quien cableó el
  escáner. *Mitigación:* AC-d5.3 usa los vectores de R2 fijados en Fase 1 (datos de entrada
  externos a este nodo), no vectores inventados aquí.

## Abierto — no fake-resolver (N10)

- El motor no verifica referencias; un anillo de avales mutuos pasa (ST-d5.2).
- El cold-start no se resuelve con código (ST-d5.3, §6.4, §6.8: «la voluntad de cooperar no se
  fabrica»).
- Un comité presionado puede admitir a quien le digan; el veteo relacional no es a prueba de
  coerción (§6.2).
