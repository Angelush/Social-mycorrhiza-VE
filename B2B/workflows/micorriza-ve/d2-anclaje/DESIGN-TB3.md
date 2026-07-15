# DESIGN-TB3 — D2: `anclar()` sobre la cadena existente

> Escrito por Opus ANTES del código (método TA.4–TB.2). Nodo TB.3, cuelga de TB.2 (`a6eb0b5`).
> Cubre **un** delta (D2), por eso vive dentro de `d2-anclaje/` y no en la raíz del sub-bundle
> (a diferencia de `DESIGN-TB2.md`, que cubría D9+D1).
>
> Specs que mandan: [`spec.md`](spec.md), [`constraints.md`](constraints.md),
> [`failure-model.md`](failure-model.md), [`evals/acceptance.md`](evals/acceptance.md).
> Este documento **no re-decide** nada de ellas: fija cómo se ejecuta y qué se delega.

## 0. El delta real: la mitad ya está hecha

Verificado en el código de `B2B-VE/src/ledger/mutual_credit_ledger.py` (confirma TB.0):

| Pieza | Estado | Dónde |
|---|---|---|
| Encadenado `prev_hash`/`hash` | **ya existe** | `_apply:370-387` |
| `verify_chain(events)` | **ya existe y testeada** | `:616-652` |
| `replay(events)` | **ya existe y testeada** | `:596-614` |
| `canonical()` determinista | **ya existe** | `:71-73` |
| `anclar()` | **no existe** | ← esto es TB.3 |

**D2 no construye una cadena: añade una función pura encima de una que ya está testeada
(AC-L4).** El nodo es aditivo puro → cero regresión esperada (AC-d2.8).

## 1. Geometría: módulo nuevo, no más ledger

`anclar` va en **`B2B-VE/src/ledger/anclaje.py`**, un módulo nuevo. **No** dentro de
`mutual_credit_ledger.py`.

*Porque:* C-d2.1 dice que `anclar` es pura y N-d2.2 que no toca el estado ni emite evento. Un
archivo aparte hace ese corte **visible en la geometría**, igual que TA.6/TA.7 sacaron las
taxonomías de dominio del bloque compartido y TA.4 puso `modo.py` como hoja del grafo. El
ledger exporta operaciones `op(state, ...) -> (new_state, event)`; `anclar` no tiene esa forma,
y meterla ahí invita al siguiente lector a darle un `ratified_by` (**F-d2.6**).

Dirección de la dependencia: `anclaje` importa de `mutual_credit_ledger` (`verify_chain`,
`canonical`); **el ledger no importa `anclaje`**. Sin ciclos, y el ledger queda literalmente
sin tocar (`git diff` vacío sobre él = la prueba de AC-d2.8).

Carga: mismo **shim de path `__file__`-relativo** que ya usa el ledger para `firewall.herencia`
(patrón TA.4) — los tests cargan por ruta con `spec_from_file_location`, sin `src` en `sys.path`.

## 2. Las cuatro funciones (tres públicas + una privada que los tests SÍ usan)

```python
def anclar(events: list, desde_seq: int, hasta_seq: int) -> dict
def prueba_de_inclusion(events: list, desde_seq: int, hasta_seq: int, seq: int) -> list
def verificar_inclusion(hoja_hash: str, prueba: list, raiz: str) -> bool
def _raiz_merkle(hojas: list) -> str          # privada, pero es el sujeto de AC-d2.1/AC-d2.4
```

**`_raiz_merkle` es privada y aun así la testean AC-d2.1 y AC-d2.4 directamente. Es
deliberado, y es la única forma de que esos dos AC existan:**

- **AC-d2.4** exige comparar la raíz de `[e1,e2,e3]` contra la de `[e1,e2,e3,e3]`. Ese segundo
  conjunto **no puede pasar por `anclar`**: `verify_chain` lo mata en la puerta (`seq != i+1`)
  antes de llegar al árbol. Si el test solo pudiera entrar por `anclar`, el AC que **más
  importa** del delta sería inexpresable — y F-d2.1 (la duplicación de Bitcoin) quedaría sin
  detección.
- **AC-d2.1** necesita el mismo acceso para comparar orden-por-seq contra orden-por-hash.

O sea: `verify_chain` protege `anclar` tan bien que **hace inalcanzable el caso que hay que
probar**. La respuesta correcta no es debilitar `anclar` para que el test entre; es testear la
construcción del árbol por debajo. El subrayado del guión bajo es para el llamador de
producción, no para el test.

## 3. La construcción del árbol (fijada en spec §4 — aquí solo se ejecuta)

- Hojas = `event["hash"]` de los eventos con `desde_seq <= seq <= hasta_seq`, **en orden de
  `seq` ascendente**. Nunca ordenadas por hash (**F-d2.5**).
- Nodo interno = `sha256(bytes.fromhex(izq) + bytes.fromhex(der)).hexdigest()`. Se concatenan
  los **bytes**, no el hex: el hex son 64 caracteres ASCII y hashear el texto es hashear una
  representación, no el valor.
- **Nivel impar → se PROMOCIONA el huérfano tal cual al nivel siguiente. JAMÁS se duplica.**
  Duplicar es `CVE-2012-2459` y es el patrón que un ejecutor copia de Bitcoin por reflejo
  (**F-d2.1**). Éste es **el** punto del nodo donde equivocarse destruye el delta entero: el
  propósito de D2 es evidencia inviolable, y la duplicación la vuelve violable.
