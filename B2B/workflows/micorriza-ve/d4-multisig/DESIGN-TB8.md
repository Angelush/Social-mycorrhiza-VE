# DESIGN TB.8 — D4: multisig de reserva (documento de gobernanza + helpers de verificación)

> Opus, 2026-07-16. Deps: **TB.1 ✅ `3ef5054` + M9 ✅ `edc0650`+`ba58bce`**. Piso citado:
> `cd B2B-VE && ../.venv-ve/bin/python -m pytest -q` → **327 passed, 3 skipped**.
> `cd B2B && ../.venv-ve/bin/python -m pytest -q` → 125 passed, 3 skipped (upstream, intacto).

## §0 — Lo que este nodo NO puede hacer, escrito primero

**El motor no custodia claves (N9/I-VE4), no firma, no consulta la cadena y no criba contra la
SDN.** D4 es un **documento de gobernanza** + **helpers puros de verificación**. De ahí sale la
consecuencia que gobierna todo el nodo:

> **Una suite verde no dice NADA sobre el umbral, los roles ni la rotación.** El motor no los
> toca. Viven en prosa, y ahí es donde se ven o no se ven.

Es lo contrario de los ocho nodos anteriores, donde el test ERA la defensa. Aquí el test cubre
la aritmética; el resto lo cubre un humano leyendo (ST-d4.3, y se dice en vez de fingir
cobertura).

## §1 — Los tres valores tienen DOS procedencias, y esa es la carga del nodo

`context.md` §2 §D4 (2026-07-16):

| Decisión | Valor | Procedencia | Estado |
|---|---|---|---|
| **Umbral** | **3 de 5** | **Propietario, 2026-07-16** | **DECIDIDO** |
| Roles firmantes | 5 cargos | **Opus (relleno)** | **PROVISIONAL** |
| Rotación | 12 meses escalonada + disparadores | **Opus (relleno)** | **PROVISIONAL** |

**El documento de gobernanza ARRASTRA la marca de provisionalidad, no la deja atrás en
`context.md`.** Si `gobernanza-multisig.md` presenta los cinco cargos con el mismo tono que el
umbral, TB.8 ha fake-resuelto una decisión de gobernanza (N10) — y lo habría hecho con formato
de entregable, que es la forma que no se ve. El documento es lo que leerá un comité para decidir
dónde pone su dinero; es exactamente el sitio donde un andamio se lee como decisión.

*Por qué esto no es celo excesivo:* un valor inventado y uno decidido son **indistinguibles
dentro de seis meses** si nadie escribe cuál fue cuál. Es el mismo fallo que M9 previene en las
verificaciones fechadas, y la misma razón por la que la firma de `2026-07-15-sanciones.md` §5
registra **cómo** se produjo («no consta lectura íntegra») en vez de ser una firma limpia.

**Lo que NO es relleno y se separa del resto:** la restricción geográfica. Ver §4.

## §2 — Geometría: módulo nuevo, aditivo puro

`B2B-VE/src/gobernanza/multisig.py` — **paquete nuevo de primer nivel**, hermano de
`ledger/`, `firewall/`, `clearing/`.

*Por qué no `src/ledger/multisig.py`* (a diferencia de `anclaje.py` y `exportes.py`, que sí
viven ahí): aquellos leen la cadena del ledger; **este no importa el ledger ni lo toca**. Es
gobernanza de una reserva que vive fuera del motor. Meterlo bajo `ledger/` invita exactamente a
lo que N-d4.2 prohíbe — que un día alguien le pase el `state` «para cuadrar el fondo con el
saldo del miembro-fondo», que es ST-d4.4 con forma de conveniencia.

**Aditivo puro, como TB.3/TB.7:**
- `git diff` sobre `mutual_credit_ledger.py`, `anclaje.py`, `exportes.py`, `herencia.py` →
  **VACÍO**. Así se PRUEBA, no se afirma.
- **Goldens NO se regeneran.** D4 no toca `create_cell` ni `params` → `head_hash` invariante.
  Si un golden se mueve en este nodo, **INVESTIGA, NO REGENERES**: significa que D4 tocó el
  motor, que es justo lo que no debe hacer.
- `herencia.py` intacto → las 7 copias, md5 `5d693ecf1833…`, **span = bloque completo con `\n`,
  3023 bytes** (= 3019 caracteres; dos unidades del mismo span, no hay discrepancia).

## §3 — Tres reconciliaciones (la spec contra la realidad)

