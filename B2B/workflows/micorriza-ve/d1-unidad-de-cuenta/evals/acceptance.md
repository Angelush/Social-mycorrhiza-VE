# Acceptance — D1: unidad de cuenta

> Binary Done: se verifica el artefacto. Ejecutables por máquina. `AC-4` es el global del
> grafo (`tasks.md` TB.2); los `AC-d1*` son locales.

## AC-4 (B2B) — FX irrepresentable

Tres niveles, del más fuerte al más débil. **El primero es el que importa**; los otros dos son
red secundaria.

1. **Por geometría:** una obligación con clave `moneda` (o `tasa_de_cambio`, o cualquier clave
   no perteneciente a `{id, debtor, creditor, amount_cents}`) es **rechazada** por el esquema
   cerrado heredado. Pass/fail: `ValueError`.
2. **Por lint:** `create_cell` con `params` conteniendo `tasa_de_cambio`, `tipo_de_cambio`,
   `exchange_rate`, `fx`, `bcv`, `paralelo`, `tasadecambio`, `tipodecambio`, `exchangerate` →
   `ValueError`. Incluye variantes con tildes (`tipo_de_cámbio`) y camelCase (`tipoDeCambio`)
   vía la maquinaria heredada. Pass/fail: raise por cada variante.
3. **Por grep-gate:** ningún literal numérico de tasa en `B2B-VE/src/`. Pass/fail: grep vacío.

## AC-d1.1 — La obligación no admite moneda (fija ST-d1.1)

`record_obligation(state, {"id": "o1", "debtor": "a", "creditor": "b", "amount_cents": 100,
"moneda": "VES"}, ts)` → `ValueError`. Pass/fail: raise.

*Porque:* «irrepresentable» es una propiedad del esquema, no un invariante de runtime. Este
test la convierte en algo que un delta futuro no puede romper en silencio.

## AC-d1.2 — `moneda` obligatoria, sin default

- `params` sin `moneda` → `ValueError`.
- `params` con `moneda="EUR"` / `"usd"` / `"USDT"` / `None` / `0` → `ValueError`.
- `params` con `moneda="USD"` → célula creada, `cell_metrics(...)["moneda"] == "USD"`.

Pass/fail: raise + igualdad. *Porque:* C-d1.2 — un default silencioso contabiliza VES como USD
y los números cuadran (F-d1.2).

## AC-d1.3 — `expira_en_dias` ⇔ VES

| `moneda` | `expira_en_dias` | Resultado |
|---|---|---|
| `VES` | ausente | `ValueError` |
| `VES` | `0` o negativo o no-int o `True` | `ValueError` |
| `VES` | `30` | célula creada |
| `USD` | `30` | `ValueError` |
| `USD` | ausente | célula creada |

Pass/fail: raise + creación. *Porque:* C-d1.3 (H4 en una dirección; célula-confundida en la otra).

## AC-d1.4 — Nada caduca solo (fija F-d1.3)

Una célula VES con `expira_en_dias=1` y una obligación registrada en `ts=0`: tras
`record_obligation(..., ts=10_000_000)` (muy posterior), la obligación original **sigue
abierta**. Ninguna operación extingue valor sin `ratified_by`.

Pass/fail: la obligación sigue en `state["obligations"]`. *Porque:* N-d1.4 — el motor es puro y
sin reloj; caducar automáticamente sería una operación de valor sin puerta humana (M8).

## AC-d1.5 — Ninguna tasa sobrevive en el estado

Tras cualquier secuencia de operaciones aceptada, ningún camino de claves del estado ni de los
eventos coincide con `_TASA_KEYS` vía `_key_matches_taxonomy`. Pass/fail: recorrido recursivo,
cero coincidencias. *Porque:* F-d1.4 — la tasa «solo de referencia» se lee en cuanto existe.

## AC-d1.6 — El rename conservó la semántica (fija F-d1.5)

Para los 4 goldens: el diff contra la versión previa afecta **exclusivamente** al nombre de
clave `turnover_eur_cents` → `turnover_cents`. **Ningún importe, hash, `seq` ni `reduction_pct`
cambia** salvo los hashes que dependan del payload renombrado, que deben recomputarse y
verificarse con `verify_chain`.

Pass/fail: comparación estructural clave a clave + `verify_chain(events)` sin lanzar.

*Porque:* la lección de TA.6 — un golden regenerado a ciegas consagra el bug que introdujo el
rename.

## AC-d1.7 — El símbolo dice la verdad

- Célula `USD`: `render_statement(...)` contiene `$` y **no** contiene `€` ni `Bs.`
- Célula `VES`: contiene `Bs.` y **no** `€` ni `$`
- Ningún `€` en toda la salida de `B2B-VE/src/` para cualquier moneda.

Pass/fail: subcadena. *Porque:* C-d1.6 — lo lee el comité para decidir.

## AC-d1.8 — Cero regresión

`cd B2B-VE && pytest -q` → **125 passed, 3 skipped** equivalentes, más los tests nuevos de
D1/D9. Los 3 skipped siguen siendo el bloque `networkx` (no se "arreglan": ver `../README.md`).

Pass/fail: salida de pytest real citada en el gate (M2 — la evidencia es el artefacto, jamás
el auto-reporte).

## AC-d1.9 — La aritmética no se tocó

Los tests de conservación heredados (AC-L1, AC-L3, AC-L7, `test_ledger_properties.py`) pasan
**sin modificación** más allá del rename de §4. Pass/fail: diff de esos archivos = solo el
rename. *Porque:* D1 cambia la etiqueta, no la aritmética; cualquier otro cambio ahí es un
bug o un alcance que se coló.

*(La conservación a 15+ dígitos a escala de hiperinflación se prueba en D10/TB.9, no aquí.)*
