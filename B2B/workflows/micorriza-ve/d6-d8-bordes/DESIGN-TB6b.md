# DESIGN TB.6b — D8: `puente_pausar()` / `puente_reanudar()`

> Opus, 2026-07-15. Nodo TB.6b (nace de partir TB.6 por la tensión M9/D8). Deps: **TB.6 ✅
> `ac3bdfd` + M9 ✅ `ba58bce`**. Piso citado:
> `cd B2B-VE && ../.venv-ve/bin/python -m pytest -q` → **297 passed, 3 skipped**.

## §0 — M9 está saldado, y lo que dice CONFIRMA el diseño

`docs/verificaciones/2026-07-15-sanciones.md` y `-cripto.md`, firmados 2026-07-15. D8 estaba
bloqueado por M9 (decisión humana del 2026-07-15) porque **`puente.pausar()` ES el mecanismo de
respuesta a sanciones**. Lo verificado no cambia una línea del motor, pero mueve dos premisas de
«intuición de diseño» a «hecho fechado»:

1. **El alivio de sanciones va por licencia general REVOCABLE**, no por derogación; la
   arquitectura (EO 13692/13808/13884) sigue en pie. → «USDT puede dejar de ser viable de un
   plumazo» (§6.1) es un hecho verificado. **I-VE7 confirmada.**
2. **Julio-2026 trajo designación DIRIGIDA, no *snapback* general.** → es **exactamente** el caso
   donde hay que parar el puente **sin** matar el crédito interno. Si el escenario real fuera un
   apagón total, `puente_pausado` ≠ `paused` daría igual; **como es puntual, la distinción ES el
   delta.** (Hallazgo 3 de sanciones.)
3. **La lista se mueve en los dos sentidos** (retiradas de designación en abr-2026) → la pausa
   **reversible de dos vías** (§4 de la spec) es la forma correcta: un **dial**, no un
   interruptor de un solo uso.

## §1 — CORRECCIÓN a DESIGN-TB6 §7: el golden y la navaja

**Lo que escribí en TB.6 §7 era falso:** «`params["puente_pausado"] = False` en `create_cell`
(**regenera el golden — es un param nuevo en `cell_created`**)». **`puente_pausado` NO es un param
del llamador.**

`create_cell` **ignora** el `paused` que le pasen: reconstruye `params` clave a clave (lista
blanca, la técnica de D3) y **fija `"paused": False` por su cuenta**. `puente_pausado` va igual, y
por la misma razón: **una célula que arranca con el puente pausado no es una cosa** — igual que
no arranca pausada. Es estado derivado, no configuración. Además P-d68.1 pide reutilizar la
maquinaria de `pause_cell`/`resume_cell` como plantilla; la simetría empieza aquí.

**Consecuencia — y es más fuerte que lo que tuvieron TB.2 y TB.4:**

`tests/golden/ledger_flow.json` fija **dos cosas independientes**:

| Campo | ¿Cambia? | Por qué |
|---|---|---|
| `final_state_sha256` | **SÍ** | es `sha256(canonical(state))` y `state["params"]` gana una clave |
| **`head_hash`** | **NO — y esto es la navaja** | el payload de `cell_created` es **idéntico**: la clave nueva no viaja en el evento |
| `seq`, `gross_open_cents` | NO | D8 no toca el flujo |

En TB.2 y TB.4 el `head_hash` cambiaba **por construcción** (el param entraba en `cell_created`),
así que la regeneración no podía auto-verificarse: había que comparar campo a campo contra `B2B/`
intacto y confiar en la comparación. **Aquí el head_hash es un invariante:**

> **`head_hash` DEBE quedar en `9fa1517955fe98a237fc9f415be0c1a360904155676d3de85d9e4dacaa83e929`.
> Si cambia, algo se coló en el payload → se investiga, NO se regenera.**

La regeneración se auto-verifica: un solo campo se mueve, el otro tiene que quedarse quieto. **Se
mantiene igualmente la comparación campo a campo contra `B2B/` intacto** (técnica de TB.2 — sin
ella un golden regenerado blanquea lo que se cuele con él).

## §2 — API

```python
def puente_pausar(state, ratified_by, ts)   -> (state, event)   # kind = "bridge_paused"
def puente_reanudar(state, ratified_by, ts) -> (state, event)   # kind = "bridge_resumed"
```

Calcadas de `pause_cell`/`resume_cell` (P-d68.1), **sin reutilizar su campo** (C-d68.4). Los dos
kinds entran en `ratification_kinds`: M8 no pide construir una puerta, pide no construir una
segunda. Validación en `_apply` (la vía del `replay`), como en TB.6.

`state["params"]["puente_pausado"]: bool`, inicial `False`. `cell_metrics` lo expone (§5.6 de la
spec) — **ahora sí**: en TB.6 habría sido el delta instalado y desactivado a la vez (F-d3.1);
aquí el mecanismo existe.

## §3 — Lo ÚNICO que hace la pausa

