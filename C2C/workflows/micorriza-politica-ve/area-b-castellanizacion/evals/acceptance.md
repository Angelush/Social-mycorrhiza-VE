# Acceptance — Área b · Castellanización

## Equivalencia
- **AC-b1** — los **293 tests equivalentes** (traducidos al castellano y al nuevo esquema) pasan,
  con comportamiento idéntico a la suite upstream.
- **AC-b2** — `grep` de residuos (ver `constraints.md`) → **vacío** salvo comentarios de procedencia.

## Consistencia de esquema
- **AC-b3** — toda clave pública de entrada/salida está en la tabla de renombrado; no hay clave en
  inglés en ningún payload de test.
- **AC-b4** — `mode` no aparece como clave en ninguna capa; `sala` (Capa 1) y `modo` (transversal)
  son distintos y ambos presentes.
- **AC-b5** — verdictos `adoptada`/`revisar`, posturas `consentir`/`objetar`/`abstenerse`,
  excepciones `ErrorDeBrecha*` presentes y usados consistentemente.

## Gate
`mode`→`sala` sin residuos (grep); 293 equivalentes verdes.
