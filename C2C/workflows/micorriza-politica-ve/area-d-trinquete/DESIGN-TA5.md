# DESIGN — TA.5 · Área d · Trinquete asimétrico + `depurar`

> Tabla de cambios ANTES de tocar código (método TA.3/TA.4). Se añade a `src/modo/modo.py`
> (NO archivo nuevo). Piso de regresión: 362 verdes. Firewall md5 `5d693ecf1833fb760e173ee3db30a263`
> (span: bloque `BEGIN…END` completo, incluido su `\n` final = 3023 bytes) intacto (modo.py no
> contiene el bloque). Gate: AC-5 completo + monotonía (hypothesis).

## 1. Orden de modos (ya existe)
`MODOS = ('paz', 'catastrofe_acotada', 'catastrofe_severa')` → índice = estrictez creciente.
`idx(m) = MODOS.index(m)`. Escalada = `idx(propuesto) > idx(actual)`; desescalada = `<`; no-op = `==`.

## 2. `validar_transicion(actual, propuesto, decision_capa6=None)` — pura
Devuelve un **estado** (str), nunca recorta; rechaza con `raise ErrorDeModo` (convención del repo).

| Caso | Condición | Resultado |
|---|---|---|
| modo inválido | `actual` o `propuesto` ∉ MODOS | `raise ErrorDeModo` |
| no-op | `idx(propuesto) == idx(actual)` | return `'no_op'` (explícito, sin error — AC-d3) |
| escalada | `idx(propuesto) > idx(actual)` | return `'escalada'` (unilateral, `decision_capa6` irrelevante — AC-M2/d1) |
| desescalada autorizada | `idx(propuesto) < idx(actual)` Y `_autoriza_desescalada(decision_capa6, propuesto)` | return `'desescalada'` |
| desescalada no autorizada | desescalada Y no autoriza | `raise ErrorDeModo` |

### 2.1 `_autoriza_desescalada(decision, propuesto)` — la correspondencia (C-d2)
Firma de 3 args ⇒ la correspondencia "esa propuesta `cambiar_modo` / ese círculo" debe ser
**auto-contenida** en `decision`. Convención de `propuesta_id` de una propuesta de cambio de modo:

    cambiar_modo:{circulo_id}:{modo_destino}

`decision` autoriza la desescalada a `propuesto` **iff** TODO se cumple:
- `decision` es dict;
- `decision['veredicto'] == 'adoptada'` (clave **`veredicto`** con e — la que devuelve
  `gobernanza.decidir`, fuente de verdad; el spec en prosa escribe `verdicto`, el código manda);
- `decision['propuesta_id'] == f"cambiar_modo:{decision['circulo_id']}:{propuesto}"`.

Cobertura de AC-d2 sin parámetro de círculo:
- **otra propuesta** → `propuesta_id` no codifica `cambiar_modo…:{propuesto}` → rechazo.
- **otro círculo** → `propuesta_id` nombra círculo A pero `decision['circulo_id']` es B
  (auto-inconsistencia: una decisión adoptada de B no puede autorizar la propuesta de A) → rechazo.
- **`veredicto == 'revisar'`** → rechazo.

NO se reimplementa gobernanza: se consume su veredicto tal cual (C-d5).

## 3. `depurar(items, modo, ahora)` — pura determinista, idempotente (AC-M3)
`ahora` = fecha ISO (granularidad días, coherente con `validar_modo`). `modo` ∉ LIMITES → `raise`.
Cada `item` tiene `tipo` y `creado_en` (ISO). Por tipo:

| tipo | ventana | acción |
|---|---|---|
| `traza` | `retencion_trazas_dias` | **RECORTAR**: `expira_en ← min(expira_en?, creado_en + ventana)`; el item se **conserva** (nunca se elimina — es el "salvo" del spec). |
| resto (`dato`, …) | `retencion_max_dias` | **ELIMINAR** si `edad = ahora − creado_en > ventana`; si no, se conserva sin cambios. |

Malformado (`creado_en` no parsea): `dato` → se descarta (evacuación conservadora: no verificable
dentro de ventana); `traza` → se descarta (sin fecha no hay ventana que recortar). **Señalado.**

Pureza: no muta entradas (las trazas recortadas son copias `dict(item)`). Idempotencia: recortar es
`min` con la misma cota (segunda pasada da el mismo `expira_en`); los datos conservados tienen
`edad ≤ ventana` y se reconservan. AC-M3 ✓.

## 4. `tras_escalada(items, actual, propuesto, ahora)` — helper de CONVENCIÓN (C-d4)
Valida que sea escalada (`validar_transicion` → `'escalada'`, si no `raise`) y devuelve
`depurar(items, propuesto, ahora)`. Fija el acoplamiento escalada→depuración por
**helper + test + convención documentada**, NO por efecto: una función pura no puede obligar al
llamador a invocarlo. NO se finge la garantía (C-d4, C-c5/failure-model).

## 5. Tests (`tests/test_area_d_trinquete.py`, archivo nuevo)
AC-M2, AC-d1, AC-d2 (otra propuesta / otro círculo / revisar), AC-d3 (no-op), AC-d4 (helper depura),
depurar por tipo + idempotencia (AC-M3), y **PB-d1 monotonía** con `hypothesis` sobre el producto
`MODOS × MODOS` (escalada siempre válida sin decisión; desescalada nunca válida sin `adoptada`).
Se construye la `decision` con la forma real de `gobernanza.decidir` (veredicto/propuesta_id/circulo_id).