### 3.1 — `AC-d4.0` pide un archivo que M9 no produjo con ese nombre

`AC-d4.0` y spec §5 exigen `docs/verificaciones/AAAA-MM-DD-sanciones-multisig.md`. M9 produjo
**`2026-07-15-sanciones.md`** y **`2026-07-15-cripto.md`**, y están **FIRMADOS** por el
propietario. `C-d4.1` es más laxa y dice `AAAA-MM-DD-*.md`.

**Manda el artefacto real.** Renombrar un documento firmado para que cuadre con un glob sería
tocar la firma — el artefacto es el hecho, el AC es la descripción. Y el reparto en dos archivos
es **mejor** que el nombre único de la spec: `AC-d4.0` exige cubrir sanciones **y** marco cripto
**y** marco fiscal, y son tres cosas con caducidades distintas (10-15 y 09-15). Un archivo único
tendría una sola fecha para tres hechos que envejecen a ritmos distintos.

→ AC-d4.0 se escribe contra los **dos** archivos, por glob `[0-9]*-*.md`.

### 3.2 — El esquema `politica` de spec §3 no admite lo que `context.md` decidió

Spec §3 trae `rol: "local"|"diaspora"`; `context.md` §2 trae **5 cargos**. No es la misma
dimensión y no colisionan: `rol` es el eje de **alcance físico** (el que exige `C-d4.4`: quién
está fuera del alcance de una presión local), el cargo es el eje de **función** (el que exige que
ninguna captura de una sola función alcance el quórum). El esquema lleva las dos, separadas.

**`cargo` sí puede entrar; `alias` es el campo peligroso.** N8 dice cargos, JAMÁS nombres — un
cargo es una función, no una persona. Pero `alias` de spec §3 es un campo de texto libre en un
repo público, y «alias» invita a poner el apodo por el que todo el mundo conoce a alguien.
Se conserva (la spec lo pide y `describir_politica` necesita algo que imprimir) **y se le aplica
el escáner de identidad heredado** (`_value_has_identity_shape`), igual que D5 hizo con
`referencias_comerciales`. Es la **segunda** superficie de forma libre de Fase 2; la memoria dice
«exactamente una» — esta nota la corrige.

*Y se dice el límite, porque es ST-d5.5 otra vez:* **el escáner es de FORMA, no de contenido.**
`alias: "el hermano del dueño de la ferretería de Chacao"` pasa limpio. El escáner caza cédulas y
RIF, no descripciones. **Señalado.**

### 3.3 — `P-d4.1` prefiere 2-de-3; el propietario decidió 3-de-5

No es contradicción: `P-d4.1` es preferencia, y el propietario decide (I3). **`verificar_umbral`
sigue aceptando los dos** — `AC-d4.1` lo exige explícitamente (fila `umbral=2, total=3` ✅). El
helper valida la **fórmula**; el documento registra la **elección**. Que el helper solo aceptara
3-de-5 sería hornear una decisión de gobernanza en el motor, que es N9 por la puerta de atrás.

## §4 — La restricción geográfica: lo único del relleno que se sostiene solo

De la aritmética de 3-de-5, no de una opinión:

- **Ningún lugar concentra el quórum** → una redada en un sitio no abre la reserva.
- **Perder un lugar no deja bajo el quórum** → un apagón o una emigración en bloque no deja la
  reserva **INACCESIBLE**. **Es el fallo simétrico y el más probable** (§6.5, éxodo continuo), y
  el que siempre se olvida porque «perder el fondo» suena a robo, no a nadie contesta el teléfono.

**Generaliza, y por eso el helper lleva la fórmula y no el número:**

```
max_por_localidad ≤ umbral − 1          (ninguna localidad concentra el quórum)
total − max_por_localidad ≥ umbral      (perder la mayor no deja bajo el quórum)
```

- 3-de-5 → máx **2** por localidad ⇒ mín **3** localidades. (Coincide con `context.md`.)
- 2-de-3 → máx **1** por localidad ⇒ mín **3** localidades. (Y `AC-d4.1` exige aceptarlo.)

Que los dos umbrales caigan de la misma fórmula es la evidencia de que la restricción no era
opinión de Opus. **Si un día se rehacen los roles, esto se conserva.**

### 4.1 — La colisión con N8, y la salida

`AC-d4.4` prohíbe **explícitamente** «ciudades concretas de firmantes» en documento y fixtures.
Pero la regla no es comprobable sin un campo de localidad. Las dos son correctas y chocan.

