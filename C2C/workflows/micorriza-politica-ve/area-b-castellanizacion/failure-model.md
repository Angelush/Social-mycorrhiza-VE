# Failure model — Área b · Castellanización

## Residuo parcial (el modo de fallo principal)
Un símbolo en inglés olvidado en un mensaje, un docstring o una clave de test. *Detección:* el
`grep` de residuos de `constraints.md` como gate del área. *Consecuencia si se cuela:* inconsistencia
de esquema y, si es una clave, posible fallo de matching bilingüe.

## Colisión de traducción
Dos símbolos ingleses distintos que traducen al mismo castellano, o `mode`/`modo` sin desambiguar.
*Mitigación:* la tabla exhaustiva primero (M7); `mode`→`sala` resuelve la única colisión conocida.

## Cambio de comportamiento accidental
Un renombrado que altera una comparación de string (p. ej. un verdicto `adopted` comparado en otro
sitio no actualizado a `adoptada`). *Detección:* los 293 tests equivalentes; un fallo aquí señala
un renombrado incompleto, no un rediseño.

## Procedencia
Los comentarios de procedencia por módulo **pueden** citar el nombre upstream (`# ex membrane.py`)
para trazabilidad; el `grep` de residuos los exceptúa explícitamente. *Señalado:* no es residuo,
es historia deliberada.
