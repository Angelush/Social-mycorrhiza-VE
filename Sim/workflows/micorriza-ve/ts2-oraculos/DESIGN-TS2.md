# DESIGN-TS2 — Oráculos Track-A nuevos (2026-07-17)

## §1 Qué se construyó

- **`sim_b2b/track_a_ve.py`** — `B2BTrackAVE` con `fx_irrepresentable`, `visibilidad_saldos`,
  `puerta_humana_ops_nuevas`; y `B2BTrackAComposite` (heredado + VE, nombres disjuntos
  asertados) cableado en la campaña → **una violación VE también DETIENE la campaña**.
- **`sim_c2c/track_a_ve.py`** — `C2CTrackAVE` con `moneda_unica_por_campana`; composite
  análogo en la campaña C2C.
- **Material observable** (sin él los oráculos son verdes y ciegos — lección M2 de TS.1):
  proposal `StatementProbe` + `ScopedStatements` (el mundo llama al `member_statement` REAL
  bajo `publico`, `miembro` propio y el cruce ajeno, y registra verbatim); proposals
  `PuentePausar`/`PuenteReanudar`; rol harness **`__auditor__`** (probes rotatorias + UN ciclo
  de puente por ronda — I-VE7: la pausa no toca el crédito interno, la campaña no se altera).
- Tests: `tests/test_ve_track_a.py` (23) — AST de independencia, plantados por AC, controles
  negativos, anti-vacuidad sobre mundos reales.

## §2 Decisiones que importan

- **Taxonomías/listas duplicadas VERBATIM, jamás importadas** (patrón de los oráculos
  heredados): `TASA_KEYS` == `_TASA_KEYS` del ledger (con variantes pegadas); `GATED_KINDS`
  == `ratification_kinds` + las ops nuevas. **Los kinds van en inglés** (`bridge_paused`,
  `member_exited`): el seam E2 está EN el cable y el oráculo sigue al cable, no a los docs.
- **`visibilidad_saldos` es un muro por TIPO** (cero hojas numéricas, bools excluidos), no una
  lista de nombres — la lección AC-7 de TB.4: `salud: 7` cae sin que nadie previera el nombre.
  Además: seudónimo **estable** por miembro (la estabilidad ES la utilidad del árbitro, D2/D3)
  y ≠ `member_id`; el cruce `miembro` ajeno debe quedar `Rejected`.
- **`puerta_humana_ops_nuevas` lleva control negativo de política:** `obligation_recorded`/
  `obligation_settled` NO exigen puerta — comerciar no se ratifica (N-d68.4 en espíritu). Un
  oráculo que exigiera puertas donde el diseño no las pone estaría inventando política.
- **`fx_irrepresentable` también vigila la FORMA:** una obligación que LLEVE `moneda` falla
  aunque el valor sea correcto — la mezcla debe seguir irrepresentable (D1), no meramente
  inusada. Y la propuesta de clearing debe llevar LA moneda de `cell_created`.
- **`moneda_unica_por_campana` juzga solo `resolver` exitosos** (un rechazo del SUT es su
  muro funcionando; el oráculo caza el muro BURLADO — mismo criterio que los heredados), y
  exige UN solo valor de moneda en request∪output (per-compromiso incluido).

## §3 Golden re-congelado (tercera vez, misma disciplina)

`entry_hash` `9ff674fc…` → `9b68b654…` POR CONSTRUCCIÓN (el reporte lleva 8 invariantes; la
traza lleva probes y ciclo de puente). Los 3 números económicos verificados **byte-idénticos**
antes de re-congelar. El shape-test de C2C (`gc1`) pasa a esperar las 7 invariantes.

## §4 Mutación — 5/5 cazadas, cada una en su test

| # | Mutación | Rojos |
|---|---|---|
| M1 | `TASA_KEYS = []` | 2 (los dos plantados de tasa) |
| M2 | muro por TIPO → «no hay `balance_cents`» | **1 exacto** (`…fails_by_type` — el plantado nominal sigue cayendo por nombre; solo el test por tipo distingue los mundos) |
| M3 | el auditor deja de emitir | 1 (anti-vacuidad de material) |
| M4 | `bridge_paused` fuera de `GATED_KINDS` | 1 (su plantado) |
| M5 | el composite devuelve solo la base | 1 (`gc1` shape — las 7 invariantes) |

## §5 Resultado

Sim-VE **149 passed** (126 + 23). Pisos citados reales 2026-07-17: Sim **121** · C2C-VE
**441** · B2B-VE **404+3** · B2B **125+3**. SIN FAN-OUT (los oráculos SON el criterio —
prohibidos de fan-out por la regla de orquestación; lo mecánico ya estaba resuelto en contexto).