**Salida: la etiqueta es OPACA.** `localidad: "L1"|"L2"|…` — un identificador de agrupación **sin
semántica geográfica**. El helper comprueba la **forma de la distribución**; el repo **nunca dice
dónde vive nadie**. El comité sabe qué es L1; el repo público no, y no le hace falta para la
aritmética.

*Es ST-d5.5 del revés:* allí el firewall solo podía ver la forma y el contenido se le escapaba —
un defecto. Aquí **la forma es exactamente lo que hay que comprobar y el contenido es
exactamente lo que no debe estar** — una virtud. Misma propiedad, signo opuesto, porque la
pregunta es distinta.

**Señalado (nuevo, → README de TB.9):** el motor no puede saber que dos etiquetas distintas son
dos localidades **realmente descorrelacionadas**. Quien ponga `L1/L2/L3` a tres barrios de
Caracas pasa el test verde y tiene un multisig de una sola ciudad — F-d4.4 intacto, con
certificado. **El motor comprueba la aritmética; que las etiquetas correspondan a lugares que no
caen juntos es del comité.** Misma familia que el hallazgo 5 de M9 (el motor no criba) y que
ST-d4.4 (nada garantiza que ledger y cadena coincidan): el motor verifica lo que puede sostener,
y **dice** lo que no.

**`localidad` es OBLIGATORIA**, no opcional. Opcional = F-d4.4 pasa en silencio para toda
política que la omita, y el campo que existe para cazarlo solo lo caza en quien se molesta en
rellenarlo.

## §5 — Los helpers (spec §3, firmas conservadas)

```python
def verificar_formato_direccion(direccion: str, cadena: str) -> bool
def verificar_umbral(politica: dict) -> None   # ValueError si es incoherente
def describir_politica(politica: dict) -> str  # markdown para el comité
```

**Todos puros.** Sin red, sin claves, sin firmar, sin saldo. Esquema **cerrado** (patrón del
ledger: lista blanca, reconstruye clave a clave) → un campo `clave_privada` **no es
representable**, no «se rechaza». I1: forma irrepresentable antes que flag.

### 5.1 — `verificar_umbral` rechaza (AC-d4.1 + §4)

`umbral > total` · `umbral < 2` (umbral 1 es una wallet con pasos extra, F-d4.3) · `total > 5` ·
`len(firmantes) != total` · direcciones duplicadas · alias duplicados · **cero `diaspora`** ·
**cero `local`** · **la fórmula de §4** · alias con forma de identidad (§3.2).

**Mensajes distinguibles y anclados con `match=`** (lección de TB.5): `umbral: minimo`,
`umbral: mayor que total`, `firmantes: duplicados`, `firmantes: sin diaspora`,
`localidad: concentra el quorum`, `localidad: perder una deja bajo el quorum`. Dos defensas
distintas con el mismo mensaje son una defensa que no se puede probar por separado (la lección de
la mutación M2 de TB.6).

### 5.2 — `verificar_formato_direccion` — formato, y SOLO formato

- **TRC-20:** base58check — prefijo `0x41`, 25 bytes, checksum = primeros 4 de `sha256d`.
  `hashlib`, que ya estaba.
- **ERC-20:** EIP-55 — necesita **keccak-256**, que **NO es** `hashlib.sha3_256` (distinto
  padding: `0x01` vs `0x06`). Implementado puro en el módulo, **cero imports**.
  **Gate, verificado ANTES de escribir esto:** 3 vectores de hash publicados (incl.
  `keccak256(b"") = c5d2460186f7233c…`) + las **4 direcciones oficiales del propio EIP-55**.
  Si un vector fallara, ERC-20 se quedaría sin checksum **y se diría** — un keccak casero
  silenciosamente mal devuelve `False` sobre direcciones válidas, y eso es «un error caro» con
  firma de software, exactamente lo que el helper existe para evitar.

*Un hash no es custodia.* `AC-d4.2` prohíbe librerías de **firma** (`ecdsa`, `eth_account`,
`nacl`); keccak es una función de resumen sin estado, sin claves y sin red — la misma clase que
`hashlib`, que el ledger usa desde upstream. Se escribe aquí porque se dirá que «el motor tiene
primitivas cripto»: las tiene, y no puede firmar con ellas.

**El docstring dice explícitamente que NO afirma que la dirección exista ni tenga saldo**
(AC-d4.5) — comprobarlo exige red (F-d4.2), y con red el fondo se vuelve capturable **a través
del motor**.

