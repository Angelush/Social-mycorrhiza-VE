"""TS3 ve_gate negative-control copy of B2B-VE ledger — DELIBERATELY BROKEN (silent gate bypass).

One surgical plant in two halves, marked "TS3 SILENT PLANT": bridge_paused loses its human
gate (removed from ratification_kinds; puente_pausar stops recording ratified_by). Never
imported outside the negative-control suite; B2B-VE/ is untouched.
"""
import json
import hashlib
import copy

# Shim de path para resolver `firewall.herencia` bajo carga standalone por ruta (los tests
# cargan cada módulo con spec_from_file_location, sin `src` en sys.path). Mismo patrón que el
# shim de `modo` en las capas C2C-VE (TA.4). `firewall.herencia` no importa el ledger (sin ciclos).
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from firewall.herencia import FORBIDDEN_KEYS, _key_matches_taxonomy, _value_has_identity_shape

MONEDAS = ("USD", "VES")

# Taxonomía FX — lista PRIVADA de D1, FUERA del bloque compartido (C-d9.3, patrón TA.6/TA.7).
# Meterla en el bloque rompería el md5 5d693ec y con él las siete copias.
# Es LINT SECUNDARIO, no el muro: el muro es que las obligaciones no llevan moneda (§2). H1 —
# «el muro real es el TIPO de salida y el cierre de esquema; la lista de claves es lint
# secundario». `params` es el único sitio de Fase 2 donde alguien podría intentar guardar una
# tasa «solo como referencia».
_TASA_KEYS = [
    'tasa_de_cambio', 'tipo_de_cambio', 'exchange_rate', 'fx', 'paralelo', 'bcv',
    # variantes pegadas (endurecidas por el reviewer en TA.6 — el mismo hueco existe aquí)
    'tasadecambio', 'tipodecambio', 'exchangerate',
]

# Símbolo por moneda. Un extracto que dice «€» en una célula USD es la misma mentira que
# decía el viejo `turnover_eur_cents` — pero esta la lee un humano que decide (C-d1.6).
_SIMBOLO = {"USD": "$", "VES": "Bs."}

def canonical(x) -> bytes:
    """Return the canonical JSON byte representation of x."""
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def _is_strict_int(x) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)

# ── D5 — `referencias_comerciales`: la ÚNICA superficie de forma libre de la Fase 2 ──────────
#
# Esquema cerrado de cada referencia. Las cinco claves están auditadas contra FORBIDDEN_KEYS
# por test (AC-d5.5), no por lectura: `veto`, `sancion` y `penalizacion` SIGUEN en la taxonomía
# heredada y siguen siendo vocabulario natural de este dominio (el comité vetea). La colisión
# está dormida solo mientras se elijan bien los nombres — por eso el campo se llama `avalista`
# y no `veto_del_comite`. Si algún día una clave necesaria colisiona: se renombra LA CLAVE,
# jamás la taxonomía (E-d5.2/N-d9.1 — es compartida con seis capas C2C-VE donde esas palabras sí
# nombran vigilancia).
_REF_KEYS_OBLIGATORIAS = ("avalista", "relacion_declarada", "antiguedad_meses")
_REF_KEYS_OPCIONALES = ("nota",)
_RELACIONES = ("proveedor", "cliente", "ambos")

# D6 — las cuatro resoluciones de una salida, y sus esquemas CERRADOS (lista blanca, patrón
# `allowed_keys`: la defensa más fuerte del ledger; ver AC-d9.6). El comité dice cuál es; el
# motor no la deduce del signo del saldo (C-d68.6/F-d68.7) — deducirla sería que el motor decide
# cómo se resuelve una salida, con consecuencias sobre un avalista que no está en la sala.
_RESOLUCIONES = {
    "simple": {"tipo"},
    "liquidacion_puente": {"tipo", "fondo"},
    "absorcion_avalista": {"tipo", "avalista"},
    "plan_de_pago": {"tipo", "plazo_meses"},
}

# Los estados desde los que un miembro puede seguir operando. Heredado literal de
# `record_obligation`: se reusa el conjunto en vez de escribir una lista paralela que envejezca
# aparte. `exited` queda fuera POR CONSTRUCCIÓN, sin código nuevo (ST-d68.4).
_ESTADOS_OPERATIVOS = {"active", "warned", "line_reduced"}


def _escanear_forma_libre(nodo) -> None:
    """Firewall heredado (D9) sobre estructura de forma libre: claves y valores, recursivo.

    VIVE AQUÍ Y NO EN `firewall.herencia` a propósito. La spec §4 nombra
    `_contains_forbidden_key`, pero D9 no lo heredó: el escáner recursivo vive FUERA del bloque
    `BEGIN…END` en las seis capas C2C-VE, y meterlo dentro cambiaría los 3023 bytes y el md5
    5d693ec de la séptima copia — que es exactamente lo que C-d9.1 prohíbe (cambian las siete o
    no cambia ninguna). Además AC-d9.2 asserta activamente que no está ahí. El bloque no se
    toca; se CONSUME su maquinaria, que es el patrón que `_TASA_KEYS` (D1) ya usa.

    Escanea las dos superficies porque el dossier entra por las dos:
      - CLAVES contra FORBIDDEN_KEYS (`puntuacion`, `scoreRelacional`, `lista_negra`…).
      - VALORES con forma de identidad, INCLUIDA la `nota` de texto libre (F-d5.3): «Pedro,
        V-12.345.678, lleva 3 años vendiéndonos» es el dossier entrando por el único campo que
        nadie valida.
    """
    if isinstance(nodo, dict):
        for clave, valor in nodo.items():
            if _key_matches_taxonomy(clave, FORBIDDEN_KEYS):
                raise ValueError("referencias_comerciales: firewall")
            _escanear_forma_libre(valor)
    elif isinstance(nodo, list):
        for item in nodo:
            _escanear_forma_libre(item)
    elif _value_has_identity_shape(nodo):
        raise ValueError("referencias_comerciales: firewall")


