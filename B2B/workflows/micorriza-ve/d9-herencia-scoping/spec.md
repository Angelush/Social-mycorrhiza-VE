# Spec — D9: herencia C2C con alcance (M5)

> Nodo TB.2 (se construye **antes** que D1). Ancla: anexo §8.9, `constraints.md` M5/M6,
> rechazo codificado R3, AC-10, ST1, C3.
>
> **Este es el delta más peligroso de la Fase 2.** No porque sea difícil, sino porque la
> versión ingenua parece correcta y rompe el motor entero.

## 1. Derogación explícita del §8.9

El anexo §8.9 dice:

> «Herencia C2C: reutilizar **verbatim** las taxonomías bilingües, el matching por tokens con
> normalización de acentos, el escaneo de valores de identidad (cédula/RIF/teléfono), y los
> modos de calibración.»

**Derogado en dos puntos.** Manda `constraints.md` M5, y el rechazo codificado R3 ya
diagnosticó esta frase como el error:

1. **"las taxonomías" (todas) → solo vigilancia/identidad.** `credito`, `saldo`, `deuda`,
   `moneda`, `precio`, `pago` son el vocabulario NUCLEAR del ledger B2B. Heredar
   `MARKET_KEYS`/`RECIPROCITY_LEDGER_KEYS` prohibiría el dominio que el firewall existe para
   proteger. Un firewall que mata al paciente.
2. **"y los modos de calibración" → herencia documentada, no integrada.** El §3.7 dice que el
   B2B opera típicamente en `paz`, y ningún nodo TB.* pide integrar `modo`. Va a Señalados
   (D10), no a `src/`.

*Porque:* «verbatim» es una instrucción de **implementación** escrita antes de saber que las
taxonomías eran cinco listas con dominios distintos. Aplicarla al pie de la letra invierte la
función de la herramienta. La letra pierde contra el porqué (E1: gana lo intocable).

## 2. Hallazgo de TB.1 — el bloque compartido YA es el conjunto heredable

Auditado `C2C-VE/src/partition/membrana.py` (TB.1, 2026-07-15). El bloque delimitado por

```
# === BEGIN shared firewall machinery (byte-identical across all six capas; AC-X) ===
...
# === END shared firewall machinery ===
```

contiene **exactamente**:

| Contenido del bloque | ¿M5 lo autoriza? |
|---|---|
| `_CAMEL_BOUNDARY_RE`, `_NON_ALNUM_RE` | ✅ maquinaria de tokenización |
| `_CEDULA_RE`, `_RIF_RE`, `_TELEFONO_RE`, `_IDENTITY_VALUE_PATTERNS` | ✅ identidad |
| `FORBIDDEN_KEYS` (score/puntuacion/reputacion/lista_negra/cedula/rif/…) | ✅ vigilancia |
| `_strip_diacritics`, `_tokenize_key`, `_key_token_set`, `_key_matches_taxonomy` | ✅ maquinaria |
| `_value_has_identity_shape` | ✅ identidad |

Y **fuera** del bloque, como taxonomías privadas de capa (decisión de TA.6, para no romper el
md5): `MARKET_KEYS`/`CLAVES_MERCADO`, `RECIPROCITY_LEDGER_KEYS`, `TASA_KEYS`, `_ENVELOPE_KEYS`,
`_contains_forbidden_key`.

**Consecuencia:** el corte que M5 exige **ya está hecho** por la geometría del archivo. D9 no
recorta ninguna lista. Copia el bloque `BEGIN…END` verbatim y **no copia nada de fuera del
bloque**. La frontera `BEGIN`/`END` se convierte en el test de que el corte se respetó.

Esto es afortunado, no casual: TA.6 sacó las taxonomías de dominio del bloque compartido
precisamente porque eran *de dominio*. M5 dice lo mismo con otras palabras.

### 2.1 Corrección a Fase 1 (hallazgo de TB.1 — «manda el código»)

**El bloque ES byte-idéntico en las seis capas** (verificado en TB.1: 3018 bytes, un solo
grupo). La afirmación sustantiva de Fase 1 es correcta.

**Pero dos cosas que Fase 1 afirmó sobre él son falsas**, y D9 no puede apoyarse en ellas:

1. **El md5 `5d693ec` es incorrecto.** El real es **`758094a99054feffa153c869ecf17d5b`**. El
   valor equivocado se propagó por `DESIGN-TA4/5/6/7`, `C2C-VE/README.md` y los comentarios de
   `membrana.py`/`aseguramiento.py` **porque ningún test lo calcula jamás**.
2. **`test_cross_layer_taxonomy` NO fija los bytes.** Fija (a) `set(FORBIDDEN_KEYS)` igual al
   frozenset canónico en las seis, (b) equivalencia de **comportamiento** del tokenizador entre
   las seis, (c) que cada escáner desciende en dicts/listas/tuplas y escanea valores. **Del
   md5 no sabe nada.**

*Consecuencia operativa:* meter una taxonomía nueva **dentro** del bloque en una sola copia no
rompería nada hoy — ni `test_cross_layer_taxonomy`, ni ningún otro test. La garantía de
byte-identidad existía **solo en prosa**, que es exactamente lo que N10 prohíbe («ningún
problema abierto resuelto en prosa sin mecanismo»).

*Por eso AC-d9.1 calcula el md5 dentro del test.* No es ceremonia heredada: es el mecanismo que
Fase 1 creyó tener y no tenía. Es la primera vez que la byte-identidad del bloque pasa de
afirmación a test.

