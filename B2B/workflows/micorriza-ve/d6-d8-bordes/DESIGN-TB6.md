# DESIGN TB.6 — D6: `salida_con_saldo`

> Opus, 2026-07-15. Nodo TB.6, **alcance solo-D6** por decisión humana (§0). Deps: TB.3 ✅.
> Piso citado: `cd B2B-VE && ../.venv-ve/bin/python -m pytest -q` → **231 passed, 3 skipped**.
>
> Un delta → DESIGN en el dir del delta (`d6-d8-bordes/`). D8 sale a **TB.6b**.

## §0 — Alcance: TB.6 es solo-D6 (decisión humana, 2026-07-15)

`tasks.md` ponía D6+D8 en TB.6 con deps solo `TB.3`; **TP.1 exige** re-verificación regulatoria
fechada (M9) **antes de D4/D8**; y la fila TB.8 sí lista M9. Es **spec contra spec** → «manda el
código» NO aplica, y no es una tensión que el ejecutor pueda zanjar leyendo más.

**Zanjado por el humano: TB.6 = solo-D6.** D8 pasa a **TB.6b** con dep `TB.3 + M9` explícita.

*Porque:* `puente.pausar()` **es** el mecanismo de respuesta a sanciones — exactamente lo que M9
vigila. Que la pausa solo REDUZCA exposición no la saca del alcance de M9: el diseño de cuándo y
por qué se pausa depende de hechos regulatorios que hoy son un hueco declarado
(`docs/verificaciones/PLANTILLA.md` sin rellenar). D6, en cambio, no toca sanciones: un
comerciante que emigra no es un evento OFAC, y su spec (§2) no depende de un solo hecho
regulatorio.

**Qué NO entra en TB.6** (y por qué no es deuda silenciosa): `params["puente_pausado"]`,
`puente_pausar`, `puente_reanudar`, y los AC que los ejercen — **AC-d68.5** (la pausa no mata el
crédito interno), **AC-d68.9** (`puente_pausado` ≠ `paused`) y las **dos primeras filas** de
AC-d68.8 (doble pausa / doble reanudación). Quedan listados en §7 como contrato de TB.6b.

**`liquidacion_puente` SÍ entra.** No es D8: es una de las cuatro resoluciones de D6. D8 no la
crea — solo le añade un interruptor. La spec §3 lo dice al revés de como se lee rápido: «lo único
que hace la pausa es rechazar `salida_con_saldo` con `resolucion.tipo == "liquidacion_puente"`».
La resolución preexiste a su interruptor; sin ella, D6 no conserva L1 para un saldo positivo.

## §1 — La puerta ya existe (M8): se le añade UN kind

`ratification_kinds` en `_apply:192`. TB.6 añade **`member_exited`** y nada más.
TB.6b añadirá `bridge_paused`/`bridge_resumed`.

**La validación va en `_apply`, no en `salida_con_saldo`** (patrón fijado en TB.5): `_apply` es
la vía del `replay`. Una validación en la función pública no protege a un evento fabricado a mano
y metido en el stream — y `replay` es lo que un árbitro correría.

## §2 — Firma y `resolucion`

```python
def salida_con_saldo(state, member_id, resolucion, ratified_by, ts) -> (state, event)
    # kind = "member_exited"
```

`ratified_by` posicional (como `add_member`/`update_member`), no keyword-only: aquí no compite
con un esquema cerrado (esa era la razón de D5), y el hermano más cercano es `update_member`.

| `resolucion` | Efecto sobre saldos |
|---|---|
| `{"tipo": "simple"}` | ninguno; exige saldo == 0 |
| `{"tipo": "liquidacion_puente", "fondo": mid}` | saliente → 0; **el fondo asume la contrapartida** |
| `{"tipo": "absorcion_avalista", "avalista": mid}` | saliente → 0; **el avalista asume la contrapartida** |
| `{"tipo": "plan_de_pago", "plazo_meses": int}` | **ninguno** — el saldo negativo sigue ahí |

En los cuatro casos `status` → **`exited`**.

### §2.1 — RECONCILIACIÓN: el fondo no tiene dónde vivir (manda el AC)