def _validar_referencias(members: dict, member_id: str, referencias) -> None:
    """Valida la lista de referencias del comité. FIREWALL PRIMERO, ESQUEMA CERRADO DESPUÉS.

    EL ORDEN NO ES ESTILO — decide si D9 es real o decorativo. `puntuacion` es a la vez clave
    prohibida por la taxonomía Y clave desconocida para el esquema cerrado. Si el esquema
    validase primero, AC-d5.3 pasaría en VERDE con el firewall completamente descableado — que
    es literalmente F-d5.4, el fallo que AC-d5.3 existe para detectar. El test certificaría la
    defensa que falta. Por eso el escáner corre sobre la estructura ENTERA antes de que el
    esquema mire una sola clave, y los mensajes son DISTINGUIBLES (`firewall` vs `clave
    desconocida`): sin esa distinción el AC no sabe quién mató al vector, y esa distinción ES
    AC-d9.5.

    Las dos defensas quedan vivas y cada una es alcanzable por separado. La lista blanca es la
    defensa fuerte (H1: el muro es el cierre de esquema; la taxonomía es lint secundario), pero
    aquí se usan las dos porque esta superficie es la que sí recibe forma libre.
    """
    if not isinstance(referencias, list):
        raise ValueError("referencias_comerciales")

    # 1) FIREWALL — sobre todo el árbol, antes que nada. Ver arriba.
    _escanear_forma_libre(referencias)

    # 2) ESQUEMA CERRADO — lista blanca, clave desconocida rechazada (C-d5.3).
    for ref in referencias:
        if not isinstance(ref, dict):
            raise ValueError("referencias_comerciales: referencia")
        for clave in ref:
            if clave not in _REF_KEYS_OBLIGATORIAS and clave not in _REF_KEYS_OPCIONALES:
                raise ValueError("referencias_comerciales: clave desconocida")
        for clave in _REF_KEYS_OBLIGATORIAS:
            if clave not in ref:
                raise ValueError("referencias_comerciales: clave ausente")

        avalista = ref["avalista"]
        if not isinstance(avalista, str) or not avalista:
            raise ValueError("referencias_comerciales: avalista")
        if avalista not in members:
            raise ValueError("referencias_comerciales: avalista")
        if avalista == member_id:
            # N-d5.4 — un aval de uno mismo no es información; admitirlo invita a inflar la
            # lista y convierte el conteo en el score que N-d5.1 prohíbe. Solo impide el
            # auto-aval TRIVIAL: un anillo de tres empresas avalándose mutuamente pasa todos
            # los checks y lo caza el comité, que conoce a la gente — o no lo caza nadie
            # (ST-d5.2, Señalado, no se fake-resuelve).
            raise ValueError("referencias_comerciales: auto-aval")

        if ref["relacion_declarada"] not in _RELACIONES:
            raise ValueError("referencias_comerciales: relacion_declarada")

        antiguedad = ref["antiguedad_meses"]
        if not _is_strict_int(antiguedad) or antiguedad < 0:
            raise ValueError("referencias_comerciales: antiguedad_meses")

        if "nota" in ref and not isinstance(ref["nota"], str):
            raise ValueError("referencias_comerciales: nota")


