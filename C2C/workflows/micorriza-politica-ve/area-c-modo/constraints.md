# Constraints — Área c · Módulo `modo` (con cláusulas-porque)

- **C-c1. El modo es por célula, en el envelope; jamás estado global.**
  *Porque:* un modo global sería un punto único de control (y de captura) sobre toda la red —
  exactamente el trono que el invariante 5 prohíbe. El policentrismo por célula es lo que permite
  que La Guaira esté en `severa` mientras Mérida sigue en `paz`.
- **C-c2. Rechazar, nunca recortar.** Un request que excede su límite de modo → `raise`.
  *Porque:* recortar silenciosamente un `expira_en` o un payload es "reparar" contenido del
  llamador, que el repo prohíbe; el llamador debe ver el rechazo y decidir, no recibir un dato
  mutilado que cree correcto.
- **C-c3. Los valores de la tabla son defaults, ajustables solo por Capa 6.**
  *Porque:* la calibración es una decisión de gobernanza, no una constante moral; incrustarlos como
  dogma escondería una decisión política en el código. Se documentan como defaults.
- **C-c4. El módulo `modo` no calibra nada fuera de retención, alcance, payload y cortacircuitos.**
  *Porque:* si un modo pudiera tocar una forma prohibida (un score en `severa`), el modo sería una
  puerta trasera a los invariantes. Los modos calibran cantidad, jamás forma (ver `lo-intocable.md`).
- **C-c5. `depurar()` es pura y determinista; su ejecución es convención del llamador.**
  *Porque:* una función pura no persiste ni dispara efectos; no puede obligar al llamador a
  depurar tras una escalada. Se declara como señalado y se acompaña de helper + test, no se finge
  garantía.
- **C-c6. `modo` no importa ninguna capa (sin ciclos).**
  *Porque:* la maquinaria compartida debe ser una hoja del grafo de dependencias; un ciclo
  capa↔modo rompería la pureza y el aislamiento entre capas.

## Hueco declarado (velocity_cap)
Los valores numéricos de `velocity_cap` (laxo/medio/estricto) se proponen en implementación y se
documentan. *Porque:* el prompt declara el hueco explícitamente; fijarlos sin dato sería inventar
una decisión de gobernanza.
