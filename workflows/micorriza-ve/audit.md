# Auditoría del lazo — micorriza-ve (el juez)

> Los reportes son donde los buenos hallazgos van a morir. Esta tabla prueba que cada F/ST
> del `failure-model.md` vive como constraint, criterio de aceptación o tarea — verificado
> abriendo el archivo, no aceptando "está cubierto". Ninguna fila puede quedar en GAP.

| Hallazgo | Descripción corta | Reflejado en (archivo + ID) | Estado |
|---|---|---|---|
| F1 | deriva en renombrado masivo | constraints.md M7, M2; acceptance.md AC-1; tasks.md TA.3 (grep de residuos) | INCLUIDA |
| F2 | degradación de contexto entre áreas | context.md §Exclusiones (contexto mínimo); simulation.md §episódico; tasks.md (un episodio por nodo) | INCLUIDA |
| F3 | alucinación de completitud | constraints.md M2 (salida pytest citada); acceptance.md AC-1 (números explícitos) | INCLUIDA |
| F4 | firewall bilingüe mata el dominio | constraints.md M6, P1; acceptance.md AC-2; golden-set `tokenizacion` | INCLUIDA |
| F5 | fallos de cola (hiperinflación, 512 B, snapback, éxodo) | acceptance.md AC-4/5/7 + §Regla de cola; tests.md niveles B/C; constraints.md E3; tasks.md TB.6 | INCLUIDA |
| F6 | Goodhart en Sim-VE | constraints.md §Matriz (Track-B Measure-only), N11; spec.md Fase 3 (muro de TIPO); tasks.md TS.2–TS.3 | INCLUIDA |
| ST1 | "verbatim" del delta 9 prohibiría el vocabulario B2B | constraints.md M5, R3; acceptance.md AC-10; golden-set `b2b_scoping` | INCLUIDA |
| ST2 | token-exacto rompe stems (`denominat`, `_cents`) | constraints.md M6; acceptance.md AC-3; golden `denominacion`; tasks.md TA.2 (auditoría de raíces) | INCLUIDA |
| ST3 | colisión `mode`→`sala` vs `modo` por orden de áreas | tasks.md deps duras TA.2→TA.3→TA.4; constraints.md M7; simulation.md (segunda trampa) | INCLUIDA |
| ST4 | escalada abusiva; `depurar()` no forzable | acceptance.md AC-5 (caso C), AC-9 (Señalados); constraints.md N10; failure-model.md §límite honesto | INCLUIDA |
| ST5 | confundir crédito/USD/USDT | constraints.md N3; acceptance.md AC-4; context.md §Terminología | INCLUIDA |
| ST6 | puertas laterales en ops nuevas | constraints.md M8; acceptance.md AC-7 (caso C: el camino no existe); spec.md §semántica de operaciones | INCLUIDA |
| ST7 | datos con forma de identidad en el repo | constraints.md N8; tests.md §goldens sintéticos; golden-set `_nota` | INCLUIDA |
| ST8 | gitlinks rotos heredados; historia B2B/Sim perdida | tasks.md T0.2/T0.3 (hecho, commits `3a22f51`/`a50f7d2`); constraints.md E4 (upstream = humano) | INCLUIDA |
| ST9 | hechos VE caducan | context.md §VOLÁTIL; constraints.md M9, E3; tasks.md TP.1, TB.8 | INCLUIDA |
| ST10 | tests de topología del entorno | constraints.md N12, R1 | INCLUIDA |

**Veredicto: todas las filas INCLUIDA — cero GAP.** Los hallazgos que por naturaleza no
tienen mecanismo (juicio escalar en texto libre; cooldown de escalada como parámetro de
gobernanza) NO se marcan resueltos: viven en la lista Señalados que AC-9 exige por presencia,
que es exactamente lo que N10 permite hacer con ellos.
