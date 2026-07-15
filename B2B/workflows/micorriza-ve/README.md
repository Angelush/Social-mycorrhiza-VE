# Sub-bundle B2B-VE — specs del fork Venezuela (Fase 2)

> Extensión VE del bundle upstream [`../micorriza/`](../micorriza/). **No lo reemplaza: lo
> extiende.** Donde este sub-bundle calla, manda el bundle upstream; donde habla, manda este.
> Driver: [`../../micorriza-b2b-venezuela-adaptacion.md`](../../micorriza-b2b-venezuela-adaptacion.md)
> (§3 arquitectura, §8 deltas 1–10). Grafo: [`../../../workflows/micorriza-ve/tasks.md`](../../../workflows/micorriza-ve/tasks.md)
> (nodos TB.0–TB.9).

Escrito en TB.1 (M1: specs ANTES que código). Cero archivos bajo `src/` en este nodo.

## Layout — organizado por DELTA, no por nodo

El grafo (`tasks.md`) enumera nodos TB.*; el anexo §8 y `spec.md` enumeran deltas D1–D10. La
unidad de trabajo verificable es el **delta** (cada uno tiene su AC), y un nodo puede llevar
dos deltas. Los directorios van por delta; esta tabla es el mapa.

| Delta | Directorio | Nodo | Qué |
|---|---|---|---|
| D9 | [`d9-herencia-scoping/`](d9-herencia-scoping/) | TB.2 (primero) | Scoping M5 de la herencia C2C — **la trampa**; se construye ANTES que D1 |
| D1 | [`d1-unidad-de-cuenta/`](d1-unidad-de-cuenta/) | TB.2 | Unidad de cuenta USD, célula mono-moneda, pista VES, FX irrepresentable |
| D2 | [`d2-anclaje/`](d2-anclaje/) | TB.3 | `anclar()` pura sobre la cadena de hashes **ya existente** |
| D3 | [`d3-visibilidad/`](d3-visibilidad/) | TB.4 | Scope `comite_credito`; seudonimización de exportes |
| D5 | [`d5-referencias-comerciales/`](d5-referencias-comerciales/) | TB.5 | Veteo relacional sin score |
| D6+D8 | [`d6-d8-bordes/`](d6-d8-bordes/) | TB.6 | `salida_con_saldo` + `puente.pausar()`, ambas por la puerta M8 |
| D7 | [`d7-exportes/`](d7-exportes/) | TB.7 | `exportar_registros(miembro, periodo)` |
| D4 | [`d4-multisig/`](d4-multisig/) | TB.8 | Gobernanza del multisig + helpers; el motor sin claves |
| D10 | [`d10-branding/`](d10-branding/) | TB.9 | Branding + README B2B-VE + conservación a escala de hiperinflación |

**Por qué D9 primero dentro de TB.2:** es maquinaria compartida, y el criterio heredado de
Fase 1 es que la maquinaria compartida se construye una sola vez, primero, con el tier más
alto (`tasks.md`, presupuesto de fiabilidad). Además D9 mal hecho no rompe un test: rompe el
vocabulario del ledger entero (ver `d9-herencia-scoping/failure-model.md`).

Cada directorio lleva `spec.md` · `constraints.md` · `failure-model.md` · `evals/acceptance.md`.
Los `DESIGN-TB*.md` los añade cada nodo al ejecutarse (patrón TA.4–TA.7), no TB.1.

## Documentos de cabecera

- [`intent.md`](intent.md) — el objetivo real del fork B2B-VE y qué NO es
- [`context.md`](context.md) — contexto VE que manda + **decisiones fechadas** (E2, D1)
- [`architecture.md`](architecture.md) — clasificación por componente, corregida para VE
- [`lo-intocable.md`](lo-intocable.md) — invariantes heredadas + las que añade el fork

## Método (heredado de Fase 1, TA.3–TA.8 — funcionó)

1. Specs y evals PRIMERO; el gate humano M1 antes de tocar `src/`.
2. Diseño en un `DESIGN-TB*.md` por nodo, escrito por el modelo tope.
3. Si toca tests, fijar el **contrato de firmas** ANTES de delegar.
4. Reconciliar spec↔código cuando la prosa y el código discrepen: **manda el código**
   (pasó en TA.6 y TA.7; vuelve a pasar aquí — ver `context.md`, §8.9 vs. M5).
5. Cada nodo cierra con suite verde + commit. El fallo se detecta en el nodo que lo produjo.

## Piso de regresión (verificado 2026-07-15, TB.0)

```
cd B2B && ../.venv-ve/bin/python -m pytest -q
125 passed, 3 skipped in 8.76s
```

**128 RECOLECTADOS = 125 passed + 3 skipped.** Los 3 skipped son un solo bloque
(`tests/test_clearing_solver.py:247`, cross-check del solver contra `networkx`) que se salta
porque `networkx` no está en `.venv-ve` — coherente con `spec.md` («networkx solo en Sim») y
con la P1 upstream («`networkx` allowed only in tests as an independent cross-check»). **No
son regresión y no hay que "arreglarlos".** Quien lea «B2B 128» en el grafo y espere 128
passed, romperá el gate por una lectura, no por un fallo.
