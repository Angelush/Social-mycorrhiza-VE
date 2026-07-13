# Acceptance — Área d · Trinquete asimétrico

## Definitorios
- **AC-M2** — **escalada sin decisión: válida**; **desescalada sin decisión `adoptada`: rechazada**.
  Casos: `paz→acotada` sin decisión → válida; `severa→paz` sin decisión → rechazada; `severa→paz`
  con `decision_capa6.verdicto == 'adoptada'` correcta → válida; con verdicto `revisar` → rechazada.
- **AC-d1** — salto directo `paz→severa` sin decisión → válida (es escalada).
- **AC-d2** — desescalada con decisión `adoptada` **de otra propuesta u otro círculo** → rechazada
  (C-d2).
- **AC-d3** — `actual == propuesto` → no-op explícito (ni válida como transición ni error espurio).

## Property-based (hypothesis)
- **PB-d1** — **monotonía del trinquete**: para todo par `(actual, propuesto)` con `propuesto`
  más estricto, `validar_transicion(actual, propuesto)` es válida sin decisión; para todo par con
  `propuesto` más laxo, es inválida salvo decisión `adoptada`. Sobre el orden total
  `paz < catastrofe_acotada < catastrofe_severa`.

## Acoplamiento con depuración
- **AC-d4** — tras una escalada, el helper de convención ejecuta `depurar()` y el resultado no
  contiene items que excedan la nueva ventana (enlaza con AC-M3).

## Gate
AC-5 completo; monotonía verificada por hypothesis; suite verde.