def _apply(state: dict | None, kind: str, payload: dict, ts: int) -> tuple[dict, dict]:
    if not _is_strict_int(ts):
        raise ValueError("ts")
    if state is None:
        if kind != "cell_created":
            raise ValueError("kind")
    else:
        if ts < state["last_ts"]:
            raise ValueError("ts")
        if state["params"]["paused"] and kind != "cell_resumed":
            raise ValueError("paused")

    state_copy = copy.deepcopy(state) if state is not None else None
    payload_copy = copy.deepcopy(payload)

    # D6 — `member_exited` entra en la puerta que YA existe. M8 no pide construir una puerta:
    # pide no construir una segunda. Una helper que mutara el estado sin pasar por aquí se
    # saltaría de una vez `ratified_by`, la monotonía de `ts`, el check de `paused`, el
    # encadenado de hashes y los post-asserts L1/L2 (F-d68.1).
    # TS3 SILENT PLANT (ve_gate), 1 of 2: "bridge_paused" removed from the gate list. The
    # ratification check LIVES in this set (M8) — removed from it, _apply never asks; replay
    # re-applies with this same broken copy, so the chain re-verifies green; the resulting
    # state (puente_pausado=True) is byte-identical to a legally produced one. SURGICAL: every
    # other gated kind stays gated (member_updated without ratified_by still raises).
    ratification_kinds = {"cell_created", "member_added", "member_updated", "clearing_applied", "cell_paused", "cell_resumed", "member_exited", "bridge_resumed"}
    if kind in ratification_kinds:
        ratified_by = payload_copy.get("ratified_by")
        if not isinstance(ratified_by, str) or not ratified_by:
            raise ValueError("ratified_by")

    if kind == "cell_created":
        if state_copy is not None:
            raise ValueError("state")
        cell_id = payload_copy.get("cell_id")
        if not isinstance(cell_id, str) or not cell_id:
            raise ValueError("cell_id")
        params = payload_copy.get("params")
        if not isinstance(params, dict):
            raise ValueError("params")
        for key in ["neg_line_bp", "pos_line_bp", "velocity_window_s", "velocity_max_cents"]:
            if key not in params or not _is_strict_int(params[key]):
                raise ValueError(key)
        if params["neg_line_bp"] < 0:
            raise ValueError("neg_line_bp")
        if params["pos_line_bp"] < 0:
            raise ValueError("pos_line_bp")
        if params["velocity_window_s"] <= 0:
            raise ValueError("velocity_window_s")
        if params["velocity_max_cents"] <= 0:
            raise ValueError("velocity_max_cents")

        # D1 — la unidad de cuenta de la célula. Sin default implícito: una célula que no dice en qué
        # unidad de cuenta lleva sus saldos no tiene invariante L1 que verificar.
        moneda = params.get("moneda")
        if moneda not in MONEDAS:
            raise ValueError("moneda")

        # D1 — `expira_en_dias` es BICONDICIONAL con VES. Obligatorio en VES porque un saldo
        # VES sin expiración es un pasivo inflacionario (H4) y el motor estaría mintiendo
        # sobre lo que guarda. Prohibido en USD: una célula USD que declara expiración está
        # confundida sobre qué es.
        expira = params.get("expira_en_dias")
        if moneda == "VES":
            if not _is_strict_int(expira) or expira <= 0:
                raise ValueError("expira_en_dias")
        else:
            if expira is not None:
                raise ValueError("expira_en_dias")

        # D3 — la sal del seudónimo. Obligatoria en TODA célula (el matraqueo no depende de la
        # moneda). Vive en `params` y no como argumento de `member_statement` porque una sal por
        # llamada la elige el llamador: dos llamadas honestas darían dos seudónimos del mismo
        # miembro, el enlace entre anclas (D2) se rompería y el árbitro no podría hacer su
        # trabajo. La sal es propiedad de la CÉLULA, y su estabilidad es lo que la hace útil.
        # Sin sal, sha256(cell_id+member_id) se revierte por fuerza bruta sobre los 30-500
        # nombres de la célula: un seudónimo reversible es identidad con un paso extra (C-d3.3).
        sal = params.get("sal_seudonimo")
        if not isinstance(sal, str) or not sal:
            raise ValueError("sal_seudonimo")

        # D1 — lint secundario FX (§5). No es el muro; el muro es la geometría.
        for key in params:
            if _key_matches_taxonomy(key, _TASA_KEYS):
                raise ValueError("tasa")

        new_state = {
            "cell_id": cell_id,
            "params": {
                "neg_line_bp": params["neg_line_bp"],
                "pos_line_bp": params["pos_line_bp"],
                "velocity_window_s": params["velocity_window_s"],
                "velocity_max_cents": params["velocity_max_cents"],
                "moneda": moneda,
                "expira_en_dias": expira,
                "sal_seudonimo": sal,
                "paused": False,
                # D8 — estado derivado, no configuración: como `paused`, se fija aquí y se
                # ignora lo que traiga el llamador. Una célula que arranca con el puente
                # pausado no es una cosa. Por eso la clave NO viaja en el payload de
                # `cell_created` y el `head_hash` del golden es invariante bajo D8.
                "puente_pausado": False
            },
            "members": {},
            "obligations": {},
            "recent_recorded": [],
            "obligation_ids_seen": [],
            "applied_proposals": [],
            "seq": 1,
            "last_ts": ts,
            "head_hash": ""
        }
    else:
        new_state = state_copy

    if kind == "member_added":
        member = payload_copy.get("member")
        if not isinstance(member, dict):
            raise ValueError("member")
        member_id = member.get("id")
        if not isinstance(member_id, str) or not member_id:
            raise ValueError("member_id")
        if member_id in new_state["members"]:
            raise ValueError(member_id)
        turnover = member.get("turnover_cents")
        if not _is_strict_int(turnover) or turnover < 0:
            raise ValueError("turnover_cents")
        credit_min = member.get("credit_min_cents")
        credit_max = member.get("credit_max_cents")
        if not _is_strict_int(credit_min) or not _is_strict_int(credit_max):
            raise ValueError("credit_min_cents")
        if not (credit_min <= 0 <= credit_max):
            raise ValueError("credit_min_cents")

        new_state["members"][member_id] = {
            "turnover_cents": turnover,
            "credit_min_cents": credit_min,
            "credit_max_cents": credit_max,
            "status": "active",
            "balance_cents": 0
        }

        # D5 — el veteo relacional del comité. Se valida DESPUÉS de insertar al miembro para
        # que el auto-aval falle como auto-aval y no como «avalista inexistente»: el mensaje es
        # lo que el comité lee cuando el motor le dice que no.
        if "referencias_comerciales" in payload_copy:
            refs = payload_copy["referencias_comerciales"]
            _validar_referencias(new_state["members"], member_id, refs)
            if refs:
                new_state["members"][member_id]["referencias_comerciales"] = refs

    elif kind == "member_updated":
        member_id = payload_copy.get("member_id")
        changes = payload_copy.get("changes")
        if not isinstance(member_id, str) or not member_id:
            raise ValueError("member_id")
        if member_id not in new_state["members"]:
            raise ValueError(member_id)
        if not isinstance(changes, dict):
            raise ValueError("changes")
        allowed_keys = {"credit_min_cents", "credit_max_cents", "status"}
        if not set(changes.keys()).issubset(allowed_keys):
            raise ValueError("changes")
        m = new_state["members"][member_id]
        new_min = changes.get("credit_min_cents", m["credit_min_cents"])
        new_max = changes.get("credit_max_cents", m["credit_max_cents"])
        new_status = changes.get("status", m["status"])
        if not _is_strict_int(new_min) or not _is_strict_int(new_max):
            raise ValueError("credit")
        if new_min > 0 or new_max < 0 or new_min > new_max:
            raise ValueError("credit")
        if not (new_min <= m["balance_cents"] <= new_max):
            raise ValueError(member_id)
        if "status" in changes:
            curr_status = m["status"]
            # D6 — `exited` es TERMINAL: no se sale de él. Hoy `ladder.index("exited")` ya
            # lanzaría, pero POR ACCIDENTE (es el `.index` de una lista, no una decisión) y con
            # un mensaje que ningún `match=` fija. Un ValueError accidental es indistinguible de
            # uno intencionado justo el día que alguien reordene el código.
            #
            # Solo se bloquea el cambio de ESTADO, no el de líneas: la spec dice «no puede llegar
            # a él ni salir de él», y eso habla de estados. Prohibir ajustar las líneas de un
            # `exited` sería alcance que nadie pidió, y L2 las sigue guardando igual.
            if curr_status == "exited":
                raise ValueError("exited")
            # …y no se LLEGA a `exited` por aquí: no está en la lista. `exited` queda fuera de la
            # escalera SANCIONADORA a propósito (C-d68.3) — `expelled` es su último peldaño, y
            # emigrar no es una sanción. Confundirlos deja en una cadena append-only la marca de
            # que a quien se mudó a Bogotá lo expulsaron, y esa marca viaja (U1/F-d68.3).
            if new_status not in ["active", "warned", "line_reduced", "suspended", "expelled"]:
                raise ValueError("status")
            if new_status != curr_status:
                ladder = ["active", "warned", "line_reduced", "suspended", "expelled"]
                idx_curr = ladder.index(curr_status)
                idx_new = ladder.index(new_status)
                if idx_new > idx_curr:
                    if idx_new != idx_curr + 1:
                        raise ValueError("status")
        m["credit_min_cents"] = new_min
        m["credit_max_cents"] = new_max
        m["status"] = new_status

        # D5 — `allowed_keys` NO SE TOCA (AC-d9.6: los esquemas cerrados heredados ni se
        # escanean ni se relajan; la lista blanca es la defensa más fuerte que hay). Las
        # referencias entran por su propio parámetro, hermano de `ratified_by`.
        #
        # Clave ausente = «no las toques»; `[]` = «vacíala». Sin esa distinción, toda
        # actualización de línea de crédito borraría el veteo EN SILENCIO.
        if "referencias_comerciales" in payload_copy:
            refs = payload_copy["referencias_comerciales"]
            _validar_referencias(new_state["members"], member_id, refs)
            if refs:
                m["referencias_comerciales"] = refs
            else:
                # «Sin referencias» tiene UNA sola representación: la clave ausente. Guardar
                # `[]` haría que un miembro creado sin referencias y uno vaciado a propósito
                # difirieran en el estado sin diferir en el hecho — una distinción sin
                # significado es una discrepancia esperando a pasar. El EVENTO sí conserva el
                # acto de vaciar (`[]` en el payload, en la cadena): el evento es el acto, el
                # estado es el hecho.
                m.pop("referencias_comerciales", None)

    elif kind == "member_exited":
        # D6 — un miembro emigra a mitad de ciclo (§6.5: éxodo continuo). El upstream no tiene
        # este caso porque España no lo tiene.
        member_id = payload_copy.get("member_id")
        resolucion = payload_copy.get("resolucion")
        if not isinstance(member_id, str) or not member_id:
            raise ValueError("member_id")
        if member_id not in new_state["members"]:
            raise ValueError(member_id)
        if not isinstance(resolucion, dict):
            raise ValueError("resolucion")
        m = new_state["members"][member_id]
        # No reversible y no repetible (N-d68.5): mueve valor y cierra una cuenta. Se corrige
        # con asientos nuevos, como los asientos — no borrando la historia de una cadena
        # append-only.
        if m["status"] == "exited":
            raise ValueError("exited")
        tipo = resolucion.get("tipo")
        if tipo not in _RESOLUCIONES:
            raise ValueError("resolucion")
        if set(resolucion.keys()) != _RESOLUCIONES[tipo]:
            raise ValueError("resolucion")

        saldo = m["balance_cents"]
        if tipo == "simple":
            # `simple` es la salida limpia, y limpia significa saldo cero. Si aceptara un saldo
            # distinto de 0, la única forma de conservar L1 sería no tocarlo — y eso YA es
            # `plan_de_pago`, con otro nombre y sin plazo. Dos nombres para un hecho es la
            # discrepancia esperando a pasar.
            if saldo != 0:
                raise ValueError("resolucion")
        elif tipo == "plan_de_pago":
            plazo = resolucion["plazo_meses"]
            if not _is_strict_int(plazo) or plazo <= 0:
                raise ValueError("plazo_meses")
            # Y NO SE TOCA EL SALDO (F-d68.8). El plan de pago es un acuerdo FUERA del motor;
            # «provisionarlo» o «reservarlo» aquí sería inventar un asiento. El saldo negativo
            # sigue ahí, en un miembro `exited`, porque esa es la verdad.
        else:
            # `liquidacion_puente` y `absorcion_avalista` son la MISMA operación de estado —
            # el saldo del saliente pasa íntegro a otro miembro — y difieren solo en quién es la
            # contraparte y por qué. Una sola regla: la contraparte HEREDA el saldo, con su
            # signo. Así L1 se conserva por construcción en vez de por dos casos que hay que
            # acordarse de cuadrar.
            clave = "fondo" if tipo == "liquidacion_puente" else "avalista"
            # D8 — LO ÚNICO que hace la pausa del puente: rechazar esta resolución. El check
            # vive aquí, junto a la resolución que rechaza, y NO en el preámbulo de `_apply`
            # (donde vive el de `paused`): ahí arriba tendría que preguntar de qué kind viene, y
            # esa pregunta es la puerta de entrada de F-d68.4 — un `if` de más y la pausa se
            # come el ledger entero. `puente_pausado` ≠ `paused` (C-d68.4): el crédito interno
            # sobrevive a la muerte del puente (I-VE7), que es la parte robusta de la red.
            if tipo == "liquidacion_puente" and new_state["params"]["puente_pausado"]:
                raise ValueError("puente_pausado")
            contraparte_id = resolucion[clave]
            if not isinstance(contraparte_id, str) or contraparte_id not in new_state["members"]:
                raise ValueError(clave)
            if contraparte_id == member_id:
                raise ValueError(clave)
            contraparte = new_state["members"][contraparte_id]
            # Una contraparte `suspended`/`expelled`/`exited` no absorbe nada: sería contagio
            # hacia alguien que ya está en la escalera, y el impago es contagioso (U2).
            if contraparte["status"] not in _ESTADOS_OPERATIVOS:
                raise ValueError(clave)
            contraparte["balance_cents"] += saldo
            m["balance_cents"] = 0
            # Que el saldo QUEPA en las líneas de la contraparte (L2) lo verifica el post-assert
            # heredado, que además lanza `ValueError(<id de la contraparte>)` — nombra a quien
            # no cabe, que es lo que AC-d68.3/AC-d68.6 piden. Flag/reject, jamás clamp (M6): un
            # avalista empujado fuera de sus líneas «porque alguien se fue» es contagio, y el
            # fondo sin línea ES la verdad (no da abasto) — se capitaliza, no se recorta el
            # check (ST-d68.1).

        m["status"] = "exited"

    elif kind == "obligation_recorded":
        ob = payload_copy.get("obligation")
        if not isinstance(ob, dict):
            raise ValueError("obligation")
        ob_id = ob.get("id")
        debtor = ob.get("debtor")
        creditor = ob.get("creditor")
        amount = ob.get("amount_cents")
        if not isinstance(ob_id, str) or not ob_id:
            raise ValueError("id")
        if ob_id in new_state["obligation_ids_seen"]:
            raise ValueError(ob_id)
        if debtor not in new_state["members"]:
            raise ValueError("debtor")
        if creditor not in new_state["members"]:
            raise ValueError("creditor")
        if debtor == creditor:
            raise ValueError("debtor")
        d_mem = new_state["members"][debtor]
        c_mem = new_state["members"][creditor]
        # D6 — el literal heredado pasa a `_ESTADOS_OPERATIVOS` (mismo conjunto, byte a byte:
        # cero cambio de comportamiento). Es lo que hace que `exited` quede excluido de recibir
        # obligaciones nuevas POR CONSTRUCCIÓN, sin código nuevo, y que no exista una lista
        # paralela que envejezca aparte (ST-d68.4). `settle_obligation` no mira el status: un
        # `exited` SÍ paga lo suyo — «paying what you owe is always legal» (N-d68.4).
        if d_mem["status"] not in _ESTADOS_OPERATIVOS:
            raise ValueError(debtor)
        if c_mem["status"] not in _ESTADOS_OPERATIVOS:
            raise ValueError(creditor)
        if not _is_strict_int(amount) or amount <= 0:
            raise ValueError("amount_cents")
        window = new_state["params"]["velocity_window_s"]
        max_velocity = new_state["params"]["velocity_max_cents"]
        pruned = [r for r in new_state["recent_recorded"] if r["ts"] > ts - window]
        debtor_recent_sum = sum(r["amount_cents"] for r in pruned if r["debtor"] == debtor)
        if debtor_recent_sum + amount > max_velocity:
            raise ValueError(debtor)
        pruned.append({"ts": ts, "debtor": debtor, "amount_cents": amount})
        new_state["recent_recorded"] = pruned

        def get_projected(m_id):
            m_bal = new_state["members"][m_id]["balance_cents"]
            owed_to = sum(o["amount_cents"] for o in new_state["obligations"].values() if o["creditor"] == m_id)
            owed_by = sum(o["amount_cents"] for o in new_state["obligations"].values() if o["debtor"] == m_id)
            return m_bal + owed_to - owed_by

        proj_debtor = get_projected(debtor) - amount
        proj_creditor = get_projected(creditor) + amount
        if proj_debtor < d_mem["credit_min_cents"]:
            raise ValueError(debtor)
        if proj_creditor > c_mem["credit_max_cents"]:
            raise ValueError(creditor)
        new_state["obligations"][ob_id] = {
            "debtor": debtor,
            "creditor": creditor,
            "amount_cents": amount,
            "ts": ts
        }
        new_state["obligation_ids_seen"].append(ob_id)

    elif kind == "clearing_applied":
        proposal = payload_copy.get("proposal")
        proposal_hash = payload_copy.get("proposal_hash")
        if not isinstance(proposal, dict):
            raise ValueError("proposal")
        if proposal.get("cell_id") != new_state["cell_id"]:
            raise ValueError(proposal.get("cell_id"))
        # D1 (TB.8b) — el evento guarda la propuesta VERBATIM y un auditor la lee: una
        # propuesta ratificada que dijera «Bs.» en una célula USD sería una mentira con
        # firma. Es la puerta M8 haciendo cumplir D1, no un check de conveniencia.
        if proposal.get("moneda") != new_state["params"]["moneda"]:
            raise ValueError("proposal_moneda")
        computed_hash = hashlib.sha256(canonical(proposal)).hexdigest()
        if proposal_hash != computed_hash:
            raise ValueError("proposal_hash")
        if proposal_hash in new_state["applied_proposals"]:
            raise ValueError("proposal_hash")
        settlements = proposal.get("settlements")
        if not isinstance(settlements, list):
            raise ValueError("settlements")
        aggregated = {}
        for s in settlements:
            if not isinstance(s, dict):
                raise ValueError("settlement")
            ob_id = s.get("obligation_id")
            reduce_by = s.get("reduce_by_cents")
            if not isinstance(ob_id, str) or not ob_id:
                raise ValueError("obligation_id")
            if not _is_strict_int(reduce_by) or reduce_by <= 0:
                raise ValueError("reduce_by_cents")
            aggregated[ob_id] = aggregated.get(ob_id, 0) + reduce_by
        member_net = {}
        for ob_id, reduce_amount in aggregated.items():
            if ob_id not in new_state["obligations"]:
                raise ValueError(ob_id)
            ob = new_state["obligations"][ob_id]
            if reduce_amount > ob["amount_cents"]:
                raise ValueError(ob_id)
            debtor = ob["debtor"]
            creditor = ob["creditor"]
            member_net[debtor] = member_net.get(debtor, 0) - reduce_amount
            member_net[creditor] = member_net.get(creditor, 0) + reduce_amount
        for m, net in member_net.items():
            if net != 0:
                raise ValueError(m)
        for ob_id, reduce_amount in aggregated.items():
            ob = new_state["obligations"][ob_id]
            ob["amount_cents"] -= reduce_amount
            if ob["amount_cents"] == 0:
                del new_state["obligations"][ob_id]
        new_state["applied_proposals"].append(proposal_hash)

    elif kind == "obligation_settled":
        ob_id = payload_copy.get("obligation_id")
        amount = payload_copy.get("amount_cents")
        if not isinstance(ob_id, str) or not ob_id:
            raise ValueError("obligation_id")
        if ob_id not in new_state["obligations"]:
            raise ValueError(ob_id)
        if not _is_strict_int(amount) or amount <= 0:
            raise ValueError("amount_cents")
        ob = new_state["obligations"][ob_id]
        if amount > ob["amount_cents"]:
            raise ValueError("amount_cents")
        debtor = ob["debtor"]
        creditor = ob["creditor"]
        d_mem = new_state["members"][debtor]
        c_mem = new_state["members"][creditor]
        d_mem["balance_cents"] -= amount
        c_mem["balance_cents"] += amount
        if d_mem["balance_cents"] < d_mem["credit_min_cents"]:
            raise ValueError(debtor)
        if c_mem["balance_cents"] > c_mem["credit_max_cents"]:
            raise ValueError(creditor)
        ob["amount_cents"] -= amount
        if ob["amount_cents"] == 0:
            del new_state["obligations"][ob_id]

    elif kind == "cell_paused":
        if new_state["params"]["paused"]:
            raise ValueError("paused")
        new_state["params"]["paused"] = True

    elif kind == "cell_resumed":
        if not new_state["params"]["paused"]:
            raise ValueError("not_paused")
        new_state["params"]["paused"] = False

    # D8 — calcadas de `cell_paused`/`cell_resumed` (P-d68.1) pero SIN reutilizar su campo. Los
    # mensajes son distinguibles de `paused`/`not_paused` a propósito: es lo que permite a un
    # `match=` probar que se rechazó por el puente y no por el cortafuegos (lección de AC-d9.5).
    elif kind == "bridge_paused":
        if new_state["params"]["puente_pausado"]:
            raise ValueError("puente_pausado")
        new_state["params"]["puente_pausado"] = True

    elif kind == "bridge_resumed":
        if not new_state["params"]["puente_pausado"]:
            raise ValueError("puente_no_pausado")
        new_state["params"]["puente_pausado"] = False

    if state_copy is None:
        seq = 1
        prev_hash = ""
    else:
        seq = state_copy["seq"] + 1
        prev_hash = state_copy["head_hash"]

    event = {
        "seq": seq,
        "ts": ts,
        "kind": kind,
        "payload": payload_copy,
        "prev_hash": prev_hash
    }
    event_hash = hashlib.sha256(canonical(event)).hexdigest()
    event["hash"] = event_hash

    new_state["seq"] = seq
    new_state["last_ts"] = ts
    new_state["head_hash"] = event_hash

    bal_sum = sum(m["balance_cents"] for m in new_state["members"].values())
    if bal_sum != 0:
        raise ValueError("balance_sum")

    for m_id, m in new_state["members"].items():
        if not (m["credit_min_cents"] <= m["balance_cents"] <= m["credit_max_cents"]):
            raise ValueError(m_id)

    # state is the caller's untouched input; state_copy aliases new_state by
    # this point, so the previous seq must come from the original.
    prev_seq = 0 if state is None else state["seq"]
    if new_state["seq"] != prev_seq + 1:
        raise ValueError("seq")

    if new_state["last_ts"] != ts:
        raise ValueError("last_ts")
    if new_state["head_hash"] != event_hash:
        raise ValueError("head_hash")

    return new_state, event