**La spec §2 se contradice con sus propios AC.** Su tabla da `liquidacion_puente` como
`{"tipo": "liquidacion_puente"}` — **sin decir quién es el fondo** — pero AC-d68.2 exige «fondo
−5000» y **AC-d68.6 exige rechazar si la contrapartida deja al fondo fuera de sus líneas**. Con la
firma de la tabla, el motor no puede saber a quién apuntar: AC-d68.6 es **inexpresable**.

Excepción de TB.7, reusada en TB.5: **cuando la spec se contradice a sí misma, manda el AC** — es
lo ejecutable. → `resolucion["fondo"]` es **obligatorio** en `liquidacion_puente`.

**Por qué en la `resolucion` y no en `params` de `create_cell`:**
1. C-d68.6 — la resolución es **explícita, provista por el comité**. El fondo es la contrapartida
   de un asiento; nombrarlo es exactamente igual de decisión que nombrar al avalista, y `avalista`
   ya vive en la `resolucion`. Simetría, no analogía.
2. Un `fondo_id` en `params` cambiaría `cell_created` → **`ledger_flow.json` a regenerar** (tercera
   vez), por un dato que ni siquiera es de la célula: el fondo puede cambiar entre una salida y la
   siguiente, y un param sugiere que no.
3. Un fondo en `params` es **configuración que nadie revisa** — la clase de F-d3.1. El comité que
   ratifica una salida tiene que teclear a quién le cae el saldo.

*Señalado (ST-d68.5, → README de TB.9):* el motor no sabe qué es «el fondo». Acepta cualquier
miembro como fondo, porque **no puede distinguir un fondo de garantía de un compadre con líneas
holgadas** — sin registro de qué miembro es el fondo, la única defensa real es que la salida la
ratifica un humano que sí lo sabe. No se disimula con un `es_fondo: bool` que nadie verifica.

### §2.2 — Por qué `simple` exige saldo == 0

La tabla de la spec pone `simple` en la fila «saldo cero». Si `simple` aceptara un saldo distinto
de 0, la única forma de conservar L1 sería **no tocarlo** — y eso ya es `plan_de_pago`, con otro
nombre y sin `plazo_meses`. Dos nombres para un hecho es la discrepancia esperando a pasar (misma
razón que `None`/`[]` en D5). → saldo != 0 con `simple` → `ValueError("resolucion")`.

### §2.3 — Por qué el motor NO deduce la resolución del signo

C-d68.6/F-d68.7. Deducirla sería que el motor decide cómo se resuelve una salida, **con
consecuencias sobre un avalista que no está en la sala**. Consecuencia deliberada: `plan_de_pago`
con saldo positivo y `liquidacion_puente` con saldo negativo **son legales**. El motor no vigila
que la resolución sea la «obvia»; vigila L1, L2 y que la haya ratificado alguien.

## §3 — `exited` fuera de la escalera (C-d68.3)

La escalera vive en `_apply:340` (`ladder`, saltos de un solo peldaño). **`exited` no entra en
esa lista.** *Porque:* `expelled` es el último peldaño **sancionador**; emigrar no es una sanción,
y confundirlos deja en una cadena append-only la marca de que a quien se mudó a Bogotá lo
expulsaron — y esa marca viaja a cualquier federación futura (U1, F-d68.3).

Tres consecuencias, dos de ellas **gratis** (se verifican, no se implementan):

1. **`update_member` no llega a `exited`**: `new_status not in [...]` (l.337) ya lanza
   `ValueError("status")`. Gratis. AC-d68.4 lo fija para que nadie lo «arregle».
2. **`update_member` no sale de `exited`**: hoy `ladder.index("exited")` lanza `ValueError`, pero
   **por accidente** — es el `.index` de una lista, no una decisión, y su mensaje
   (`'exited' is not in list`) no lo fija ningún `match=`. Un `ValueError` accidental es
   indistinguible de uno intencionado justo el día que alguien reordene el código.
   → **check explícito** `if m["status"] == "exited": raise ValueError("exited")`, **solo cuando
   `"status" in changes`** (lectura estrecha y literal de la spec: «no puede llegar a él ni salir
   de él» habla de estados). Las líneas de crédito de un `exited` siguen siendo ajustables y L2
   sigue guardándolas: prohibirlo sería alcance que nadie pidió.
