# Spec — Área e · Doble moneda USD/VES sin conversión (Capa 4 + Capa 1)

> Capa 4 (aseguramiento) mono-moneda + taxonomía de mercado bilingüe en Capa 1. Cubre §D.

## Reglas de moneda (Capa 4)
1. Toda campaña de aseguramiento declara **`moneda: 'USD' | 'VES'`** (obligatoria).
2. Importes en **enteros de unidad mínima**: `centavos` (USD) / `centimos` (VES). **Prohibido
   float** (regla del repo, conservada).
3. **Compromisos y bono del patrocinador DEBEN coincidir con la moneda de la campaña.** Mezcla →
   `ErrorDeBrechaAseguramiento`. Sin excepciones.
4. **El tipo de cambio es irrepresentable dentro del motor.** Añadir a la taxonomía rechazada de
   Capa 4 los tokens/bigramas: `tasa_de_cambio, tipo_de_cambio, exchange_rate, fx, paralelo, bcv`.
5. **Convención documentada (no forzable):** `expira_en` corto para VES por riesgo inflacionario; el
   motor no modela inflación (sería otra tasa). Señalado.
6. **Conservación exacta a escala de hiperinflación:** el reparto del bono conserva la suma exacta
   con importes VES de 15+ dígitos (enteros de Python; testear explícitamente).
7. **Patrón de uso (README, sin código):** diáspora patrocina en USD junto a campañas locales en
   VES — **dos campañas paralelas mono-moneda, jamás una mixta**.

## Taxonomía de mercado (Capa 1)
La sala `precio_de_mercado` admite denominación; las salas `don_comunal` e `igualdad` la rechazan
(membrana direccional). La taxonomía `CLAVES_MERCADO` es bilingüe (ver `area-a-firewall-bilingue/`)
e incluye `usd, ves, dolar, dolares, bolivar, bolivares` para que la moneda solo sea representable
en la sala de mercado.

## Conservación (heredada, reforzada)
La suma de asignaciones del bono == bono (enteros; resto determinista). No se crea ni se pierde
valor. La no-pérdida (todo comprometido se hace entero si no se alcanza el umbral) se conserva del
motor original.
