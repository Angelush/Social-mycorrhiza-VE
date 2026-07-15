# Constraints — D10: branding y cierre

## MUST

- **C-d10.1 — El lenguaje de producto es «circuito de crédito comercial» de la cámara/gremio.**
  *Porque:* P2/§8.10. El Petro y Sunacrip dejaron cicatrices: cualquier «moneda» nueva huele a
  estafa (H5). Un nombre equivocado no es un problema de adopción — es el motivo por el que un
  comerciante no abre la puerta.
- **C-d10.2 — La lista Señalados se consolida desde los failure-models de D1–D9, sin resolver
  ninguno.** *Porque:* N10 — flagged, not fake-resolved. Es la filosofía heredada, y un
  Señalado «resuelto» en prosa es peor que uno abierto: nadie vuelve a mirarlo.
- **C-d10.3 — El README referencia las fuentes únicas; no las re-teclea.** Unidad de cuenta →
  D1; invariantes → bundle upstream; deltas → este sub-bundle. *Porque:* el failure-model de
  Fase 1 lo prohíbe explícitamente (TA.8: la tabla de MODOS se referenció, no se copió). Una
  tabla copiada diverge y la copia es la que se lee.
- **C-d10.4 — AC-9 es un checklist de HONESTIDAD.** El README no promete lo que el código no
  hace. *Porque:* es el documento con el que un comité decide si confía; y es lo que un
  ejecutor futuro lee antes de romper algo.
- **C-d10.5 — La conservación se prueba a 15+ dígitos.** *Porque:* M4 — inflación ~229%
  (§2.1); los enteros de Python lo permiten y el test lo fija. Es el único sitio donde se
  prueba a esa escala.

## MUST-NOT

- **N-d10.1 — Ni «moneda», ni «coin», ni «token», ni «petro», ni «comunal», ni «puntos», ni
  «billetera» en el lenguaje de producto.** *Porque:* P2 + N1. Y la razón dura: **el branding
  es la primera línea de defensa de N1**. Si el vocabulario dice «moneda», alguien pedirá que
  sea transferible fuera de la red, y sonará razonable porque el nombre ya lo prometió.
- **N-d10.2 — No confundir la clave del esquema con el lenguaje de producto.**
  `params["moneda"]` es correcto (describe la unidad de cuenta); «la moneda de la cámara» no lo
  es. *Porque:* es la misma distinción de M5 — la palabra no es el problema; lo es qué nombra.
- **N-d10.3 — Ningún float en ninguna ruta de valor.** *Porque:* M4/I3 heredadas.
- **N-d10.4 — El README no promete neutralidad fiscal, ni protección contra matraqueo, ni que
  el multisig elimine la coerción.** *Porque:* N-d7.2 + C-d10.4. Son promesas que el fork no
  puede cumplir y que expondrían a los miembros que se las creyeran.
- **N-d10.5 — No renombrar identificadores.** *Porque:* E2 (pospuesto a decisión explícita). El
  seam bilingüe se **documenta**, no se cierra por iniciativa de este nodo.

## PREFERENCIAS

- **P-d10.1 —** Ante duda sobre si algo va a Señalados: va. *Porque:* el coste de un Señalado
  de más son tres líneas; el de uno de menos es que alguien confíe en una garantía inexistente.

## ESCALADA

- **E-d10.1 —** Si un Señalado parece resoluble con un mecanismo pequeño → **no se resuelve en
  TB.9**. Se abre un nodo. TB.9 es documental; resolver aquí significa hacerlo sin spec y sin
  gate (M1), que es como se cuelan los invariantes mal leídos.
- **E-d10.2 —** Si el vocabulario correcto colisiona con una clave heredada → gana la claridad
  para el humano en los docs; el esquema no se toca (E2/N-d10.5).
