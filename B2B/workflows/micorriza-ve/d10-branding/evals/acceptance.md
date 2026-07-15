# Acceptance — D10: branding y cierre

> `AC-4` y `AC-9` globales (`tasks.md` TB.9); `AC-d10*` locales. **AC-9 es gate humano** — el
> único sin máquina (ST-d10.3).

## AC-9 — Checklist de honestidad del README (**gate humano, M1**)

Un humano lee `B2B-VE/README.md` y confirma, frase por frase:

1. ¿Promete algo que el código no hace? En particular: ¿dice o sugiere «tus saldos son
   privados» (el motor **no autentica** — F-d3.6), «el multisig protege el fondo» (**reparte**
   la coerción, no la elimina — ST-d4.1), «compliance-ready» sin decir que **el sistema no
   declara por nadie** (§5/D7)?
2. ¿Está la lista Señalados completa contra los failure-models de D1–D9? (≥ las 22 entradas de
   `spec.md` §4.)
3. ¿Hay algún Señalado «resuelto» en prosa sin mecanismo? (N10 — F-d10.3.)
4. ¿Las tablas **referencian** su fuente única en vez de copiarla? (C-d10.3 — F-d10.4.)
5. ¿Está dicho el seam bilingüe de E2, sin disimulo? (`context.md` §2.)
6. ¿Está dicho que los modos C2C son herencia documentada y **no integrada**? (D9 §1.)
7. ¿Dice qué NO es el producto (moneda, token, inversión, banco)?

Pass/fail: aprobación humana explícita. *Porque:* es el documento con el que un comité decide
si confía, y lo que un ejecutor futuro lee antes de romper algo.

## AC-4 (D10) — Conservación a escala de hiperinflación (**el que importa**)

Property test (hypothesis) con importes de **15+ dígitos** en centavos:

- `clear()`: `net_positions` antes == después, **exactamente** (igualdad de dicts de ints).
- El ledger: `sum(balance_cents) == 0` tras cualquier secuencia aceptada.
- Ningún float en ningún importe de salida.

Pass/fail: property test. *Porque:* C-d10.5/M4 — inflación ~229% (§2.1). **Es el único sitio
donde se prueba a esta escala** (D1 §7 lo difirió aquí a propósito).

## AC-d10.4 — El property test no pasa por vacuidad (fija F-d10.6/ST-d10.4)

Dos comprobaciones sobre la **estrategia**, no sobre el resultado:

1. Los importes generados son de **≥ 15 dígitos** — verificado afirmándolo dentro del test, no
   confiando en el default de hypothesis (que genera 6 dígitos y haría el AC-4 una mentira).
2. Una fracción de los casos generados **contiene al menos un ciclo**, y en ésos se afirma
   `gross_debt_after < gross_debt_before`. Sin esto, `clear()` no hace nada y la conservación
   se cumple trivialmente.

Pass/fail: aserciones dentro del test + `hypothesis.event()`/estadísticas de cobertura.
*Porque:* ST5 upstream (auto-confirmación) y el gate de vacuidad del harness Sim.

## AC-d10.1 — El vocabulario está limpio en todo lo legible

Grep sobre `B2B-VE/README.md`, docstrings, mensajes de error, `docs/`, y las salidas de
`render_statement`/`render_report`/`exportar_registros`/`describir_politica`:

**Cero coincidencias** de: `coin`, `token`, `petro`, `comunal`, `billetera`, `puntos`,
«la moneda de», «nuestra moneda», `wallet`.

Pass/fail: grep vacío. *Porque:* C-d10.1 — el vocabulario del producto es lo que el usuario lee
**cada día**, no la portada (F-d10.1).

## AC-d10.2 — El esquema no se tocó (fija F-d10.2)

`params["moneda"]` **sigue existiendo y sigue admitida**. AC-10 (D9) pasa sin cambios; los 4
goldens no cambian; ningún identificador se renombró (E2/N-d10.5).

Pass/fail: AC-10 verde + diff de goldens vacío. *Porque:* N-d10.2 — la palabra no es el
problema, lo es qué nombra. El celo de D10 es el riesgo aquí, no la laxitud.

## AC-d10.3 — Las tablas referencian, no copian

El README **no** contiene una copia de: la tabla de límites/unidad de cuenta de D1, las
invariantes L1–L6/I1–I5 del bundle upstream, ni la tabla de deltas de `spec.md`. Contiene
enlaces a cada una.

Pass/fail: ausencia de duplicación + enlaces presentes. *Porque:* C-d10.3 — la lección literal
de TA.8; una tabla copiada diverge y la copia es la que se lee.

## AC-d10.5 — Señalados ordenados por consecuencia

La lista se ordena por **quién paga** (el comerciante · el comité · la red), no por delta de
procedencia. Pass/fail: gate humano. *Porque:* ST-d10.2 — 22 entradas ordenadas por índice son
un índice; ordenadas por consecuencia son accionables.

## AC-d10.6 — Suite completa verde (M2)

`cd B2B-VE && ../.venv-ve/bin/python -m pytest -q` con la salida real citada en el gate:
los 125 passed + 3 skipped equivalentes, más todo lo añadido en TB.2–TB.9.

Los 3 skipped siguen siendo el bloque `networkx` — **no son regresión y no se "arreglan"**
(ver `../../README.md`). Pass/fail: salida pytest real — la evidencia es el artefacto, jamás
el auto-reporte.
