# Acceptance — D7: exportes

> `AC-7` global (`tasks.md` TB.7: seudonimización si público); `AC-d7*` locales.

## AC-7 (D7) — Seudonimización en público

`exportar_registros(..., scope="publico")` no contiene ningún `member_id` real ni ningún
importe individual, en **ninguno** de los dos formatos. Pass/fail: ausencia por búsqueda de
subcadena sobre la salida cruda.

*Cubierto además, automáticamente, por AC-7 de D3*, que enumera las funciones públicas por
introspección — `exportar_registros` cae dentro sin que nadie tenga que acordarse (F-d7.5).

## AC-d7.1 — El scope es el de D3

`exportar_registros` acepta los mismos tres scopes con las mismas reglas: `miembro` exige
`solicitante == member_id`; scope ausente o desconocido → `ValueError`. Pass/fail: raise.
*Porque:* C-d7.3 — no se inventa un control nuevo.

## AC-d7.2 — Pura, sin I/O

Devuelve `str`. No acepta ruta ni descriptor. Con `open` y `socket.socket` del módulo
parcheados para lanzar, completa. No muta `state` ni `events` (comparación profunda).
Pass/fail: tipo + completa + igualdad. *Porque:* C-d7.1 (F-d7.4).

## AC-d7.3 — Enteros, sin float (fija F-d7.2)

Ningún importe de la salida contiene `.` ni `,` decimal; todos son enteros de centavos. En
JSON: `isinstance(v, int)` para todo campo de importe. En CSV: cada celda de importe casa
`^-?\d+$`. Pass/fail: type walk + regex. *Porque:* C-d7.6/M4.

## AC-d7.4 — No declara nada (fija F-d7.1)

La salida no contiene: `igtf`, `iva`, `gravable`, `retencion`, `seniat`, `impuesto`,
`base_imponible`, ni ningún campo derivado que clasifique fiscalmente. Ninguna función de
`B2B-VE/src/` calcula un porcentaje sobre un importe.

Pass/fail: ausencia + AST (cero funciones que multipliquen un importe por una constante
fraccionaria). *Porque:* N-d7.1 — declarar por el miembro bajo un marco ambiguo le crea el
problema (§5).

## AC-d7.5 — La moneda va una vez (fija F-d7.3)

- La moneda aparece en la **cabecera**, exactamente una vez.
- Ninguna línea/fila tiene columna `moneda`.
- La salida no contiene ninguna clave de `_TASA_KEYS` (D1) ni ningún total en otra moneda.

Pass/fail: conteo + ausencia. *Porque:* C-d7.5 — el formato también puede hacer representable
el FX.

## AC-d7.6 — Derivado de los eventos, no del estado (fija F-d7.7)

Un exporte del período `[t0, t1]` sobre una cadena que continúa hasta `t9` refleja **los saldos
al final de t1**, no los actuales. Pass/fail: comparación contra el estado reconstruido por
`replay(events[:hasta])`. *Porque:* C-d7.2 — un exporte de marzo con saldos de julio cuadra
consigo mismo y es falso.

## AC-d7.7 — `raiz_ancla` solo si hay ancla (fija ST-d7.2)

Período sin ancla publicada → el campo `raiz_ancla` **se omite**; no se rellena con una raíz
calculada al vuelo. Pass/fail: ausencia de clave. *Porque:* una raíz no publicada no prueba
nada ante un tercero, y ponerla da falsa sensación de prueba.

## AC-d7.8 — El exporte es verificable

Para cada línea del exporte de un miembro, `hash_evento` corresponde a un evento real y
`verify_chain` lo valida. Pass/fail: cada hash existe en el stream. *Porque:* P-d7.1 — sin
tribunales, el exporte vale lo que valga su verificabilidad.

## AC-d7.9 — CSV sin inyección (fija ST-d7.4)

Un `member_id` o `referencia` que empiece por `=`, `+`, `-` o `@` sale escapado en el CSV.
Pass/fail: la celda no empieza por el carácter crudo. *Porque:* los `member_id` los eligen
humanos y el CSV lo abre Excel.

## AC-d7.10 — Los dos formatos coinciden

`json` y `csv` del mismo `(miembro, periodo, scope)` contienen exactamente los mismos hechos.
Pass/fail: parsear ambos → estructuras equivalentes. *Porque:* dos formatos que discrepan
convierten «cuál es la verdad» en una pregunta, justo en el artefacto que un miembro le
presenta a un tercero.
