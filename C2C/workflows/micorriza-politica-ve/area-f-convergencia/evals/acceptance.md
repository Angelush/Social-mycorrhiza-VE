# Acceptance — Área f · Convergencia

## Definitorio
- **AC-C1** — perfil de convergencia: una ráfaga de `presencia` sobre `zona:X` → **throttled** por el
  cap del modo (estricto en `severa`); `paso_maquinaria` sobre `zona:X` **representable**; **ninguna
  señal sobre una persona representable** (`sobre: 'persona:*'` → rechazado).

## Cortacircuitos
- **AC-f1** — una `alerta` sin contexto → amortiguada (contexto-antes-de-juicio).
- **AC-f2** — el velocity-cap está activo en los tres modos; el cap exigido en `severa` ≥ `acotada` ≥
  `paz` en estrictez (enlaza con AC-c5). Ningún modo lo apaga.
- **AC-f3** — alcance celular / cero-broadcast: una traza no se propaga fuera de su célula.

## Señal ambiental
- **AC-f4** — `paso_maquinaria` está en la whitelist de señales; solo válida sobre `zona:*`, nunca
  sobre `persona:*`.

## Gate
AC-6; suite verde.
