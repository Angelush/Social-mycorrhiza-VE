# Acceptance — D3: visibilidad

> `AC-7` global (`tasks.md` TB.4); `AC-d3*` locales. Ejecutables por máquina.

## AC-7 (D3) — Ningún punto de consulta público expone saldo + identidad (**el que importa**)

Test **exhaustivo por enumeración**, no por lista de casos: para **toda** función pública del
módulo del ledger (descubiertas por introspección: `dir(module)`, sin `_` inicial), llamada con
`scope="publico"` donde lo acepte, ninguna salida contiene a la vez un `member_id` real y un
importe.

Pass/fail: recorrido recursivo de cada salida; cero coincidencias.

*Porque:* N7/I-VE3. Y **por qué por enumeración y no por lista:** una lista de funciones a
probar envejece — el delta siguiente añade una vista, nadie actualiza la lista, y el test sigue
verde. La introspección hace que una vista nueva sin scope **rompa este test el día que se
escriba**, en el nodo que la produjo.

## AC-d3.1 — `scope` obligatorio

`member_statement(state, "m1")` sin `scope` → `TypeError`/`ValueError`. `scope="admin"`,
`None`, `""` → `ValueError`. Pass/fail: raise. *Porque:* C-d3.1 (F-d3.1).

## AC-d3.2 — `miembro` solo se ve a sí mismo

| Llamada | Resultado |
|---|---|
| `scope="miembro", solicitante="m1", member_id="m1"` | extracto completo |
| `scope="miembro", solicitante="m2", member_id="m1"` | `ValueError` |
| `scope="miembro"` sin `solicitante` | `ValueError` |

Pass/fail: raise + igualdad. *Porque:* C-d3.2.

## AC-d3.3 — El TIPO de salida pública es cerrado (fija F-d3.4)

Bajo `scope="publico"`, el conjunto de claves de la salida es **exactamente** `{"seudonimo"}`.
No un subconjunto de una lista permitida: **igualdad exacta de conjuntos**.

Pass/fail: `set(salida.keys()) == {"seudonimo"}`.

*Porque:* H1 — el muro es el TIPO de salida, no la lista de nombres prohibidos. Un
`salud_crediticia` o un `percentil_de_actividad` futuro rompe este test **sin que nadie tenga
que haberlo previsto**. Una lista negra de claves no lo cazaría; una lista blanca cerrada sí.

## AC-d3.4 — El seudónimo resiste la fuerza bruta (fija F-d3.2)

El test **ejecuta el ataque**: dados `cell_id`, la lista completa de `member_id` de la célula y
el seudónimo público, intentar revertirlo sin la sal probando los 500 candidatos. Debe fallar.
Y sin sal (control), debe tener éxito — demostrando que el test discrimina.

Pass/fail: el ataque falla con sal y triunfa sin ella. *Porque:* un test que solo verifique que
«hay una sal en el código» no prueba que sirva.

## AC-d3.5 — La sal no sale nunca

Tras cualquier secuencia de operaciones: ninguna salida de `scope="publico"`, ni
`cell_metrics`, ni `exportar_registros` (D7), ni `anclar` (D2) contiene el valor de
`params["sal_seudonimo"]`. Pass/fail: recorrido recursivo, cero coincidencias.
*Porque:* C-d3.3 (F-d3.3) — la sal filtrada revela todos los seudónimos a la vez.

## AC-d3.6 — El seudónimo es determinista y estable

Mismo `(cell_id, member_id, sal)` → mismo seudónimo, entre procesos. Miembros distintos →
seudónimos distintos. Pass/fail: igualdad + desigualdad. *Porque:* D2 necesita enlazar el ancla
con lo anclado; un seudónimo inestable rompe la evidencia (§4 de la spec).

## AC-d3.7 — `cell_metrics` sigue siendo público y agregado

`cell_metrics(state)` no exige scope y sus claves siguen siendo exactamente las heredadas +
`moneda`/`expira_en_dias` (D1). Ningún `member_id`, ningún importe individual.
Pass/fail: igualdad de conjuntos de claves. *Porque:* son agregados de célula, no de persona;
el TIPO de salida hace irrepresentable el escalar por persona.

## AC-d3.8 — Cero cambio de semántica en la regresión

Los tests heredados que llamaban `member_statement` pasan con `scope="comite_credito"` y
devuelven **exactamente lo mismo** que antes del delta. Pass/fail: igualdad de dicts contra el
golden previo. *Porque:* §6 — D3 declara desde dónde se mira; no cambia lo que el comité ve.