**Señalado para Fase 1** (no se arregla aquí — sería alcance colado en TB.1): el md5 falso
sigue escrito en 4 DESIGN, el README de C2C-VE y 2 comentarios de `src/`. Corregirlo es un
nodo de Fase 1, con su gate.

## 3. El hallazgo incómodo — la lista de vigilancia TAMBIÉN colisiona

La lectura ingenua de M5 es «mercado/reciprocidad es la mitad peligrosa;
vigilancia/identidad es la mitad segura, se hereda sin pensar». **Es falsa.**

`FORBIDDEN_KEYS` contiene `'veto'`, `'sancion'`, `'penalizacion'`, `'penalty'`. Y B2B hace,
legítimamente y por invariante heredada:

- **Veteo** — crédito mutuo *permissioned* con veto de admisión (brief inv. 10; §1.1 «el
  impago es contagioso»; U2 «NO cruzar las lógicas de admisión»).
- **Sanciones graduadas** — `active → warned → line_reduced → suspended → expelled` (brief
  inv. 5; `spec-ledger.md` §1.3; **AC-L9 se llama literalmente "Graduated sanctions"**).

Es la misma clase de colisión que R2 (`ban` ⊂ `urbana`, `banco_de_tiempo`), pero peor: allí
era un accidente de substring que el token-exacto arregló. **Aquí el token es exacto y la
colisión es real** — C2C y B2B usan la misma palabra para dos cosas distintas.

### La distinción que la resuelve (y que un ejecutor no puede inferir)

| | C2C: `sancion`/`veto` en una carga | B2B: sanción/veto |
|---|---|---|
| Qué es | Un **escalar pegado a una persona** | Una **posición en una escalera, ratificada por humanos** |
| Quién lo produce | El sistema, computando | El comité, juzgando (`ratified_by`) |
| Dónde vive | En una carga de forma libre | En un esquema **cerrado** (`status` ∈ 5 valores, escalera adyacente) |
| Por qué se prohíbe / permite | Reconstruye el dossier (intocable 1) | Es la gobernanza de la célula (inv. 5/10) |

**No es que B2B "relaje" la vigilancia: es que en B2B esas palabras no nombran vigilancia.**

### Estado actual: dormido, no ausente

Hoy no hay colisión porque E2 dejó los identificadores B2B en inglés y el campo se llama
`status`. **La colisión se despierta en D5**, cuyo esquema `referencias_comerciales` es nuevo
y castellano. Ver §4.

## 4. El scoping real: no solo QUÉ listas — también QUÉ SUPERFICIES

M5 se formula por taxonomía, pero el corte que de verdad protege es por **superficie de
entrada**. El ledger B2B no tiene el problema que el firewall C2C resuelve:

- **Los esquemas del ledger son CERRADOS.** `_apply` valida clave por clave; `update_member`
  tiene `allowed_keys = {credit_min_cents, credit_max_cents, status}` y rechaza cualquier otra
  (`if not set(changes.keys()).issubset(allowed_keys)`). Una forma de dossier **no tiene dónde
  entrar**: no hay carga de forma libre.
- **El firewall C2C existe porque C2C sí tiene** carga de forma libre (`carga` en el sobre) y
  salas sin barrera de admisión.

**Regla de D9:**

> El bloque compartido se hereda verbatim, pero se **aplica solo a las superficies de entrada
> de forma libre que introduzcan los deltas nuevos**. No se aplica a los esquemas cerrados
> heredados, que ya están protegidos por algo más fuerte: la lista blanca.

*Porque:* aplicar un escáner de taxonomía sobre un esquema cerrado no añade seguridad (la
lista blanca ya rechaza lo desconocido) y sí añade la posibilidad de rechazar vocabulario
legítimo. Es coste sin beneficio, en la dirección del fallo que mata al paciente.

**Superficies de forma libre en Fase 2:** exactamente una — `referencias_comerciales` (D5), que
es texto y estructura provista por humanos del comité. Ahí sí se escanea. Ahí, y en ningún
otro sitio de Fase 2.

## 5. Contrato de implementación (TB.2)

1. Crear el árbol `B2B-VE/` a partir de `B2B/{src,tests}` + goldens (patrón TA.2). `B2B/`
   queda intacto como referencia upstream.
2. Nuevo módulo `B2B-VE/src/firewall/herencia.py` que contiene el bloque `BEGIN…END`
   **byte-idéntico** al de las seis capas C2C-VE (md5 `758094a9`), y **nada más** dentro del
   bloque.
3. **No** se copia `MARKET_KEYS`, `RECIPROCITY_LEDGER_KEYS`, `TASA_KEYS`, `CLAVES_MERCADO`,
   `_ENVELOPE_KEYS` ni `_contains_forbidden_key`.
4. La taxonomía FX de D1 (`TASA_KEYS` B2B) va en una lista **privada** de `d1`, fuera del
   bloque — mismo patrón que TA.6, mismo porqué (no romper el md5).
5. D9 **no** integra el módulo `modo` (§1, punto 2).

**Por qué un módulo propio y no un import de C2C-VE:** las seis capas C2C-VE duplican el
bloque a propósito (se cargan standalone por ruta). B2B-VE es otro árbol; importar cruzaría los
dos forks y acoplaría sus ciclos de vida. La duplicación es la decisión heredada y el md5 es
lo que la hace segura.

## 6. Qué NO hace D9

- No aplica el firewall a los esquemas cerrados del ledger (§4).
- No renombra nada (E2).
- No añade `modo` al motor.
- No decide el esquema de `referencias_comerciales` — eso es D5; D9 solo fija que **esa** es
  la superficie que se escanea.
