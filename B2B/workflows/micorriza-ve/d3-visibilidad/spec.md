# Spec — D3: visibilidad de saldos con scope

> Nodo TB.4 (depende de D2: la seudonimización usa la maquinaria de hashes). Ancla: anexo §8.3,
> §3.3, §6.2; N7, N8, I-VE3, H3.

## 1. Qué añade al bundle upstream

Nada que derogar: el upstream **no tiene** control de visibilidad. `member_statement(state,
member_id)` devuelve saldo + líneas + posición proyectada a quien lo llame, porque en España
el problema no existía.

**Aquí sí.** Un libro de saldos legible es un **mapa de matraqueo**: quién tiene superávit =
lista de objetivos de extorsión (§3.3, H3). Esto **ENDURECE** el diseño respecto a España; no
es una traducción.

## 2. El scope

```python
member_statement(state, member_id, scope, solicitante=None) -> dict
```

`scope` ∈ `("comite_credito", "miembro", "publico")`. **Obligatorio, sin default.**

| `scope` | Quién | Qué ve |
|---|---|---|
| `comite_credito` | el comité de crédito de la célula | todo: saldo, líneas, proyectada, estado, identidad |
| `miembro` | un miembro sobre **sí mismo** | lo suyo y nada más — exige `solicitante == member_id` |
| `publico` | cualquiera | **seudónimo + métricas agregadas.** Jamás saldo con identidad |

*Porque `scope` obligatorio y no `scope="comite_credito"` por defecto:* un default es la
configuración que nadie revisa. El fallo por omisión debe ser el seguro, y aquí el seguro es
que quien no dice desde dónde mira, no mira (M10 heredado en espíritu: rechazar, no recortar).

*Porque `miembro` exige `solicitante`:* sin él, `scope="miembro"` sería «cualquiera ve el
extracto de cualquiera», que es el scope `publico` con otro nombre.

## 3. Qué es «público» exactamente

Bajo `scope="publico"`, el motor devuelve:
- `seudonimo`: `sha256(canonical([cell_id, member_id, sal]))[:16]` — compromiso, no identidad.
- **Ningún importe individual.** Ni saldo, ni líneas, ni proyectada, ni owed_by/owed_to.
- `estado`: **no**. La escalera de sanciones sobre un seudónimo sigue siendo una marca.

`cell_metrics(state)` sigue siendo público **tal cual está**: cuenta de miembros, cuenta de
obligaciones abiertas, `gross_open_cents`, `sum_balances_cents` (siempre 0), `paused`, `seq`.

*Porque:* son agregados de célula, no de persona. `sum_balances_cents == 0` no revela nada
—es un invariante—, y `gross_open_cents` es la métrica que hace legible la salud de la célula
sin señalar a nadie. **El muro es el TIPO de salida** (H1): un agregado de célula no puede
convertirse en un escalar de persona por mucho que se le insista.

### La sal (`sal`)

`sal` es un parámetro de la célula (`params["sal_seudonimo"]`, obligatorio, string no vacío).

*Porque:* sin sal, `sha256(cell_id + member_id)` es reversible por fuerza bruta en segundos —
el espacio de `member_id` de una célula es de 30–500 nombres (§7). Un seudónimo reversible es
identidad con un paso extra. **La sal jamás sale del motor** en ninguna salida `publico`
(AC-d3.5).

## 4. Correlación entre salidas: lo que el scope NO resuelve

Un seudónimo estable permite correlacionar: quien vea dos anclas públicas (D2) o dos exportes
(D7) del mismo período ve que `a3f9…` sigue ahí. Eso ya es información.

**No se resuelve en el motor.** Un seudónimo rotatorio rompería la utilidad del anclaje (dos
raíces sobre la misma entidad no serían enlazables ni por el árbitro). La decisión —qué se
publica y con qué frecuencia— es del comité. **Señalado** (D10), no fake-resuelto (N10).

*Herencia de Fase 1:* la lista Señalados de C2C-VE ya lleva «correlación entre salidas» por la
misma razón y con la misma respuesta.

## 5. Contrato de implementación (TB.4)

1. `SCOPES = ("comite_credito", "miembro", "publico")`; `scope` obligatorio y validado.
2. `scope="miembro"` sin `solicitante` o con `solicitante != member_id` → `ValueError`.
3. `render_statement(state, member_id, scope, solicitante=None)` — mismo scope, misma regla.
4. `params["sal_seudonimo"]` obligatorio en `create_cell` (D1 ya toca `params`; se añade ahí).
5. **Cero cambios en el estado ni en los eventos.** D3 es una capa de vistas: `member_statement`
   ya era pura y de solo lectura, y sigue siéndolo.

## 6. Regresión esperada

`scope` obligatorio rompe todas las llamadas existentes a `member_statement`/`render_statement`
en los tests (misma clase que `moneda` en TA.6). Se actualizan pasando
`scope="comite_credito"`, que es el que reproduce la semántica upstream. **Ningún test cambia
de significado**; solo declara desde dónde mira.

## 7. Qué NO hace D3

- No cifra nada. El scope es control de **qué devuelve la función**, no criptografía.
- No autentica. Quién es el llamador es problema de la integración (no hay auth en el motor —
  `spec-ledger.md` §5, sigue vigente). El scope es un **contrato explícito**, no un guardia.
  **Señalado:** un llamador puede mentir y pedir `comite_credito`. El motor no puede impedirlo
  y no finge que puede.
- No resuelve la correlación (§4).
- No toca `cell_metrics` (§3).
