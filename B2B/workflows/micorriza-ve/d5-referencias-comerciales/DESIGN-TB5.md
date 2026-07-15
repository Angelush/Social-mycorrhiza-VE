# DESIGN-TB5 — D5: `referencias_comerciales` (veteo relacional, sin score)

> Nodo TB.5 (deps: TB.2 ✅). Delta único → este DESIGN vive en `d5-referencias-comerciales/`.
> Piso de entrada, citado real (M2):
> `cd B2B-VE && ../.venv-ve/bin/python -m pytest -q` → **205 passed, 3 skipped**.
>
> Este delta salda **AC-d9.5** (pendiente desde TB.2) y despierta la colisión dormida
> `veto`/`sancion`/`penalizacion`.

## 0. Reconciliación spec↔código — cuatro hechos leídos antes de diseñar

El método de TA.6/TA.7/TB.1/TB.2/TB.4: **manda el código**. Y la excepción de TB.7: **cuando la
spec se contradice a sí misma, manda el AC** (es lo ejecutable).

### 0.1 `_contains_forbidden_key` NO EXISTE — y no puede existir donde la spec lo pone

Spec §4: «se escanea con `_contains_forbidden_key` + `FORBIDDEN_KEYS` + los patrones de
identidad». Pero `_contains_forbidden_key` **no se heredó**: el docstring de `herencia.py` lo
excluye por nombre, y **`AC-d9.2` (`test_d9_herencia.py:66`) asserta activamente que NO está**
en el módulo. La spec nombra una función que D9 decidió no traer.

**No se resuelve añadiéndola a `herencia.py`:** eso rompería AC-d9.2, y sobre todo el escáner
recursivo vive **fuera** del bloque `BEGIN…END` en las seis capas C2C-VE — meterlo dentro
cambiaría los 3023 bytes y el md5 `5d693ec` **en la séptima copia**, que es exactamente lo que
C-d9.1 prohíbe (cambian las siete o no cambia ninguna).

→ **El walker recursivo se escribe en el ledger**, que es quien lo usa, y consume la maquinaria
heredada (`_key_matches_taxonomy`, `_value_has_identity_shape`). Es el patrón que ya existe:
el ledger ya importa `_key_matches_taxonomy` de `firewall.herencia` (l.51) para `_TASA_KEYS`
(D1). **El bloque no se toca. Jamás.**

### 0.2 Payload-only haría AC-d5.4 verdadero POR VACUIDAD

Spec §5.4 dice «se guarda en el payload del evento». Spec §5.5 y C-d5.5 dicen «visible **solo**
con `scope="comite_credito"`». **Las dos no pueden ser toda la verdad:** `member_statement` lee
`state`, no la cadena. Si las referencias viven únicamente en el payload:

- `member_statement(scope="comite_credito")` **no puede mostrarlas** → el comité no puede leer
  por el motor lo que el motor guarda para que el comité lea. El delta queda instalado y
  desactivado a la vez (F-d3.1, otra vez).
- **AC-d5.4 pasaría sin que nadie hubiera escrito una línea de D5** — «`publico` no las
  contiene» es trivialmente cierto si no existen en ninguna vista. Es exactamente el fallo que
  TB.7 destapó: *un test verde puede estar pasando por vacuidad*. Y es el aviso del grafo: **un
  delta que no deja leer ninguna referencia pasa cualquier test de no-exposición** (AC-10).

→ **Ambas cosas.** Payload (cadena, auditable, anclable por D2 — AC-d5.6) **y**
`state["members"][id]["referencias_comerciales"]` (vista, acotada por scope — AC-d5.4).
No hay contradicción real: §5.4 habla de auditoría, §5.5 de visibilidad. Se cumplen las dos.

### 0.3 `add_member` deja caer las claves desconocidas EN SILENCIO