## §6 — AC-7 (D3): el módulo nuevo, y un defecto en el propio AC-7

Escribir tres funciones públicas nuevas **pondrá AC-7 rojo. Es el diseño de TB.4 funcionando.**
Las tres van a `SIN_SCOPE` **con motivo escrito**: no reciben `state`, no hay miembro que acotar.
`describir_politica` sí rinde una vista legible, pero **de la política** (un documento de
gobernanza), no del ledger — y `AC-d4.7` la acota por su cuenta (direcciones truncadas).

**PERO:** `test_ac7` enumera una **lista literal de módulos** (`[led, anclaje, exportes]`). Un
módulo nuevo **no rompe nada**: sus funciones simplemente no se enumeran. **Es el mismo defecto
que AC-7 existe para prevenir, un nivel más arriba** — TB.4 mató la lista de funciones que
envejece y dejó viva una lista de módulos que envejece igual. TB.7 ya lo parcheó una vez a mano
(F-d7.5) añadiendo `exportes`; TB.8 sería la segunda. **A la segunda no se parchea: se arregla.**

→ **La enumeración descubre los módulos por glob sobre `src/**/*.py`.** Un módulo nuevo entra
solo. Coste honesto: entran también `clearing_solver.py` y `herencia.py`, cuyas públicas hay que
clasificar **con motivo**. Es trabajo real y es el correcto: hoy nadie las enumera y nadie
decidió que no hiciera falta.

## §7 — AC-d4.0: la caducidad, ejecutable

`AC-d4.0` pide «fecha parseable». **Se escribe más fuerte: el test falla si la verificación está
CADUCADA** (sanciones 2026-10-15, cripto 2026-09-15, declaradas por M9).

*Por qué, sabiendo que es un test que se pondrá rojo por el calendario y no por un cambio de
código:* es literalmente `C-d4.1` — «re-verificar, no recordar; un dato de hace seis meses no es
información, es una suposición con fecha». Un test que siguiera verde en 2027 sobre una
verificación de 2026 sería el fake-resolve que M9 existe para prevenir, **con formato de
cobertura**. La alternativa —comprobar solo que la fecha se parsea— convierte M9 en folclore: el
archivo está, luego el requisito está cumplido, para siempre.

*El riesgo, dicho:* en octubre alguien le pone un `skip` en vez de re-verificar. No se puede
impedir desde el test. Lo que sí se puede es que el mensaje diga qué hacer: **«re-verifica, no
borres el test»**, con la ruta del archivo y el nodo (M9) que lo produce.

## §8 — Plan de AC

| AC | Qué fija | Dónde |
|---|---|---|
| AC-d4.0 | M9 presente, fechado, **no caducado**, secciones, sin datos personales | `test_d4_multisig.py` |
| AC-d4.1 | `verificar_umbral` — la tabla + la fórmula de §4 | idem |
| AC-d4.2 | **EL QUE IMPORTA** — el motor no custodia: grep + AST sobre todo `src/` | idem |
| AC-d4.3 | pureza: `socket`/`open` parcheados; no muta la entrada | idem |
| AC-d4.4 | sin identidades: escáner heredado sobre documento + fixtures | idem |
| AC-d4.5 | formato y solo formato; vectores TRC-20 y EIP-55; docstring | idem |
| AC-d4.6 | el documento dice qué NO cubre | idem (presencia) + **gate humano M1** |
| AC-d4.7 | `describir_politica` legible, direcciones truncadas, no inventa | idem |
| AC-7 (D3) | glob de módulos + las 3 nuevas clasificadas | `test_d3_visibilidad.py` |

**Control negativo obligatorio** en AC-d4.2 (una clave privada de juguete **es** cazada por el
grep — si no, el grep pasa por vacuidad) y en AC-d4.4 (una cédula sintética **sí** dispara el
escáner sobre el mismo texto que se declara limpio; y una dirección base58 **no** lo dispara,
porque `\b[VE]-?\d…` necesita un límite de palabra que dentro de una tirada alfanumérica de 34
caracteres **no existe** — verificado, no supuesto).

## §9 — Mutaciones planificadas (+ una NO planificada, obligatoria)

Van **seis** defectos cazados así en tests de criterio de Opus (TA.9, TB.4, TB.5, TB.6, TB.6b,
TB.7). Un test de invariante que no se ha visto fallar no se sabe si prueba algo.

