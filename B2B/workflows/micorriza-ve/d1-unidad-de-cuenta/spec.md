# Spec — D1: unidad de cuenta USD, célula mono-moneda, FX irrepresentable

> Nodo TB.2 (después de D9). Ancla: anexo §8.1, §3.1, §2.1, §2.2; `constraints.md` M4/N3/N4;
> I-VE1, I-VE2, H4. Decisión humana fechada: [`../context.md`](../context.md) §2.

## 1. Qué deroga del bundle upstream

`spec-ledger.md` se titula «Mutual-Credit Ledger (**EUR**, no chain)» y su §1.2 dice
«Balances are mutual-credit **EUR** cents». **Derogado.** La unidad de cuenta es el **USD**.

*Porque:* el euro era la respuesta a MiCA (§1.2 del anexo: emitir un EMT exige €1,5M + CNMV).
MiCA no aplica en Venezuela. El USD es la unidad de cuenta **de facto** (§2.1), y el crédito
mutuo denominado en USD resuelve a la vez la sequía de crédito y la inflación: contabilidad a
prueba de devaluación **sin necesitar los dólares físicos escasos**. Es el truco WIR aplicado
a la escasez de divisas.

**Un crédito NO es un dólar ni un USDT.** Es compensación de obligaciones, a la par, con el
dólar como unidad de cuenta. El motor jamás asume 1 USDT = 1 USD (§2.4: primas P2P de hasta
~40% en pánico).

## 2. La decisión central: `moneda` vive en la CÉLULA

```python
create_cell(cell_id, params, ratified_by, ts)
# params ahora exige:
#   "moneda": "USD" | "VES"        ← OBLIGATORIO, sin default implícito
#   "expira_en_dias": int > 0      ← OBLIGATORIO si y solo si moneda == "VES"
```

Las obligaciones **no cambian**: `{id, debtor, creditor, amount_cents}`. Sin campo `moneda`.
Los saldos tampoco: `balance_cents`, sin moneda.

### Por qué así (lo que un ejecutor no puede inferir)

**L1 (`sum(balance_cents) == 0`) ES la definición de crédito mutuo**, y solo significa algo
dentro de una unidad de cuenta. Sumar centavos USD con centavos VES no da cero: da basura.

Tres consecuencias que se siguen, y que son el diseño entero:

1. **La mezcla es irrepresentable, no rechazada.** No hay campo donde escribir «esta
   obligación es en VES». I1 pide forma irrepresentable **antes** que flag, y aquí se puede
   pagar ese precio.
2. **El FX no tiene dónde escribirse.** Una tasa solo hace falta para relacionar dos monedas
   dentro de un mismo ámbito. Si el ámbito es mono-moneda, la tasa es un campo sin sitio.
   I-VE1 sale gratis de la geometría, en vez de vigilarse con un escáner.
3. **La "pista VES" del §3.1 = una célula VES aparte.** El §3.1 dice literalmente
   «contabilidad separada». Dos células, dos ledgers, dos L1 independientes, un mismo padrón
   humano de miembros si el gremio quiere.

### Por qué esto NO copia el patrón de TA.6

En C2C-VE (área e) la mezcla se rechaza con `ErrorDeBrechaAseguramiento` y hay una taxonomía
`TASA_KEYS` escaneada. Ahí hacía falta: varias campañas conviven en un motor y el sobre lleva
`moneda`. **Aquí no.** La forma no existe. Copiar el check de TA.6 sería más código para una
garantía más débil — y es el reflejo que hay que resistir en TB.2.

*(La taxonomía FX sí se conserva, pero como red secundaria: ver §5.)*

## 3. USD y VES no son simétricas

**El VES no sirve como depósito de valor** (decisión humana, 2026-07-15). Las tres funciones
del dinero se separan en Venezuela:

| Función | USD | VES |
|---|---|---|
| Unidad de cuenta | ✅ la del sistema | parcial (menudeo, obligaciones estatales) |
| Medio de pago | ✅ | ✅ (Pago Móvil) |
| **Depósito de valor** | ✅ | ❌ **>70% perdido desde oct. 2025** |

Un **saldo** de crédito mutuo es, por definición, valor sostenido en el tiempo — exactamente
la función que el VES no cumple. De ahí:

- `USD` es el default y la unidad de cuenta del sistema. `VES` es una pista opcional.
- **`expira_en_dias` no es una precaución: es lo que impide que el motor finja que un saldo
  VES almacena valor.** Una pista VES sin expiración es un pasivo inflacionario (H4).
- **El motor NO modela inflación.** Modelarla exigiría una tasa, y eso es N3. La expiración es
  la única respuesta a la inflación que no requiere representar el FX. (P3: el motor no
  modela inflación — «sería otra tasa».)

