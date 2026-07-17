# TS.2 — Oráculos Track-A nuevos (invariantes VE)

## Qué son y dónde viven

Cuatro oráculos de integridad sobre las invariantes que las Fases 1–2 añadieron. **Ninguno
importa el SUT ni el adaptador** (AST-check): re-derivan todo de la traza registrada, con sus
PROPIAS copias de taxonomías y listas (duplicadas verbatim, jamás importadas) — un oráculo que
consulta al SUT mide la autodefensa del SUT, no la invariante.

| Oráculo | Lado | Módulo | Qué re-deriva |
|---|---|---|---|
| `fx_irrepresentable` | B2B | `sim_b2b/track_a_ve.py` | ningún evento/propuesta/extracto emitido lleva clave con forma de TASA (taxonomía propia bilingüe + variantes pegadas); las obligaciones NO llevan `moneda` (la mezcla sigue irrepresentable); toda propuesta de clearing lleva LA moneda de la célula (`cell_created`) |
| `visibilidad_saldos` | B2B | `sim_b2b/track_a_ve.py` | bajo `publico` el extracto es EXACTAMENTE `{"seudonimo"}` y **cero hojas numéricas — muro por TIPO**, no lista de nombres (lección AC-7 de TB.4); el seudónimo es estable por miembro (contrato del árbitro, D2/D3) y ≠ `member_id`; pedir `miembro` ajeno queda RECHAZADO |
| `puerta_humana_ops_nuevas` | B2B | `sim_b2b/track_a_ve.py` | todo evento de un kind con puerta (lista PROPIA: `cell_created`, `member_added`, `member_updated`, `clearing_applied`, `cell_paused`, `cell_resumed`, `member_exited`, `bridge_paused`, `bridge_resumed` — los dos últimos son «ops nuevas» D8; kinds en inglés por el seam E2) lleva `ratified_by` no vacío; `obligation_recorded`/`obligation_settled` NO la exigen (control negativo: no inventar puertas donde el diseño no las pone — comerciar no se ratifica, N-d68.4 en espíritu) |
| `moneda_unica_por_campana` | C2C | `sim_c2c/track_a_ve.py` | en cada `resolver` exitoso: `moneda` de salida == la del sobre; todo `moneda`/`bono_moneda` por-compromiso del request coincide con la del sobre (si el SUT dejó pasar una mezcla, el oráculo la ve); un solo VALOR de moneda en toda la salida |

## Material observable (el harness tiene que producirlo)

- **`StatementProbe`** (proposal nueva) + rol harness **`__auditor__`**: el mundo llama al
  `member_statement` real bajo los tres scopes (`publico` sin solicitante; `miembro` con
  `solicitante=member_id`; y el intento CRUZADO `miembro` con solicitante ajeno, que debe
  quedar `Rejected`) y registra `ScopedStatements` en la traza. Pass-through: el mundo no
  adjudica, registra lo que el SUT real devolvió o lanzó.
- **Ciclo `puente_pausar`/`puente_reanudar`** una vez por ronda (el auditor lo dispara):
  material real para `puerta_humana_ops_nuevas` sobre las ops NUEVAS — sin él, ese tramo del
  oráculo sería vacuo hasta TS.3. La pausa del puente no detiene el crédito interno (I-VE7),
  así que el resto de la campaña no se ve afectado.
- Los `resolver` ya fluyen (Convener, TS.1) con `moneda` en el sobre.

## Integración

`B2BTrackAComposite` / `C2CTrackAComposite`: corren el Track A heredado + el VE y funden los
resultados (nombres disjuntos). Las campañas usan el composite → **una violación VE también
DETIENE la campaña** (Track A es parada dura, no un dato más).

## Criterios de aceptación

- **AC-s2.1 (independencia, AST):** `track_a_ve.py` (ambos) no importa ningún módulo del SUT
  ni el adaptador; solo engine + dataclasses del propio mundo.
- **AC-s2.2 (fx):** traza limpia PASS; evento plantado a mano con clave `tasa_bcv` → FAIL;
  variante PEGADA (`tasadecambio`) → FAIL (la taxonomía no es la palabra exacta); obligación
  plantada con `moneda` → FAIL; propuesta de clearing con OTRA moneda → FAIL.
- **AC-s2.3 (visibilidad):** probe real PASS; `publico` plantado con `balance_cents` → FAIL
  **por tipo** (también con un campo que no está en ninguna lista, p.ej. `salud: 7` → FAIL);
  seudónimo == `member_id` plantado → FAIL; cruce ajeno NO rechazado → FAIL.
- **AC-s2.4 (puerta):** traza limpia PASS; `member_exited` plantado sin `ratified_by` → FAIL;
  `bridge_paused` plantado sin `ratified_by` → FAIL; control negativo: `obligation_recorded`
  sin `ratified_by` NO falla.
- **AC-s2.5 (moneda única):** traza limpia PASS; `resolver` plantado con salida en otra
  moneda → FAIL; request plantado con compromiso `moneda: "VES"` bajo sobre USD y salida
  exitosa → FAIL.
- **AC-s2.6 (anti-vacuidad, lección M2 de TS.1):** la campaña B2B real produce
  `ScopedStatements` y el ciclo `bridge_paused`/`bridge_resumed` en la traza, y la C2C
  produce `resolver` exitosos — los oráculos tienen material, no solo rechazos.
- **AC-s2.7:** campañas B2B y C2C con composite quedan verdes; suite completa verde;
  pisos intactos.

## Verificación por mutación (obligatoria)

(1) vaciar la taxonomía TASA del oráculo → AC-s2.2 rojo; (2) quitar el muro por TIPO de
`visibilidad_saldos` (dejar solo el set de claves) → el plantado `salud: 7`… ojo: `salud` es
clave fuera del set → seguiría cayendo; la mutación correcta es quitar AMBOS y dejar solo
«no hay balance_cents» → los plantados no-nominales quedan verdes = rojo del AC; (3) el
auditor deja de emitir probes → AC-s2.6 rojo; (4) quitar `bridge_paused` de la lista de la
puerta → su plantado queda verde = AC-s2.4 rojo; (5) el composite deja de fundir el VE →
los AC de campaña/plantados sobre composite rojos.