`add_member` (l.453) reconstruye `resolved_member` clave a clave — `id`, `turnover_cents`,
`credit_min_cents`, `credit_max_cents` — igual que `_apply` hace con `params` (hallazgo de
TB.4). Consecuencia dura: **`referencias_comerciales` metidas dentro de `member` se pierden sin
un solo error**. Firewall nunca invocado, referencias nunca guardadas, suite verde: F-d5.4 y
F-d9.5 servidos en bandeja.

→ **Parámetro propio**, no una clave dentro de `member`. Coincide con spec §2 («dentro del
payload que ya lleva `ratified_by`»): es hermano de `ratified_by`, no de `turnover_cents`.

Lo mismo en `update_member`: su `allowed_keys` (l.214) es `{credit_min_cents, credit_max_cents,
status}` con `issubset` → meterlas en `changes` daría `ValueError("changes")`. Van también como
parámetro hermano, y **`allowed_keys` no se toca** (AC-d9.6: los esquemas cerrados heredados no
se escanean ni se relajan).

### 0.4 EL ORDEN IMPORTA: firewall ANTES del esquema cerrado

Este es el hallazgo que decide si D9 es real o decorativo. AC-d5.3 espera `ValueError` para una
clave `puntuacion`. Pero `puntuacion` **también** es una clave desconocida para el esquema
cerrado (C-d5.3). Si el esquema valida primero:

> **AC-d5.3 pasa en verde con el firewall completamente descableado** — que es literalmente
> F-d5.4, el fallo que AC-d5.3 existe para detectar. El test certificaría la defensa que falta.

→ **Firewall primero, esquema cerrado después.** Ambas defensas quedan vivas y cada una es
alcanzable y demostrable por separado:

| Vector | Quién lo mata | Mensaje |
|---|---|---|
| `puntuacion`, `scoreRelacional`, `lista_negra` | firewall (taxonomía) | `ValueError("referencias_comerciales: firewall")` |
| `nota: "Pedro V-12.345.678…"` | firewall (identidad en valor) | idem |
| `color: "azul"` (desconocida, benigna) | esquema cerrado | `ValueError("referencias_comerciales: clave desconocida")` |

**Mensajes distinguibles, y los AC usan `match=`** (lección de TB.2: `pytest.raises(ValueError)`
pelado atrapa CUALQUIER `ValueError` y pasa con el mecanismo muerto). Sin `match=`, este AC no
distingue «lo mató el firewall» de «lo mató la lista blanca» — y esa distinción **es** AC-d9.5.

**HALLAZGO AL EJECUTAR — la spec de AC-d5.2 se contradice en su propio ejemplo.** La fila
«clave desconocida (`"puntaje_interno": 5`) → `ValueError`» usa como vector de **esquema** una
clave que `puntaje` hace **de firewall** (está en `FORBIDDEN_KEYS`). La mata el firewall, no la
lista blanca: el ejemplo elegido para probar la lista blanca no puede probarla. **No es un
fallo del código — es el orden de §0.4 funcionando.** Se conserva el vector (con expectativa
`firewall`) y la fila de esquema pasa a una clave desconocida **benigna** (`color: "azul"`),
que es la única forma de que las dos defensas queden alcanzables y demostrables **por
separado**. Es la excepción de TB.7 otra vez: cuando la spec se contradice, manda lo ejecutable.

**Y el orden solo es observable en las claves que son AMBAS cosas** (prohibida + desconocida).
Una `nota` con una cédula es clave **válida** del esquema: solo el firewall puede cazarla, en
cualquier orden. Lo confirmó la mutación 2 (§7): invertir el orden enrojece los **tres**
vectores de clave y deja verdes los **dos** de `nota`. Por eso el vector de §0.4 tiene que ser
una clave, no una nota — con una nota, AC-d5.3 pasaría con el orden invertido.

## 1. Firma

```python
def add_member(state, member, ratified_by, ts, *, referencias_comerciales=None) -> (state, event)
def update_member(state, member_id, changes, ratified_by, ts, *, referencias_comerciales=None)
```

