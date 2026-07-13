# Constraints — Área f · Convergencia (con cláusulas-porque)

- **C-f1. Reutilizar Capa 5; no construir capa nueva.**
  *Porque:* el problema de convergencia es de estigmergia + cortacircuitos, ya implementados; una
  capa nueva duplicaría mecanismo y superficie de ataque. El prompt lo exige explícitamente.
- **C-f2. `paso_maquinaria` es señal sobre una ZONA, jamás sobre una persona.**
  *Porque:* toda traza ambiental es sobre artefactos/caminos; una señal sobre persona sería un
  escalar/marca encubierta (invariantes 1/2). Se añade a la whitelist y se verifica que no admite
  `sobre: 'persona:*'`.
- **C-f3. Los cortacircuitos nunca se apagan; solo varían sus parámetros por modo.**
  *Porque:* invariante 8 — el anti-cascada es estructural; un modo que apagara el velocity-cap
  abriría la estampida que el sistema existe para amortiguar.
- **C-f4. `velocity_cap` estricto es el mínimo exigido en `catastrofe_severa`.**
  *Porque:* es justo en la crisis cuando la ráfaga de voluntarios es mayor y el canal (SMS/LoRa) más
  estrecho; el cap estricto es el amortiguador de estampida.
- **C-f5. Una `alerta` sin contexto se amortigua (contexto-antes-de-juicio).**
  *Porque:* una alerta desnuda propagada es el germen de una cascada de pánico o de una marca
  informal; el cortacircuito de contexto la retiene hasta que porte contexto.

## Alcance
Solo Capa 5 (más el `modo` para el cap por modo). No toca aseguramiento, membrana ni gobernanza.
