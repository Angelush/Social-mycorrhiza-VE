# Spec — D6+D8: salida con saldo y pausa del puente

> Nodo TB.6 (depende de D2/TB.3). Ancla: anexo §8.6, §8.8, §3.5, §6.1, §6.5, §6.6; M8, I-VE5,
> I-VE7, I3.
>
> Los dos deltas van juntos porque comparten **la misma puerta**, y esa puerta es el delta.

## 1. Hallazgo de TB.0: la puerta ya existe

`mutual_credit_ledger.py:42`:

```python
ratification_kinds = {"cell_created", "member_added", "member_updated",
                      "clearing_applied", "cell_paused", "cell_resumed"}
if kind in ratification_kinds:
    ratified_by = payload_copy.get("ratified_by")
    if not isinstance(ratified_by, str) or not ratified_by:
        raise ValueError("ratified_by")
```

**M8 no pide construir una puerta: pide no construir una segunda.** D6/D8 añaden `kind`s a
este conjunto y pasan por `_apply`. Nada más.

*Porque:* «ninguna helper directa sobre el ledger» (M8). Una función que mute el estado sin
pasar por `_apply` se salta, de una vez: `ratified_by`, la monotonía de `ts`, el check de
`paused`, el encadenado de hashes, y los post-asserts L1/L2. La puerta de un solo sentido no
admite puertas laterales «por conveniencia» (ST6).

## 2. D6 — `salida_con_saldo`

Un miembro emigra a mitad de ciclo (§6.5: éxodo continuo). El upstream no tiene este caso
porque España no lo tiene.

```python
def salida_con_saldo(state, member_id, resolucion, ratified_by, ts) -> (state, event)
    # kind = "member_exited"  → añadido a ratification_kinds
```

`resolucion` ∈:

| Saldo | `resolucion` | Efecto |
|---|---|---|
| **positivo** (le deben) | `{"tipo": "liquidacion_puente"}` | el saldo se lleva a 0 vía puente; la contrapartida la asume el fondo |
| **negativo** (debe) | `{"tipo": "plan_de_pago", "plazo_meses": int}` | queda registrado; el saldo **no** se mueve |
| **negativo** | `{"tipo": "absorcion_avalista", "avalista": "member_id"}` | el saldo pasa al avalista |
| **cero** | `{"tipo": "simple"}` | salida limpia |

**Reglas duras:**
- `state["members"][member_id]["status"]` pasa a `expelled`… **no**: pasa a un estado nuevo
  `exited`. *Porque:* `expelled` es el último peldaño de la escalera **sancionadora** (inv. 5);
  irse del país no es una sanción. Confundirlos marca a un emigrante como moroso.
  `exited` es terminal y **no** está en la escalera: `update_member` no puede llegar a él ni
  salir de él.
- **L1 se conserva siempre.** `sum(balance_cents) == 0` después de la salida. Por eso
  `liquidacion_puente` y `absorcion_avalista` **mueven** la contrapartida a otro miembro
  (fondo o avalista): un saldo no se evapora. `plan_de_pago` no mueve nada — el saldo negativo
  **sigue ahí**, en un miembro `exited`, que es exactamente la verdad.
- `absorcion_avalista`: el avalista debe existir, estar activo, y **el saldo absorbido debe
  caber en sus líneas** (L2). Si no cabe → `ValueError`. Nunca se recorta.
- Un miembro `exited` no registra obligaciones nuevas. Sus obligaciones abiertas **sí** se
  pueden liquidar (herencia: «sanctions never trap debt; paying what you owe is always legal»).

*Por qué `resolucion` es explícita y no la deduce el motor del signo del saldo:* deducirla
sería que el motor decide cómo se resuelve una salida. Eso es juicio del comité — y con
consecuencias sobre un avalista que no está en la sala. El motor exige que le digan qué se
decidió.

## 3. D8 — `puente.pausar()`

```python
def puente_pausar(state, ratified_by, ts) -> (state, event)    # kind = "bridge_paused"
def puente_reanudar(state, ratified_by, ts) -> (state, event)  # kind = "bridge_resumed"
```

`state["params"]["puente_pausado"]: bool`, inicial `False`.

**Lo único que hace la pausa:** rechazar `salida_con_saldo` con `resolucion.tipo ==
"liquidacion_puente"`. **Y nada más.**

| Con el puente pausado | ¿Funciona? |
|---|---|
| `record_obligation` | ✅ |
| `apply_clearing` | ✅ |
| `settle_obligation` | ✅ |
| `add_member` / `update_member` | ✅ |
| `anclar` | ✅ |
| `salida_con_saldo` tipo `plan_de_pago` / `absorcion_avalista` / `simple` | ✅ |
| `salida_con_saldo` tipo `liquidacion_puente` | ❌ `ValueError` |

*Porque:* **I-VE7 — la red local sobrevive a la muerte del puente.** USDT puede dejar de ser
viable de un plumazo (§6.1: riesgo Tether + congelamiento OFAC; §6.6: snapback). El crédito
interno es la parte robusta; el puente es la frágil. Si la pausa detuviera el crédito interno,
el sistema habría acoplado su supervivencia a la pieza más frágil — exactamente al revés.

### `puente_pausado` NO es `paused`

`params["paused"]` (heredado) es el **cortafuegos de la célula**: bloquea toda mutación
(inv. 8). `params["puente_pausado"]` bloquea **una** resolución de salida.

Son dos conceptos y dos campos. *Porque:* reutilizar `paused` para el puente mataría el crédito
interno al pausar el puente, que es I-VE7 rota. Es el error más barato de prevenir aquí y el
más caro de depurar — misma clase que la colisión `mode`/`modo` de Fase 1 (M7/F1).

## 4. Reversibilidad

| Operación | ¿Reversible? | Por qué |
|---|---|---|
| `puente_pausar` / `puente_reanudar` | **sí, dos vías** | es un dial operativo; el comité lo mueve según el riesgo del mes |
| `salida_con_saldo` | **no** | mueve valor y cierra una cuenta. Como los asientos: se corrige con asientos nuevos, no borrando |

Pausar un puente pausado (o reanudar uno activo) → `ValueError`. *Porque:* es la convención
heredada de `pause_cell`/`resume_cell`, y hace que un doble clic no oculte un estado real.

## 5. Contrato de implementación (TB.6)

1. `ratification_kinds` += `{"member_exited", "bridge_paused", "bridge_resumed"}`.
2. Estado `exited` **fuera** de la escalera; `update_member` no lo alcanza ni lo abandona.
3. `params["puente_pausado"] = False` en `create_cell`.
4. Los tres `kind` nuevos van por `_apply`. **Cero helpers directas.**
5. Post-asserts heredados sin cambio: L1 y L2 se verifican después, como para toda operación.
6. `cell_metrics` añade `puente_pausado`.

## 6. Qué NO hace

- **No toca USDT, ni rieles, ni direcciones.** «El núcleo solo registra la obligación saldada»
  (§3.2); los rieles (Zelle, efectivo, Pago Móvil) son agnósticos y viven en los bordes.
  `liquidacion_puente` registra que se liquidó; **no liquida**.
- No custodia claves (N9/I-VE4).
- No decide la resolución de una salida (§2).
- No modela el spread. Los spreads de liquidación son decisión humana, jamás hardcodeados
  (§2.4/N-d1.5).
