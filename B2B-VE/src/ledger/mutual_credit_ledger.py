"""Mutual-credit ledger (mono-moneda por célula, no chain) — event-sourced system-of-record
for one cell.

Members, credit lines, zero-sum balances, open obligations, hash-chained audit
log. Pure functional core: op(state, ...) -> (new_state, event); no I/O, no
clock, no randomness (time is an integer input). Hosts the one-way door:
apply_clearing commits a Capa-1 solver proposal only with explicit human
ratification (M5 / brief invariant 2), verifying per-member conservation
independently. Every violation raises ValueError; never repairs (E2/N4).

D1 (fork VE) — DEROGA el «EUR» del título upstream de spec-ledger.md. La unidad de cuenta es
el USD; el euro era la respuesta a MiCA, que en Venezuela no aplica. Un crédito NO es un dólar
ni un USDT: es compensación de obligaciones a la par, con el dólar como unidad de cuenta. El
motor jamás asume 1 USDT = 1 USD.

`moneda` ∈ {USD, VES} es parámetro de la CÉLULA, jamás de la obligación:
  - L1 (`sum(balance_cents) == 0`) ES la definición de crédito mutuo, y solo significa algo
    dentro de una unidad de cuenta: sumar centavos USD con centavos VES no da cero, da basura.
  - Por eso una obligación mixta es IRREPRESENTABLE, no rechazada: no hay campo donde
    escribirla (I1 — forma irrepresentable antes que flag). Y el FX no tiene dónde escribirse,
    porque una tasa solo hace falta para relacionar dos monedas dentro de un mismo ámbito.
  - La «pista VES» del anexo §3.1 es una célula VES APARTE («contabilidad separada»).
  - NO se copia el patrón de TA.6 (que sí rechaza la mezcla con un check): allí varias
    campañas conviven en un motor y el sobre lleva la moneda. Aquí la forma no existe; el
    check sería más código para una garantía más débil.

`expira_en_dias` (obligatorio ⇔ VES) NO es una precaución: es lo que impide que el motor finja
que un saldo VES almacena valor. El VES no sirve como depósito de valor (>70% perdido desde
oct. 2025) y un saldo ES valor sostenido en el tiempo. El motor NO modela inflación —
modelarla exigiría una tasa, y eso es N3. Es una convención DECLARADA y verificable, no un
efecto: el motor no tiene reloj (`ts` es entrada) y caducar por su cuenta sería una operación
de valor sin puerta humana (M8). La declara el motor; la ejecuta el comité.

Spec: workflows/micorriza/spec-ledger.md (upstream)
      B2B/workflows/micorriza-ve/d1-unidad-de-cuenta/spec.md (delta VE; manda donde habla)
Acceptance: workflows/micorriza/evals/acceptance-ledger.md (AC-L1..L9); AC-10, AC-d1.*

Provenance: drafted by agy-gemini-3-flash via multi-model-orchestration,
reviewed by Claude. D1 (fork VE) por Opus en TB.2. stdlib only.
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
from firewall.herencia import _key_matches_taxonomy

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

    ratification_kinds = {"cell_created", "member_added", "member_updated", "clearing_applied", "cell_paused", "cell_resumed"}
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

        # D1 — la moneda de la célula. Sin default implícito: una célula que no dice en qué
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
                "paused": False
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
        if d_mem["status"] not in {"active", "warned", "line_reduced"}:
            raise ValueError(debtor)
        if c_mem["status"] not in {"active", "warned", "line_reduced"}:
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

def add_member(state: dict, member: dict, ratified_by: str, ts: int) -> tuple[dict, dict]:
    """Add a new member with optional initial credit lines."""
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
    return _apply(state, "member_added", payload, ts)

def update_member(state: dict, member_id: str, changes: dict, ratified_by: str, ts: int) -> tuple[dict, dict]:
    """Apply administrative changes to credit limits or status."""
    payload = {
        "member_id": member_id,
        "changes": changes,
        "ratified_by": ratified_by
    }
    return _apply(state, "member_updated", payload, ts)

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
    return {
        "member_id": member_id,
        "status": m["status"],
        "balance_cents": m["balance_cents"],
        "credit_min_cents": m["credit_min_cents"],
        "credit_max_cents": m["credit_max_cents"],
        "owed_by_cents": owed_by,
        "owed_to_cents": owed_to,
        "projected_cents": projected
    }

def _fmt_cents(cents: int, moneda: str) -> str:
    """Formatea un importe con el símbolo de la moneda de la CÉLULA (C-d1.6).

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
