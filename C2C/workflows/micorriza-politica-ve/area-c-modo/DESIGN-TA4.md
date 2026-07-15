# TA.4 — Diseño de implementación · Área c · módulo `modo`

> Deliverable de diseño (Opus) previo al cableado mecánico. Fija las invariantes, resuelve los
> huecos declarados con propuestas documentadas, y da la tabla de cambios exacta por archivo.
> Alcance TA.4 = tabla de límites + `validar_modo` + integración en las 6 capas + propuesta
> `velocity_cap`. **`depurar()` y `validar_transicion()` son TA.5 (área d)** según `tasks.md`;
> NO se implementan aquí (se omiten del módulo para no dejar código muerto).

## Decisiones de arquitectura

- **D1 — Módulo único importado, NO copiado.** El failure-model exige "la tabla vive en un solo
  módulo; las capas la consultan, no la copian". Por eso `modo` NO sigue el patrón byte-idéntico
  del bloque firewall (ese se duplica *a propósito* para resistir un único parche debilitador). La
  tabla de límites es una constante de gobernanza y debe tener fuente única (mitiga "deriva de
  límites entre capas").
- **D2 — Import bajo carga standalone vía shim `__file__`-relativo.** Cada capa se carga en los
  tests con `spec_from_file_location` sin `src` en `sys.path`. Las capas resuelven `modo` con, al
  tope del archivo (FUERA del bloque firewall):
  ```python
  import os, sys
  sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
  from modo.modo import validar_modo, ErrorDeModo
  ```
  Verificado: la carga standalone resuelve `modo.modo` con este shim. `modo` no importa ninguna
  capa (C-c6, sin ciclos): es hoja del grafo.
- **D3 — Integración guardada `if 'modo' in <envelope>:`.** El gate de TA.4 es "suite verde"
  (piso 341). Los 341 tests existentes no llevan `modo`. Cada capa invoca `validar_modo` **solo si
  el envelope trae `modo`**; ausencia de `modo` en el envelope de una capa = no engancha (compat).
  **Señalado:** la mandatoriedad dura de `modo` (spec: "obligatorio junto a `celula_id`") es
  postura de *despliegue*, no del motor en fase de construcción; el envelope opta por `modo` y,
  presente, se aplica sin piedad. `validar_modo` *sí* es estricto por contrato (AC-c2): recibido un
  request con `modo` ausente/ inválido → `raise`. La distinción es: la función es estricta; el
  punto de llamada de cada capa es opt-in mientras los envelopes migran.
- **D4 — La capa re-lanza como su propio `ErrorDeBrecha*` (AC-c4).** `validar_modo` levanta
  `ErrorDeModo`; cada capa lo captura y re-lanza como su excepción (`raise ErrorDeBrechaX(str(e))
  from e`), para que "un límite excedido se rechaza en la capa correspondiente con su
  `ErrorDeBrecha*`".

## Tabla de límites (`LIMITES`) — defaults (C-c3)

| clave interna | `paz` | `catastrofe_acotada` | `catastrofe_severa` |
|---|---|---|---|
| `retencion_max_dias` | 365 | 45 | 7 |
| `retencion_trazas_dias` | 90 | 14 | 3 (72 h) |
| `max_hops` | 4 | 3 | 2 |
| `max_payload_bytes` | 65536 | 8192 | 512 |
| `max_proposals` | 20 | 10 | 5 |
| `estrictez_velocidad` (ordinal) | 1 (laxo) | 2 (medio) | 3 (estricto) |
| `tope_velocidad_max` (propuesto) | 50 | 10 | 3 |

`retencion_trazas_dias` lo consumirá `depurar()` en TA.5; se declara ya para tener la tabla completa
en un solo sitio.

## Huecos declarados — propuestas (documentadas)

- **`velocity_cap`.** El prompt declara el hueco. Propongo dos representaciones:
  - `estrictez_velocidad`: ordinal `1<2<3` que satisface AC-c5 (la *relación* `paz ≤ acotada ≤
    severa`, no un valor absoluto).
  - `tope_velocidad_max`: cota concreta propuesta (50 / 10 / 3) sobre el `tope_velocidad` que ya
    consume `estigmergia.sentir`. Menor = más estricto → severa la más estricta. Es una **propuesta
    de gobernanza**, no un valor validado en campo (failure-model). `validar_modo` la aplica solo si
    el request trae `tope_velocidad`.

## Semántica de medición (decisiones deterministas)

- **Payload.** `max_payload_bytes` se mide sobre el **envelope completo** serializado en JSON
  canónico: `json.dumps(request, sort_keys=True, ensure_ascii=False,
  separators=(',', ':')).encode('utf-8')`, `len(...)`. Justificación: el límite de 512 B en severa
  modela SMS/LoRa, donde lo que debe caber en el canal es *el mensaje entero*, no un sub-campo.
  Universal a las 6 capas (ninguna necesita un campo `carga` dedicado). AC-c1 fija la frontera
  512/513 construyendo un envelope que serializa a ese tamaño exacto.
- **Retención.** `expira_en − ahora` en granularidad de **días de calendario**: se parsean los
  primeros 10 caracteres (`YYYY-MM-DD`) de `expira_en` y `ahora` como `date`; si
  `(expira - ahora).days > retencion_max_dias` → `raise`. Se aplica **solo** cuando `expira_en` y
  `ahora` son ambos cadenas ISO. **Señalado:** en Capa 5 `ahora` es un tick entero sin mapeo
  calendario fijo → la retención por tiempo NO se aplica ahí vía `validar_modo`; la ventana de
  trazas de Capa 5 la gobierna `depurar()` (TA.5) en ticks provistos por quien llama.
- **`max_hops` / `max_proposals`.** Se aplican solo si la clave existe en el request (enteros, no
  `bool`); `> límite` → `raise`. `max_hops` es Capa 2, `max_proposals` es Capa 3, pero
  `validar_modo` es agnóstico: valida el campo si está presente.

## Superficie del módulo (TA.4)

- `MODOS = ('paz', 'catastrofe_acotada', 'catastrofe_severa')`
- `class ErrorDeModo(Exception)`
- `LIMITES: dict` (tabla de arriba)
- `ESTRICTEZ_VELOCIDAD`, `TOPE_VELOCIDAD_MAX` (derivables de `LIMITES`; se exponen para el test AC-c5)
- `validar_modo(request) -> str` — estricto: `modo` ausente/inválido → `raise ErrorDeModo`; aplica
  payload, retención, `max_hops`, `max_proposals`, `tope_velocidad`. Devuelve el `modo` validado.
- `estrictez_velocidad(modo) -> int` — helper ordinal para AC-c5.

## Tabla de cambios por archivo

| archivo | cambio |
|---|---|
| `src/modo/__init__.py` | nuevo, vacío (paquete) |
| `src/modo/modo.py` | nuevo módulo (superficie de arriba) |
| `src/partition/membrana.py` | shim import + `'modo'` añadido a `_ENVELOPE_KEYS` + llamada guardada en `admitir` re-lanzando `ErrorDeBrechaMembrana` |
| `src/legibility/legibilidad.py` | shim import + llamada guardada en `consultar` → `ErrorDeBrechaLegibilidad` |
| `src/matcher/emparejador.py` | shim import + llamada guardada en `emparejar` → `ErrorDeBrechaEmparejador` |
| `src/stigmergy/estigmergia.py` | shim import + llamada guardada en `sentir` → `ErrorDeBrechaEstigmergia` |
| `src/governance/gobernanza.py` | shim import + llamada guardada en `decidir` → `ErrorDeBrechaGobernanza` |
| `src/assurance/aseguramiento.py` | shim import + llamada guardada en `resolver` → `ErrorDeInvarianteAseguramiento` (su tipo de brecha) |
| `tests/test_area_c_modo.py` | nuevo: AC-M1, AC-c1..c6 |

**Invariantes que NO se tocan:** bloque firewall byte-idéntico en las 6 — md5
`5d693ecf1833fb760e173ee3db30a263` (span: bloque `BEGIN…END` completo, incluido su `\n` final
= 3023 bytes) — (el shim y
la llamada van FUERA de `BEGIN/END shared firewall machinery`); `FORBIDDEN_KEYS` canónico
(`test_cross_layer_taxonomy`); escáneres privados. Piso de regresión: **341 verdes**.
