# Constraints — Área d · Trinquete asimétrico (con cláusulas-porque)

- **C-d1. Escalada unilateral e inmediata; desescalada solo por `adoptada` de Capa 6.**
  *Porque:* la asimetría es deliberada — en crisis el error seguro es escalar de más (se pierde
  riqueza de coordinación, recuperable); el error caro es escalar tarde (los datos abiertos se
  vuelven pasivo bajo represión). Volver atrás re-expande la exposición, así que exige consentimiento
  colectivo.
- **C-d2. La desescalada exige la propuesta `cambiar_modo` correcta para ESE círculo.**
  *Porque:* una decisión `adoptada` de otro círculo o de otra propuesta no autoriza; el consentimiento
  es local y específico (invariante de gobernanza circular, sin auto-propagación).
- **C-d3. `validar_transicion` fuerza el PROCEDIMIENTO, no la buena fe.**
  *Porque:* el código no puede impedir que un miembro malicioso escale repetidamente; solo garantiza
  que desescalar requiera consentimiento. La buena fe y el cooldown son decisiones de gobernanza
  abiertas (señaladas), no mecanismos incrustados.
- **C-d4. La escalada obliga a `depurar()` por convención, no por efecto.**
  *Porque:* `validar_transicion` es pura; no persiste ni dispara `depurar`. El acoplamiento
  escalada→depuración es convención documentada + test + helper. Fingir que la función lo garantiza
  sería "fake-resolved".
- **C-d5. Usar la Capa 6 existente; no construir capa nueva.**
  *Porque:* el consentimiento sociocrático ya está implementado y testeado en `gobernanza.py`;
  duplicarlo crearía dos fuentes de verdad de "adoptada".

## Vector documentado (señalado)
Escalada abusiva: un token puede degradar la coordinación escalando en bucle. Contrapeso: la
desescalada por consentimiento. Parámetro de fricción opcional (cooldown) = decisión de gobernanza
abierta, documentada en `failure-model.md`.
