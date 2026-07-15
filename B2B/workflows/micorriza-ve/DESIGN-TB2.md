# DESIGN-TB2 — árbol `B2B-VE/` + D9 (herencia con alcance) + D1 (unidad de cuenta)

> Escrito por Opus ANTES del código (método TA.4–TA.7). Nodo TB.2, gate M1 aprobado
> 2026-07-15. Cubre **dos deltas** (D9 y D1, en ese orden), por eso vive en la raíz del
> sub-bundle y no dentro de un directorio de delta.
>
> Specs que manda: [`d9-herencia-scoping/`](d9-herencia-scoping/) y
> [`d1-unidad-de-cuenta/`](d1-unidad-de-cuenta/). Este documento **no re-decide** nada de
> ellas: fija cómo se ejecutan y qué se delega.

## 0. El árbol (patrón TA.2)

`B2B-VE/` = copia de `B2B/{src,tests}` + los 4 goldens. `B2B/` queda **intacto** como
referencia upstream.

```
B2B-VE/src/{clearing,ledger}/           ← copiados sin tocar
B2B-VE/tests/                           ← 5 archivos
B2B-VE/workflows/micorriza/evals/golden-set/{test_A,test_B,test_C,ledger_flow}.json
```

Las specs **no** se copian (viven en `B2B/workflows/micorriza-ve/`), igual que en C2C-VE.
Piso reproducido en el árbol nuevo antes de tocar nada: **125 passed, 3 skipped** — los 3
skipped son el cross-check `networkx` de `test_clearing_solver.py:247`, ausente en `.venv-ve`
a propósito. No son regresión.

## 1. D9 — `src/firewall/herencia.py`

### Qué contiene

```python
"""..."""
import re
import unicodedata

# === BEGIN shared firewall machinery (byte-identical across all six capas; AC-X) ===
...  # 3023 bytes, md5 5d693ecf1833fb760e173ee3db30a263
# === END shared firewall machinery ===
```

Los `import re` / `import unicodedata` van **fuera** del bloque: el bloque los usa pero no los
declara (así es en las seis capas C2C-VE). Meterlos dentro rompería la byte-identidad.

### Qué NO contiene (C-d9.2)

`MARKET_KEYS`, `CLAVES_MERCADO`, `RECIPROCITY_LEDGER_KEYS`, `TASA_KEYS`, `_ENVELOPE_KEYS`,
`_contains_forbidden_key`. **El corte ya lo hace la geometría del archivo**: TA.6 sacó las
taxonomías de dominio del bloque compartido porque eran *de dominio*, y M5 pide exactamente
ese mismo corte. Se copia el bloque; no se copia nada de fuera.

### El md5 y su span — leer antes de tocar

El span canónico es el bloque **completo, incluido su `\n` final**: 3023 bytes,
`5d693ecf1833fb760e173ee3db30a263`. Es el número que Fase 1 publicó como `5d693ec` y **es
correcto**.

TB.1 afirmó lo contrario (que el real era `758094a9…`) porque extrajo con `.strip()` — el
mismo bloque, 3022 bytes, otro número. Corregido en este nodo; los artefactos de Fase 1 no se
tocan. **El span es parte de la constante** (C-d9.1): un md5 sin span declarado no es
verificable, y esa ausencia es lo que costó un nodo. Por eso AC-d9.1 comprueba **también el
byte-count 3023**, para que un cambio de convención falle distinto que un cambio de contenido.

Si el md5 no cuadra: se arregla la copia. **Nunca el literal, nunca el span** (ST-d9.3/ST-d9.6).

### Dónde se aplica — y dónde no (§4 de la spec)

| Superficie | ¿Se escanea? | Por qué |
|---|---|---|
| Esquemas cerrados del ledger (`update_member.allowed_keys`, `params`, obligaciones) | **NO** | Ya los protege una lista blanca, que es más fuerte que un escáner. Aplicarlo ahí es coste sin beneficio, en la dirección de matar al paciente (AC-d9.6). |
| `params` de `create_cell` — taxonomía **FX** | Sí, pero con `_TASA_KEYS` **privada de D1** | Lint secundario (D1 §5), no el muro. |
| `referencias_comerciales` (D5) | Sí — **la única** superficie de forma libre de Fase 2 | AC-d9.5, se verifica en **TB.5**, no aquí. |

**AC-d9.5 queda declarado pendiente y enlazado a TB.5** — hoy no hay superficie de forma libre
que probar; fingir que la hay sería el módulo-importado-y-nunca-llamado de F-d9.5.

### La colisión dormida

`FORBIDDEN_KEYS` contiene `veto`, `sancion`, `penalizacion` — y B2B hace veteo (inv. 10) y
sanciones graduadas (inv. 5, AC-L9). No hay colisión **hoy** porque E2 dejó los identificadores
en inglés (`status`). AC-d9.4 es el centinela que se disparará el día que un nombre castellano
sí colisione. **Si colisiona: se renombra la clave, jamás la taxonomía** (N-d9.1) — es
compartida con las 6 capas C2C-VE.

## 2. D1 — unidad de cuenta (después de D9)

