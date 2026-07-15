# Constraints — D3: visibilidad

## MUST

- **C-d3.1 — `scope` obligatorio, sin default.** *Porque:* un default es la configuración que
  nadie revisa. El fallo por omisión debe ser el seguro: quien no dice desde dónde mira, no
  mira. (M10 en espíritu: rechazar, no recortar.)
- **C-d3.2 — `scope="miembro"` exige `solicitante == member_id`.** *Porque:* sin eso,
  `miembro` es `publico` con otro nombre.
- **C-d3.3 — La sal del seudónimo es obligatoria y jamás sale del motor.** *Porque:* el espacio
  de `member_id` de una célula son 30–500 nombres (§7); sin sal, el seudónimo se revierte por
  fuerza bruta en segundos y es identidad con un paso extra.
- **C-d3.4 — Toda exportación pública pasa por seudonimización.** *Porque:* N7 — nunca
  identidad + monto en claro. Aplica a D7 (exportes) y a cualquier dato anclado (D2).

## MUST-NOT

- **N-d3.1 — Saldos jamás públicos con identidad.** Ni saldo, ni líneas, ni proyectada, ni
  owed_by/owed_to bajo `scope="publico"`. *Porque:* I-VE3/H3 — un libro público de saldos es un
  mapa de matraqueo. Quién tiene superávit = lista de objetivos de extorsión.
- **N-d3.2 — Ni el `estado` bajo `scope="publico"`.** *Porque:* la escalera de sanciones sobre
  un seudónimo estable sigue siendo una marca (U1: una ausencia informativa es
  `sin_informacion_desde_tu_posicion`, jamás una marca).
- **N-d3.3 — Ningún escalar de persona en ninguna salida.** *Porque:* N2/I-VE6. Y ojo: `H1` —
  el escalar con nombre benigno (`fertilidad`, `alcance`, `salud_crediticia`) es la forma que
  esto toma. El muro es el TIPO de salida, no la lista de nombres prohibidos.
- **N-d3.4 — El motor no autentica y no finge que lo hace.** *Porque:* no hay auth en el motor
  (`spec-ledger.md` §5). Un scope que pretendiera ser un guardia daría una garantía falsa —
  peor que ninguna.

## PREFERENCIAS

- **P-d3.1 —** Ante duda sobre si un campo va en `publico`: no va. La dirección del fallo es el
  sobre-rechazo (P1), y aquí el coste de un falso negativo lo paga un comerciante.

## ESCALADA

- **E-d3.1 —** Si un delta necesita exponer un importe individual en público → **parar**. Es
  N7, y N7 es lo que endurece este diseño respecto a España. Si persiste, E1.
- **E-d3.2 —** Presión sobre el comité para revelar saldos (§6.2: «un comité de crédito puede
  ser presionado») → no es un problema del motor. Quién gobierna decide; el motor no puede
  impedirlo y no lo simula. Señalado (D10).