3. **Un `exited` no recibe obligaciones nuevas**: `record_obligation:390` filtra
   `status not in {"active","warned","line_reduced"}`. Gratis (ST-d68.4). Y `settle_obligation`
   **no mira el status** → paga lo suyo. Gratis, y es N-d68.4 literal («paying what you owe is
   always legal»). AC-d68.10 lo fija.

## §4 — L1 y L2: se REUSAN los post-asserts, no se reimplementan

`_apply:529` ya verifica `sum(balance_cents) == 0` (L1) y `credit_min <= balance <= credit_max`
para **todo** miembro (L2), después de toda operación, y lanza `ValueError(m_id)`.

- **L1** (C-d68.2): no hace falta un check nuevo. `liquidacion_puente`/`absorcion_avalista`
  mueven la contrapartida; si alguien la «olvidara», el post-assert L1 lanza `balance_sum`.
  Es F-d68.2 ya cazado por la maquinaria heredada. AC-d68.2 lo prueba por numérico.
- **L2 / el avalista atropellado** (C-d68.5, F-d68.5, AC-d68.3): el post-assert **ya nombra al
  avalista** (`raise ValueError(m_id)` con `m_id` = avalista) y `_apply` trabaja sobre un
  `deepcopy` → **el estado del llamador queda intacto** sin escribir nada. Igual para el fondo
  (AC-d68.6, ST-d68.1: el fondo sin línea **es** la verdad; se capitaliza, no se recorta el check).
  P4: reutilizar antes que crear. **La mutación tiene que confirmar que este reuso es real** —
  si el post-assert no fuera suficiente, AC-d68.3 pasaría por el mensaje equivocado.

**Lo que sí se valida explícitamente** (el post-assert no lo cubre): que el avalista **exista** y
esté en `{"active","warned","line_reduced"}` → `ValueError("avalista")`. Un avalista `exited`,
`suspended` o `expelled` no absorbe: sería contagio hacia alguien que ya está en la escalera.
Mismo filtro de estado que `record_obligation` — reuso del conjunto, no una lista paralela.

## §5 — AC-7 (D3): dónde va `salida_con_saldo`, y por qué

**Va a `SIN_SCOPE`. Y esa decisión ES el delta, así que va con su motivo escrito.**

El test (`tests/test_d3_visibilidad.py:260`) parte la superficie pública de los tres módulos en
puntos de consulta (`CON_SCOPE`) y todo lo demás (`SIN_SCOPE`, con motivo). Lo no clasificado
rompe el test — **y va a romperlo en cuanto exista `salida_con_saldo`. Eso es el diseño
funcionando, no una regresión.**

La objeción que hay que contestar, no esquivar: *`salida_con_saldo` devuelve saldo + identidad*.
**Es cierto, y no la hace un punto de consulta.** Devuelve `(state, event)` — el mismo par
canónico que `add_member`, `record_obligation` y `settle_obligation`, que también devuelven un
`state` lleno de saldos e identidades reales. Si el par canónico contara como salida acotable,
**los ocho mutadores estarían mal clasificados desde TB.4** y el delta no sería este.

Lo que decide es el porqué de C-d3.1, no la forma del valor de retorno:

1. **Un mutador no tiene a quién acotar.** El scope acota lo que un solicitante ve. Quien llama a
   `salida_con_saldo` no está consultando: está **ratificando**, ya pasó la puerta de M8 y trae un
   `ratified_by`. Un `scope="publico"` aquí no tendría significado — ¿una salida que se ejecuta
   pero devuelve el saldo tachado? El estado ya está mutado.
2. **Acotar el `state` de vuelta rompería `replay`.** El AC-7 de D6 exige que
   `replay(events)` reconstruya el estado **byte a byte**. Un `state` filtrado por scope no es el
   estado. El muro de tipo de AC-7 («cero numéricos bajo `publico`») aplicado a un mutador mataría
   al paciente — F-d9.1, la clase de fallo que el control negativo existe para cazar.