def create_cell(cell_id: str, params: dict, ratified_by: str, ts: int) -> tuple[dict, dict]:
    """Bootstrap the mutual-credit ledger cell."""
    payload = {
        "cell_id": cell_id,
        "params": params,
        "ratified_by": ratified_by
    }
    return _apply(None, "cell_created", payload, ts)

def add_member(state: dict, member: dict, ratified_by: str, ts: int, *,
               referencias_comerciales: list | None = None) -> tuple[dict, dict]:
    """Add a new member with optional initial credit lines.

    D5 — `referencias_comerciales` es el input del veteo del comité, y va como PARÁMETRO
    HERMANO de `ratified_by`, jamás como clave dentro de `member`. No es estilo: `member` se
    reconstruye clave a clave más abajo (`resolved_member`), así que unas referencias metidas
    ahí **se perderían sin un solo error** — firewall nunca invocado, referencias nunca
    guardadas, suite verde. Es F-d5.4 servido en bandeja. La spec §2 ya lo dice al llamarlas
    «parte del payload que ya lleva `ratified_by`».

    Keyword-only y OPCIONAL (P-d5.1): el veteo ES la reunión del comité, no el campo. Exigirlo
    haría que el comité invente referencias para dar de alta a quien conoce de toda la vida —
    el campo pasaría de informar el juicio a SUSTITUIRLO con teatro (F-d5.6). Aquí sí hay
    default y en `scope` no, y la diferencia es real: «no hay referencias» es un hecho del
    mundo; un `scope` ausente era una pregunta sin responder.
    """
    if not isinstance(member, dict):
        raise ValueError("member")
    member_id = member.get("id")
    if not isinstance(member_id, str) or not member_id:
        raise ValueError("id")
    turnover = member.get("turnover_cents")
    if not _is_strict_int(turnover) or turnover < 0:
        raise ValueError("turnover_cents")
    neg_line_bp = state["params"]["neg_line_bp"]
    pos_line_bp = state["params"]["pos_line_bp"]
    credit_min = member.get("credit_min_cents")
    if credit_min is None:
        credit_min = -(turnover * neg_line_bp) // 10000
    elif not _is_strict_int(credit_min):
        raise ValueError("credit_min_cents")
    credit_max = member.get("credit_max_cents")
    if credit_max is None:
        credit_max = (turnover * pos_line_bp) // 10000
    elif not _is_strict_int(credit_max):
        raise ValueError("credit_max_cents")
    resolved_member = {
        "id": member_id,
        "turnover_cents": turnover,
        "credit_min_cents": credit_min,
        "credit_max_cents": credit_max
    }
    payload = {
        "member": resolved_member,
        "ratified_by": ratified_by
    }
    # Ausente, no `None` (patrón `ancla` de TB.7): una clave con `None` invita a rellenarla, y
    # además `cell_created` no se toca → los goldens NO cambian por construcción. Si la suite
    # pidiera regenerar un golden, algo se coló: se investiga, no se regenera.
    if referencias_comerciales is not None:
        payload["referencias_comerciales"] = referencias_comerciales
    return _apply(state, "member_added", payload, ts)

