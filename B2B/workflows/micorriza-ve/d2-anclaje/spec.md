# Spec — D2: `anclar()` sobre la cadena existente

> Nodo TB.3. Ancla: anexo §8.2, §3.3, §2.11; N5, I-VE5, M8.

## 1. Hallazgo de TB.0: la cadena YA existe

`spec-ledger.md` §5 lista «no on-chain anchoring» como límite de alcance y añade: «the hash
chain is its future attachment point». **Ese futuro es este delta, y la mitad del trabajo está
hecha.**

Verificado en el código (TB.0): `_apply` ya encadena
(`event["prev_hash"] = state_copy["head_hash"]`, `hash = sha256(canonical({seq,ts,kind,payload,prev_hash}))`),
`verify_chain(events)` ya valida el enlace completo, `replay(events)` ya reconstruye byte a byte
y `canonical()` ya es determinista (`sort_keys`, separadores fijos, `ensure_ascii=False`).

**D2 no construye una cadena. Añade una función pura que emite el hash raíz de un período**
sobre la cadena que ya está testeada (AC-L4).

## 2. Por qué el anclaje deja de ser opcional

En España la cadena de hashes era auditoría ante un regulador. En Venezuela **no hay
tribunales que ejecuten contratos** (§2.11): la resolución de disputas es social (comité +
árbitro gremial) y necesita evidencia que nadie pueda reescribir. El anclaje **sustituye
parcialmente al enforcement judicial**.

Eso cambia el requisito, no solo la prioridad: la evidencia debe servirle a un **árbitro
humano** que necesita comprobar un hecho concreto («¿existía esta obligación el 3 de marzo?»)
**sin que se le entregue el libro entero** — porque el libro entero es el mapa de matraqueo
(N7/I-VE3).

## 3. La decisión: árbol de Merkle, no hash de la lista

`anclar()` emite la **raíz de un árbol de Merkle** sobre los hashes de los eventos del
período, no un `sha256` de la lista concatenada.

*Porque:* un hash de la lista solo prueba «este conjunto exacto de eventos existía». Para
probarle a un árbitro que **un** evento estaba dentro, habría que enseñarle **todos** los
demás. Merkle permite una **prueba de inclusión** de tamaño logarítmico: se revela un evento y
~log₂(n) hashes hermanos, y nada más. Es exactamente la propiedad que pide §3.3 («cualquier
dato anclado públicamente va con seudónimos/compromisos, nunca identidades ni montos en
claro») cruzada con §2.11 (el árbitro necesita comprobar hechos).

Sin esa propiedad, el anclaje solo sirve para detectar que **algo** cambió — útil, pero no es
lo que la ausencia de tribunales exige.

## 4. Contrato

```python
def anclar(events: list, desde_seq: int, hasta_seq: int) -> dict:
    """Emite el compromiso criptográfico del período [desde_seq, hasta_seq].
    PURA: sin I/O, sin reloj, sin red. Publicar la raíz es del llamador."""
    # -> {"desde_seq", "hasta_seq", "n_eventos", "raiz": hex,
    #     "primer_hash": hex, "ultimo_hash": hex}

def prueba_de_inclusion(events: list, desde_seq: int, hasta_seq: int, seq: int) -> list:
    """Camino de hashes hermanos que prueba que el evento `seq` está bajo la raíz.
    -> [{"lado": "izq"|"der", "hash": hex}, ...]"""

def verificar_inclusion(hoja_hash: str, prueba: list, raiz: str) -> bool:
    """Verificación independiente: NO recibe los eventos. Un árbitro puede correr
    esto con la hoja, la prueba y la raíz publicada, y nada más."""
```

**Construcción del árbol (fijada, porque el determinismo lo exige):**
- Hojas = `event["hash"]` de los eventos con `desde_seq <= seq <= hasta_seq`, **en orden de
  `seq` ascendente** (el orden de la cadena, no ordenado por hash).
- Nodo interno = `sha256(bytes.fromhex(izq) + bytes.fromhex(der))`.
- Nivel impar: **se promociona el último nodo sin duplicarlo** (`n` impar → el huérfano sube
  al nivel siguiente tal cual). *Porque:* duplicar la última hoja es la vulnerabilidad CVE de
  Bitcoin (dos árboles distintos con la misma raíz); promocionar no la tiene.
- `n_eventos == 1` → la raíz **es** la hoja.
- `n_eventos == 0` → `ValueError`. No se ancla la nada: una raíz de período vacío es un
  compromiso que no compromete a nada, y publicarla da falsa sensación de evidencia.

**Precondición:** `anclar` llama a `verify_chain(events)` primero y propaga el `ValueError`.
*Porque:* anclar una cadena rota publicaría un compromiso sobre evidencia ya inválida — y el
compromiso le daría credibilidad. Es peor que no anclar.

## 5. `anclar` NO es una operación de valor

`anclar` es **read/emit** (`spec.md` global, semántica de operaciones): pura, radio de
explosión ninguno, no toca el estado, no emite evento, **no requiere `ratified_by`**.

Esto **no** contradice M8/I-VE5 («toda operación de valor nueva pasa por la puerta»): `anclar`
no mueve valor. No añade un `kind` a `ratification_kinds` porque no añade ningún `kind`.

*Y por eso mismo:* publicar la raíz **sí** es un acto consecuente (irreversible, público) — y
por eso está **fuera del motor** (N5). El llamador publica; el motor emite. La frontera es que
el motor no tiene red.

## 6. Qué NO hace D2

- **No publica.** Ni a cadena, ni a ningún sitio. Sin red, sin I/O (N5).
- **No firma.** Ningún manejo de claves (N9/I-VE4).
- **No hay smart contract de clearing on-chain.** Gas + complejidad + apagones, sin beneficio
  que lo justifique (§3.3, N5). La cadena pública recibe un hash, nada más.
- **No cambia la cadena existente.** Ni el formato de evento, ni `verify_chain`, ni `replay`.
  D2 es puramente aditivo → cero regresión esperada.
