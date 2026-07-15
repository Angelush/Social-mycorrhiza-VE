# Acceptance — D5: referencias comerciales

> `AC-8` global (`tasks.md` TB.5: N2); `AC-d5*` locales. Ejecutables por máquina.

## AC-8 (D5) — Ningún escalar de persona (**el que importa**)

Dos comprobaciones, ninguna basada en una lista de nombres prohibidos:

1. **Por TIPO de salida:** el conjunto de claves de toda salida que incluya
   `referencias_comerciales` es cerrado y contiene la lista **tal cual se guardó** — ningún
   campo derivado. Pass/fail: igualdad de conjuntos + igualdad profunda con el input.
2. **Por ausencia de derivación (AST):** ninguna función de `B2B-VE/src/` toma
   `referencias_comerciales` (o un campo suyo) y devuelve un `int`/`float` que no estuviera
   literalmente en el input. Pass/fail: análisis AST — cero funciones.

*Porque:* H1 — el muro es el TIPO de salida y el cierre de esquema; la lista de claves es lint
secundario. Un `indice_relacional` futuro rompe (1) sin que nadie lo hubiera previsto; un
`sum(r["antiguedad_meses"] …)` rompe (2).

## AC-d5.1 — El motor no deriva ningún número

Concreción de AC-8(2), con los nombres que un ejecutor elegiría: no existe
`confianza`, `fiabilidad`, `indice_relacional`, `antiguedad_media`, `n_avales`,
`salud_crediticia`, `linea_sugerida` ni `percentil_*` en ninguna salida ni como función
pública. Pass/fail: introspección del módulo + recorrido de salidas.

*Porque:* F-d5.1/F-d5.2. Esta lista **no es el test** (lo es AC-8): es el canario que hace
legible el fallo cuando ocurre.

## AC-d5.2 — Esquema cerrado

| Input | Resultado |
|---|---|
| `avalista` inexistente en `state["members"]` | `ValueError` |
| `avalista` == el solicitante (auto-aval) | `ValueError` |
| `relacion_declarada` fuera del enum | `ValueError` |
| `antiguedad_meses` negativo / no-int / `True` | `ValueError` |
| clave desconocida (`"puntaje_interno": 5`) | `ValueError` |
| lista válida | `add_member` completa; queda en el payload del evento |
| campo ausente | `add_member` completa (P-d5.1: opcional) |

Pass/fail: raise + creación.

## AC-d5.3 — El firewall se aplica de verdad, end-to-end (fija F-d9.5/F-d5.4)

Sobre `add_member(...)` **real**, no sobre el escáner aislado:

| Vector | Resultado |
|---|---|
| clave `puntuacion` dentro de una referencia | `ValueError` |
| clave `scoreRelacional` (camelCase → token `score`) | `ValueError` |
| clave `lista_negra` (bigrama) | `ValueError` |
| `nota: "Pedro V-12.345.678 lleva 3 años"` (cédula en texto libre) | `ValueError` |
| `nota: "RIF J-12345678-9, buen pagador"` | `ValueError` |
| `nota: "Buen proveedor desde 2023"` | **aceptada** |
| `avalista: "bancoDeTiempo"` → tokens `banco,de,tiempo` | **aceptada** (R2: no colisiona con `ban`) |

Pass/fail: raise / aceptación. *Porque:* C-d5.2. Los vectores salen de R2 (Fase 1), no se
inventan aquí (ST-d5.4).

> **El caso positivo es obligatorio:** un firewall que rechaza todo pasa cualquier test que
> solo compruebe rechazos (F-d9.1). `"Buen proveedor desde 2023"` y `bancoDeTiempo` son lo que
> distingue un firewall con alcance de uno que mató al paciente.

## AC-d5.4 — Las referencias no son públicas

`member_statement(..., scope="publico")` no las contiene. `exportar_registros` (D7) público
tampoco. Pass/fail: ausencia de clave. *Porque:* C-d5.5 — «quién avala a quién» es el mapa de
la red (F-d5.7).

## AC-d5.5 — Las claves de D5 no colisionan (fija F-d5.5)

`_key_matches_taxonomy(k, FORBIDDEN_KEYS) is False` para `referencias_comerciales`,
`avalista`, `relacion_declarada`, `antiguedad_meses`, `nota`. Pass/fail: todos `False`.
*Porque:* C-d5.4. Es la instancia local de AC-d9.4 y el centinela de la colisión dormida
`veto`/`sancion`.

## AC-d5.6 — Las referencias quedan en la cadena

Tras `add_member` con referencias, `replay(events)` reconstruye el estado byte a byte y
`verify_chain` pasa; las referencias están en el payload del evento y son anclables (D2).
Pass/fail: igualdad byte + sin raise. *Porque:* §5.4 — el veteo es auditable, y sin tribunales
la evidencia de por qué se admitió a alguien importa.

## AC-d5.7 — Datos sintéticos (N8)

Todo vector con forma de identidad en fixtures y goldens es sintético y está marcado como tal.
Pass/fail: revisión + los valores no corresponden a cédulas/RIF emitidos reales.