3. **La fuga real de una salida no está en su retorno: está en su EVENTO**, que lleva `member_id`
   y la `resolucion` (y con ella el `avalista` o el `fondo` — quién avaló a quién, que D5 reserva
   al comité, C-d5.5). Y el evento **ya está cubierto**: `anclar` solo emite hashes, y
   `exportar_registros` está en `CON_SCOPE` desde TB.7. Poner scope en el mutador no taparía esa
   fuga; taparla donde ya está tapada es teatro.

*Señalado nuevo (ST-d68.6, → README de TB.9):* `exportar_registros` bajo `publico` da
`lineas == []`, pero un `member_exited` **existe en la cadena** que `anclar` cubre. La salida de
un miembro es un hecho más ruidoso que una obligación: quien compare dos anclas ve **cuándo dejó
de haber actividad** de un seudónimo. El seudónimo es estable a propósito (D3) — esa estabilidad
**es** la utilidad para el árbitro y **es** la correlación. No se resuelve en el motor.

## §6 — `cell_metrics`

**No se toca en TB.6.** El contrato §5.6 de la spec («`cell_metrics` añade `puente_pausado`») es
D8 → TB.6b. Añadir hoy la clave con `False` fijo sería el delta **instalado y desactivado a la
vez** (F-d3.1). No se añade `exited_count` ni nada equivalente: nadie lo pidió y
`cell_metrics` es agregado de célula, no censo de estados.

**Goldens: `ledger_flow.json` NO se regenera.** D6 no toca `cell_created` — ni un param nuevo, ni
una clave nueva en un evento existente. Si la suite pide regenerar, **algo se coló: se investiga,
no se regenera.**

## §7 — Contrato de TB.6b (D8, dep M9) — lo que TB.6 deja escrito y sin hacer

`params["puente_pausado"] = False` en `create_cell` (**regenera el golden — es un param nuevo en
`cell_created`; comparar campo a campo contra `B2B/` intacto, técnica de TB.2**);
`puente_pausar`/`puente_reanudar` con kinds `bridge_paused`/`bridge_resumed` en
`ratification_kinds`; el rechazo de `liquidacion_puente` con el puente pausado; `cell_metrics` +
`puente_pausado`; AC-d68.5, AC-d68.9 y las filas 1–2 de AC-d68.8. **`puente_pausado` ≠ `paused`:
no reutilizar el flag (I-VE7, F-d68.4).**

## §8 — Plan de AC y reparto

| AC | Qué fija | Estado en TB.6 |
|---|---|---|
| AC-7 (D6) | los 5 puntos de la puerta sobre `member_exited` | ✅ |
| AC-7 (D3) | clasificación de `salida_con_saldo` en `SIN_SCOPE` | ✅ (§5) |
| AC-d68.1 | cero helpers directas (AST) | ✅ |
| AC-d68.2 | L1 en las cuatro resoluciones | ✅ |
| AC-d68.3 | el avalista no se atropella | ✅ |
| AC-d68.4 | `exited` no es una sanción | ✅ |
| AC-d68.6 | el fondo es un miembro con líneas | ✅ |
| AC-d68.7 | el motor no liquida (sin red/disco) | ✅ |
| AC-d68.8 | `salida_con_saldo` sobre un `exited` → `ValueError` | ✅ parcial (filas 1–2 → TB.6b) |
| AC-d68.10 | un `exited` no recibe pero paga | ✅ |
| AC-d68.5, AC-d68.9 | la pausa | ⛔ TB.6b |

**Reparto — regla de coste (TA.9, re-aplicada en TB.5):** el fixture (célula + fondo + avalista +
saldos que sumen 0) **es el piso → nunca a fan-out**. AC-7(D3), AC-d68.1 (AST) y AC-d68.7 son
criterio → Opus. **Candidato real a fan-out: AC-d68.2 + AC-d68.3 + AC-d68.4 + AC-d68.10** — es la
tabla de cuatro resoluciones × saldos y la de transiciones de estado: **volumen mecánico**, que es
donde el fan-out rinde. Decisión final **después** de escribir el fixture, no aquí: si el contrato
de firmas cuesta lo mismo que el test, no se delega. **El reparto lo decide Opus nodo a nodo, no
esta tabla.**

