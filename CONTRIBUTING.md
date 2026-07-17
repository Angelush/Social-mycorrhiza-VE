# Contribuir a Micorriza-VE

Gracias por el interés. Este proyecto valora unas pocas cosas con fuerza — léelas antes de
abrir un PR.

## Reglas de base (invariantes de diseño, no negociables)

1. **El agente propone, la puerta dispone.** Todo lo que mueva valor real permanece
   determinista y con puerta humana. No automatices la puerta irreversible de un solo sentido.
2. **Una invariante rota DETIENE, no promedia.** Una violación es un titular (corrida parada +
   traza del exploit), jamás un dato más dentro de una tasa de aciertos.
3. **La simulación conduce el código real.** `Sim/`/`Sim-VE/` jamás se convierten en una
   segunda copia del mecanismo. Se prueba contra los sistemas reales, no contra mocks.
4. **Anti-vigilancia primero (rama social).** No añadas legibilidad/scoring por delante de las
   partes que hacen imposible armar el scoring como arma.
5. **El FX es irrepresentable (rama VE).** No hay dónde escribir una tasa de cambio en el
   motor, a propósito. No abras ese hueco «por conveniencia».

Si un cambio tensiona una de estas, abre un issue para discutirlo *antes* de escribir código.

## Flujo de trabajo

1. Haz fork y rama desde `master` (`feature/nombre-corto` o `fix/nombre-corto`).
2. Prepara el entorno (dos venvs, a propósito — networkx solo es legítimo en Sim):
   ```bash
   python3 -m venv .venv-ve  && .venv-ve/bin/pip install pytest hypothesis
   python3 -m venv .venv-sim && .venv-sim/bin/pip install pytest hypothesis networkx
   ```
3. Haz el cambio. Acótalo y respeta el estilo circundante.
4. Corre las suites relevantes — todas deben seguir verdes:
   ```bash
   (cd B2B    && ../.venv-ve/bin/python  -m pytest -q)   # 125 passed, 3 skipped
   (cd C2C    && ../.venv-ve/bin/python  -m pytest -q)
   (cd B2B-VE && ../.venv-ve/bin/python  -m pytest -q)   # 404 passed, 3 skipped
   (cd C2C-VE && ../.venv-ve/bin/python  -m pytest -q)   # 441 passed
   (cd Sim    && ../.venv-sim/bin/python -m pytest -q)   # 121 passed
   (cd Sim-VE && ../.venv-sim/bin/python -m pytest -q)   # 185 passed
   ```
   Los 3 `skipped` de `B2B*/` son un bloque a propósito (cross-check networkx, ausente en
   `.venv-ve`): no son regresión y no se «arreglan».
5. Añade tests para el comportamiento nuevo (aceptación / propiedad / golden, según toque).
   Si el test es de criterio, verifícalo por mutación: un test que no se ha visto fallar no
   se sabe si prueba algo.
6. Abre un PR diciendo *qué* cambió y *contra qué invariantes lo verificaste*.

## Mensajes de commit

Asunto corto en imperativo; el cuerpo explica el «porqué». Referencia la sección del brief o
el AC de la spec cuando ayude (p. ej. `brief §10 paso 1`, `AC-L3`, `AC-d1.7`).

## Reportar problemas

Para bugs, incluye una reproducción mínima y el sub-proyecto (`B2B` / `C2C` / `Sim` / árbol
`-VE`). Para una sospecha de violación de invariante, incluye la traza del exploit — es el
reporte más valioso que existe aquí.

## Licencia de las contribuciones

Al enviar una contribución aceptas que se licencia bajo los términos del proyecto:
**GPLv3** para código y **CC BY-SA 4.0** para documentación (ver [`LICENSE.md`](LICENSE.md)).
