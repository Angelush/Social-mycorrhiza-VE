# Suite de tres niveles — micorriza-ve

> Por cada AC: un caso Normal (A), uno de Borde (B) y uno Adversarial (C). Los C tienen forma
> de cola: la acción correcta contradice la obvia. Entrada → salida esperada → regla de
> verificación. Los pares canónicos ejecutables viven en `golden-set/casos.json` y se
> convierten en tests reales en TA.2/TA.5/TA.6/TB.2.

## AC-2 / AC-3 — Firewall bilingüe (área a)

| Nivel | Entrada | Esperado | Verificación |
|---|---|---|---|
| A | clave `puntuacion` en cualquier capa | rechazada | token exacto en CLAVES_PROHIBIDAS |
| A | clave `banco_de_tiempo` en sala `don_comunal` | **admitida** | tokens `banco,de,tiempo` sin colisión |
| B | clave `bancoDeTiempo` (camelCase) | admitida | tokenización camelCase → mismos tokens |
| B | clave `puntuación` (con tilde) | rechazada | NFD → `puntuacion` |
| B | clave `zona_urbana` | admitida | regresión: `ban` ⊄ tokens (era FP substring) |
| C | clave `lista_negra_local` | rechazada | bigrama `lista+negra` — el matching por tokens NO puede perder claves compuestas |
| C | clave `descripción_del_score_musical` | **rechazada** | dirección de fallo CAL-1 conservada: `score` ES un token presente |
| C | valor string `"V-12.345.678"` dentro de un payload anidado (tuplas incluidas) | rechazado | escaneo de VALORES desciende como AC-X exige; regex cédula |
| C | clave `denominacion` en Capa 1 | rechazada | auditoría de expansión de raíces (M6): `denominat` era stem de substring |

## AC-4 — Dinero exacto (área e / delta 1)

| Nivel | Entrada | Esperado | Verificación |
|---|---|---|---|
| A | campaña `USD`, compromisos `USD`, bono repartido | conservación exacta | suma de repartos == bono |
| B | campaña `VES` con bono de 15+ dígitos de céntimos y 7 participantes | conservación exacta | hypothesis: ∀ montos, suma exacta; resto determinista |
| C | campaña `USD` con UN compromiso `VES` entre veinte válidos | `ErrorDeBrechaAseguramiento` — rechazo total, no filtrado del intruso | rechazar, nunca reparar |
| C | clave `tasa_de_cambio` en el request de campaña; clave `bcv` en B2B | rechazadas en AMBOS motores | N3 cruza los dos workstreams |

## AC-5 — Modos y trinquete (áreas c/d)

| Nivel | Entrada | Esperado | Verificación |
|---|---|---|---|
| A | request con retención 30 días en `paz` | admitido | tabla de límites |
| A | escalada `paz`→`catastrofe_severa` sin decisión | válida e inmediata | unilateral por diseño (U3) |
| B | el MISMO request válido en `paz`, en `catastrofe_severa` (retención > 7 días, payload > 512 B, hops > 2) | rechazado (no recortado) | M10 |
| B | `depurar(items, modo, ahora)` dos veces sobre el mismo estado | resultado byte-idéntico | pureza + determinismo |
| C | desescalada `catastrofe_severa`→`paz` con decisión `revisar` (no `adoptada`) | rechazada | el trinquete no cede ante decisiones tibias |
| C | secuencia: escalada→desescalada `adoptada`→escalada inmediata (miembro malicioso ciclando) | cada transición válida por separado; el ciclo queda REGISTRADO como vector en Señalados | ST4: el código fuerza el procedimiento, no la buena fe — sin cooldown inventado en silencio |

## AC-6 — Convergencia (área f)

| Nivel | Entrada | Esperado | Verificación |
|---|---|---|---|
| A | traza `presencia` sobre `zona:guaira-7` | admitida | señal whitelisted sobre ZONA |
| B | ráfaga de 50 `presencia` sobre la misma zona en `catastrofe_severa` | throttled por `velocity_cap` estricto | el cap ES el amortiguador de estampida |
| C | señal `paso_maquinaria` sobre `persona:X` (no zona) | irrepresentable/rechazada | jamás señal ambiental sobre persona |

## AC-7 — Puerta humana B2B (deltas 2/3/6/8)

| Nivel | Entrada | Esperado | Verificación |
|---|---|---|---|
| A | `anclar()` sobre el mismo período, dos nodos distintos | mismo hash raíz | determinismo I4 |
| B | `puente.pausar()` y, con puente pausado, un ciclo completo de clearing interno | clearing normal; solo el borde inerte | AC-7: sobrevivir a "USDT deja de ser viable" |
| B | `salida_con_saldo` negativo con avalista | plan de pago o absorción, vía ratificación | M8; el saldo no se esfuma |
| C | llamada directa a la helper interna de salida SIN pasar por ratificación | no existe tal camino (API no lo expone) | M8: la puerta no tiene lateral |
| C | export "público" pedido con identidad+saldo en claro | seudonimizado o rechazado | N7: mapa de matraqueo |

## AC-10 — Scoping (delta 9)

| Nivel | Entrada | Esperado | Verificación |
|---|---|---|---|
| A | `{"saldo": 120000}` en el esquema propio del ledger B2B | admitido | vocabulario nuclear (M5) |
| C | `{"saldo_de_favores": 3}` en C2C Capa 1 `don_comunal` | rechazado | CLAVES_LIBRO_RECIPROCIDAD sigue viva en C2C |
| C | `{"cedula": "V-12.345.678"}` en B2B | **rechazado** | B2B SÍ hereda vigilancia/identidad — el scoping no es un boquete |

## Regla de captura de la corrida

Interrupciones, reintentos y correcciones a mitad de área se registran en el commit del gate
(qué falló, por qué, qué se re-corrió): la corrida es la unidad de evaluación, no el estado
final. Un gate cuyo pytest pasó "a la tercera" lo dice.
