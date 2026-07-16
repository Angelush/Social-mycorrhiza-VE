# DESIGN — TB.8b: nodo correctivo del `€` hardcodeado (defecto de D1, hallado por TB.8)

**Fecha:** 2026-07-16 · **Decisión humana:** correctivo ANTES de TB.9 (como TA.9 para Fase 1).
**Alcance:** completar AC-d1.7, que ya existía y TB.2 implementó a medias.

## 0. El defecto, con precisión

`B2B-VE/src/clearing/clearing_solver.py:252` imprime `€` hardcodeado en `format_cents`.
La spec de D1 §6.6 nombra `render_report` EXPLÍCITAMENTE («el símbolo `€` está hardcodeado en
`render_statement` y `render_report`. Pasa a derivarse de `params["moneda"]`») y AC-d1.7 exige
«ningún `€` en toda la salida de `B2B-VE/src/` para cualquier moneda». TB.2 corrigió el ledger
(`_fmt_eur`→`_fmt_cents`) y el solver quedó fuera; el test de AC-d1.7 solo cubría
`render_statement` → **verde certificando la mitad del AC**. Consecuencia: una célula VES emite
hoy una propuesta de liquidación que dice «725.74 €» — la mentira exacta que C-d1.6 prohíbe,
en el documento que el comité lee para RATIFICAR.

**No es spec nueva ni alcance nuevo: es un AC existente cuyo test pasaba por cobertura parcial.**
(Familia del hallazgo M9 de TB.8: la defensa estaba escrita, pero nadie comprobaba que cubriera
toda su superficie declarada.)

## 1. La forma del arreglo — la moneda viaja con el input, no con el render

El solver es standalone (no importa el ledger; upstream `B2B/` queda intacto). La célula es
mono-moneda (D1) y `to_clearing_input` ES la foto de la célula → **`moneda` entra ahí**:

1. **`to_clearing_input`** añade `"moneda": state["params"]["moneda"]`.
2. **Solver `_validate`**: `moneda` OBLIGATORIA, validada contra `_SIMBOLO = {"USD": "$",
   "VES": "Bs."}` local. *Sin default* — un default `€` (o `USD`) sería la configuración que
   nadie revisa (lección F-d3.1): el defecto seguiría vivo para todo llamador que no la pase.
   Faltante o inválida → `ValueError` con `match=`. **`EUR` se rechaza: el euro es
   irrepresentable en el fork, no deprecado.**
3. **`clear()`** conserva `"moneda"` en el resultado (el render no puede derivar lo que el
   resultado no lleva; y la propuesta que se ratifica debe decir en qué unidad habla).
4. **`render_report`** deriva el símbolo de `result["moneda"]`.
5. **`clearing_applied` (ledger)**: la propuesta debe traer `moneda` == la de la célula →
   `ValueError("proposal_moneda")`. *Porque:* el evento guarda la propuesta VERBATIM y un
   auditor la lee (hallazgo 2 de TB.6b) — una propuesta ratificada que dice `Bs.` en una célula
   USD sería una mentira con firma. Es la puerta M8 haciendo cumplir D1, no un check nuevo de
   conveniencia.

`_SIMBOLO` queda DUPLICADO ledger/solver a propósito (el solver no puede importar el ledger sin
acoplar lo que D9 separó); el anti-drift lo fija un test de igualdad de los dos mapas.

## 2. Goldens — los dos se regeneran, por construcción, y se prueba

- **`test_A/B/C.json`** (solver): `input` gana `moneda: "USD"` y `expected_output` gana
  `moneda: "USD"`. Regenerados POR PROGRAMA; diff campo a campo = exactamente esas dos claves.
- **`ledger_flow.json`**: el payload de `clearing_applied` lleva la propuesta (con `moneda`
  nueva) y su hash → **`head_hash` SE MUEVE, por construcción**. La navaja de TB.6b («head_hash
  primero, INVESTIGA NO REGENERES») se obedece: se registra el hash viejo/nuevo aquí (§4) y se
  compara campo a campo contra `B2B/` intacto — el único delta NUEVO respecto a TB.8 debe ser
  `moneda` dentro de `proposal` (+ su `proposal_hash` y la cascada de hashes).

## 3. Qué NO hace TB.8b

- No toca la aritmética de conservación (spec D1 §6.7) — solo validación de entrada y render.
- No añade función pública alguna → AC-7 (enumeración D3) no cambia de censo.
- No toca `herencia.py` (las 7 copias, `5d693ec`) ni `B2B/` upstream.
- No decide qué moneda «deberían» tener los goldens del solver más allá de USD: son fixtures
  de aritmética, no de política.

## 4. Resultado (2026-07-16)

**Suite: 388+3 → 396 passed + 3 skipped (+8, todos en `test_d1_moneda.py`).** `B2B/` intacto
(125+3), `C2C-VE/` intacto (441), `herencia.py` diff VACÍO, `5d693ec` en las 7 copias.

**Goldens, con la navaja obedecida:**
- `test_A/B/C.json`: regenerados por programa; asertado en el generador que el único delta es
  `moneda` (input y expected_output).
- `ledger_flow.json`: `head_hash` `9fa1517…e929` → `be1a31be…4ae1`, `final_state_sha256`
  `85bde4e1…0305` → `fd7e99a2…39b6`. INVESTIGADO, no regenerado a ciegas: el payload de
  `clearing_applied` lleva la propuesta VERBATIM y la propuesta ahora declara `moneda` (+ su
  `proposal_hash`) → la cadena se mueve POR CONSTRUCCIÓN. `seq`/`gross_open_cents` intactos.
  **Probado contra `B2B/` intacto:** propuesta VE == propuesta upstream campo a campo; único
  delta = la clave `moneda`.

**Mutación: 5 corridas, 5 cazadas** (más el control negativo del escáner AST, que cayó dentro
de M1):
- **M1** `€` de vuelta en `format_cents` → **5 rojos** (renders + AC-d1.7 nuevos + escáner AST).
- **M2** default `USD` en `_validate` → **1 rojo, exactamente
  `test_acd17_solver_sin_moneda_rechaza`** (F-d3.1 fijada con precisión).
- **M3** símbolos volteados en el solver → **5 rojos** (incl. el anti-drift ledger↔solver).
- **M4** quitar la puerta `proposal_moneda` de `clearing_applied` → **1 rojo, exactamente
  `test_acd17_apply_clearing_rechaza_moneda_ajena`**.
- **M5** `to_clearing_input` deja de llevar `moneda` → **25 rojos**.

**Incidente de procedimiento, para no repetirlo:** restaurar mutaciones con `git checkout`
sobre un árbol SIN COMMITEAR revirtió el arreglo entero — las corridas M2/M3 originales midieron
«solver sin D1», no la mutación, y se INVALIDARON y repitieron con backup por `\cp -f`.
**Regla: en un nodo con trabajo sin commitear, las mutaciones se restauran por copia, jamás por
git.** (El síntoma que lo destapó: M2/M3 daban 32 rojos idénticos — un mutante de un check
puntual no tumba 32 tests.)

**Propuestas forjadas de `test_ledger.py`:** ganaron `moneda: "USD"` para que sigan ejerciendo
SU defensa (con la puerta nueva delante habrían quedado verdes por la razón equivocada —
lección M2 de TB.6).

**Deuda que hereda TB.9 (Señalados):** ninguna nueva. El defecto queda CERRADO, no señalado.
