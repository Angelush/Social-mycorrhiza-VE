# DESIGN-TB4 — D3: visibilidad de saldos con scope

> Nodo TB.4 (deps: TB.3 ✅). Delta único → este DESIGN vive en `d3-visibilidad/` (el de TB.2
> iba en la raíz del sub-bundle porque cubría dos deltas).
> Piso de entrada: `cd B2B-VE && ../.venv-ve/bin/python -m pytest -q` → **184 passed, 3 skipped**.

## 0. Reconciliación spec↔código (manda el código — TA.6, TA.7, TB.1, TB.2)

Leído el código real antes de diseñar. Cuatro hechos que la spec no podía saber:

1. **`state["params"]` es una lista blanca POR CONSTRUCCIÓN** (`_apply`, `cell_created`): el
   estado nuevo **reconstruye** `params` clave a clave (7 nombradas), no copia el dict de
   entrada. Consecuencia: `sal_seudonimo` **no llega al estado si no se añade ahí a propósito**
   — y una sal que no llega al estado no existe para `member_statement`. Es el mismo patrón que
   `moneda` en TB.2, y es una defensa, no un estorbo: nada de forma libre entra en `params`.
2. **`member_statement` ya es pura y de solo lectura** → la spec §5.5 («cero cambios en estado
   ni eventos») es alcanzable tal cual. D3 es una capa de vistas.
3. **`cell_metrics` no devuelve `params` entero**: expone 5 campos nombrados uno a uno. F-d3.3
   («la sal filtrada por `cell_metrics` que devuelve params por transparencia») **ya es
   irrepresentable por construcción**. AC-d3.5 sigue escribiéndose igual — es un test de
   regresión contra el futuro, no contra el presente.
4. **La superficie pública real son 15 funciones** (introspección, ver §4). Solo 2 llevan scope.

## 1. La firma

```python
member_statement(state, member_id, scope, solicitante=None) -> dict
render_statement(state, member_id, scope, solicitante=None) -> str
```

`scope` **posicional obligatorio, sin default** (C-d3.1). No `scope=None` validado después:
que Python lance `TypeError` al omitirlo es una defensa más barata y más temprana que la
nuestra. `SCOPES = ("comite_credito", "miembro", "publico")`.

*Porque no hay default:* un default es la configuración que nadie revisa. `comite_credito` por
default dejaría el delta **instalado y desactivado a la vez** (F-d3.1) — el peor estado
posible, porque la suite verde certifica que existe.

## 2. La sal — dónde vive y qué arrastra

`params["sal_seudonimo"]`: string no vacío, **obligatorio para toda célula** (no solo VES; el
matraqueo no depende de la moneda). Se añade a la reconstrucción de `params` en `cell_created`.

**Por qué en `params` y no como argumento de `member_statement`:** una sal por llamada la elige
el llamador → dos llamadas honestas producen dos seudónimos distintos para el mismo miembro →
el enlace entre anclas (D2) se rompe y el árbitro no puede hacer su trabajo. La sal es
propiedad **de la célula**, y su estabilidad es justo lo que la hace útil.

**Consecuencia asumida — los goldens se regeneran.** `sal_seudonimo` entra en el payload de
`cell_created` → cambia el hash → `ledger_flow.json` cambia **por construcción**, igual que con
`moneda` en TB.2. Se aplica la técnica de TB.2, que es la razón de que `B2B/` siga intacto:
**comparar el flujo campo a campo contra `B2B/` upstream** y demostrar que el único delta es la
sal (members, obligations, seq, last_ts, applied_proposals, saldos al centavo, L1=0). Un golden
regenerado sin esa comparación blanquea cualquier cosa que se haya colado con él.

**La sal en el stream de eventos NO viola C-d3.3.** C-d3.3 dice que la sal jamás sale del
**motor** en una salida pública. El stream de eventos es el libro interno de la célula, no una
salida `publico`; `anclar` (D2) emite hashes y raíces, jamás payloads. AC-d3.5 lo fija.

## 3. Qué devuelve cada scope

| scope | salida |
|---|---|
| `comite_credito` | el dict actual, **sin tocar** (8 claves) |
| `miembro` | idéntico a `comite_credito`, previo `solicitante == member_id` |
| `publico` | **exactamente** `{"seudonimo": sha256(canonical([cell_id, member_id, sal]))[:16]}` |

`canonical` ya existe y es la serialización del motor: reusarla, no inventar un formato.

**AC-10 — se prueba la ADMISIÓN, no solo el rechazo.** Un scope que no deja ver nada a nadie
pasa cualquier test de no-exposición. El comité TIENE que poder hacer su trabajo: el test fija
que `comite_credito` devuelve las 8 claves **con los valores correctos** (no «no lanza»), y que
`miembro` sobre sí mismo devuelve **exactamente lo mismo** que `comite_credito`. Sin eso, un
`return {}` pasaría AC-7, AC-d3.3 y AC-d3.5 a la vez.

## 4. AC-7 por enumeración — y la trampa de la lectura ingenua