- `n == 1` → la raíz **es** la hoja (bucle de niveles no entra; sin envolturas).
- `n == 0` → `ValueError` (**C-d2.6**). No se ancla la nada.

## 4. Orden de validación en `anclar` — importa

1. `verify_chain(events)` **primero**, y se propaga su `ValueError` (**C-d2.2**). Anclar una
   cadena rota le presta credibilidad al fraude: es peor que no anclar (**F-d2.3**).
2. Luego el rango: enteros estrictos (`_is_strict_int`, no `bool`), `desde <= hasta`, y ambos
   dentro de los `seq` existentes.
3. Luego las hojas; `n == 0` → `ValueError`.

Con `events == []`, `verify_chain` pasa trivialmente (itera sobre nada) y el rango es quien
lanza. Correcto y deliberado: el orden 1→2 es una regla sobre **qué se ancla**, no un atajo de
validación.

**`anclar` recibe la lista COMPLETA de eventos y el rango como enteros** — nunca una sublista
pre-recortada (**ST-d2.4**). Es lo que hace que la verificación sea de la cadena y no de un
fragmento que el llamador eligió.

## 5. Lo que `anclar` NO hace (y por qué el nodo se resiste a añadirlo)

| Reflejo | Por qué se resiste |
|---|---|
| Publicar la raíz | **N5/F-d2.2.** Un motor con red se cae en el apagón (§2.9) y se vuelve capturable. El motor emite; el llamador publica. La frontera **es** que el motor no tiene red. |
| Pedir `ratified_by` | **F-d2.6.** `anclar` es read/emit: radio ninguno, no mueve valor. M8 nombra las operaciones de valor nuevas; ésta no lo es. Añadirlo es fricción que además le miente al siguiente lector. |
| Firmar / manejar claves | **N-d2.3/N9.** Eso es D4 (TB.8) y ni allí el motor custodia. |
| Un `kind` nuevo | No añade ningún evento → no toca `ratification_kinds`. |

## 6. Señalados (no fake-resueltos — N10)

- **ST-d2.1 — La raíz sola no prueba CUÁNDO.** Merkle prueba «esto estaba en este conjunto»,
  no «esto existía el martes». La marca temporal la da la publicación, que está fuera del
  motor. **El motor produce el insumo de lo que §2.11 necesita, no la propiedad.** Va al README
  de TB.9.
- **ST-d2.2 — El anclaje no impide reescribir; permite detectarlo.** Una célula puede llevar
  dos libros y anclar el conveniente. El contra-mecanismo es social (réplica entre nodos, §3.3),
  no criptográfico.
- Cadencia, cadena pública y quién paga el gas: decisión operativa del comité (P-d2.1). El
  motor recibe el rango, no lo elige.

## 7. Reparto — **todo Opus, sin fan-out**

`multi-model-orchestration`: al cierre de TB.2, `coding` → `agy-gemini-3-flash` fit **+12.09**
(seen 28, 6/6 verdes) sería el candidato de siempre para los tests mecánicos.

**No se delega en este nodo.** Dos razones, y la segunda es la que decide:

1. El usuario no está para aprobar el fan-out, y el reparto es decisión suya (regla
   permanente del workstream: *preguntar antes de asumir*). Sin aprobación → Opus, como TB.1.
2. Aunque estuviera, **AC-d2.4 y AC-d2.7 no son tests mecánicos**. AC-d2.4 es exactamente el
   caso de **ST-d2.3 (auto-confirmación)**: quien no entiende la promoción escribe un test que
   verifica la implementación contra sí misma y pasa en verde con el árbol roto. Ese test
   **es** el delta. Es criterio, no mecánica → Opus por la regla que ya existe.

`reasoning` → sin modelo libre probado → specs e invariantes siempre Opus.

## 8. AC de cierre del nodo

- **AC-7** (global) — `anclar` determinista: mismos eventos + mismo rango → dicts byte-idénticos
  vía `canonical`; y misma raíz con `PYTHONHASHSEED` distinto (subproceso real).
- **AC-d2.1** — la raíz depende del orden de `seq`, no del hash.
- **AC-d2.2** — pureza: no muta `events`; sin `state` en la firma; `socket.socket` y el `open`
  del módulo parcheados para lanzar.
- **AC-d2.3** — `verificar_inclusion` verifica **sin los eventos en el ámbito**; prueba
  manipulada → `False`.
- **AC-d2.4** — **el que importa:** `[e1,e2,e3]` vs `[e1,e2,e3,e3]` → raíces **distintas**.
- **AC-d2.5** — cadena rota (alterar `payload`/`ts`/`prev_hash`/`hash`) → `ValueError`, sin raíz.
- **AC-d2.6** — bordes del rango (n=1 → raíz es la hoja; n=0, `desde>hasta`, fuera de rango,
  sublista → `ValueError`).
- **AC-d2.7** — property (hypothesis): toda hoja del período es probable; ninguna de fuera lo es.
- **AC-d2.8** — cero regresión: `git diff` vacío sobre `mutual_credit_ledger.py`; piso
  **155 passed + 3 skipped** intacto, más los nuevos. Salida pytest real citada (M2).

**Los `ValueError` de los tests van con `match=`** — `pytest.raises(ValueError)` a secas atrapa
cualquier `ValueError` y pasa aunque el mecanismo esté muerto (lección de TB.2). Y se prueba la
**ADMISIÓN** (un período legítimo se ancla y su prueba verifica), no solo el rechazo: un
`anclar` que lanzara siempre pasaría todos los tests de rechazo (AC-10).
