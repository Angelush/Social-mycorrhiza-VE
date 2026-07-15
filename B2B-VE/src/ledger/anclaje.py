"""Anclaje (D2, fork VE) — compromiso criptográfico de un período sobre la cadena que el
ledger YA encadena.

La cadena de hashes no se construye aquí: `_apply` ya encadena, `verify_chain` ya valida el
enlace completo, `replay` ya reconstruye byte a byte y `canonical` ya es determinista.
`spec-ledger.md` §5 upstream listaba «no on-chain anchoring» como límite y añadía que «the hash
chain is its future attachment point». Este módulo es ese futuro, y solo la mitad que faltaba:
una función PURA que emite el hash raíz de un período. Encima, no dentro.

POR QUÉ deja de ser opcional: en España la cadena era auditoría ante un regulador. En Venezuela
no hay tribunales que ejecuten contratos (§2.11) — la disputa la resuelve un comité y un
árbitro gremial, y necesitan evidencia que nadie pueda reescribir. El anclaje sustituye
PARCIALMENTE al enforcement judicial.

POR QUÉ MERKLE Y NO sha256 DE LA LISTA: un hash de la lista solo prueba «este conjunto exacto
existía»; para probarle a un árbitro que UN evento estaba dentro habría que entregarle todos
los demás — y el libro entero es el mapa de matraqueo (N7/I-VE3). Merkle prueba una hoja con
~log2(n) hermanos y nada más. Es §3.3 (lo anclado va con seudónimos/compromisos, jamás
identidades ni montos en claro) cruzado con §2.11 (el árbitro comprueba hechos).

EL MOTOR NO PUBLICA (N5). `anclar` emite; publicar es del llamador. Un motor con red se cae en
los apagones (§2.9) y se vuelve un punto capturable. La frontera es que el motor no tiene red,
y esa frontera es lo que lo hace correr en un apagón.

Señalados (N10 — no fake-resueltos):
  - La raíz sola NO prueba CUÁNDO (ST-d2.1). Merkle prueba pertenencia a un conjunto, no fecha.
    La marca temporal la da la publicación, que está fuera. El motor produce el insumo de lo
    que §2.11 necesita, no la propiedad.
  - El anclaje no impide reescribir: permite DETECTARLO (ST-d2.2). Una célula puede llevar dos
    libros y anclar el conveniente; contra eso el mecanismo es social (réplica entre nodos de
    la célula, §3.3), no criptográfico.

Spec: B2B/workflows/micorriza-ve/d2-anclaje/{spec,constraints,failure-model}.md
      B2B/workflows/micorriza-ve/d2-anclaje/DESIGN-TB3.md
Acceptance: AC-7 (global), AC-d2.1..d2.8

Provenance: Opus en TB.3 (sin fan-out). stdlib only.
"""
import hashlib

# Shim de path para carga standalone por ruta (los tests usan spec_from_file_location, sin
# `src` en sys.path). Mismo patrón que el shim de `firewall.herencia` en el ledger (TA.4).
# El ledger NO importa este módulo: la dependencia es de un solo sentido, sin ciclos.
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from ledger.mutual_credit_ledger import verify_chain, _is_strict_int


def _es_hash(h) -> bool:
    """Un hash de la cadena: 64 hex. Se valida porque `bytes.fromhex` de una cadena rara
    lanza ValueError con un mensaje que no dice nada al lector."""
    if not isinstance(h, str) or len(h) != 64:
        return False
    try:
        bytes.fromhex(h)
    except ValueError:
        return False
    return True


def _par(izq: str, der: str) -> str:
    """Nodo interno = sha256 de los BYTES concatenados, no del hex.

    El hex son 64 caracteres ASCII: hashearlo sería hashear una representación en vez del
    valor. Es la convención de toda implementación Merkle seria, y cambiarla parte la
    verificación independiente del árbitro.
    """
    return hashlib.sha256(bytes.fromhex(izq) + bytes.fromhex(der)).hexdigest()


def _raiz_merkle(hojas: list) -> str:
    """Raíz del árbol de Merkle sobre `hojas` (hex), en el orden en que vienen.

    NIVEL IMPAR: EL HUÉRFANO SE PROMOCIONA TAL CUAL. JAMÁS SE DUPLICA.
    Duplicar la última hoja (`if impar: hojas.append(hojas[-1])`, el patrón de Bitcoin clásico
    que un ejecutor copia por reflejo) es CVE-2012-2459: hace que dos conjuntos de eventos
    DISTINTOS produzcan la MISMA raíz. Sería destruir la evidencia inviolable en el delta cuyo
    único propósito es que lo sea (C-d2.4/F-d2.1). AC-d2.4 construye el par colisionante.

    Privada de nombre, pero AC-d2.1 y AC-d2.4 la testean DIRECTAMENTE a propósito: el conjunto
    [e1,e2,e3,e3] que hay que comparar no puede entrar por `anclar` — `verify_chain` lo mata en
    la puerta. Sin este punto de entrada, el AC que más importa del delta sería inexpresable.
    """
    if not hojas:
        raise ValueError("hojas")
    for h in hojas:
        if not _es_hash(h):
            raise ValueError("hoja")
    nivel = list(hojas)
    while len(nivel) > 1:
        siguiente = [_par(nivel[i], nivel[i + 1]) for i in range(0, len(nivel) - 1, 2)]
        if len(nivel) % 2 == 1:
            siguiente.append(nivel[-1])  # promoción, no duplicación
        nivel = siguiente
    return nivel[0]


