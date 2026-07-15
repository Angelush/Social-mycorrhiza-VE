# Failure model — D3: visibilidad

## Modos de fallo (F-d3#)

- **F-d3.1 — El default cómodo.** `scope="comite_credito"` como default para no romper los
  tests. Todas las llamadas existentes siguen pasando… y toda llamada futura que olvide el
  scope ve **todo**. El delta queda instalado y desactivado a la vez. *Mitigación:* C-d3.1.
  *Detección:* AC-d3.1.
- **F-d3.2 — El seudónimo sin sal.** `sha256(cell_id + member_id)`. Parece un compromiso; con
  30–500 nombres candidatos se revierte por fuerza bruta en segundos. **Un mapa de matraqueo
  con un paso extra.** *Mitigación:* C-d3.3. *Detección:* AC-d3.4 (el test hace la fuerza bruta).
- **F-d3.3 — La sal filtrada.** La sal se guarda en `params`, y `cell_metrics` o un exporte
  público devuelve `params` entero «por transparencia». La sal sale, y con ella todos los
  seudónimos. *Mitigación:* C-d3.3. *Detección:* AC-d3.5.
- **F-d3.4 — El escalar con nombre benigno.** Bajo `publico` no hay saldo… pero sí un
  `salud_crediticia: "buena"` o un `percentil_de_actividad: 0.8`, «que no es un saldo».
  Es N2/H1: el escalar de persona reconstruido con otro nombre. *Mitigación:* N-d3.3.
  *Detección:* AC-d3.3 verifica el **TIPO de salida** (conjunto de claves cerrado), no una lista
  de nombres prohibidos.
- **F-d3.5 — El estado que se cuela.** `estado: "suspended"` sobre un seudónimo estable, «que no
  es un importe». Es una marca (U1) y señala al objetivo igual de bien. *Mitigación:* N-d3.2.
- **F-d3.6 — El scope como guardia.** El ejecutor añade una comprobación de identidad al scope y
  el equipo cree que el motor autentica. No lo hace: no hay auth (`spec-ledger.md` §5). Una
  garantía falsa es peor que ninguna porque nadie pone la de verdad encima.
  *Mitigación:* spec §7 lo dice y va a Señalados.
- **F-d3.7 — La agregación reversible.** `cell_metrics` con **un** miembro: `gross_open_cents`
  es el importe de ese miembro. La agregación no anonimiza en células diminutas.
  *Mitigación:* ninguna en el motor — es matemática. **Señalado**; el comité no publica métricas
  de una célula de Etapa 0 (§7: 30–50 pymes es el mínimo).

## Hallazgos de estrés (ST-d3#)

- **ST-d3.1 — La correlación entre salidas.** Seudónimo estable ⇒ dos publicaciones enlazables.
  Rotarlo rompería el anclaje (D2: el árbitro no podría enlazar). *Sin mecanismo* — decisión
  del comité sobre qué y cuándo publica. **Señalado** (D10). Mismo tratamiento y mismo porqué
  que en C2C-VE (TA.8).
- **ST-d3.2 — El motor no es la superficie de ataque más probable.** El matraqueo no necesita
  romper `sha256`: necesita presionar a un miembro del comité (§6.2). D3 reduce la superficie
  **técnica**; no toca la social, y no debe fingir que sí. **Señalado.**
- **ST-d3.3 — La suma cero delata en célula de dos.** Con dos miembros, `sum == 0` implica que
  el saldo de uno es el negado del otro: conocer uno es conocer ambos. Es aritmética, no un
  bug. Otra razón por la que la Etapa 0 son 30–50 pymes.
- **ST-d3.4 — `to_clearing_input` no tiene scope y no debe tenerlo.** Devuelve líneas y
  obligaciones de todos: es el input del solver, que corre **dentro** de la célula. Ponerle
  scope rompería el clearing sin proteger nada. *Verificado en TB.1:* es una vista interna, no
  un punto de consulta. Se documenta para que nadie «complete» el delta.

## Abierto — no fake-resolver (N10)

- Correlación entre salidas (ST-d3.1).
- El motor no autentica; el scope es un contrato, no un guardia (F-d3.6).
- La agregación no anonimiza en células diminutas (F-d3.7, ST-d3.3).
- Un comité presionado revela lo que quiera; ningún mecanismo del motor lo impide (§6.2).