### Semántica de `expira_en_dias`

Parámetro **de la célula**, no de la obligación. Es una **convención declarada y verificable**,
no un efecto automático: el motor no tiene reloj (`ts` es un entero de entrada, `spec-ledger.md`
§1) y no puede caducar nada por su cuenta. Lo que hace:

- `create_cell` con `moneda="VES"` y sin `expira_en_dias` (o ≤ 0) → `ValueError`.
- `create_cell` con `moneda="USD"` y **con** `expira_en_dias` → `ValueError` (una célula USD
  que declara expiración está confundida sobre qué es).
- `cell_metrics(state)` expone `expira_en_dias` para que el comité y los exportes (D7) lo
  vean.

*Porque:* el motor es puro y sin reloj; caducar obligaciones automáticamente exigiría un tick,
y un tick sobre valor es una operación de valor sin puerta humana (I-VE5/M8). La expiración se
**declara** en el motor y se **ejecuta** por el comité. Igual que `depurar()` en C2C-VE (TA.5)
es convención + test, no efecto forzado. **Señalado** (D10): una célula VES puede incumplir su
propia expiración; el motor lo hace visible, no lo impide.

## 4. `turnover_eur_cents` → `turnover_cents`

Rename mecánico. **No viola E2** (sigue en inglés; no es castellanización): es una corrección
de veracidad — la moneda ya vive en la célula, así que el campo no debe nombrar ninguna.

Alcance: `src/ledger/mutual_credit_ledger.py`, `src/clearing/clearing_solver.py`
(`_validate` lo exige y `to_clearing_input` lo emite), los 5 archivos de test y los 4 goldens
`evals/golden-set/{test_A,test_B,test_C,ledger_flow}.json`.

*Regresión esperada:* misma clase que TA.6 (`moneda` obligatoria rompió fixtures). Remedio
idéntico: actualizar **conservando la semántica**, jamás el byte. Los goldens se regeneran a
partir de su input actualizado y se revisa que el diff sea solo el nombre del campo.

## 5. La taxonomía FX (red secundaria, lista PRIVADA)

Aunque el FX es irrepresentable por geometría (§2), se conserva un escáner como **lint
secundario**, no como el muro:

```python
# Lista PRIVADA de d1 — FUERA del bloque compartido (C-d9.3, patrón TA.6/TA.7)
_TASA_KEYS = [
    'tasa_de_cambio', 'tipo_de_cambio', 'exchange_rate', 'fx', 'paralelo', 'bcv',
    # variantes pegadas (endurecidas por el reviewer en TA.6 — el mismo hueco existe aquí)
    'tasadecambio', 'tipodecambio', 'exchangerate',
]
```

Aplicada a `params` en `create_cell`, con `_key_matches_taxonomy` del bloque heredado.

*Porque:* H1 — «el muro real es el TIPO de salida y el cierre de esquema; la lista de claves
es lint secundario». `params` es el único sitio de Fase 2 donde alguien podría intentar
guardar una tasa «solo como referencia». El muro es que las obligaciones no llevan moneda; la
lista es el aviso temprano.

**Fuera del bloque compartido**, en lista privada → md5 `758094a9` intacto (C-d9.3).

## 6. Contrato de implementación (TB.2)

1. `MONEDAS = ('USD', 'VES')`. `params["moneda"]` obligatorio, validado contra la tupla.
2. `expira_en_dias`: obligatorio ⇔ `moneda == "VES"`; entero > 0.
3. `_TASA_KEYS` privada; escaneo de `params` en `create_cell`.
4. Rename `turnover_eur_cents` → `turnover_cents` en los dos módulos, tests y goldens.
5. `cell_metrics` añade `moneda` y `expira_en_dias`.
6. `_fmt_eur` / `format_cents` → el símbolo `€` está hardcodeado en `render_statement` y
   `render_report`. Pasa a derivarse de `state["params"]["moneda"]`: `USD` → `$`, `VES` →
   `Bs.`. *Porque:* un extracto que dice «€» en una célula USD es la misma mentira que
   `turnover_eur_cents`, y este sí lo lee un humano.
7. **Cero cambios en la ruta de conservación.** Los enteros + `divmod` ya dan exactitud a
   15+ dígitos (M4); D1 no toca aritmética. La conservación a escala de hiperinflación se
   prueba en D10/TB.9.

## 7. Qué NO hace D1

- No modela inflación (§3).
- No caduca nada automáticamente (§3).
- No convierte, ni guarda tasas, ni asume 1 USDT = 1 USD.
- No renombra nada más allá de §4 (E2).
- No toca `sum(balance_cents) == 0` ni ninguna invariante L*.
