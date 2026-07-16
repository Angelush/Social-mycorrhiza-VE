# Sim-VE — sub-bundle de Fase 3 (workstream S)

> Especificaciones de la adaptación del harness de simulación (`Sim/`) a los contratos VE
> producidos por las Fases 1 (`C2C-VE/`, cerrada en TA.9) y 2 (`B2B-VE/`, cerrada en
> TB.9). **El código del fork vive en `Sim-VE/`; `Sim/` queda intacto
> como referencia upstream** (piso 121), el mismo patrón que `C2C/`→`C2C-VE/` (TA.2) y
> `B2B/`→`B2B-VE/` (TB.2). Este sub-bundle vive dentro de `Sim/workflows/` por el mismo
> motivo que el de Fase 2 vive en `B2B/workflows/micorriza-ve/`: la spec acompaña al
> upstream que adapta.

## Mapa de nodos (Fase 3, `workflows/micorriza-ve/tasks.md` filas TS.1–TS.4)

| Nodo | Qué | Dir |
|---|---|---|
| TS.1 | Adaptadores del harness a los contratos VE; árbol `Sim-VE/`; suite equivalente verde | [`ts1-adaptadores/`](ts1-adaptadores/) |
| TS.2 | Oráculos Track-A nuevos (`fx_irrepresentable`, `moneda_unica_por_campana`, `visibilidad_saldos`, `puerta_humana_ops_nuevas`) — independientes del SUT (AST-check) | `ts2-oraculos/` (lo crea TS.2) |
| TS.3 | Control negativo por invariante nueva — planta SILENCIOSA (gate ST6-vacuidad del upstream, replicado) | `ts3-control-negativo/` (lo crea TS.3) |
| TS.4 | Campañas descriptivas VE — Track-B distribucional, reproducible byte a byte | `ts4-campanas/` (lo crea TS.4) |

## Reglas heredadas que gobiernan toda la fase

- **N11 — el SUT real se importa, jamás se reimplementa.** El adaptador es pass-through
  verbatim; un check «útil» dentro del adaptador es una segunda copia del mecanismo.
- **El norte del upstream sigue vigente:** el sim es conductor y oráculo, nunca segunda
  copia; Track A (integridad) y Track B (distribuciones) jamás se mezclan; Track B de C2C
  no puede emitir un escalar por persona **por el tipo de su salida**.
- Los oráculos de TS.2 **no importan el SUT** (si el oráculo consulta al SUT, mide la
  autodefensa del SUT, no la invariante).
- Las plantas de TS.3 deben burlar **todos** los guards propios del SUT VE — incluidos los
  que la Fase 2 añadió (p. ej. la puerta `proposal_moneda` de TB.8b) — o el control negativo
  prueba la autodefensa, no el oráculo (ST6-vacuidad).
- networkx es legítimo aquí (spec.md raíz) y **solo** aquí → venv propio `.venv-sim/`
  (meterlo en `.venv-ve` despertaría los 3 skipped a-propósito de `B2B*/`).
