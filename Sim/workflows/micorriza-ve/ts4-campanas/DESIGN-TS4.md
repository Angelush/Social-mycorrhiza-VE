# DESIGN-TS4 — Campañas descriptivas VE (2026-07-17)

## §1 Qué se construyó

- **`sim_b2b/campanas_ve.py`** — 5 escenarios: `usd_buena/neutra/mala`, `ves_buena/mala`
  (célula VES = `moneda="VES"` + `expira_en_dias=60` declarado — el escenario §3.1:
  hiperinflación se responde con expiración, jamás con una tasa representable).
- **`sim_c2c/campanas_ve.py`** — 4 escenarios: `paz_buena/mala`, `catastrofe_acotada`
  (TA.4 bajo carga real) y `ves_campana` (TA.6 mono-moneda).
- **Plomería (criterio):** `RoundConfig` B2B gana `moneda`/`expira_en_dias`;
  `params_de_celula(cfg)` = fuente ÚNICA de los params (campaña Y tests — sin segunda copia);
  **la bicondicionalidad NO se re-implementa en el harness** (N11): la campaña declara y el
  ledger REAL rechaza la config confundida — probado en las DOS direcciones (VES sin
  expiración Y USD con expiración).
- **`cell_created` encabeza la traza de cada ronda.** Hallazgo de diseño: el oráculo fx lee
  la moneda de la célula DEL TRACE (`cell_created`) — sin sembrarlo, su cruce
  moneda-propuesta **nunca se armaba dentro de una campaña** (verde y ciego, la familia M2
  de TS.1). Ahora está armado, y AC-s4.3 juzga la traza, no la config.
- `tests/test_campanas_ve.py` (19): byte-a-byte por escenario (history E `entry_hash` del
  journal — el testigo fuerte), Track A completo y verde (set de invariantes asertado →
  desconectar el composite se VE), modo/moneda verificados EN EL CABLE, Track B
  distribucional/sin dimensión por agente, controles negativos de config.

## §2 Golden re-congelado (4ª vez, misma disciplina)

`9b68b654…` → `d783c1bc…` por construcción (`cell_created` en la traza); los 3 números
económicos verificados **byte-idénticos** antes de re-congelar.

## §3 Fan-out — séptima derogación de la regla de coste (TA.9)

TS.4 era «el candidato bueno» (volumen mecánico). Al diseñar, el volumen mecánico se encogió
otra vez: la plomería y el hallazgo de `cell_created` eran criterio; los tests quedaron en
~180 líneas parametrizadas cuyo contrato (nombres de escenario, asserts de traza, las dos
direcciones de la bicondicional, el testigo del journal) ES la parte difícil. Contrato ≈
artefacto → no se delegó. **Patrón de fase completa: en Sim-VE el fan-out no rindió ni una
vez** — el harness es criterio denso con poco relleno; distinto de los tests de AC de Fase 2
donde sí rindió (TB.2/TB.4/TB.7).

## §4 Mutación — 5/5

| # | Mutación | Rojos |
|---|---|---|
| M1 | desconectar el composite del build | 5 (el set de invariantes en cada escenario B2B) |
| M2 | `ves_buena` sin `expira_en_dias` | 2 (el ledger real mata el arranque) |
| M3 | 2ª corrida con otra semilla | 5 — el byte-a-byte compara de verdad, no consigo mismo |
| M4 | `catastrofe_acotada` degradada a `paz` | 1 exacto (el assert de modo EN EL CABLE) |
| M5 | `usd_mala` pierde un adversario | 1 exacto (composición de población) |

## §5 Resultado

Sim-VE **185 passed** (166 + 19). Pisos citados reales 2026-07-17: Sim **121** · C2C-VE
**441** · B2B-VE **404+3** · B2B **125+3**. **TS.1–TS.4 completos → Fase 3 (Sim-VE) CERRADA.**