1. `umbral < 2` → `umbral <= 0` (F-d4.3, el umbral 1 pasa).
2. La fórmula de §4 → solo «mín. 3 localidades» (deja pasar 3+1+1 con umbral 3: **una localidad
   con el quórum entero** — la redada abre la reserva y hay 3 localidades, test verde).
3. La fórmula → solo «máx. 2 por localidad» (deja pasar 2+2+1 **con umbral 4**… y el fallo
   simétrico: perder una deja 3 < 4. La reserva inaccesible, que es el más probable).
4. `localidad` obligatoria → opcional con default.
5. Escáner de identidad fuera de `alias`.
6. Direcciones completas en `describir_politica` (AC-d4.7).
7. La caducidad de AC-d4.0 → solo «fecha parseable».
8. `sha3_256` en vez de keccak en EIP-55 (**el defecto plausible de verdad**: la línea se lee
   idéntica y `hashlib` la ofrece).
9. Glob de módulos → lista literal (AC-7 vuelve a envejecer).

## §10 — Reparto (skill `multi-model-orchestration`)

Estado: `coding` → `agy-gemini-3-flash`, score **+15**, seen 32, 8/8 verdes.

**SIN FAN-OUT.** El DESIGN lo listaba como buen candidato («helpers mecánicos con contrato
fijable») y **se deroga aquí, como TB.5 derogó al candidato de su propio DESIGN**: la regla de
coste de TA.9 dice que si redactar el contrato de firmas cuesta lo mismo que el test, no se
delega. Aquí es peor que empatar:

- La parte con volumen (vectores base58check/EIP-55) **ya está resuelta en contexto** — la sonda
  de keccak corrió antes de escribir este DESIGN.
- La parte que queda **es criterio puro**: la fórmula de §4 y sus dos direcciones, la
  clasificación de AC-7, la caducidad de AC-d4.0, el control negativo del `\b`. Explicar por qué
  3+1+1 debe fallar **es** el trabajo.
- Y el entregable principal es un **documento de gobernanza cuya carga es la procedencia de cada
  valor** (§1). Está en la lista de «NUNCA a fan-out».

TB.9 (README largo) y TS.4 (campañas) siguen siendo los candidatos buenos que quedan.

---

## §11 — RESULTADO (Opus, 2026-07-16). Suite **327+3 → 388 passed + 3 skipped** (+61)

`B2B/` upstream intacto (125+3) · `C2C-VE` intacto (441) · bloque firewall `5d693ec`, **3023
bytes = 3019 caracteres**, idéntico en las 7 copias.

**Aditivo puro, PROBADO:** `git diff` sobre `src/ledger/`, `src/firewall/`, `src/clearing/` y
`evals/` → **VACÍO**. Los goldens **no se regeneraron** y no hizo falta: D4 no toca
`create_cell`. Lo único modificado fuera de D4 es `test_d3_visibilidad.py` (AC-7, ver §11.2).

### §11.1 — Mutaciones: **12 corridas, 10 cazadas, 2 equivalentes** (verificadas, no supuestas)

| # | Mutación | Resultado |
|---|---|---|
| M1 | `umbral < 2` → `umbral <= 0` | **3 rojos** (F-d4.3) |
| M2 | la fórmula → solo «mín. 3 localidades» | **3 rojos** |
| M3 | la fórmula → solo «máx. 2 por localidad» | **1 rojo** — y **solo el del fallo simétrico** |
| M4 | `localidad` obligatoria → opcional | **1 rojo** |
| M5 | el escáner no mira `alias` | **1 rojo** |
| M6 | direcciones completas en `describir_politica` | **1 rojo** |
| M7 | verificación de sanciones caducada (reloj real) | **1 rojo**, con el mensaje correcto |
| M8 | `sha3_256` en vez de keccak en EIP-55 | **5 rojos** |
| M9 | el glob de AC-7 → lista literal | **NO CAZADA** → ver §11.2 |
| M10 | truncar con `[:10]+"…"` | no cazada — **equivalente** |
| M11 | escanear identidad también en `direccion` | no cazada — **equivalente** |
| M12 | cargos duplicados dejan de rechazarse | **1 rojo** |

**M3 es la que justifica que la fórmula tenga dos condiciones y no una:** cae en el test del
fallo simétrico **y solo en él** — el de la reserva INACCESIBLE, que es el más probable (§6.5) y
el que la intuición no busca, porque «perder el fondo» suena a robo y no a que nadie contesta el
teléfono. Una sola condición habría dejado ese mundo verde.