def update_member(state: dict, member_id: str, changes: dict, ratified_by: str, ts: int, *,
                  referencias_comerciales: list | None = None) -> tuple[dict, dict]:
    """Apply administrative changes to credit limits or status.

    D5 — mismo parámetro hermano que en `add_member`, y por una razón adicional: `allowed_keys`
    de `changes` es `{credit_min_cents, credit_max_cents, status}` con `issubset`, así que unas
    referencias metidas en `changes` darían `ValueError("changes")`. La lista blanca heredada
    NO se relaja para hacerles sitio (AC-d9.6): es la defensa más fuerte del ledger.

    `None` = «no las toques» · `[]` = «vacíala». Sin esa distinción, cada ajuste de línea de
    crédito borraría el veteo en silencio.
    """
    payload = {
        "member_id": member_id,
        "changes": changes,
        "ratified_by": ratified_by
    }
    if referencias_comerciales is not None:
        payload["referencias_comerciales"] = referencias_comerciales
    return _apply(state, "member_updated", payload, ts)

def salida_con_saldo(state: dict, member_id: str, resolucion: dict, ratified_by: str,
                     ts: int) -> tuple[dict, dict]:
    """D6 — registrar la salida de un miembro que emigra, con su saldo resuelto.

    `resolucion` la decide el COMITÉ, no el motor (C-d68.6): `{"tipo": "simple"}` ·
    `{"tipo": "liquidacion_puente", "fondo": mid}` · `{"tipo": "absorcion_avalista",
    "avalista": mid}` · `{"tipo": "plan_de_pago", "plazo_meses": int}`.

    El miembro pasa a `exited`, que es TERMINAL y está FUERA de la escalera sancionadora:
    emigrar no es una sanción (C-d68.3).

    Esta función NO liquida: no toca USDT, ni rieles, ni direcciones, ni claves (N-d68.2/N9).
    `liquidacion_puente` **registra** que se liquidó — «el núcleo solo registra la obligación
    saldada» (§3.2). Que el USDT se haya movido de verdad es fe en el comité: no hay oráculo, y
    fingir uno sería peor (N10).

    Toda la validación vive en `_apply`, que es la vía del `replay`: una validación aquí no
    protegería a un evento fabricado a mano y metido en el stream.
    """
    payload = {
        "member_id": member_id,
        "resolucion": resolucion,
        "ratified_by": ratified_by
    }
    return _apply(state, "member_exited", payload, ts)

