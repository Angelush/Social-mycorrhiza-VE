# Acceptance — Área e · Doble moneda

## Definitorios
- **AC-D1** — campaña `USD` con compromiso `VES` (o bono `VES`) → **rechazada**
  (`ErrorDeBrechaAseguramiento`). Simétrico: campaña `VES` con compromiso `USD` → rechazada.
- **AC-D2** — **conservación exacta** del bono con céntimos VES de **15+ dígitos**: suma de
  asignaciones == bono; resto determinista; sin float.
- **AC-D3** — clave `tasa_de_cambio` (y `fx`, `paralelo`, `bcv`, bigrama `tipo_de_cambio`) en un
  payload de Capa 4 → **rechazada**.

## Moneda y salas
- **AC-e1** — `moneda` ausente → rechazo (obligatoria).
- **AC-e2** — clave de precio/`usd`/`ves` en sala `don_comunal` o `igualdad` (Capa 1) → rechazada;
  en `precio_de_mercado` → admitida.

## Property-based (hypothesis)
- **PB-e1** — conservación monetaria: para todo bono y todo conjunto de comprometidos, `sum(asignaciones)
  == bono` con enteros arbitrariamente grandes (incluye escala hiperinflacionaria).

## No-pérdida (heredada)
- **AC-e3** — si no se alcanza el umbral, todo comprometido se hace entero (reembolso completo) en la
  moneda de la campaña.

## Gate
AC-4 (doble moneda); suite verde a escala de 15+ dígitos.
