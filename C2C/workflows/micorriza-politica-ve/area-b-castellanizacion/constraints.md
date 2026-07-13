# Constraints — Área b · Castellanización (con cláusulas-porque)

- **C-b1. La tabla exhaustiva se escribe ANTES del renombrado (M7).**
  *Porque:* un renombrado mecánico sin mapa completo deja residuos parciales (un `asker` olvidado
  en un mensaje) que rompen la consistencia y el matching; el mapa primero convierte el renombrado
  en una transformación verificable con `grep`.
- **C-b2. `mode`→`sala` es obligatorio, no opcional.**
  *Porque:* el fork introduce `modo` de calibración; mantener `mode` crearía una colisión semántica
  entre "sala relacional" y "modo de hostilidad" imposible de leer y de matchear.
- **C-b3. Claves de esquema sin tildes; valores y mensajes con tildes.**
  *Porque:* separar robustez (claves ASCII, estables ante entrada inconsistente) de legibilidad
  (mensajes castellanos correctos para el humano que dispone).
- **C-b4. El renombrado no cambia ninguna semántica ni firma lógica.**
  *Porque:* es traducción, no rediseño; los 293 tests equivalentes deben pasar idénticos en
  comportamiento. Cualquier cambio de comportamiento pertenece a otra área, no a esta.
- **C-b5. Excepciones a `ErrorDeBrecha*` conservan su jerarquía y su punto de `raise`.**
  *Porque:* "rechazar, nunca reparar" depende de que cada breach siga levantando en el mismo lugar;
  renombrar la clase no debe mover ni tragar el `raise`.

## Verificación de residuos (gate)
`grep -rniE '\b(mode|asker|target|expires_at|vouches|facts|traces|adopted|revisit|admit|query|
match|sense|decide)\b' src/ tests/` → **vacío** (salvo dentro de comentarios de procedencia que
citen el nombre upstream explícitamente).
