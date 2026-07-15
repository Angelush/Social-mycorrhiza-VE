# Acceptance — D2: anclaje

> `AC-7` es el global del grafo (`tasks.md` TB.3: «anclar determinista»); los `AC-d2*` son
> locales. Todos ejecutables por máquina.

## AC-7 — `anclar` es determinista

Dos llamadas con los mismos eventos y el mismo rango → dicts byte-idénticos
(`canonical(a) == canonical(b)`). Y desde dos procesos distintos (`PYTHONHASHSEED` distinto) →
misma raíz. Pass/fail: igualdad de bytes.

*Porque:* I4/L4 — el clearing y la evidencia corren en cualquier nodo; dos raíces distintas
para el mismo período parten la célula en dos verdades.

## AC-d2.1 — La raíz depende del orden de `seq`, no del hash

Un conjunto de eventos cuyo orden por `seq` **difiere** del orden por hash produce una raíz
distinta a la que produciría el orden por hash. Pass/fail: desigualdad. *Porque:* F-d2.5 —
canonicalizar por hash rompe la correspondencia con la cadena.

## AC-d2.2 — `anclar` es pura

- No muta `events` (comparación profunda antes/después).
- No devuelve estado ni evento; `state` no aparece en la firma.
- Sin red ni disco: el test corre con `socket.socket` parcheado para lanzar y con el `open`
  del módulo parcheado para lanzar. Pass/fail: completa sin tocar ninguno.

*Porque:* C-d2.1/N5 — un motor con red no sobrevive a un apagón y sí a una captura.

## AC-d2.3 — La prueba de inclusión no necesita el libro

`verificar_inclusion(hoja_hash, prueba, raiz) -> True` **sin que `events` esté disponible** (el
test lo borra del ámbito antes de verificar). Una prueba manipulada (cualquier hash o `lado`
alterado) → `False`. Pass/fail: booleano.

*Porque:* C-d2.5 — es la función del árbitro, y por N7 el árbitro no recibe el ledger. Si el
test necesita los eventos para verificar, el delta no resolvió nada (F-d2.4).

## AC-d2.4 — Sin colisión por hoja impar (**el AC que importa**)

Con `n` impar, se construye explícitamente el conjunto que la **duplicación** volvería
colisionante: eventos `[e1, e2, e3]` frente a `[e1, e2, e3, e3]`. Las dos raíces deben ser
**distintas**.

Pass/fail: desigualdad. *Porque:* F-d2.1 — es el fallo que convierte la evidencia inviolable
en violable, y el patrón que un ejecutor copiará de Bitcoin por defecto. Este test no comprueba
la implementación contra sí misma: construye el par que la implementación incorrecta colapsa
(ST-d2.3).

## AC-d2.5 — Cadena rota no se ancla

Alterar cualquier campo de cualquier evento (`payload`, `ts`, `prev_hash`, `hash`) → `anclar`
lanza `ValueError` y **no devuelve raíz**. Pass/fail: raise. *Porque:* C-d2.2 — un ancla sobre
evidencia inválida le presta credibilidad al fraude (F-d2.3).

## AC-d2.6 — Casos de borde del rango

| Caso | Resultado |
|---|---|
| `n_eventos == 1` | raíz **es** la hoja |
| `n_eventos == 0` (rango vacío) | `ValueError` |
| `desde_seq > hasta_seq` | `ValueError` |
| rango fuera de los `seq` existentes | `ValueError` |
| `events` es una sublista pre-recortada | `ValueError` vía `verify_chain` (`seq != i+1`) |

Pass/fail: raise / igualdad. *Porque:* C-d2.6 + ST-d2.4.

## AC-d2.7 — Propiedad: toda hoja del período es probable (hypothesis)

Para cualquier cadena de `n ∈ [1, 50]` eventos y cualquier rango válido: **para todo** `seq` en
el rango, `verificar_inclusion(hash(seq), prueba_de_inclusion(..., seq), raiz) == True`; y para
todo `seq` **fuera** del rango, no existe prueba válida contra esa raíz.

Pass/fail: property test. *Porque:* P3 upstream (property-based para los invariantes) y porque
una prueba que funcione solo para las hojas de índice par es un bug clásico de Merkle que un
test de ejemplo no caza.

## AC-d2.8 — Cero regresión

D2 es puramente aditivo: no toca formato de evento, `verify_chain`, `replay` ni `canonical`.
`cd B2B-VE && pytest -q` → los 125 + 3 skipped siguen igual, más los nuevos. Pass/fail: salida
pytest real citada (M2).