def record_obligation(state: dict, obligation: dict, ts: int) -> tuple[dict, dict]:
    """Record a trade credit obligation between two members."""
    payload = {
        "obligation": obligation
    }
    return _apply(state, "obligation_recorded", payload, ts)

def apply_clearing(state: dict, proposal: dict, ratified_by: str, ts: int) -> tuple[dict, dict]:
    """Apply a balanced cycle-clearing proposal."""
    proposal_hash = hashlib.sha256(canonical(proposal)).hexdigest()
    payload = {
        "proposal": proposal,
        "proposal_hash": proposal_hash,
        "ratified_by": ratified_by
    }
    return _apply(state, "clearing_applied", payload, ts)

def settle_obligation(state: dict, obligation_id: str, amount_cents: int, ts: int) -> tuple[dict, dict]:
    """Bilateral settlement of an open obligation."""
    payload = {
        "obligation_id": obligation_id,
        "amount_cents": amount_cents
    }
    return _apply(state, "obligation_settled", payload, ts)

def pause_cell(state: dict, ratified_by: str, ts: int) -> tuple[dict, dict]:
    """Pause the cell, rejecting all subsequent mutating ops."""
    payload = {
        "ratified_by": ratified_by
    }
    return _apply(state, "cell_paused", payload, ts)

