# Spec — Área f · Perfil de convergencia en desastre (sobre Capa 5)

> Reutiliza la estigmergia existente; **no** construye capa nueva. Cubre §G.

## El problema modelado
Convergencia de voluntarios en desastre ("las motos obstaculizando la maquinaria pesada"): una
ráfaga de presencia sobre una zona satura la coordinación. Se modela sobre las trazas y
cortacircuitos existentes de Capa 5, no con lógica nueva.

## Trazas y señales
- Trazas con `sobre: 'zona:<id>'` (artefacto, nunca persona).
- Señales existentes castellanizadas: `presencia` (ex `presence`), `camino` (`path`), `alerta`
  (`flag`), `contribucion` (`contribution`), `respaldo` (`endorsement`).
- **Nueva señal ambiental en la whitelist: `paso_maquinaria`** — una zona señalada para paso de
  maquinaria pesada. Es señal **sobre una ZONA (artefacto)**, jamás sobre una persona: debe
  verificarse que no viola la regla de traza-ambiental (whitelist, no sobre-persona).

## El amortiguador de estampida
El `velocity_cap` de Capa 5 **es** el amortiguador de convergencia de voluntarios: throttlea la
ráfaga de `presencia` sobre una zona por ventana. En `catastrofe_severa` el cap mínimo exigido es
**estricto** (ver `area-c-modo/`).

## Cortacircuitos (heredados, activos en todo modo)
- Fricción / velocity-cap por ventana (parámetro por modo).
- Contexto-antes-de-juicio: una `alerta` sin contexto se amortigua.
- Alcance celular / cero-broadcast.
El mecanismo **nunca se apaga**; solo varían sus parámetros por modo (invariante 8).

## Ejemplo venezolano completo (a documentar en el bundle)
Zonas de **La Guaira / Caracas** tras un deslave: ráfaga de `presencia` sobre `zona:la-guaira-01`
→ throttling por el cap estricto de `severa`; una zona marcada `paso_maquinaria` queda
representable y visible; una `alerta` sin contexto sobre la zona se amortigua; **ninguna señal
sobre una persona es representable**.
