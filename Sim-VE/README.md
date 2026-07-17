# Sim-VE — harness de simulación, fork Venezuela (workstream Fase 3)

> Árbol de trabajo del fork venezolano del harness **Sim**. El harness upstream vive intacto en
> `../Sim/` como referencia; las especificaciones del fork (el *porqué* de cada decisión) viven
> en el sub-bundle [`../Sim/workflows/micorriza-ve/`](../Sim/workflows/micorriza-ve/); este
> README consolida, no reemplaza.

El harness maneja el código **REAL** de `B2B-VE/` y `C2C-VE/` con poblaciones de actores
buenos/neutros/malos — driver y oráculo, jamás una segunda copia del mecanismo (regla N11: el
SUT se importa, nunca se reimplementa). Una invariante violada detiene la corrida; nunca se
promedia.

## Qué añadió el fork (TS.1–TS.4, cerradas 2026-07-17)

| Tarea | Qué es | Commit |
|---|---|---|
| TS.1 | Adaptadores del harness a los contratos VE (nombres castellanos, envelope con `modo`); adaptador pass-through, sin lógica propia | `1b57e15` |
| TS.2 | Oráculos Track-A nuevos: `fx_irrepresentable`, `moneda_unica_por_campana`, `visibilidad_saldos`, `puerta_humana_ops_nuevas` — independientes del SUT (verificado por AST-check) | `f780894` |
| TS.3 | Control negativo por invariante nueva: plantas **silenciosas** (el SUT roto burla sus propios guards; si se auto-detectara, el test probaría la autodefensa del SUT, no el oráculo) | `a3a7d53` |
| TS.4 | Campañas descriptivas VE (poblaciones buena/neutra/mala; Track-B distribucional), reproducibles byte a byte | `526bdb0` |

## Estructura

- `src/engine/` — motor compartido (campaña, mundo, journal, medición, políticas)
- `src/sim_b2b/`, `src/sim_c2c/`, `src/sim_integrated/` — los tres harness contra los SUT reales
- `src/*/negative_control/*_fixture/` — copias **deliberadamente rotas** del SUT (plantas):
  parecen duplicación, no lo son; consolidarlas destruiría el control negativo
- `tests/` — 185 tests

## Correr la suite

Venv propio (`networkx` solo es legítimo aquí, no en `.venv-ve`):

```bash
python3 -m venv .venv-sim && .venv-sim/bin/pip install pytest hypothesis networkx   # en la raíz, una vez
cd Sim-VE && ../.venv-sim/bin/python -m pytest -q   # 185 passed
```
