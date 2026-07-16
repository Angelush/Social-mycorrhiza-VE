# DESIGN — TB.9: D10, branding + README B2B-VE + conservación a hiperinflación

**Fecha:** 2026-07-16 · **Deps:** TB.2–TB.8b ✅ · **Piso de entrada:** 396+3 (tras TB.8b).
Nodo documental + property tests finales. Análogo a TA.8. **SIN FAN-OUT** (regla de coste TA.9,
quinta aplicación consecutiva: el criterio del README y los Señalados JAMÁS se delegan, y el
contrato de firmas del test de conservación —estrategia hypothesis con garantía anti-vacuidad,
AC-d10.4— ES el test; lo mecánico que quedaba no llega al volumen que hace rentable el reparto).

## 0. Entregables

1. **`B2B-VE/README.md`** — spec §3, siete secciones; AC-9 es GATE HUMANO (queda pendiente de
   lectura del propietario; se dice, no se finge — ST-d10.3).
2. **`B2B-VE/tests/test_conservacion_hiperinflacion.py`** — PB-1..PB-4 + AC-d10.4 (anti-vacuidad).
3. **`B2B-VE/tests/test_d10_branding.py`** — AC-d10.1 (vocabulario), AC-d10.2 (esquema intacto),
   AC-d10.3 (referencia, no copia — la parte mecanizable).
4. **Corrección del volátil caducado** (obligación de M9 §4.2): la brecha ~16,5% →
   **12,27%** en `B2B/micorriza-b2b-venezuela-adaptacion.md` (líneas 40 y 108 — es donde vive;
   `context.md` la cita por referencia), APUNTANDO a `docs/verificaciones/2026-07-15-cripto.md`,
   no duplicando la verificación.
5. **Vocabulario:** el barrido previo cazó `«wallet»` en un MENSAJE DE ERROR de
   `multisig.py:250` (fijado con `match=` en `test_d4_multisig.py`) → se reforma mensaje y test.

## 1. Reconciliaciones (spec contra AC — manda lo ejecutable, patrón TB.7)

1. **Spec §3.1 pide decir «Qué NO es: moneda, token, inversión, banco»; AC-d10.1 exige CERO
   `token` en el README.** Manda el AC: el README dice las negaciones por perífrasis («no es
   una moneda, no es un activo criptográfico transferible, no es una inversión, no es un
   banco») — la intención de §3.1 se cumple sin violar el grep. «moneda» a secas NO está
   prohibida (solo «la moneda de»/«nuestra moneda», N-d10.2).
2. **`token(s)` aparece en `herencia.py` (bloque congelado, md5 `5d693ec`) y `tokenize` en el
   ledger** — uso LÉXICO, no lenguaje de producto (N-d10.2: la palabra no es el problema, lo es
   qué nombra), y el bloque es intocable por AC-d9.1. → lista `ADMITIDAS` con motivo escrito en
   el test (patrón AC-d7.4), no relajando la regla.
3. **`«petro»` en `docs/verificaciones/2026-07-15-cripto.md`** cita la Gaceta (ley que nombra
   al petro) y es un ARTEFACTO FIRMADO → manda el artefacto (patrón TB.8); además vive fuera de
   `B2B-VE/`. El scan cubre `B2B-VE/` (README, docs/, src/) y las salidas de los 4 renders.

## 2. Los property tests (spec §5)

- **PB-1 (AC-4):** importes de 15+ dígitos en centavos; `clear()` conserva `net_positions`
  EXACTAMENTE; `sum(balance_cents)==0` en el ledger tras secuencias aceptadas.
- **AC-d10.4 (anti-vacuidad, F-d10.6/ST-d10.4):** la ESTRATEGIA afirma ≥15 dígitos dentro del
  test (no se confía en el default de hypothesis) y una fracción de casos lleva ciclo GARANTIZADO
  por construcción — en ésos se afirma `gross_after < gross_before` y se registra con
  `hypothesis.event()`.
- **PB-2:** type-walk recursivo: ningún `float` en estados, eventos ni salida de `clear()`.
- **PB-3:** L1 tras secuencias arbitrarias aceptadas que INCLUYEN `salida_con_saldo`,
  `puente_pausar/reanudar` (las nuevas). Las rechazadas (`ValueError`) no cuentan pero tampoco
  ensucian (assert_rejects implícito: el estado no cambia).
- **PB-4:** determinismo de `anclar` sobre cadenas arbitrarias (mismo stream → misma raíz).

## 3. Qué NO hace (E-d10.1, F-d10.7)

No resuelve ningún Señalado (ST-d68.7 entra como PREGUNTA ABIERTA, no como resuelto); no
renombra identificadores (E2); no toca goldens; no toca `herencia.py`; no cierra el seam
bilingüe. Todo Señalado «resoluble con un mecanismo pequeño» → nodo futuro, no aquí.

## 4. Resultado (2026-07-16)

**Suite: 396+3 → 404 passed + 3 skipped** (+4 `test_conservacion_hiperinflacion.py`,
+4 `test_d10_branding.py`). `B2B/` 125+3, `C2C-VE/` 441, `herencia.py` diff VACÍO, `5d693ec`
en las 7 copias, **goldens NO tocados** (AC-d10.2).

**Entregados:** `B2B-VE/README.md` (34 Señalados ordenados por quién paga — miembro/comité/red,
AC-d10.5; ST-d68.7 como PREGUNTA ABIERTA; procedencia por módulo; seam E2 sin disimulo) ·
property tests PB-1..PB-4 + AC-d10.4 · scanner de vocabulario (archivos + SALIDAS VIVAS de los
4 renders) · volátil 16,5%→12,27% corregido en `micorriza-b2b-venezuela-adaptacion.md`
APUNTANDO a la verificación fechada · `«wallet»` eliminado del mensaje de error de multisig
(test `match=` reformado con él).

**Mutación: 5 corridas, 5 cazadas — pero M1 NO CAYÓ A LA PRIMERA (sexto defecto en un test de
criterio de Opus, y es EXACTAMENTE la vacuidad que AC-d10.4 vigila):** el assert de 15 dígitos
comparaba contra `MIN_15` — la misma constante que la mutación degradaba → **tautología: la
vara degeneraba con la estrategia y la suite quedaba en 404 verdes con AC-4 convertido en
mentira.** Endurecido a vara LITERAL (`len(str(x)) >= 15`); M1 repetida → 1 rojo.
**Lección (familia de M9/TB.8): un assert que vigila una constante no puede medirse CON esa
constante — la vara y lo medido tienen que tener orígenes distintos.**
- M2 el solver pierde 1 centavo de un settlement → **6 rojos** (PB-1 incluido: la conservación
  a 15+ dígitos caza el centavo).
- M3 `obligation_settled` acredita `amount+1` → **30 rojos** (L1 por todas partes).
- M4 `_hojas` ordenadas por hash → **7 rojos** (PB-4 + D2).
- M5 «wallet» en un docstring del ledger → **1 rojo, exactamente el escáner** (control negativo).

**Reconciliaciones ejecutadas (§1):** negaciones por perífrasis (el README no contiene
`token`); `herencia.py` ADMITIDA con motivo (léxico + bloque congelado); «petro» en la
verificación firmada, fuera del scan (manda el artefacto).

**GATE HUMANO SALDADO — AC-9 y AC-d10.5 APROBADOS por el propietario el 2026-07-17**
(«APROBADO. Cierra la fase 2»). Con esa aprobación **TB.9 queda CERRADO y Fase 2 CERRADA**.
Piso final de Fase 2: **B2B-VE 404 passed + 3 skipped** · B2B 125+3 · C2C-VE 441.
