# Acceptance — D6+D8: bordes

> `AC-7` global (`tasks.md` TB.6); `AC-d68*` locales. Ejecutables por máquina.

## AC-7 (D6/D8) — Las operaciones nuevas pasan por la puerta existente (**el que importa**)

Por **enumeración**, no por lista: para cada `kind` nuevo (`member_exited`, `bridge_paused`,
`bridge_resumed`):

1. `ratified_by` ausente / `""` / no-str / `None` → `ValueError`.
2. La operación emite un evento con `prev_hash == state["head_hash"]` previo y `seq == prev+1`.
3. `verify_chain(events)` pasa y `replay(events)` reconstruye el estado **byte a byte**.
4. `ts < last_ts` → `ValueError` (monotonía heredada).
5. Con `params["paused"] == True` → `ValueError` (cortafuegos heredado).

Pass/fail: raise + igualdad byte.

*Porque:* M8/I-VE5. **(3) es el test que de verdad cierra F-d68.1:** una helper que mutara el
estado directamente no podría producir un stream que `replay` reconstruya, porque no habría
pasado por `_apply`. No hace falta prohibir la helper: basta con hacer imposible que su
resultado pase.

## AC-d68.1 — Cero helpers directas

Ninguna función pública de `B2B-VE/src/ledger/` muta `state` sin devolver `(state, event)`.
Pass/fail: AST — toda función pública que reciba `state` o devuelve una vista de solo lectura,
o devuelve la tupla. *Porque:* C-d68.1.

## AC-d68.2 — L1 se conserva en toda salida

Para las cuatro resoluciones, `sum(balance_cents) == 0` después, y
`cell_metrics(...)["sum_balances_cents"] == 0`:

| Resolución | Saldo previo | Después |
|---|---|---|
| `simple` | 0 | saliente 0; nadie más cambia |
| `liquidacion_puente` | +5000 | saliente 0; **fondo −5000** |
| `absorcion_avalista` | −3000 | saliente 0; **avalista −3000** |
| `plan_de_pago` | −3000 | saliente **−3000** (sin mover); nadie más cambia |

Pass/fail: numérico. *Porque:* C-d68.2 (F-d68.2) y §2 (F-d68.8: el plan de pago **no** mueve
el saldo — el negativo sigue ahí porque esa es la verdad).

## AC-d68.3 — El avalista no se atropella

`absorcion_avalista` cuyo saldo absorbido dejaría al avalista fuera de `[credit_min,
credit_max]` → `ValueError` nombrando al avalista, **y el estado queda intacto**.
Pass/fail: raise + igualdad de estado. *Porque:* C-d68.5 — flag/reject, jamás clamp (M6).

También: avalista inexistente, `exited`, `suspended` o `expelled` → `ValueError`.

## AC-d68.4 — `exited` no es una sanción

- `exited` **no** está en la escalera: `update_member(..., {"status": "exited"})` → `ValueError`.
- Desde `exited`, `update_member` a cualquier estado → `ValueError` (terminal).
- Tras `salida_con_saldo`, `status == "exited"`, **no** `"expelled"`.
- La escalera heredada sigue intacta: `active→warned` ✅, `active→expelled` ❌ (AC-L9 pasa sin
  cambios).

Pass/fail: raise + igualdad. *Porque:* C-d68.3 — confundirlos marca a un emigrante como moroso
y esa marca viaja (F-d68.3).

## AC-d68.5 — La pausa del puente NO mata el crédito interno (**el que importa**)

Con `puente_pausado == True`, el flujo completo del piloto (AC-L8) corre **entero**:
`add_member` → `record_obligation` → `clear(to_clearing_input(state))` → `apply_clearing` →
`settle_obligation` → `anclar` → `salida_con_saldo` tipo `plan_de_pago`. **Todo pasa.**

Y solo `salida_con_saldo` tipo `liquidacion_puente` → `ValueError`.

Pass/fail: el flujo completa; solo la liquidación lanza.

*Porque:* **I-VE7** — es el invariante que define este delta. Si este test pasa con una
implementación que reutiliza `params["paused"]`, el test está mal escrito: por eso ejerce el
flujo entero, no una operación de muestra (F-d68.4).

## AC-d68.6 — El fondo es un miembro con líneas (fija ST-d68.1)

`liquidacion_puente` cuya contrapartida dejaría al fondo fuera de sus líneas → `ValueError`.
Pass/fail: raise. *Porque:* el fondo sin línea **es** la verdad (no da abasto); la respuesta es
capitalizarlo, no recortar el check.

## AC-d68.7 — El motor no liquida

`salida_con_saldo` con `liquidacion_puente` no toca red ni disco (test con `socket` y `open`
parcheados para lanzar), no contiene direcciones, claves ni spreads, y **solo registra**.
Pass/fail: completa sin tocar ninguno + grep sin literales de dirección/tasa.
*Porque:* N-d68.2/N9 (F-d68.6).

## AC-d68.8 — Reversibilidad correcta

| Operación | Test |
|---|---|
| `puente_pausar` sobre puente pausado | `ValueError` |
| `puente_reanudar` sobre puente activo | `ValueError` |
| `pausar` → `reanudar` → `pausar` | los tres pasan; estado coherente |
| `salida_con_saldo` sobre un `exited` | `ValueError` (no reversible, no repetible) |

Pass/fail: raise + estado. *Porque:* §4 — convención heredada de `pause_cell`/`resume_cell`.

## AC-d68.9 — `puente_pausado` ≠ `paused`

Son dos claves distintas en `params`; `pause_cell` no toca `puente_pausado` y `puente_pausar`
no toca `paused`. Pass/fail: igualdad de campos. *Porque:* C-d68.4 (F-d68.4).

## AC-d68.10 — Un `exited` no recibe obligaciones nuevas pero paga las suyas

- `record_obligation` con un `exited` como deudor o acreedor → `ValueError`.
- `settle_obligation` de una obligación abierta de un `exited` → **pasa**.

Pass/fail: raise + éxito. *Porque:* N-d68.4 — «paying what you owe is always legal».
*Verificado en TB.1:* sale gratis del filtro heredado (ST-d68.4); el test lo fija para que
nadie lo «arregle».
