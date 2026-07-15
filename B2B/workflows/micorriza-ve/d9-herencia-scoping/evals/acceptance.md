# Acceptance — D9: herencia con alcance

> Binary Done: se verifica el artefacto, jamás el auto-reporte. Todos ejecutables por máquina.
> `AC-10` es global (`../../../../workflows/micorriza-ve/`); los `AC-d9*` son locales.

## AC-10 — El vocabulario nuclear sigue vivo (**el criterio que importa**)

Las claves que C2C-VE rechaza y B2B-VE **debe admitir**, verificadas sobre operaciones reales
del ledger, no sobre un escáner aislado:

| Clave | En B2B-VE | En C2C-VE |
|---|---|---|
| `moneda` | **ADMITIDA** — `params["moneda"] = "USD"` crea la célula (D1) | RECHAZADA en Capa 1 salas `don_comunal`/`igualdad` (`MARKET_KEYS`) |
| `saldo`, `balance` | **ADMITIDA** | RECHAZADA en Capa 1 sala `don_comunal` (`RECIPROCITY_LEDGER_KEYS`) |
| `credito`, `credit` | **ADMITIDA** | RECHAZADA ídem |
| `deuda`, `debt` | **ADMITIDA** | RECHAZADA ídem |
| `precio`, `pago`, `centavos` | **ADMITIDA** | RECHAZADA (`MARKET_KEYS`) |

Pass/fail: `create_cell(...)` + un flujo de obligaciones con esas claves **completa sin
lanzar**; y las mismas claves siguen lanzando `ErrorDeBrechaMembrana` en la suite C2C-VE (que
no se toca).

> **Por qué este AC prueba la ADMISIÓN y no el rechazo:** un firewall roto que rechaza todo
> pasa cualquier test que solo compruebe rechazos (F-d9.1). El caso positivo es el único que
> distingue «firewall con alcance» de «firewall que mató al paciente».

## AC-d9.1 — El bloque compartido es byte-idéntico (**mecanismo nuevo**)

El test extrae el bloque `BEGIN…END` de `B2B-VE/src/firewall/herencia.py` por regex, calcula su
md5 y lo compara con el literal:

```python
BLOQUE_MD5 = "758094a99054feffa153c869ecf17d5b"   # verificado en TB.1 sobre las 6 capas C2C-VE
```

Pass/fail: igualdad de cadena.

*Porque:* es el mecanismo que **Fase 1 creyó tener y no tenía** (ver `../spec.md` §2.1). El md5
que circulaba en los DESIGN, el README y los comentarios de C2C-VE era `5d693ec` —
**incorrecto**, y sobrevivió cinco nodos porque ningún test lo calculaba. Este AC es la primera
vez que la byte-identidad del bloque pasa de prosa a test (N10).

*Y por qué importa aquí y no allí:* `test_cross_layer_taxonomy` fija el conjunto
`FORBIDDEN_KEYS` y el comportamiento del tokenizador. Una taxonomía **extra** dentro del bloque
deja ambos intactos y solo la rompe la byte-identidad (F-d9.3).

**El literal es un dato de entrada, jamás una salida de este nodo** (ST-d9.3): si el md5
calculado no coincide, la respuesta es arreglar la copia — nunca actualizar el literal.

## AC-d9.2 — Nada de fuera del bloque se heredó

El módulo `herencia.py` **no** define `MARKET_KEYS`, `CLAVES_MERCADO`,
`RECIPROCITY_LEDGER_KEYS`, `TASA_KEYS`, `_ENVELOPE_KEYS` ni `_contains_forbidden_key`.
Pass/fail: `hasattr` sobre el módulo — todos `False`. Además grep-gate: ningún token de esas
listas aparece en `B2B-VE/src/firewall/`.

## AC-d9.3 — La maquinaria heredada funciona

Sobre `herencia.py`, los casos que fijó el área a de Fase 1 (R2):
- `bancoDeTiempo` → tokens `banco,de,tiempo` → **admitida** (no colisiona con `ban`).
- `lista_negra_local` → bigrama `lista_negra` → **rechazada**.
- `descripción_del_score_musical` → token `score` → **rechazada** (dirección de fallo
  conservada).
- `"V-12.345.678"` como VALOR → `_value_has_identity_shape` → **True**.

Pass/fail: booleano por caso. *Porque:* si la copia funciona distinto que el original, el md5
pasó pero el bloque se cargó mal (p. ej. un import faltante).

## AC-d9.4 — La colisión de dominio está auditada

Para cada clave que introduzcan D1–D8 en castellano, `_key_matches_taxonomy(clave,
FORBIDDEN_KEYS)` es `False`. Cobertura mínima: `moneda`, `expira_en_dias`,
`referencias_comerciales`, `avalista`, `relacion_declarada`, `antiguedad_meses`,
`comite_credito`, `salida_con_saldo`, `puente_pausar`, `anclar`.

Pass/fail: todos `False`. **Si alguna da `True`, se renombra la clave** (N-d9.1) y se re-corre
— jamás se toca `FORBIDDEN_KEYS`.

*Porque:* C-d9.5. Este AC es el que mantiene dormida la colisión `veto`/`sancion`: es un
centinela que se dispara el día que alguien elija un nombre castellano que sí colisione.

## AC-d9.5 — El firewall no es decorativo

La superficie de forma libre de D5 (`referencias_comerciales`) rechaza de verdad, end-to-end:
una referencia con una clave `puntuacion` o con un valor de forma cédula es rechazada por la
operación real del comité, no por una llamada directa al escáner. Pass/fail: raise.

*Porque:* F-d9.5 — un módulo importado y nunca llamado aparenta una defensa que no existe.
**Este AC se verifica en TB.5** (cuando D5 exista); en TB.2 se declara pendiente y se enlaza.

## AC-d9.6 — Los esquemas cerrados NO se escanean

`update_member(state, mid, {"credit_max_cents": N}, ...)` completa sin invocar el firewall, y
una clave desconocida sigue siendo rechazada por la lista blanca heredada (`allowed_keys`), no
por la taxonomía. Pass/fail: la operación legítima pasa; `{"cualquier_cosa": 1}` lanza
`ValueError`.

*Porque:* C-d9.4/N-d9.2 — la defensa correcta ya estaba, y es más fuerte.
