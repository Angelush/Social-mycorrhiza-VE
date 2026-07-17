# DESIGN-TS3 — Control negativo por invariante nueva (2026-07-17)

## §1 Qué se construyó

Cuatro fixtures con UNA planta silenciosa cada una (`# TS3 SILENT PLANT` en el punto exacto),
construidas POR PROGRAMA copiando el SUT VE real y aplicando la cirugía (misma técnica que las
fixtures de TS.1); `tests/test_ve_negative_control.py` (17) con los cuatro patrones del gate
upstream por planta: **a** silencio · **b** caza por el oráculo · **c** control contra el SUT
real · **d** cirugía (los demás guards de la MISMA fixture siguen vivos).

| Fixture | Planta | Por qué es silenciosa (verificado, no supuesto) |
|---|---|---|
| `ve_fx_fixture` | `apply_clearing` escribe `tasa_referencia {bcv, paralelo}` en el payload COMMITEADO | `_TASA_KEYS` vigila params de ENTRADA, no lo que el motor escribe en su log; `proposal_moneda` pasa; `proposal_hash` cuadra (la planta va FUERA de `proposal`); L1 intacto |
| `ve_vis_fixture` | `publico` devuelve también `balance_cents` | el scope ES el muro; no hay segundo guard detrás (F-d3.6) |
| `ve_gate_fixture` | `bridge_paused` fuera de `ratification_kinds` + payload sin `ratified_by` | el check VIVE en esa lista (M8): quitado, `_apply` no pregunta; `replay` re-aplica con la misma copia rota; el estado resultante es byte-idéntico al legal |
| `ve_moneda_fixture` | el match `moneda` por-compromiso (TA.6/AC-D1) desactivado | la SALIDA es indistinguible de una legal; la mezcla solo se ve comparando request∪output — que es lo que hace el oráculo |

## §2 Hallazgo menor

El escáner recursivo del oráculo fx nombra la clave INTERNA (`bcv`) antes que la externa
(`tasa_referencia`) — ambas están en su taxonomía; el test acepta cualquiera de las tres.
No se «arregló» el orden del escáner: el exploit_trace nombra una clave real de la brecha.

## §3 Mutación — 5/5, cada una en su test exacto

| # | Mutación | Rojo |
|---|---|---|
| M1 | des-silenciar `ve_gate` (el kind vuelve a la lista) | `.a` (+`.b`) — **prueba que el gate mide el oráculo, no la autodefensa (ST6)** |
| M2 | `ve_vis` «re-derivada» sin planta | `.a`/`.b` (sanity de que la planta disparó) |
| M3 | cegar el oráculo fx (`TASA_KEYS=[]`) | `.b` de fx |
| M4 | demoler en vez de operar (quitar también `member_updated`) | `.d` del gate |
| M5 | el control `.c` apuntado a la fixture | `.c` de moneda — el control es control |

## §4 Resultado

Sim-VE **166 passed** (149 + 17). Pisos citados reales 2026-07-17: Sim **121** · C2C-VE
**441** · B2B-VE **404+3** · B2B **125+3**. Los SUT reales byte-intactos (test AC-s3.5 lo
fija). SIN FAN-OUT (las plantas son criterio puro — qué guard burlar y por qué es exactamente
lo que no se delega).