def resume_cell(state: dict, ratified_by: str, ts: int) -> tuple[dict, dict]:
    """Resume the cell to allow regular operations."""
    payload = {
        "ratified_by": ratified_by
    }
    return _apply(state, "cell_resumed", payload, ts)

def puente_pausar(state: dict, ratified_by: str, ts: int) -> tuple[dict, dict]:
    """D8 — pausar el puente de liquidación externa. Reversible (`puente_reanudar`).

    Lo ÚNICO que hace: rechazar `salida_con_saldo` con resolución `liquidacion_puente`. Todo lo
    demás sigue corriendo — obligaciones, compensación, saldos, altas, anclajes y las otras tres
    resoluciones de salida. *Porque* I-VE7: la red local sobrevive a la muerte del puente. El
    crédito interno es la parte robusta; el puente es la frágil. Una pausa que detuviera el
    crédito interno acoplaría la supervivencia del sistema a su pieza más frágil, y fallaría
    exactamente en el escenario para el que se diseñó (F-d68.4).

    Es un DIAL, no un interruptor de un solo uso: la lista de designaciones se mueve en los dos
    sentidos (`docs/verificaciones/2026-07-15-sanciones.md`, hallazgo 4), y el alivio vigente va
    por licencia general REVOCABLE (hallazgo 2) — de ahí que esto exista.

    El motor NO criba contra la lista SDN y no debe: quién está designado lo sabe el comité, con
    datos que el motor no tiene (N8/N9/I3). Esta función registra una decisión humana; no la toma.
    """
    # TS3 SILENT PLANT (ve_gate), 2 of 2: the payload no longer records who ratified.
    payload = {}
    return _apply(state, "bridge_paused", payload, ts)

def puente_reanudar(state: dict, ratified_by: str, ts: int) -> tuple[dict, dict]:
    """D8 — reanudar el puente de liquidación externa. Inversa de `puente_pausar`."""
    payload = {
        "ratified_by": ratified_by
    }
    return _apply(state, "bridge_resumed", payload, ts)

def to_clearing_input(state: dict) -> dict:
    """Generate state slice for the clearing engine."""
    state_cp = copy.deepcopy(state)
    members_list = []
    for m_id, m in state_cp["members"].items():
        members_list.append({
            "id": m_id,
            "turnover_cents": m["turnover_cents"],
            "credit_min_cents": m["credit_min_cents"],
            "credit_max_cents": m["credit_max_cents"]
        })
    members_list.sort(key=lambda x: x["id"])
    obs_list = []
    for ob_id, ob in state_cp["obligations"].items():
        obs_list.append({
            "id": ob_id,
            "debtor": ob["debtor"],
            "creditor": ob["creditor"],
            "amount_cents": ob["amount_cents"]
        })
    obs_list.sort(key=lambda x: x["id"])
    return {
        "cell_id": state_cp["cell_id"],
        # D1 (TB.8b) — la célula es mono-moneda y este dict ES la foto de la célula: la
        # moneda viaja con el input para que el solver no tenga que adivinarla (C-d1.6).
        "moneda": state_cp["params"]["moneda"],
        "members": members_list,
        "obligations": obs_list
    }

SCOPES = ("comite_credito", "miembro", "publico")


def _seudonimo(state: dict, member_id: str) -> str:
    """Compromiso estable con el miembro, NO su identidad (D3 §3).

    Reusa `canonical` (la serialización del motor) en vez de inventar un formato: dos formatos
    de serialización es una discrepancia esperando a pasar.
    """
    sal = state["params"]["sal_seudonimo"]
    return hashlib.sha256(canonical([state["cell_id"], member_id, sal])).hexdigest()[:16]


def member_statement(state: dict, member_id: str, scope: str, solicitante: str | None = None) -> dict:
    """Extracto del miembro, acotado por `scope` (D3).

    `scope` es POSICIONAL OBLIGATORIO, sin default: un default es la configuración que nadie
    revisa, y `comite_credito` por default dejaría el delta instalado y desactivado a la vez
    (F-d3.1) — con la suite verde certificando que existe. Quien no dice desde dónde mira, no
    mira (C-d3.1; M10 en espíritu: rechazar, no recortar).

    El scope es un CONTRATO, no un guardia: el motor no autentica (spec-ledger §5) y un
    llamador puede mentir y pedir `comite_credito`. No lo impedimos y no fingimos que sí
    (N-d3.4) — una garantía falsa es peor que ninguna, porque nadie pone la de verdad encima.
    """
    if scope not in SCOPES:
        raise ValueError("scope")
    if scope == "miembro" and solicitante != member_id:
        # Sin esto, `miembro` es `publico` con otro nombre (C-d3.2). Cubre también
        # `solicitante=None`: omitirlo no puede ser la vía a ver el extracto ajeno.
        raise ValueError("solicitante")
    if member_id not in state["members"]:
        raise ValueError(member_id)

    if scope == "publico":
        # Conjunto de claves CERRADO, no una lista de nombres prohibidos: el muro es el TIPO de
        # salida (H1). Ni saldo, ni líneas, ni proyectada, ni owed_* (N-d3.1: un libro público
        # de saldos es un mapa de matraqueo — quién tiene superávit = lista de objetivos).
        # Ni `status`: la escalera de sanciones sobre un seudónimo estable sigue siendo una
        # marca (N-d3.2). Un `salud_crediticia` futuro rompe AC-d3.3 sin que nadie lo previera.
        return {"seudonimo": _seudonimo(state, member_id)}

    m = state["members"][member_id]
    owed_to = sum(o["amount_cents"] for o in state["obligations"].values() if o["creditor"] == member_id)
    owed_by = sum(o["amount_cents"] for o in state["obligations"].values() if o["debtor"] == member_id)
    projected = m["balance_cents"] + owed_to - owed_by
    salida = {
        "member_id": member_id,
        "status": m["status"],
        "balance_cents": m["balance_cents"],
        "credit_min_cents": m["credit_min_cents"],
        "credit_max_cents": m["credit_max_cents"],
        "owed_by_cents": owed_by,
        "owed_to_cents": owed_to,
        "projected_cents": projected
    }

    # D5 — las referencias SOLO para el comité (C-d5.5). La rama no-`publico` servía a `miembro`
    # y a `comite_credito` a la vez; se parte aquí, y es criterio, no mecánica:
    #
    # EL MIEMBRO NO VE QUIÉN LE AVALA. «Quién avala a quién» es el mapa de la red (F-d5.7, N7):
    # público es la lista de a quién presionar para llegar a quién. Y dárselo al PROPIO avalado
    # convierte el aval en una posición negociable —«sé que me avalaste»— y por tanto
    # presionable. El comité las lee porque decide; el miembro no decide.
    #
    # Se devuelven TAL CUAL se guardaron, sin derivar nada de ellas (C-d5.1): ni `n_avales`, ni
    # `antiguedad_media`, ni «confianza». Cualquier función que las tome y devuelva un número ES
    # un score, se llame como se llame (H1) — y AC-8 lo fija por tipo de salida y por AST, no
    # por una lista de nombres prohibidos. Que el comité cuente avalistas y ordene mentalmente
    # es SU JUICIO y es el diseño (ST-d5.1): la línea es que el SISTEMA no compute.
    #
    # `deepcopy` porque una vista no le da al llamador un asa sobre el estado.
    if scope == "comite_credito" and "referencias_comerciales" in m:
        salida["referencias_comerciales"] = copy.deepcopy(m["referencias_comerciales"])
    return salida

