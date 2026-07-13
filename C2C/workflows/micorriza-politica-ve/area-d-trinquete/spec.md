# Spec — Área d · El trinquete asimétrico (transiciones de modo)

> Usa la Capa 6 existente (`gobernanza.py`), no construye capa nueva. Implementa
> `validar_transicion(actual, propuesto, decision_capa6=None)` en `src/modo/modo.py`. Cubre §F.

## La asimetría (el corazón del área)

| Sentido | Regla | Racional |
|---|---|---|
| **Escalada** (`paz`→`acotada`→`severa`, o salto directo a `severa`) | **Unilateral e inmediata**: cualquier token del círculo la dispara. | En un terremoto los segundos cuentan. El coste de una escalada falsa es solo menor riqueza de coordinación; el coste de una escalada tardía es que los datos se vuelven pasivo en plena crisis. |
| **Desescalada** (cualquier sentido hacia `paz`) | **Requiere `decision_capa6.verdicto == 'adoptada'`** sobre una propuesta `cambiar_modo` para ese círculo (consentimiento, sin objeción primordial). | Volver a un modo más laxo re-expande retención/alcance/payload: es una decisión de riesgo colectivo, no de un individuo. |

## Contrato de `validar_transicion(actual, propuesto, decision_capa6=None)`
Devuelve válido **solo si**:
- (a) es una **escalada** (el orden es `paz < catastrofe_acotada < catastrofe_severa`; `propuesto`
  es más estricto que `actual`), **o**
- (b) es una **desescalada** Y `decision_capa6 is not None` Y
  `decision_capa6.verdicto == 'adoptada'` para esa propuesta `cambiar_modo` y ese círculo.

Una transición no válida → rechazo. `actual == propuesto` no es transición (no-op explícito).

## La escalada obliga a `depurar()`
Por **convención + test** (no por efecto de una función pura): tras una escalada, el llamador debe
ejecutar `depurar(items, propuesto, ahora)` para que los items que exceden la nueva ventana más
estricta se eliminen/recorten. El helper y el test lo fijan; la garantía es convención (señalado).

## Monotonía
`validar_transicion` es monótona respecto al orden de modos: toda escalada es válida sin decisión;
ninguna desescalada es válida sin decisión `adoptada`. Se verifica con property-based (hypothesis)
sobre el orden total de los tres modos.
