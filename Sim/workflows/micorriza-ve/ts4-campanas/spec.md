# TS.4 — Campañas descriptivas VE

## Qué son

Escenarios de campaña con NOMBRE sobre los SUT VE — poblaciones **buena / neutra / mala** —
para los dos lados, cada uno **end-to-end reproducible byte a byte**. Track B sigue siendo
DESCRIPTIVO (distribuciones, jamás escalar por persona; jamás objetivo del loop — el guard
descriptive-only de TS.1/upstream sigue puesto). Track A (composite con los oráculos VE de
TS.2) sigue siendo parada dura.

## Escenarios

**B2B (`sim_b2b/campanas_ve.py`):** `ESCENARIOS_VE` con nombre →
- `usd_buena` — célula USD, población 100% circulator, `adversary_intensity=0`.
- `usd_neutra` — mezcla con neutrales (hoarder/wallflower), adversidad baja.
- `usd_mala` — los 4 arquetipos adversarios presentes, adversidad alta.
- `ves_buena` — **célula VES**: `moneda="VES"` + `expira_en_dias` (bicondicional D1, la
  campaña lo declara — el motor no tiene reloj y no caduca por su cuenta).
- `ves_mala` — VES + adversidad alta (hiperinflación + ataque: el escenario §3.1).

Plomería nueva (criterio, no mecánica): `RoundConfig` gana `moneda="USD"` y
`expira_en_dias=None`; `build_campaign` los pasa a `create_cell`. **La bicondicionalidad NO
se re-implementa en el harness** (sería una segunda copia del mecanismo — N11): la campaña
pasa lo que su config dice y el ledger real es quien rechaza una config confundida.

**C2C (`sim_c2c/campanas_ve.py`):** `ESCENARIOS_VE` →
- `paz_buena` — modo `paz`, mezcla cooperativa.
- `paz_mala` — modo `paz`, mezcla adversarial alta.
- `catastrofe_acotada` — **modo `catastrofe_acotada`** (la superficie TA.4 bajo carga real,
  con los topes del modo apretando de verdad).
- `ves_campana` — `moneda="VES"` en las campañas de aseguramiento.

## Criterios de aceptación

- **AC-s4.1 (byte a byte):** para CADA escenario, dos corridas con la misma semilla →
  `history` idéntico E `entry_hash` del journal idéntico (el hash es el testigo fuerte:
  cubre config, medidas y decisiones del researcher).
- **AC-s4.2 (Track A verde y completo):** ningún escenario se detiene; el reporte lleva las
  invariantes heredadas + las VE (composite conectado — si alguien lo desconecta, esto lo ve).
- **AC-s4.3 (VES de verdad):** en los escenarios VES, el evento `cell_created` de la traza
  lleva `moneda="VES"` y `expira_en_dias` — verificado sobre la TRAZA, no sobre la config
  (que la campaña diga VES no prueba que la célula lo sea).
- **AC-s4.4 (descriptivo):** Track B de cada escenario entrega distribuciones/agregados y el
  search space no contiene ningún objetivo derivado de Track B (guard existente, ejercido
  por escenario). C2C: el tipo `WelfareReport` sin dimensión por-agente sigue siendo el muro.
- **AC-s4.5 (control negativo de config):** una config VES SIN `expira_en_dias` no arranca —
  el LEDGER real la rechaza (`ValueError("expira_en_dias")`); el harness no la repara ni la
  completa (rechazar-no-reparar llega hasta la config de campaña).
- **AC-s4.6:** suite completa verde; pisos intactos.

## Verificación por mutación

(1) desconectar el composite en un build de escenario → AC-s4.2 rojo; (2) `ves_buena` deja
de pasar `expira_en_dias` → AC-s4.5/arranque rojo (el ledger real lo mata); (3) semilla
distinta en la segunda corrida del test byte-a-byte → rojo (el test no compara consigo
mismo); (4) escenario `catastrofe_acotada` degradado a `paz` → su assert de modo sobre los
envelopes de la traza rojo; (5) quitar un arquetipo adversario de `usd_mala` → el assert de
composición de población rojo.