def _fmt_cents(cents: int, moneda: str) -> str:
    """Formatea un importe con el símbolo de la unidad de cuenta de la CÉLULA (C-d1.6).

    Antes era `_fmt_eur` con «€» hardcodeado. El símbolo se deriva de params["moneda"]: un
    extracto es lo que lee el humano que decide, y decidir sobre un número con la etiqueta
    equivocada es peor que no verlo.
    """
    sign = "-" if cents < 0 else ""
    a = abs(cents)
    return f"{sign}{a//100}.{a%100:02d} {_SIMBOLO[moneda]}"

def render_statement(state: dict, member_id: str, scope: str, solicitante: str | None = None) -> str:
    """Render the member statement as markdown. Mismo scope, misma regla (D3 §5.3).

    Delega la decisión en `member_statement`: dos implementaciones del scope es una que se
    olvida de endurecer. Bajo `publico` el render es el seudónimo y nada más — un extracto
    renderizado con importes es exactamente lo que N-d3.1 prohíbe, por muy markdown que sea.
    """
    stmt = member_statement(state, member_id, scope, solicitante)
    if scope == "publico":
        return f"# Statement — {stmt['seudonimo']}\n"
    cell_id = state["cell_id"]
    moneda = state["params"]["moneda"]
    def _f(c):
        return _fmt_cents(c, moneda)
    lines = [
        f"# Statement — {member_id} @ {cell_id}",
        f"- Status: {stmt['status']}",
        f"- Balance: {_f(stmt['balance_cents'])}",
        f"- Credit Limit: {_f(stmt['credit_min_cents'])} to {_f(stmt['credit_max_cents'])}",
        f"- Owed By Member: {_f(stmt['owed_by_cents'])}",
        f"- Owed To Member: {_f(stmt['owed_to_cents'])}",
        f"- Projected Balance: {_f(stmt['projected_cents'])}"
    ]
    return "\n".join(lines) + "\n"

def cell_metrics(state: dict) -> dict:
    """Compute aggregated metrics for a cell."""
    members_cnt = len(state["members"])
    open_obs_cnt = len(state["obligations"])
    gross_open = sum(ob["amount_cents"] for ob in state["obligations"].values())
    sum_balances = sum(m["balance_cents"] for m in state["members"].values())
    return {
        "cell_id": state["cell_id"],
        "members": members_cnt,
        "open_obligations": open_obs_cnt,
        "gross_open_cents": gross_open,
        "sum_balances_cents": sum_balances,
        # D1 — expuestos para que el comité y los exportes (D7) los vean. `expira_en_dias` es
        # None en células USD: la expiración no existe donde la unidad de cuenta guarda valor.
        "moneda": state["params"]["moneda"],
        "expira_en_dias": state["params"]["expira_en_dias"],
        "paused": state["params"]["paused"],
        # D8 — el comité tiene que poder ver si el puente está parado sin leer el stream. En TB.6
        # exponerlo habría sido instalar el delta y desactivarlo a la vez (F-d3.1); aquí el
        # mecanismo existe.
        "puente_pausado": state["params"]["puente_pausado"],
        "seq": state["seq"]
    }

def replay(events: list) -> dict:
    """Recompute the cell state from event sequence."""
    if not events:
        raise ValueError("events")
    state = None
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("event")
        kind = event.get("kind")
        payload = event.get("payload")
        ts = event.get("ts")
        state, computed = _apply(state, kind, payload, ts)
        if event.get("seq") != computed["seq"]:
            raise ValueError("seq")
        if event.get("prev_hash") != computed["prev_hash"]:
            raise ValueError("prev_hash")
        if event.get("hash") != computed["hash"]:
            raise ValueError("hash")
    return state

def verify_chain(events: list) -> None:
    """Verify hash linkage and integrity of the log."""
    for i, event in enumerate(events):
        if not isinstance(event, dict):
            raise ValueError("event")
        seq = event.get("seq")
        ts = event.get("ts")
        kind = event.get("kind")
        payload = event.get("payload")
        prev_hash = event.get("prev_hash")
        h = event.get("hash")
        if not _is_strict_int(seq) or seq != i + 1:
            raise ValueError("seq")
        if not _is_strict_int(ts):
            raise ValueError("ts")
        if not isinstance(kind, str) or not kind:
            raise ValueError("kind")
        if not isinstance(payload, dict):
            raise ValueError("payload")
        if not isinstance(prev_hash, str):
            raise ValueError("prev_hash")
        if i == 0:
            if prev_hash != "":
                raise ValueError("prev_hash")
        else:
            if prev_hash != events[i-1].get("hash"):
                raise ValueError("prev_hash")
        core = {
            "seq": seq,
            "ts": ts,
            "kind": kind,
            "payload": payload,
            "prev_hash": prev_hash
        }
        computed_hash = hashlib.sha256(canonical(core)).hexdigest()
        if h != computed_hash:
            raise ValueError("hash")