def _rango_valido(events: list, desde_seq: int, hasta_seq: int) -> None:
    if not _is_strict_int(desde_seq) or not _is_strict_int(hasta_seq):
        raise ValueError("rango")
    if desde_seq > hasta_seq:
        raise ValueError("rango")
    seqs = {e.get("seq") for e in events}
    if desde_seq not in seqs or hasta_seq not in seqs:
        # Rango fuera de los seq existentes. No se ancla un período que el libro no cubre:
        # la raíz saldría igual y afirmaría sobre eventos que nadie entregó (AC-d2.6).
        raise ValueError("rango")


def _hojas(events: list, desde_seq: int, hasta_seq: int) -> list:
    """Hojas = event['hash'] del período, EN ORDEN DE `seq` ASCENDENTE.

    Jamás ordenadas por hash «para canonicalizar»: eso rompe la correspondencia con la cadena y
    vuelve ambigua la prueba de inclusión (F-d2.5). El orden ya es canónico porque
    `verify_chain` exige `seq == i+1`.
    """
    hojas = [e["hash"] for e in events if desde_seq <= e["seq"] <= hasta_seq]
    if not hojas:
        # Período vacío. Una raíz que no compromete a nada da falsa sensación de evidencia:
        # publicarla es afirmar algo sin contenido (C-d2.6).
        raise ValueError("periodo_vacio")
    return hojas


def anclar(events: list, desde_seq: int, hasta_seq: int) -> dict:
    """Emite el compromiso criptográfico del período [desde_seq, hasta_seq].

    PURA: sin I/O, sin red, sin reloj, sin aleatoriedad (C-d2.1). Publicar la raíz es del
    llamador (N5) — y publicar SÍ es un acto consecuente e irreversible, por eso está fuera.

    NO es una operación de valor: es read/emit, radio de explosión ninguno, no toca el estado,
    no emite evento y NO lleva `ratified_by` (N-d2.2). Esto no contradice M8/I-VE5 («toda
    operación de valor nueva pasa por la puerta»): `anclar` no mueve valor, y no añade ningún
    `kind` a `ratification_kinds` porque no añade ningún kind. Darle una puerta sería fricción
    que además le sugiere al siguiente lector que mueve valor (F-d2.6).

    Recibe la lista COMPLETA de eventos y el rango como enteros, nunca una sublista
    pre-recortada: `verify_chain` verifica lo que recibe, así que sobre una sublista la
    verificación sería del fragmento que el llamador eligió (ST-d2.4).
    """
    # verify_chain PRIMERO: anclar una cadena rota publica un compromiso sobre evidencia ya
    # inválida, y el sello le presta al fraude la credibilidad que le faltaba. Es PEOR que no
    # anclar (C-d2.2/F-d2.3). Se propaga su ValueError tal cual.
    verify_chain(events)
    _rango_valido(events, desde_seq, hasta_seq)
    hojas = _hojas(events, desde_seq, hasta_seq)
    return {
        "desde_seq": desde_seq,
        "hasta_seq": hasta_seq,
        "n_eventos": len(hojas),
        "raiz": _raiz_merkle(hojas),
        "primer_hash": hojas[0],
        "ultimo_hash": hojas[-1],
    }


def prueba_de_inclusion(events: list, desde_seq: int, hasta_seq: int, seq: int) -> list:
    """Camino de hashes hermanos que prueba que el evento `seq` está bajo la raíz del período.

    -> [{"lado": "izq"|"der", "hash": hex}, ...]  ('lado' = de qué lado va el HERMANO)

    Tamaño ~log2(n): es lo que le permite al árbitro comprobar UN hecho sin recibir el libro
    entero (N7). Con n == 1 la prueba es vacía y la raíz es la propia hoja.
    """
    verify_chain(events)
    _rango_valido(events, desde_seq, hasta_seq)
    if not _is_strict_int(seq) or not (desde_seq <= seq <= hasta_seq):
        raise ValueError("seq")
    hojas = _hojas(events, desde_seq, hasta_seq)
    i = seq - desde_seq  # verify_chain garantiza seq == i+1 → el período es contiguo
    prueba = []
    nivel = hojas
    while len(nivel) > 1:
        siguiente = [_par(nivel[j], nivel[j + 1]) for j in range(0, len(nivel) - 1, 2)]
        impar = len(nivel) % 2 == 1
        if impar:
            siguiente.append(nivel[-1])
        if impar and i == len(nivel) - 1:
            # El huérfano promocionado no tiene hermano en este nivel: sube sin aportar paso.
            i = len(siguiente) - 1
        else:
            if i % 2 == 0:
                prueba.append({"lado": "der", "hash": nivel[i + 1]})
            else:
                prueba.append({"lado": "izq", "hash": nivel[i - 1]})
            i = i // 2
        nivel = siguiente
    return prueba


def verificar_inclusion(hoja_hash: str, prueba: list, raiz: str) -> bool:
    """Verificación independiente: NO recibe los eventos. Solo hoja, prueba y raíz.

    Es la función que corre el ÁRBITRO, y por N7 el árbitro no debe recibir el ledger. Si
    necesitara los eventos, el delta no habría resuelto nada (C-d2.5/F-d2.4) — la firma cómoda
    `verificar_inclusion(events, seq, raiz)` es exactamente el fallo.

    Devuelve bool, no lanza ante una prueba manipulada: para el llamador, «esta prueba no
    sostiene la raíz» es una respuesta, no un error del programa.
    """
    if not _es_hash(hoja_hash) or not _es_hash(raiz) or not isinstance(prueba, list):
        return False
    acumulado = hoja_hash
    for paso in prueba:
        if not isinstance(paso, dict):
            return False
        hermano = paso.get("hash")
        lado = paso.get("lado")
        if not _es_hash(hermano) or lado not in ("izq", "der"):
            return False
        acumulado = _par(hermano, acumulado) if lado == "izq" else _par(acumulado, hermano)
    return acumulado == raiz