**Keyword-only, opcional, default `None`** (P-d5.1 / spec §5.1). Aditivo: ~80 tests existentes
no se tocan (a diferencia de `moneda`/`sal_seudonimo`, que eran obligatorios por diseño).

*Por qué aquí SÍ hay default y en `scope` no:* la ausencia de referencias es un estado legítimo
y frecuente — el veteo **es la reunión**, no el campo (P-d5.1, F-d5.6). La ausencia de `scope`
no era un estado legítimo: era una pregunta sin responder. Un default es la configuración que
nadie revisa **cuando la configuración importa**; aquí «no hay referencias» no es una
configuración, es un hecho del mundo.

**Semántica de `None` vs `[]` en `update_member`** (decisión, no accidente):
`None` = «no las toques» · `[]` = «vacíala». Sin esta distinción, toda actualización de línea de
crédito borraría el veteo en silencio.

## 2. Dónde vive la validación: en `_apply`, no en `add_member`

`_apply` es **la vía del replay**. Una validación que solo viva en `add_member` no protege a
`replay(events)`: un evento fabricado a mano entra por debajo y reconstruye estado. Y AC-d5.6
exige que `replay` reconstruya byte a byte.

→ `_validar_referencias(new_state, member_id, refs)` se llama desde `_apply`, en las ramas
`member_added` y `member_updated`. `add_member`/`update_member` solo construyen el payload; el
`ValueError` sale de `_apply` igualmente y AC-d5.2 se cumple por la firma pública.
Es el patrón que el propio código ya usa (los checks de `turnover` viven en `_apply`).

## 3. La vista: solo `comite_credito`

En `member_statement`, la rama no-`publico` sirve HOY a `miembro` **y** a `comite_credito`. Las
referencias van **solo** bajo `comite_credito` (C-d5.5) → la rama se parte.

*El miembro no ve quién le avala.* Es criterio, y va escrito: «quién avala a quién» es el mapa
de la red (F-d5.7, N7). Dárselo al propio avalado convierte el aval en una posición negociable
—«sé que me avalaste»— y presionable. El comité lo lee porque decide; el miembro no decide.

Bajo `publico` la salida sigue siendo **exactamente `{"seudonimo"}`** — conjunto cerrado, no
lista de prohibidos: por eso AC-d5.4 ya está estructuralmente cubierto, y aun así se escribe
(regresión contra el futuro, no contra el presente — patrón de AC-d3.5).

## 4. Goldens: NO se regeneran — y eso se comprueba, no se supone

A diferencia de TB.2 (`moneda`) y TB.4 (`sal_seudonimo`), D5 **no toca `cell_created`** ni añade
ningún param obligatorio. Y la clave se omite cuando no se pasa: **ausente, no `None`** (patrón
`ancla` de TB.7 — una clave con `None` invita a rellenarla), tanto en el payload como en
`state["members"][id]`.

→ Los eventos y hashes de `ledger_flow.json` **no cambian por construcción**. Si la suite
pidiera regenerar un golden, es señal de que algo se coló donde no debía: **se investiga, no se
regenera**. Los goldens son el piso.

## 5. AC-7 de D3 sigue verde (y es correcto que así sea)

D5 **no añade ninguna función pública**: solo parámetros a `add_member`/`update_member`
(ya en `SIN_SCOPE`, con motivo escrito) y un campo a `member_statement` (ya en `CON_SCOPE`).
El walker es privado (`_`). → nada que clasificar, AC-7 no se toca.
(Contraste con TB.6, que **sí** pondrá AC-7 en rojo al añadir `salida_con_saldo` — eso será el
diseño funcionando, no una regresión.)

## 6. AC-d5.5 y la colisión dormida — se despierta y se pasa

Las cinco claves elegidas se auditan contra `FORBIDDEN_KEYS` **por test, no por lectura**:
`referencias_comerciales`, `avalista`, `relacion_declarada`, `antiguedad_meses`, `nota` →
`_key_matches_taxonomy(k, FORBIDDEN_KEYS) is False` para las cinco.