Rechazar `salida_con_saldo` con `resolucion.tipo == "liquidacion_puente"`. **Y nada más.**

Todo lo demás sigue: `record_obligation`, `apply_clearing`, `settle_obligation`, `add_member`,
`update_member`, `anclar`, y `salida_con_saldo` de tipo `plan_de_pago`/`absorcion_avalista`/
`simple`.

*Porque:* **I-VE7 — la red local sobrevive a la muerte del puente.** El crédito interno es la
parte robusta; el puente es la frágil. Si la pausa detuviera el crédito interno, el sistema
habría acoplado su supervivencia a su pieza más frágil — **fallaría exactamente en el escenario
para el que se diseñó** (F-d68.4).

**Dónde va el check:** en la rama `member_exited` de `_apply`, junto a la resolución que rechaza.
**No** en el preámbulo de `_apply` (donde vive el check de `paused`): un check ahí arriba
tendría que saber de qué kind viene, y esa es la puerta de entrada de F-d68.4 — un `if` de más y
la pausa se come todo el ledger. **La pausa del puente es una regla de UNA resolución, y se
escribe donde vive esa resolución.**

### `puente_pausado` NO es `paused` (C-d68.4)

`params["paused"]` es el **cortafuegos de la célula**: bloquea toda mutación (inv. 8).
`params["puente_pausado"]` bloquea **una** resolución de salida. Dos conceptos, dos campos.
Reutilizar `paused` mataría el crédito interno al pausar el puente = I-VE7 rota. Misma clase que
la colisión `mode`/`modo` de Fase 1 (M7/F1): **la más barata de prevenir y la más cara de
depurar.**

## §4 — Reversibilidad (§4 de la spec)

Pausar un puente pausado → `ValueError("puente_pausado")`. Reanudar uno activo →
`ValueError("puente_no_pausado")`. Convención heredada de `pause_cell`/`resume_cell`: **un doble
clic no oculta un estado real.** `pausar → reanudar → pausar` los tres pasan (es un dial, §0.3).

**Mensajes distinguibles de los de `paused`/`not_paused`**, y no es cosmética: es lo que hace que
un `match=` pueda probar que se rechazó por el puente y no por el cortafuegos. Misma lección que
AC-d9.5 en TB.5 (`firewall` vs `clave desconocida`).

## §5 — AC-7 (D3): los dos mutadores nuevos → `SIN_SCOPE`

Mismo motivo que `salida_con_saldo` en TB.6, y más fácil: no devuelven ni saldo ni identidad —
mueven un booleano. Mutadores por la puerta de ratificación; quien llama **ratifica, no
consulta**. Se añaden a la lista con motivo escrito (**va a ponerse rojo al escribirlos: es el
diseño funcionando**).

## §6 — Plan de AC

| AC | Qué fija |
|---|---|
| **AC-d68.5** | **EL QUE IMPORTA** — con el puente pausado, el flujo del piloto corre ENTERO; solo `liquidacion_puente` lanza. Ejerce el flujo completo, no una operación de muestra (F-d68.4) |
| **AC-d68.9** | `puente_pausado` ≠ `paused`: `pause_cell` no toca `puente_pausado` y `puente_pausar` no toca `paused` |
| AC-d68.8 (1–2) | doble pausa / doble reanudación → `ValueError`; el ciclo pausar→reanudar→pausar pasa |
| AC-7 (D6/D8) | los 5 puntos de la puerta, ahora sobre `bridge_paused`/`bridge_resumed` |
| AC-7 (D3) | clasificación de los dos mutadores |
| golden | `head_hash` **invariante**; `final_state_sha256` regenerado |

**Sin fan-out:** el nodo es pequeño y su contrato de firmas es el DESIGN entero (regla de coste
TA.9, re-aplicada en TB.5 y TB.6). El golden **nunca** va a fan-out: es el piso.

## §7 — Mutaciones planificadas (+ una NO planificada, obligatoria)

1. `puente_pausar` reutiliza `params["paused"]` → **F-d68.4**, debe caer AC-d68.5 entero.
2. El check del puente sube al preámbulo de `_apply` (aplica a todo kind) → AC-d68.5.
3. La pausa rechaza también `plan_de_pago` → AC-d68.5 (I-VE7: solo la liquidación).
4. `puente_pausado` no entra en `ratification_kinds` → AC-7(1).
5. Doble pausa permitida (idempotente) → AC-d68.8.
6. `puente_pausado` inicial `True` → el flujo del piloto entero.
7. **`puente_pausado` colado en el payload de `cell_created`** → **el `head_hash` del golden**.
   Es la navaja de §1 y no existía en TB.2/TB.4.

**Obligatoria: una mutación que este DESIGN no previó.** Lleva cinco defectos cazados en tests de
criterio de Opus (TA.9, TB.4, TB.7, TB.5 y **TB.6**, donde destapó que AC-d68.4 pasaba por la
razón equivocada). Un test de invariante que no se ha visto fallar no se sabe si prueba algo.