Contrato ya fijado en `d1-unidad-de-cuenta/spec.md` §6. Nada que re-decidir. Los puntos donde
un ejecutor se equivocaría:

1. **NO copiar el patrón de TA.6.** Allí la mezcla se rechaza con `ErrorDeBrechaAseguramiento`
   porque varias campañas conviven en un motor. Aquí la mezcla **es irrepresentable**: las
   obligaciones no llevan `moneda` y no hay dónde escribirla. Añadir el check sería más código
   para una garantía más débil. **Este es el reflejo a resistir en TB.2.**
2. **`expira_en_dias` es bicondicional:** obligatorio ⇔ `moneda == "VES"`. Una célula USD que
   lo declara es un `ValueError` — está confundida sobre qué es.
3. **No caduca nada.** El motor no tiene reloj (`ts` es entrada). La expiración se **declara**
   y la ejecuta el comité; un tick sobre valor sería una operación de valor sin puerta humana
   (M8). Convención + test, como `depurar()` en TA.5. Va a Señalados.
4. **`turnover_eur_cents` → `turnover_cents`** no viola E2 (sigue inglés; es veracidad). Toca
   los 2 módulos, 5 tests y 4 goldens.
5. **El símbolo `€` hardcodeado** en `render_statement`/`render_report` se deriva de
   `params["moneda"]`: `USD` → `$`, `VES` → `Bs.`. Un extracto con `€` en una célula USD es la
   misma mentira que el nombre del campo, y este lo lee un humano que decide.
6. **Cero cambios en la aritmética.** Enteros + `divmod` ya dan M4.

### La regresión de los goldens

`moneda` obligatoria + el rename rompen fixtures y los 4 goldens — misma clase que TA.6. Los
goldens se **regeneran desde su input actualizado** y se revisa que el diff sea solo el campo
renombrado y el `moneda` añadido: se conserva **la semántica, jamás el byte**. Los goldens
pinean `sha256(canonical(state))` y `head_hash`, así que cambiarán por construcción; lo que
tiene que no cambiar es el **flujo**.

## 3. Reparto (skill `multi-model-orchestration`, ratings consultados)

`pick_model.py coding` → `agy-gemini-3-flash` fit **+10.50**, seen 24, 4/4 verdes en TA.5–TA.8.
`pick_model.py reasoning` → sin modelo libre probado (`agy-claude-sonnet-4-6` seen=1) →
**specs y scoping siempre Opus**.

| Trabajo | Quién | Por qué |
|---|---|---|
| Este DESIGN, `herencia.py`, D1, goldens | **Opus** | Criterio-dependiente; los goldens son el piso de regresión |
| Tests AC-d9.1..d9.4, d9.6 y AC-10 + D1 | **agy-gemini-3-flash** | Mecánicos, con **contrato de firmas fijado por Opus** antes de delegar |

**Los goldens no van a fan-out.** Es la clase de regresión de TA.6 y toca el piso.

### Contrato de firmas para el fan-out (fijado ANTES de delegar)

```python
# B2B-VE/src/firewall/herencia.py
FORBIDDEN_KEYS: list[str]
_key_matches_taxonomy(key: str, taxonomy) -> bool
_value_has_identity_shape(value) -> bool
_tokenize_key(key: str) -> list[str]

# B2B-VE/src/ledger/mutual_credit_ledger.py  (D1)
MONEDAS: tuple = ('USD', 'VES')
create_cell(cell_id: str, params: dict, ratified_by: str, ts: int) -> tuple[dict, dict]
#   params: {neg_line_bp, pos_line_bp, velocity_window_s, velocity_max_cents,
#            moneda: 'USD'|'VES', expira_en_dias: int>0 sii moneda=='VES'}
#   viola → ValueError
cell_metrics(state: dict) -> dict   # ahora incluye 'moneda' y 'expira_en_dias'
# miembros: 'turnover_cents' (antes 'turnover_eur_cents')
```

## 4. AC de cierre del nodo

- **AC-10** — el vocabulario nuclear (`moneda`/`saldo`/`credito`/`deuda`) **ADMITIDO** en un
  flujo real del ledger. Prueba la admisión, **no el rechazo**: un firewall que mata al
  paciente pasa cualquier test que solo compruebe rechazos.
- **AC-d9.1** — md5 `5d693ecf1833…` + byte-count 3023, calculados dentro del test.
- **AC-d9.2** — `hasattr` False para todo lo de fuera del bloque + grep-gate.
- **AC-d9.3** — `bancoDeTiempo` admitida, `lista_negra_local` rechazada,
  `descripción_del_score_musical` rechazada, `"V-12.345.678"` → identidad.
- **AC-d9.4** — centinela: toda clave castellana de D1–D8 da `False` contra `FORBIDDEN_KEYS`.
- **AC-d9.6** — `update_member` legítimo pasa sin firewall; clave desconocida → `ValueError`
  por la lista blanca.
- **AC-d9.5** — **pendiente, enlazado a TB.5.**
- **Piso:** ≥ 125 passed + 3 skipped, más los tests nuevos.
