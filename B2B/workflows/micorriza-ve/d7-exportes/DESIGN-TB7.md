# DESIGN-TB7 — D7: `exportar_registros`

> Nodo TB.7 (deps: TB.4 ✅). Delta único → DESIGN en `d7-exportes/`.
> Piso de entrada: `cd B2B-VE && ../.venv-ve/bin/python -m pytest -q` → **195 passed, 3 skipped**.

## 0. Tres reconciliaciones antes de escribir código

### 0.1 El `scope="miembro"` por defecto de la spec §2 — se DEROGA

La firma de spec §2 trae `scope="miembro"` **con default**. Contradice dos cosas a la vez:

- **C-d3.1** (heredado vía C-d7.3, «reutilizar el scope de D3»): scope obligatorio, sin
  default, porque *un default es la configuración que nadie revisa* (F-d3.1: el delta queda
  instalado y desactivado a la vez).
- **AC-d7.1**, en el mismo bundle: «scope **ausente** o desconocido → `ValueError`». Con un
  default, un scope ausente **no lanza nada**: la firma y su propio AC no pueden ser ciertos a
  la vez.

**Manda el AC** (es lo ejecutable) **y manda D3** (C-d7.3 dice reutilizar su scope, y su scope
no tiene default). → `scope` **posicional obligatorio**, como en `member_statement`. Reutilizar
el scope de D3 y darle un default sería reutilizar la firma y tirar el porqué.

*Matiz sobre el tipo de error:* con `scope` posicional obligatorio, omitirlo da `TypeError` de
Python, no `ValueError`. AC-d7.1 dice `ValueError`. Se cumple **el porqué** (no hay default
cómodo) con una defensa **más temprana y más barata** que la nuestra — y es exactamente lo que
ya hace `member_statement` (AC-d3.1 lo admite explícitamente: «`TypeError`/`ValueError`»). Se
documenta aquí para que nadie «arregle» la firma para que case con la letra del AC.

### 0.2 Dónde vive — módulo nuevo, y qué le hace eso a AC-7

`src/ledger/exportes.py`, **no dentro del ledger**. Precedente exacto de TB.3 (`anclaje.py`):
el ledger exporta `op(state, …) -> (new_state, event)`; `exportar_registros` no tiene esa forma
(no mueve valor, no emite evento), y meterla ahí **invita a darle un `ratified_by`** (F-d2.6).
Dependencia de un solo sentido (`exportes` → `ledger`), sin ciclos. Shim de path
`__file__`-relativo (patrón TA.4).

**Pero eso rompe una promesa de la spec.** F-d7.5 dice que AC-7 de D3 cubre
`exportar_registros` **automáticamente** «por eso está escrito por enumeración». Falso si la
función vive en otro módulo: **la enumeración de TB.4 recorre el módulo del ledger y no la
vería**. La spec asumió que D7 iba dentro del ledger.

**Arreglo — se extiende la enumeración, no se mueve la función:** el AC-7 de
`test_d3_visibilidad.py` pasa a enumerar la superficie pública de **los tres módulos**
(`mutual_credit_ledger`, `anclaje`, `exportes`). Así la promesa de F-d7.5 se vuelve cierta y,
de paso, cubre `anclaje.py`, que **hasta ahora nadie enumeraba**. La geometría correcta del
módulo se conserva; el que se adapta es el test. (Y una función pública nueva en cualquiera de
los tres, sin clasificar, sigue rompiendo el test el día que se escribe.)

### 0.3 `raiz_ancla` — el motor NO puede saber si hay ancla

AC-d7.7 exige omitir `raiz_ancla` si el período no está anclado. Pero **anclar ≠ publicar**
(ST-d2.1: la marca temporal la da la publicación, que ocurre fuera del motor), así que el motor
no tiene forma de saberlo. Calcularla al vuelo es justo lo prohibido: daría **falsa sensación
de prueba** (ST-d7.2).

→ Parámetro explícito `ancla=None`. Si el llamador no pasa un ancla publicada, **el campo no
existe** en la salida (se omite la clave, no se pone `None` — una clave con `None` invita a
rellenarla). Quien tiene el ancla es quien la publicó; el motor no lo adivina.

## 1. Contrato

```python
exportar_registros(state, events, member_id, desde_ts, hasta_ts, scope,
                   solicitante=None, formato="json", ancla=None) -> str
```

`scope` antes de los opcionales (es obligatorio). `formato ∈ ("json","csv")` sí lleva default:
no es una propiedad de seguridad, es una preferencia de presentación.

**Pura**: devuelve `str`, no toca disco ni red (C-d7.1) — el mismo porqué que `anclar`: es lo
que hace que el motor corra en un apagón y no sea capturable. No muta `state` ni `events`.