La colisión no desaparece: `veto`, `sancion` y `penalizacion` siguen en la taxonomía y siguen
siendo vocabulario legítimo de B2B. **Se esquiva por elección de nombres, y el test es el
centinela** de que se sigue esquivando. Si algún día una clave necesaria colisiona: **se renombra
la clave, jamás la taxonomía** (E-d5.2/N-d9.1 — es compartida con seis capas C2C-VE donde esos
tokens sí nombran vigilancia).

## 7. Verificación por mutación (obligatoria — TB.3/TB.4/TB.7)

Un invariante que no se ha visto fallar no se sabe si prueba algo. Planificadas:

1. **Descablear el firewall** (no llamar al walker) → AC-d5.3 debe ponerse rojo **con `match=`
   distinguiendo firewall de esquema**. Es la mutación que prueba AC-d9.5. Si sigue verde, el
   test no probaba el firewall sino la lista blanca (§0.4).
2. **Invertir el orden** (esquema antes que firewall) → AC-d5.3 rojo por mensaje.
3. **Añadir `n_avales = len(refs)`** a la salida → AC-8(1) rojo por igualdad de conjuntos.
4. **Añadir `antiguedad_media = sum(...)/len(...)`** → AC-8(2) rojo **por AST**, aunque no se
   llame «score» (la prueba de que el muro no es la palabra — patrón de AC-d7.4).
5. **Permitir auto-aval** → AC-d5.2 rojo.
6. **Mostrar referencias bajo `miembro`** → AC-d5.4 rojo.
7. **Control negativo obligatorio:** `nota: "Buen proveedor desde 2023"` y
   `avalista: "bancoDeTiempo"` **aceptados**. Un firewall que mata al paciente pasa cualquier
   test que solo compruebe rechazos (F-d9.1, AC-10). Sin este caso, no hay delta: hay un muro.

### Resultado (ejecutado — las 7 cazadas, piso 205→231)

| # | Mutación | Cazada por |
|---|---|---|
| 1 | firewall descableado | **7 rojos**, incl. los 5 vectores de AC-d5.3 |
| 2 | orden invertido | **5 rojos**: los 3 de clave; los 2 de `nota` verdes **a propósito** (§0.4) |
| 3 | `n_avales = len(refs)` | AC-8(1) + AC-8(2) + AC-d5.1 |
| 4 | `antiguedad_media` | AC-8(1) + **AC-8(2) por AST**, sin llamarse «score» |
| 5 | auto-aval | AC-d5.2 |
| 6 | referencias bajo `miembro` | AC-d5.4 |
| **7** | **NUEVA — la sugerencia amable (F-d5.2):** `credit_max = credit_max * len(refs)` en `add_member` | **SOLO AC-8(2)** |

**La 7 no estaba planificada y es la que justifica el AST.** `linea_sugerida` como campo nuevo
sería trivial de cazar; la forma real de F-d5.2 es **inflar un campo que ya existe y es
legítimo**. AC-8(1) no la ve (`credit_max_cents` es una clave esperada, y su valor sale del
`turnover`, no de un nombre nuevo), el canario AC-d5.1 no la ve (no se llama nada), y la suite
entera sigue verde: el comité recibiría una línea mayor por tener más avales y **nadie lo
habría decidido**. Solo el rastreo de datos por AST la caza. Es la prueba de que el muro no es
la palabra — el hallazgo equivalente al `recargo_centavos` de TB.7.

## 8. Reparto

- **Opus:** este DESIGN, el walker, el orden §0.4, AC-8 (AST + tipo), AC-d5.3 (el que salda
  AC-d9.5), AC-d5.4, el corte de `member_statement`. Todo criterio.
