# Acceptance — Área c · Módulo `modo`

## Validación de límites
- **AC-M1** — el **mismo request válido en `paz` es rechazado en `catastrofe_severa`** si excede
  retención, `max_hops` o payload. (Se prueba cada uno de los tres límites por separado.)
- **AC-c1** — un request en `severa` con payload de 513 bytes → rechazado; con 512 → admitido.
- **AC-c2** — request sin `modo` o con `modo` inválido → `raise` (no default silencioso).
- **AC-c3** — rechazo, nunca recorte: un `expira_en` que excede la ventana **no** se recorta; se
  levanta la excepción y el request no produce salida.

## Depuración
- **AC-M3** — `depurar()` tras escalada **elimina/recorta determinísticamente** todo lo que exceda
  la nueva ventana; llamada dos veces con los mismos argumentos da el mismo resultado (idempotencia).

## Integración
- **AC-c4** — cada una de las seis capas invoca `validar_modo` sobre su envelope; un límite excedido
  se rechaza en la capa correspondiente con su `ErrorDeBrecha*`.
- **AC-c5** — `velocity_cap`: la estrictez exigida crece monótonamente `paz ≤ acotada ≤ severa`
  (relación, no valor absoluto).

## No-cruce con invariantes (parte de M1)
- **AC-c6** — en los tres modos, toda forma prohibida sigue rechazada idénticamente (el modo no
  abre ninguna puerta a un escalar/lista negra/peso de voto).

## Gate
Suite verde; AC-5 (parte M1) satisfecho.
