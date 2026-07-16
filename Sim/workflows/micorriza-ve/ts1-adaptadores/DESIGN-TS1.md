# DESIGN-TS1 — Adaptadores del harness a los contratos VE (2026-07-17)

## §1 Decisiones de arquitectura

1. **Árbol `Sim-VE/`** = copia de `Sim/{src,tests}`; `Sim/` intacto como referencia upstream
   (patrón TA.2/TB.2). Verificado: `Sim/` sigue en **121 passed** tras el nodo.
2. **Se adapta el CABLE, no el harness** (forma E2 aplicada a este árbol): los identificadores
   internos del sim (dataclasses, nombres de método del engine, `FirmState`, `RoundConfig`)
   quedan en inglés; TODO lo que cruza al SUT habla VE. Los nombres de método del adaptador
   siguen al SUT (uno-a-uno, verbatim): `admitir/consultar/emparejar/resolver/sentir/decidir`.
3. **venv propio `.venv-sim/`** (pytest+hypothesis+networkx). networkx es legítimo SOLO en Sim;
   instalarlo en `.venv-ve` habría despertado los 3 skipped a-propósito de `B2B*/` y cambiado
   el piso documentado. Gitignored.
4. **Sub-bundle en `Sim/workflows/micorriza-ve/`** (patrón B2B: la spec acompaña al upstream);
   la spec de TS.1 se escribió ANTES del código (SALIDAS de spec.md raíz — tasks.md no tiene
   nodo de bundle para Fase 3; se satisfizo dentro de TS.1 sin decidir nada del humano).

## §2 El mapa de contratos (medido en vivo, no del papel)

- **C2C-VE:** sobres castellanos por la tabla M7 de TA.3 + `modo` (TA.4, guardado por capa —
  el harness lo manda SIEMPRE, knob `RoundConfig.modo='paz'`) + `moneda` en Capa 4 (TA.6,
  knob `RoundConfig.moneda='USD'`).
- **Reconciliación spec↔código (manda el código):** las TRAZAS de estigmergia conservan
  `about` (`_TRACE_KEYS` real); los HECHOS de legibilidad sí usan `sobre`/`afirmacion`.
  La tabla M7 decía `about`→`sobre` en general; el código de TA.7 no lo aplicó a trazas.
- **B2B-VE:** `create_cell` exige `moneda`+`sal_seudonimo`; `member_statement(id, scope,
  solicitante)` con scope posicional (el LLAMADOR lo dice: dios-del-harness = `comite_credito`,
  una firma mirándose a sí misma = `miembro` con `solicitante=ella`); `turnover_cents` (D1).
  Pass-throughs nuevos uno-a-uno: `salida_con_saldo`, `puente_pausar`, `puente_reanudar`.
- **Oráculos (track_a) y track_b re-derivan del cable VE**: taxonomías = las bilingües de VE
  duplicadas verbatim (jamás importadas); `_TOP_SCHEMA` = esquemas de salida VE sondeados en
  vivo contra los módulos reales y congelados en el oráculo.

## §3 Fixtures de control negativo — re-derivadas, misma planta

Las 5 fixtures (c2c n01/n02, b2b n01/n02, xcell) se reconstruyeron **copiando el SUT VE y
re-aplicando por programa la MISMA planta** documentada en cada cabecera. Verificado que cada
planta sigue SILENCIOSA contra los guards VE: la puerta `proposal_moneda` de TB.8b NO
auto-caza N-01 (guarda la unidad de cuenta, no la conservación — la propuesta corrupta lleva
la moneda legal de la célula); el check `_ESTADOS_OPERATIVOS` de TB.6 no caza NI-02 (el
extraño auto-registrado entra `active`). Los tests de control negativo del upstream pasan
todos contra las fixtures VE (AC-s1.7).

**Nota:** las fixtures B2B llevan copia VERBATIM de `firewall/herencia.py` (el ledger VE lo
importa por shim `__file__`-relativo). Son dependencias congeladas de una copia rota del SUT,
no «capas» nuevas del firewall; byte-idénticas a la de B2B-VE (verificado por md5 del archivo).

## §4 El golden del harness — investigado antes de regenerar

`test_golden.py` derivó SOLO en `entry_hash` (los params de `create_cell` llevan
`moneda`/`sal_seudonimo` y entran al hash del journal POR CONSTRUCCIÓN). Los tres números
ECONÓMICOS (42.5 / 64.62585034013605 / 0.23529411764705882) son **byte-idénticos** al
congelado upstream — verificado ANTES de re-congelar; el delta declarado vive en comentario
junto al hash nuevo.

## §5 Mutación (obligatoria) — 5/5 cazadas, M2 destapó un hueco real

| # | Mutación | Resultado |
|---|---|---|
| M1 | el adaptador traga la excepción del SUT (`admitir` → `{"admitido": False}`) | **7 rojos** (AC-s1.1 y familia) |
| M2 | el mundo emite `mode` en vez de `sala` | **VERDE al principio — hueco real**: Track A salta los `Rejected` POR DISEÑO, así que un mundo con el cable roto en todas partes parece un mundo con muros perfectos. → test nuevo `test_cooperative_interactions_are_actually_admitted`; tras él, **1 rojo exacto** |
| M3 | el mundo pierde `modo` del sobre | **1 rojo exacto** (el test anti-vacuidad `test_every_module_envelope_carries_modo` — el SUT guarda `modo`, nada más lo vería) |
| M4 | la raíz redirigida a `C2C/` upstream | **9 rojos** (AC-s1.6 incluido, diciendo qué pasó) |
| M5 | fixture n01 derivada del upstream inglés | **2 rojos** (la planta y el pin de archivos VE) |

**Lección de M2 (general):** un harness cuyo oráculo ignora los rechazos necesita un test
POSITIVO de flujo — «lo cooperativo pasa» — o el cable puede romperse entero en silencio.
Familia de la vacuidad ST6, del lado del conductor en vez del oráculo.

## §6 Resultado

- **Sim-VE: 126 passed** = 121 equivalentes + 5 de TS.1 (`pin_points_at_ve_tree`,
  `admitir_modo_invalido…`, `fixtures_derive_from_the_ve_sut`, `envelope_carries_modo`,
  `cooperative…admitted`). Grep-gate del cable inglés limpio.
- Pisos intactos, citados reales el 2026-07-17: Sim **121** · C2C-VE **441** ·
  B2B-VE **404+3** · B2B **125+3**.
- SIN FAN-OUT: el volumen era mecánico pero el contrato (qué se traduce y qué NO — el cable
  sí, el harness no; `about` vs `sobre`) era criterio fino en cada archivo; sexta aplicación
  de la regla de coste TA.9.