**Derivado de `events`, no de `state`** (C-d7.2): un exporte de marzo con saldos de julio
**cuadra consigo mismo y es falso** (F-d7.7). El saldo del período se reconstruye por `replay`
sobre el prefijo del stream, que es la misma maquinaria que ya verifica la cadena → el exporte
hereda la integridad gratis.

## 2. Contenido

Cabecera (una vez): `celula_id`, `miembro_id`, `moneda`, `periodo`, `saldo_inicial`,
`saldo_final`, y `raiz_ancla` **solo si** se pasó ancla (§0.3).
Por línea: `fecha`(ts) · `tipo` · `contraparte` · `importe_centavos` · `referencia` ·
`hash_evento`.

**`moneda` va en la cabecera y JAMÁS por línea** (C-d7.5). Una columna por línea sugiere que
puede variar, y la pregunta siguiente es «¿a qué tasa convierto?». **El formato del exporte
puede hacer representable el FX aunque el motor no lo represente** — no se le da la forma.

**Centavos enteros** (C-d7.6/M4): `cents/100` «para que quede bonito» reintroduce el float
exactamente donde el número sale del sistema y entra en una hoja de cálculo — que es donde el
redondeo se vuelve dinero.

Bajo `publico`: seudónimo de D3 (`_seudonimo`, reusado — no reimplementado), sin importes
individuales, sin contrapartes.

## 3. Lo que NO hace — y por qué el silencio es el diseño

**No calcula IGTF, no marca gravable, no genera nada del SENIAT** (N-d7.1). El tratamiento del
crédito mutuo es **ambiguo** y el riesgo es *enforcement arbitrario, no incumplimiento de una
norma clara* (§5). Si el motor clasificara y la interpretación fuera incorrecta, **el sistema
le creó el problema al miembro**. Es lo que I3 reserva al humano. Compliance-**ready**, no
compliance-dependent. Y no se promete neutralidad fiscal en ningún sitio (N-d7.2).

AC-d7.4 lo fija por **AST sobre todo `src/`**: cero multiplicaciones de un importe por una
constante fraccionaria. Un test de ausencia de la palabra «igtf» solo caza al que lo nombra.

## 4. CSV e inyección (ST-d7.4)

Un `member_id` que empiece por `=`, `+`, `-` o `@` se ejecuta como fórmula al abrir el CSV en
Excel. Los `member_id` **los eligen humanos**: no es paranoia. Se escapa el prefijo. Ojo con
`-`: un importe negativo (`-2500`) **no** debe escaparse — es un número, no una fórmula, y
escaparlo rompería AC-d7.3 (`^-?\d+$`). El escape aplica a **celdas de texto**, no numéricas.

## 5. Verificación por mutación (obligatoria — sin ella el nodo no cierra)

1. `importe = cents/100` en el CSV (F-d7.2, el float que vuelve) → AC-d7.3 rojo.
2. columna `moneda` por línea (F-d7.3) → AC-d7.5 rojo.
3. exporte derivado de `state` en vez de `events` (F-d7.7) → AC-d7.6 rojo.
4. `raiz_ancla` calculada al vuelo cuando no hay ancla (ST-d7.2) → AC-d7.7 rojo.
5. `member_id` crudo en el CSV (ST-d7.4) → AC-d7.9 rojo.
6. añadir `igtf_centavos = importe * 0.03` (F-d7.1, el exporte servicial) → AC-d7.4 rojo **por
   AST**, no por la palabra.
7. `publico` con identidad (F-d7.6) → AC-7 rojo, **incluido el AC-7 de D3 por enumeración** —
   que es la prueba de que §0.2 quedó bien resuelto.

## 6. Reparto

- **Opus:** este DESIGN, las tres reconciliaciones, la extensión de AC-7 a tres módulos, el
  AST de AC-d7.4, `exportes.py`.
- **`agy-gemini-3-flash`** (coding, fit +12.93, seen 30, 7/7 verdes): AC-d7.3/d7.5/d7.9/d7.10,
  mecánicos con contrato fijado por Opus. Al revisar: `match=` obligatorio y control negativo.

## 7. Señalados de D7 → README de TB.9

- **El exporte es la superficie de fuga más probable, y no por un bug: su propósito es salir
  del sistema** (ST-d7.1). El scope protege lo que el motor devuelve; lo que el miembro haga
  con su CSV está fuera. Correcto e irreducible.
- La verificabilidad ante terceros depende de una publicación que el motor no hace (ST-d7.2).
- Un exporte de una célula de dos identifica a la contraparte (ST-d7.3) — aritmética, como
  ST-d3.3.
- No se promete neutralidad fiscal; una reclasificación agresiva del SENIAT es escenario real
  (§6.7) → asesoría local, jamás una interpretación incrustada en el código.
