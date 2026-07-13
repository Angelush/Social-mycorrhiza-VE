# Acceptance — Área a · Firewall bilingüe

> Todos deterministas, offline, stdlib + pytest/hypothesis. Los tests de forma prohibida se
> parametrizan sobre `modo ∈ {paz, catastrofe_acotada, catastrofe_severa}` (invariante en los tres).

## Cross-layer (heredado, endurecido)
- **AC-X** — las seis capas comparten taxonomías **byte-idénticas** (las compartidas) y el escáner
  **desciende en tuplas/estructuras anidadas**. Se verifica por comparación directa de los
  conjuntos y por un payload anidado con forma prohibida en cada capa.

## Nuevos tests definitorios
- **AC-T1** — `banco_de_tiempo` **ADMITIDO** en sala `don_comunal` (regresión del falso positivo de
  substring; el test que define el fix).
- **AC-T2** — `puntuación` y `puntuacion` (con y sin tilde) **rechazadas** en las seis capas; ídem
  `cedula`/`cédula`, `rif`. (Normalización NFD.)
- **AC-T3** — valor string `"V-12.345.678"` en cualquier payload → **rechazado**; ídem un RIF
  `"J-12345678-9"` y un teléfono `"0412-1234567"`. (Escaneo de valores; probar anidado.)
- **AC-T4** — claves `zona_urbana`, `underscore`, `rango_de_fechas` **admitidas** (sin falsos
  positivos de substring).
- **AC-Ta5** — `lista_negra` (y `listaNegra`) **rechazada** por bigrama, aunque `lista` y `negra`
  por separado no lo estén.

## Property-based (hypothesis)
- **PB-a1** — tokenización/normalización: para toda cadena, `normalizar(NFD(x))` es idempotente y
  elimina diacríticos latinos; camelCase y no-alfanum producen la misma partición.
- **PB-a2** — el escáner de valores es estable bajo reordenamiento de claves del dict (determinismo).

## Gate
Suite completa verde; los 293 equivalentes traducidos siguen verdes tras integrar el firewall.
