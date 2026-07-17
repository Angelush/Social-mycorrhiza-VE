# TS.3 — Control negativo por invariante nueva (planta SILENCIOSA)

## El gate

El gate del harness upstream (ST6-vacuidad), replicado para CADA oráculo de TS.2: contra una
copia deliberadamente rota del SUT VE, el harness debe **cazar la brecha con su oráculo
independiente** — y la planta debe burlar **todos** los guards propios del SUT. Si el SUT roto
se auto-detecta (lanza), el test prueba la autodefensa del SUT, no el oráculo. Un harness que
no caza una planta silenciosa no es creíble cuando reporte una real.

## Las cuatro plantas (una por oráculo, quirúrgicas, en copias — el SUT real jamás se toca)

| Fixture | Oráculo que debe cazarla | La planta | Por qué es SILENCIOSA |
|---|---|---|---|
| `sim_b2b/negative_control/ve_fx_fixture` | `fx_irrepresentable` | `apply_clearing` inyecta `tasa_referencia` (la brecha BCV/paralelo del día) en el payload del evento `clearing_applied` que COMMITEA | el escáner `_TASA_KEYS` del ledger vigila los `params` de ENTRADA, no lo que el propio motor escribe en su log; la puerta `proposal_moneda` pasa (la moneda es la legal); L1 intacto (no mueve un centavo) |
| `sim_b2b/negative_control/ve_vis_fixture` | `visibilidad_saldos` | `member_statement` bajo `publico` devuelve TAMBIÉN `balance_cents` | el scope ES el muro — no hay segundo guard detrás (F-d3.6: el motor no autentica); nada relanza |
| `sim_b2b/negative_control/ve_gate_fixture` | `puerta_humana_ops_nuevas` | `bridge_paused` sale de `ratification_kinds` Y `puente_pausar` deja de escribir `ratified_by` en el payload | el check de ratificación vive EN esa lista (M8): quitado de la lista, `_apply` no pregunta; `replay` re-aplica con la MISMA copia rota → verde; el estado (`puente_pausado=True`) es idéntico al legal |
| `sim_c2c/negative_control/ve_moneda_fixture` | `moneda_unica_por_campana` | `resolver` deja de rechazar el `moneda` por-compromiso distinto del sobre (el check de coincidencia TA.6 se desactiva) y resuelve normal | la salida es indistinguible de una legal (la moneda del sobre); la mezcla solo se ve comparando request∪output — exactamente lo que hace el oráculo |

Cada planta se marca `# TS3 SILENT PLANT` en el punto exacto de diferencia y la cabecera del
archivo dice qué se rompió y por qué no se auto-caza.

## Criterios de aceptación (por planta, los cuatro patrones del gate upstream)

- **AC-s3.x.a (silencio):** la operación rota NO lanza — la planta burla los guards del SUT.
  (Si esto falla, el gate era la autodefensa: ST6.)
- **AC-s3.x.b (caza):** el oráculo VE independiente da FAIL sobre la traza del mundo/llamada
  conducida contra la fixture, con `exploit_trace` que nombra la brecha.
- **AC-s3.x.c (control):** el SUT real, mismo escenario → o rechaza (gate/moneda), o no emite
  (fx/vis), y el oráculo da PASS.
- **AC-s3.x.d (no-vacuidad quirúrgica, donde aplica):** el resto de guards de la fixture
  siguen VIVOS — p. ej. en `ve_gate_fixture` un `member_updated` sin `ratified_by` SIGUE
  lanzando (solo se abrió la puerta del puente); en `ve_moneda_fixture` un `moneda` de sobre
  inválido SIGUE lanzando (solo se abrió el per-compromiso).
- **AC-s3.5:** el SUT real byte-intacto (las plantas viven solo bajo `negative_control/`);
  suite completa verde; pisos intactos.

## Verificación por mutación

(1) des-silenciar una planta (reactivar el guard del SUT en la fixture) → su test `.a` rojo —
prueba que el gate mide el oráculo y no la autodefensa; (2) fixture «re-derivada» del SUT real
sin planta → `.a`/`.b` rojos (sanity de que la planta disparó); (3) cegar el oráculo
correspondiente (mutación TS.2-M1 re-aplicada) → `.b` rojo; (4) romper la cirugía (quitar
TAMBIÉN el guard vecino en `ve_gate_fixture`) → `.d` rojo; (5) `.c` contra fixture en vez del
real → rojo (el control es control).