AC-7 dice: introspección de `dir(module)`, llamar con `scope="publico"` **donde lo acepte**.
Leído literal, el test solo comprueba las funciones que aceptan scope — y entonces **su propio
porqué es falso**: «una vista nueva sin scope rompe este test el día que se escriba» no se
cumple, porque una vista nueva sin scope simplemente no se llama.

Y hay un caso real que lo demuestra: **`to_clearing_input` devuelve líneas y saldos de todos
con identidad, no acepta scope, y NO debe aceptarlo** (ST-d3.4: es el input del solver, que
corre dentro de la célula; ponerle scope rompe el clearing sin proteger nada).

**Diseño que sí cumple el porqué:** el test enumera las 15 públicas y las parte en dos con una
**lista blanca explícita y razonada** de las que no llevan scope:

- llevan scope: `member_statement`, `render_statement` → se llaman con `publico` y se asertan.
- no llevan scope, **con motivo escrito en el test**: `to_clearing_input` (ST-d3.4, vista
  interna), `cell_metrics` (agregado de célula, §3), `create_cell`/`add_member`/…/`replay`/
  `verify_chain`/`canonical` (mutadores y maquinaria, no puntos de consulta).

Una función pública nueva que no esté en ninguna de las dos listas **rompe el test el día que
se escribe**, y su autor tiene que decidir a cuál pertenece y escribir el porqué. Eso es lo que
AC-7 quería: la lista que envejece se convierte en la lista que se defiende sola.

## 5. Hallazgo nuevo — el oráculo de pertenencia (ST-d3.5, NO se fake-resuelve)

`member_statement` lanza `ValueError(member_id)` si el miembro no existe. Bajo `scope="publico"`
eso convierte la función en un **oráculo de pertenencia**: preguntar por «Ferretería Acme» y
recibir un seudónimo en vez de un error dice que Acme está en la célula. Contra el modelo de
amenaza real (§3.3: quién está dentro ya es información — la célula es una red de comerciantes
con superávit potencial), eso es una fuga que el scope no tapa.

**No se resuelve en el motor y no se disimula.** Devolver un seudónimo falso para no-miembros
haría irreconocible el error legítimo y rompería `miembro`/`comite_credito`. La respuesta real
es de despliegue (quién puede llamar), y el motor **no autentica** (N-d3.4). → **Señalado**,
va al README de TB.9 junto a los de D2. Es N10: nombrarlo, no fingir que está cerrado.

## 6. Regresión esperada

- `scope` obligatorio rompe las **19 llamadas** existentes a `member_statement`/
  `render_statement` (`test_ledger.py`, `test_ledger_properties.py`, `test_d1_moneda.py`) →
  se pasan a `scope="comite_credito"`, que **reproduce la semántica upstream exacta**. Ningún
  test cambia de significado; solo declara desde dónde mira. Misma clase que `moneda` en TB.2.
- `sal_seudonimo` obligatorio rompe toda creación de célula en fixtures → se añade.
- `ledger_flow.json` se regenera (§2), con la comparación contra `B2B/` como prueba.

## 7. Verificación por mutación (técnica de TB.3 — obligatoria, sin ella el nodo no cierra)

Un test de invariante que no se ha visto fallar no se sabe si prueba algo. Se romperá a
propósito y se comprobará que la suite lo caza:

1. `publico` devuelve además `balance_cents` → AC-d3.3 y AC-7 en rojo.
2. `publico` devuelve `estado` (N-d3.2, la marca) → AC-d3.3 en rojo por igualdad de conjuntos.
3. seudónimo sin sal (`sha256(cell_id+member_id)`) → AC-d3.4 en rojo **por fuerza bruta real**,
   no por inspección del código.
4. `scope` con default `"comite_credito"` (F-d3.1, el fallo más probable) → AC-d3.1 en rojo.
5. `member_statement` devuelve `{}` bajo `comite_credito` → **AC-10 en rojo** (el control de
   admisión; si esto no enrojece, el nodo prueba que el firewall mata al paciente y lo llama
   éxito).

## 8. Reparto

- **Opus:** este DESIGN, el scoping, la lista blanca razonada de §4, la regeneración de goldens
  y su comparación contra `B2B/` (los goldens son el piso — **nunca a fan-out**), el Señalado
  de §5.
- **Candidato a `agy-gemini-3-flash`** (coding, fit +12.09, seen 28, 6/6 verdes): los tests
  mecánicos de AC-d3.1/d3.2/d3.4 con **contrato de firmas fijado por Opus ANTES**.
  Al revisar: exigir `match=` en todo `pytest.raises(ValueError)` (lección de TB.2 — atrapa
  CUALQUIER ValueError y pasa con el mecanismo muerto) y **control negativo** (AC-d3.4 ya lo
  lleva por spec: sin sal el ataque debe TRIUNFAR).

## 9. Qué NO hace TB.4

No cifra, no autentica, no toca `cell_metrics`, no toca `to_clearing_input`, no resuelve la
correlación entre salidas (ST-d3.1) ni el oráculo de pertenencia (§5). Cero kinds nuevos, cero
`ratified_by`: D3 no mueve valor — como `anclar`, es read-only, y por la misma razón no se
confunde con M8.