- **Fan-out candidato** (`agy-gemini-3-flash`, coding +15, seen 32, 8/8 verdes) **con contrato de
  firmas cerrado por Opus:** AC-d5.2 (tabla de esquema cerrado, 7 filas mecánicas), AC-d5.5
  (5 asserts), AC-d5.6 (replay/verify_chain). Es volumen mecánico → rinde (regla de coste de
  TA.9). **Se verifica corriendo la suite, no leyendo el reporte** (lección TB.7).
- **Nunca:** goldens, el bloque del firewall, §0.4.

**EJECUTADO SIN FAN-OUT — la regla de coste de TA.9 derogó al candidato.** Los tres AC
mecánicos suman ~65 líneas, y el contrato de firmas que había que redactar (fixture con
`bancoDeTiempo`, los mensajes exactos `firewall`/`clave desconocida`, la semántica `None`/`[]`,
el stream completo desde `cell_created`) **cuesta lo mismo que el test**, con todo ya resuelto
en contexto. El fan-out rinde con volumen (TB.4: 11 tests; TB.7: 4 con 449 líneas de fixture ya
hechas), no con esto. Mismo criterio que TA.9. El reparto lo decide Opus **nodo a nodo**, no la
lista de candidatos del DESIGN.

## 9. Señalados → README de TB.9 (D10)

- **ST-d5.1 —** el conteo es un score aunque nadie lo compute: el comité puede contar avalistas
  y ordenar mentalmente. **Y debe poder**: es su juicio. La línea es «el **sistema** no computa»,
  no «que nadie compare nunca». Se documenta para que nadie «arregle» lo que no está roto.
- **ST-d5.2 —** el aval no se verifica. Un anillo de tres empresas avalándose mutuamente pasa
  todos los checks. `N-d5.4` solo impide el auto-aval trivial. Lo caza el comité, que conoce a
  la gente — o no lo caza nadie.
- **ST-d5.3 —** el cold-start VE no se arregla con código (§6.4): D5 da el formato del juicio,
  no el sustrato. La voluntad de cooperar no se fabrica.
- **NUEVO ST-d5.5 —** *el firewall de valores es de FORMA, no de contenido.* `_value_has_identity_shape`
  caza cédulas, RIF y teléfonos **con forma venezolana**. Una nota que diga «el hermano del
  dueño de la panadería de la esquina de Chacao» es un identificador perfecto y pasa limpia. El
  texto libre no se puede sanear; solo se pueden cazar las formas conocidas. **No se disimula.**
- **NUEVO ST-d5.6 —** *el scope es un contrato, no un guardia* (heredado de D3, N-d3.4): el
  motor no autentica, así que un llamador puede pedir `comite_credito` y leer el grafo de avales
  entero. D5 no empeora esto ni lo arregla — pero ahora lo que hay detrás de esa puerta es el
  mapa de la red, no solo un saldo.
- **NUEVO ST-d5.7 (de la mutación 7) —** *el score no necesita un campo nuevo para existir.*
  La forma peligrosa de F-d5.2 no es `linea_sugerida` (visible, cazable por cualquier test de
  claves) sino **inflar un campo legítimo que ya existe**: `credit_max_cents` derivado de
  `len(referencias)` deja la superficie pública **idéntica** y la suite verde. AC-8(2) lo caza
  hoy dentro de `src/`; **lo que ningún test puede cazar es que el comité haga esa multiplicación
  en su cabeza** — y ahí es donde debe estar (ST-d5.1). La línea es del motor, no del juicio.
- **NUEVO ST-d5.8 —** *el aval no caduca.* `antiguedad_meses` es una foto del día del alta:
  el motor no tiene reloj (`ts` es entrada) y nada re-verifica una referencia de hace cinco
  años. Un avalista que se fue del país (§6.4, el éxodo) sigue avalando en el estado. **No se
  arregla con código** —caducarlas sería una operación de valor sin puerta humana (M8), el
  mismo argumento que `expira_en_dias` en D1— y quien las lee debe saber que lee una foto,
  no un hecho vigente.