## §9 — Mutaciones planificadas (+ al menos una NO planificada)

1. `liquidacion_puente` pone el saldo a 0 sin mover la contrapartida → L1 (F-d68.2).
2. `exited` metido en `ladder` → AC-d68.4 rojo (F-d68.3).
3. Deducir la resolución del signo del saldo → F-d68.7.
4. `absorcion_avalista` que recorta (clamp) en vez de rechazar → AC-d68.3 (F-d68.5, M6).
5. `plan_de_pago` que «provisiona» el saldo → AC-d68.2 fila 4 (F-d68.8).
6. Helper directa que muta `state` sin `_apply` → AC-7(3) vía `replay` (F-d68.1).
7. `salida_con_saldo` fuera de `ratification_kinds` → AC-7(1).

**Obligatoria: una mutación que este DESIGN no previó.** Ha cazado cuatro defectos en tests de
criterio de Opus (TA.9, TB.4, TB.7) y en TB.5 destapó ST-d5.7. Un test de invariante que no se ha
visto fallar no se sabe si prueba algo.

## §10 — RESULTADO de la mutación (ejecutada; 8 mutaciones + 1 sonda)

Las 7 planificadas + M8 (`_ESTADOS_OPERATIVOS` += `exited`, el «arréglalo» que ST-d68.4 avisa):
**todas cazadas**, salvo una — y esa es el hallazgo del nodo.

### M2 NO SE CAZÓ: mi propio AC-d68.4 pasaba por la razón equivocada

`exited` metido dentro de `ladder` → **292 verdes**. El test probaba
`update_member(active → exited)` y esperaba `ValueError("status")`. Con `exited` en la escalera,
**ese ValueError sigue saliendo**: desde `active`, `exited` es un salto de cinco peldaños y lo
rechaza la regla de «un solo peldaño» (inv. 5) — **no** la regla que este AC existe para fijar.
Mismo mensaje en los dos mundos, así que ni el `match=` los distinguía.

**Desde `expelled`, en cambio, `exited` sería un salto de UN peldaño: legal y silencioso.** Es
F-d68.3 exacto — el emigrante convertido en el último grado de la escalera sancionadora.
→ AC-d68.4 pasa a recorrer la escalera **entera** por parametrización; M2 ahora cae, y cae
**solo en `[expelled]`**, que es donde era invisible. **El peldaño que importa es el último, no
el primero.** Quinto defecto que la mutación caza en un test de criterio de Opus (TA.9, TB.4,
TB.7, TB.5).

### ST-d68.7 — la sonda no planificada: la resolución es una foto del saldo

`salida_con_saldo` resuelve el **saldo**, y una obligación **en vuelo** todavía no es saldo. El
comité puede ratificar una salida `simple` («no debe nada») de un miembro con 3000 en vuelo; al
liquidarse, el `exited` queda en **−3000 sin plan de pago, sin avalista y sin ratificación de ese
hecho**. **L1 y L2 se conservan y la suite queda verde: por eso no se ve.**

No es un defecto de `simple` — es de las cuatro: `absorcion_avalista` mueve el saldo del día T al
avalista y lo que estaba en vuelo aterriza en el saliente en T+1, **sin que el avalista lo cubra**.

**No se arregla en TB.6, y no es dejadez** (N10 — nombrar, no fake-resolver): «prohibir salir con
obligaciones en vuelo» lo **descarta la spec** (AC-d68.10 exige que un `exited` conserve y liquide
las suyas), y hacer que el aval cubra las liquidaciones futuras convertiría un acto puntual en una
**garantía permanente que el avalista no ratificó** — operación de valor sin puerta humana, la
forma exacta de ST-d5.8. Las dos salidas son decisión de **spec**, no del ejecutor (I3). Quien ve
la cascada es el comité (ST-d68.2, misma familia).

Fijado en `test_st_d68_7_la_resolucion_es_una_foto_del_saldo_no_del_compromiso`: el
comportamiento queda como **decisión registrada, no accidente**, y cambiarlo cuesta discutirlo.
→ README de TB.9 + **pregunta abierta para el humano**.
