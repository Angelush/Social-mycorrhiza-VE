# Criterios de aceptación — micorriza-ve

> Binarios y verificables por un revisor independiente sin preguntar al autor. "Terminó" no
> es "se acepta": cada AC verifica el ARTEFACTO producido (código, test, doc), jamás el
> reporte del ejecutor. Los AC-T*/AC-D*/AC-M*/AC-C* del prompt fundacional quedan mapeados
> aquí; `evals/tests.md` les da los tres niveles (normal / borde / adversarial).

| ID | Criterio | Verificación (comando/artefacto) | Fija |
|---|---|---|---|
| **AC-1** | Piso de regresión: B2B 128 · C2C 293-equivalentes · Sim 121+ verdes en CADA gate de área | `pytest` por paquete; salida citada en el commit del gate | M2 |
| **AC-2** | El dominio vive: `banco_de_tiempo` ADMITIDA en sala `don_comunal`; `zona_urbana`, `underscore`, `rango_de_fechas` admitidas (cero falsos positivos de substring) | tests AC-T1/AC-T4 del área a; goldens `tokenizacion` | R2, P1 |
| **AC-3** | La vigilancia muere: `puntuación`/`puntuacion`, `cedula`/`cédula`, `rif` rechazadas en las 6 capas; bigramas (`lista`+`negra`) rechazados; valor string `"V-12.345.678"` (sintético) rechazado en cualquier payload; `descripción_del_score_musical` SIGUE rechazada | tests AC-T2/AC-T3; goldens `valores_identidad`; AC-X byte-idéntico | §B/§C, M6 |
| **AC-4** | Dinero exacto: campaña `USD` con compromiso `VES` → rechazada; conservación exacta del bono con céntimos VES de 15+ dígitos (hypothesis); `tasa_de_cambio`/`bcv`/`paralelo` irrepresentables en Capa 4 C2C **y** en B2B-VE | tests AC-D1/D2/D3 + delta 1; goldens `conservacion_ves` | M4, N3, N4 |
| **AC-5** | Modos y trinquete: request válido en `paz` rechazado en `catastrofe_severa` si excede retención/hops/payload; escalada unilateral válida; desescalada sin decisión `adoptada` → rechazada; `depurar()` determinista post-escalada | tests AC-M1/M2/M3; goldens `trinquete`; monotonía (hypothesis) | M10, U3 |
| **AC-6** | Convergencia: ráfaga de `presencia` sobre `zona:X` throttled por el cap del modo; `paso_maquinaria` representable (señal de ZONA); ninguna señal sobre PERSONA representable | test AC-C1 del área f | §G, P4 |
| **AC-7** | Puerta humana B2B: `salida_con_saldo` y `puente.pausar()` SOLO vía ratificación (ninguna helper directa); la pausa NO detiene el crédito interno; `anclar()` pura y determinista (mismo período → mismo hash); ningún punto de consulta público expone saldo+identidad | tests de los deltas 2/3/6/8 | M8, N7 |
| **AC-8** | Intocables: los 10 del prompt verificables por test en los TRES modos; invariantes B2B originales intactas (conservación, líneas acotadas, sanciones graduadas); en B2B-VE no existe score computado de solvencia | suite de intocables por modo; N2 test | M12 |
| **AC-9** | Honestidad: el README de cada workstream consolida **Señalados** (Sybil; juicio escalar en texto libre; `depurar` como convención del llamador; escalada abusiva; transporte/malla; parámetros de modo como gobernanza; E2 si sigue abierta) — presencia de CADA ítem, y ningún abierto "resuelto" solo en prosa | checklist sobre el README (binario por ítem) | N10 |
| **AC-10** | Scoping de taxonomías: `credito`/`saldo`/`deuda`/`moneda` ADMITIDAS en los esquemas propios del ledger B2B-VE; las mismas claves RECHAZADAS en C2C Capa 1 donde corresponde | goldens `b2b_scoping`; tests del delta 9 | M5, R3 |

## Regla de cola (donde vive el valor)

Los AC-4 (15+ dígitos), AC-5 (payload 512 B, severa), AC-7 (pausa con crédito vivo) y los
adversariales de `tests.md` son deliberadamente de cola: la agregada puede verse perfecta
mientras el caso raro y caro falla. Un gate NO pasa con los normales en verde y un solo caso
de cola rojo.
