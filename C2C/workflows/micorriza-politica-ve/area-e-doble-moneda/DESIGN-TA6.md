# DESIGN-TA6 — Área e · Doble moneda USD/VES sin conversión

> Diseño Opus (invariantes de moneda/conservación). Implementación de las 2 capas por Opus;
> `test_area_e_doble_moneda.py` delegado a modelo gratis (agy-gemini-3-flash) vía
> multi-model-orchestration, revisado por Opus + agy-claude-opus-4-6. Método TA.3–TA.5:
> DESIGN antes del código.

## Decisión de firewall (resuelta por la convención ya existente)
El bloque `BEGIN/END shared firewall` — md5 `5d693ecf1833fb760e173ee3db30a263` (span: bloque
`BEGIN…END` completo, incluido su `\n` final = 3023 bytes) — termina en la l.106/121 de cada capa.
Las taxonomías **de dominio** (`MARKET_KEYS`, `RECIPROCITY_LEDGER_KEYS`) ya viven **fuera** del
bloque, como taxonomías **privadas** de la capa. TA.6 sigue esa convención al pie:

- Los tokens de tipo-de-cambio de Capa 4 van en una taxonomía **privada nueva** `TASA_KEYS`,
  NO dentro del bloque compartido.
- La taxonomía de mercado de Capa 1 es la ya-existente `MARKET_KEYS` (privada).

**⇒ El md5 5d693ec queda byte-idéntico en las 6 capas; `test_cross_layer_taxonomy` NO se toca.**

## Capa 4 — `src/assurance/aseguramiento.py` (mono-moneda)

### Nueva excepción
```python
class ErrorDeBrechaAseguramiento(ValueError):
    """Brecha de dominio-moneda: mezcla de monedas o tasa de cambio incrustada.
    Subclase de ValueError (convención TA.3: el rechazo de sobre es ValueError-atrapable),
    pero con nombre propio que exige la spec (C-e2). NO confundir con
    ErrorDeInvarianteAseguramiento (aborto interno, deliberadamente NO-ValueError)."""
```
*Por qué subclase de `ValueError`:* la mezcla de monedas es culpa del **llamador** (entrada
inválida), no un motor-roto; debe ser atrapable por `except ValueError` como el resto de rechazos
de sobre (convención fijada en TA.3). El nombre propio satisface la spec sin romper esa convención.

### Campo `moneda` (obligatorio) y matching mono-moneda
| Campo | Nivel | Regla | Error |
|---|---|---|---|
| `moneda` | campaña | **obligatorio**; `'USD'` \| `'VES'` exacto | ausente/otro → `ErrorDeBrechaAseguramiento` (AC-e1) |
| `bono_moneda` | campaña (opcional) | si presente, **==** `moneda` | mezcla → `ErrorDeBrechaAseguramiento` (AC-D1) |
| `moneda` | compromiso (opcional) | si presente, **==** `moneda` de campaña | mezcla → `ErrorDeBrechaAseguramiento` (AC-D1) |

- `moneda` es obligatoria para **toda** campaña (spec regla 1, AC-e1 sin calificar por tipo). Un
  binario sin dinero igual la declara; queda inerte pero explícita.
- Importes siguen en **enteros de unidad mínima** (`monto_centavos`/`bono_patrocinador_centavos`).
  `centavos`=USD, `centimos`=VES: **misma clave** `*_centavos` (unidad mínima genérica), la moneda
  la fija `moneda`. Float sigue prohibido (regla del repo, ya vigente).

### Taxonomía privada nueva `TASA_KEYS` (tipo de cambio irrepresentable)
```python
# Fuera del bloque firewall compartido; privada de Capa 4 (como MARKET_KEYS en Capa 1).
TASA_KEYS = ['tasa_de_cambio', 'tipo_de_cambio', 'exchange_rate', 'fx', 'paralelo', 'bcv']
```
Escaneo recursivo con la maquinaria compartida `_key_matches_taxonomy` (tokeniza NFD+bigramas):
`tasa_de_cambio`→compuesto completo; `exchange_rate`→bigrama `exchange_rate`; `fx`/`paralelo`/`bcv`
→token simple. Cualquier clave-tasa en el payload (a cualquier profundidad) → `ErrorDeBrechaAseguramiento`
(AC-D3). *Por qué:* incrustar una tasa (BCV vs paralelo) = incrustar una decisión política capturable
(C-e3). La conversión es siempre decisión humana fuera del protocolo.

### Conservación exacta a 15+ dígitos (AC-D2, PB-e1)
Ya se cumple: `divmod` sobre enteros de Python (arbitrariamente grandes), resto determinista por
orden ascendente de ficha. La moneda **no** cambia la aritmética; solo la compuerta. Guardas
`ErrorDeInvarianteAseguramiento` intactas. Se añade property test hypothesis explícito con céntimos
VES de 15+ dígitos.

### Orden en `resolver()`
1. `isinstance dict` → `ValueError` (sin cambio).
2. guard `modo` (sin cambio, TA.4).
3. **NUEVO**: scan `TASA_KEYS` → `ErrorDeBrechaAseguramiento` (AC-D3).
4. scan `FORBIDDEN_KEYS` (sin cambio) → `ValueError`.
5. **NUEVO**: validar `moneda` obligatoria + `bono_moneda` (AC-e1, AC-D1).
6. validaciones existentes (campana_id, tipo, umbral, bono…).
7. bucle de compromisos: **NUEVO** matching `moneda` por compromiso (AC-D1).
8. reparto/conservación (sin cambio).

## Capa 1 — `src/partition/membrana.py` (taxonomía de mercado)
`MARKET_KEYS` ya incluye `usd, ves, dolar, dolares, bolivar, bolivares` (añadidos en TA.2) y ya se
rechazan en `don_comunal`/`igualdad` y se admiten en `precio_de_mercado` → **AC-e2 ya se cumple**.
Único cambio: alias de trazabilidad con la spec, fuera del bloque firewall:
```python
CLAVES_MERCADO = MARKET_KEYS  # alias castellano (spec área e); misma lista, misma referencia.
```

## Convención documentada (no forzable — señalar en README, sin código)
- `expira_en` corto para VES por riesgo inflacionario; el motor **no** modela inflación (sería otra
  tasa disputada) — C-e5, failure-model. Señalado, no mecanismo.
- Patrón diáspora: USD (diáspora) + VES (local) = **dos campañas paralelas mono-moneda**, jamás una
  mixta (spec regla 7).

## Impacto en regresión (piso 383)
Fixtures existentes sin `moneda` se **actualizan** (añadir `"moneda"`), conservando toda aserción:
- `tests/test_assurance_engine.py`: `TEST_A`, `TEST_B` → `+ "moneda"`.
- `tests/test_assurance_properties.py`: estrategia `campanas()` → `moneda = draw(sampled_from(['USD','VES']))`.
Se añade `tests/test_area_e_doble_moneda.py` (AC-D1/D2/D3, AC-e1/e2/e3, PB-e1). Meta: 383 → +N verdes.

## Gate TA.6
`AC-4; suite verde`; md5 firewall 5d693ec idéntico en las 6; grep-gate; `test_cross_layer_taxonomy`
intacto; conservación exacta a 15+ dígitos (PB-e1).
