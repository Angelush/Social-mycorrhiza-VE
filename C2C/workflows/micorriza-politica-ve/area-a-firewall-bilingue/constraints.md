# Constraints — Área a · Firewall bilingüe (con cláusulas-porque)

- **C-a1. Las cinco taxonomías son byte-idénticas entre las capas que las comparten.**
  *Porque:* si una capa tiene una lista distinta, se abre una grieta por donde una forma prohibida
  entra por la capa más laxa; la identidad byte-a-byte es lo que AC-X verifica y lo que hace del
  firewall una sola superficie, no seis.
- **C-a2. Matching por token exacto, nunca por substring.**
  *Porque:* el substring es la causa raíz de las auditorías 1 y 2 — deja pasar variantes
  (`puntuacion` no contiene `score`) y rechaza inocentes (`'ban' in 'banco'`). El token exacto +
  normalización cierra ambas.
- **C-a3. Normalización NFD con eliminación de diacríticos en la comparación; los VALORES y
  mensajes conservan tildes correctas.**
  *Porque:* robustez de matching (no depender de que el usuario escriba `puntuación` con tilde) sin
  degradar la legibilidad castellana de la salida. Las **claves de esquema van sin tildes**
  (`celula_id`), los valores/mensajes sí.
- **C-a4. Claves compuestas prohibidas se evalúan por bigramas de tokens adyacentes.**
  *Porque:* `lista_negra` tokeniza a `lista`+`negra`, ninguno prohibido por sí solo; sin el bigrama
  la lista negra entra disfrazada de dos palabras neutras.
- **C-a5. El escaneo de valores rechaza patrones de identidad; no intenta juicio semántico.**
  *Porque:* una cédula en un valor es una forma de dossier detectable por regex; pero "esta persona
  es un 3/10" es semántica, fuera del alcance de un firewall determinista (señalado en
  `failure-model.md` y `lo-intocable.md`). Se fija lo detectable, se declara lo que no.
- **C-a6. El escáner desciende en estructuras anidadas (tuplas/listas/dicts).**
  *Porque:* un patrón de identidad escondido en un valor anidado evadiría un escáner de superficie;
  AC-X exige el descenso.
- **C-a7. La expansión de cada raíz se audita antes de fijarla (M6).**
  *Porque:* una raíz demasiado ávida (`denominat`, `cents`) puede crear un falso positivo nuevo en
  el dominio de ayuda mutua; el sesgo "sobre-rechazar es seguro" **deja de serlo** cuando colisiona
  con ayuda mutua, así que cada raíz se justifica.

## Patrones exactos (fijados)
- Cédula: `\b[VE]-?\d{1,2}\.?\d{3}\.?\d{3}\b`
- RIF: `\b[JGVEP]-?\d{8}-?\d\b`
- Teléfono VE: `\b(\+58|0058|0)(4\d{2}|2\d{2})[\s.\-]?\d{7}\b`

*Porque:* fijar el patrón exacto en el spec (no dejarlo "aprox.") es lo que hace el test AC-T3
reproducible y byte-idéntico entre capas.