**M10 y M11 no son defectos, y se dice en vez de inflar el marcador a 12/12:**
- **M10** — el test fija la **propiedad** (la dirección completa no sale; el prefijo se ve para
  poder cotejar), no el formato exacto. Un prefijo de 10 tampoco es la dirección. Fijar el
  formato sería sobre-especificar el render.
- **M11** — aplicar el escáner de identidad a `direccion` es un **no-op**, y eso ya lo predice
  `test_acd44_control_negativo_...`: `_CEDULA_RE` empieza por `\b`, y dentro de una tirada
  alfanumérica de 34 caracteres **no hay límite de palabra**, así que ninguna dirección puede
  casar. La mutación confirma el control negativo en vez de contradecirlo.

### §11.2 — HALLAZGO (M9) — **AC-7 no protegía su propia cobertura, y la predicción falló**

§6 predijo que escribir tres funciones públicas nuevas pondría AC-7 rojo. **NO LO HIZO: la suite
se quedó verde.** El módulo era nuevo, la lista de módulos era literal, y `multisig.py`
simplemente no se enumeraba. TB.6 dejó escrito «AC-7 se pondrá rojo al escribir funciones
públicas nuevas: es el diseño funcionando» — y es **falso para un paquete nuevo**.

Se cambió a glob (§6). **Pero la mutación M9 destapó que eso tampoco bastaba:** al devolver el
glob a una lista literal, **la suite seguía en 388 verdes**. El endurecimiento era **una defensa
que no habla**, y se deshacía con un `git revert` silencioso.

→ **La enumeración ahora se declara completa y se comprueba:** `{m.__file__} == {src/**/*.py}`.
Con el glob es trivialmente cierto; con una lista literal **falla y dice qué módulo falta**.
Repetida M9 con el assert puesto: **1 rojo**, señalando el módulo.

**Lección general (la de TB.6b, en otra forma):** una defensa por enumeración necesita que
**alguien enumere al enumerador**. Sin eso, el nivel de arriba siempre queda sin cubrir, y el
síntoma es el peor posible — **verde**.

### §11.3 — Lo que el glob encontró que nadie había clasificado

`clear` y `render_report` (`clearing_solver.py`, upstream): **nadie las enumeraba y nadie había
decidido nada sobre ellas** desde TB.4. Clasificadas `SIN_SCOPE` con motivo escrito —
`render_report` es la cara de `clear` y el par simétrico de `to_clearing_input` (ST-d3.4): corre
**dentro** de la célula, y lo que sale pasa por `exportar_registros`, que sí lleva scope.

### §11.4 — HALLAZGO COLATERAL — **`render_report` imprime `€` hardcodeado. Es un defecto de D1, no de D4**

`clearing_solver.py:252` → `f"{sign}{a // 100}.{a % 100:02d} €"`. D1 (TB.2) convirtió
`_fmt_eur` en `_fmt_cents(cents, moneda)` **en el ledger** y el solver se quedó fuera:
`to_clearing_input` **ni siquiera le pasa `moneda`**. Hoy una célula VES emite una propuesta de
liquidación que dice **«725.74 €»** — en el país donde D1 existe precisamente porque el VES no
sostiene valor.

**NO se arregla en TB.8** (es D1, toca `clearing_solver` + `to_clearing_input` + posiblemente los
goldens, y sería scope creep en un nodo de gobernanza). **Señalado, y es decisión del humano:**
candidato a nodo correctivo, como TA.9 lo fue para Fase 1.

### §11.5 — Reconciliaciones aplicadas

1. **AC-d4.0 pedía `AAAA-MM-DD-sanciones-multisig.md`;** M9 produjo dos archivos firmados con
   otro nombre. **Manda el artefacto** (§3.1): glob, y se exigen los **dos** temas.
2. **AC-d4.7 contra mi propio código:** el pie de `describir_politica` metía en el render una
   advertencia sobre la SDN que **no está en la política**. **Manda el AC.** Y hay una razón
   mejor que la literal: una advertencia copiada en cada render se separa del documento con el
   tiempo, y entonces nadie sabe cuál manda. **El render APUNTA al documento, no lo duplica** —
   el mismo principio con el que el bundle apunta a las verificaciones fechadas.
3. **`P-d4.1` (2-de-3) contra la decisión del propietario (3-de-5):** no es contradicción. El
   helper valida **la fórmula**; el documento registra **la elección** (§3.3).
