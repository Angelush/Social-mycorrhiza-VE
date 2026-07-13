"""N-02 negative-control copy of B2B/src/ledger/mutual_credit_ledger.py — DELIBERATELY BROKEN.

Full copy of the real ledger with the "reject on bound breach" behavior of both
`obligation_recorded` and `obligation_settled` replaced by a SILENT CLAMP of the effective
amount to whatever headroom remains, marked "# N-02 PLANT" at each point of difference from
../../../../B2B/src/ledger/mutual_credit_ledger.py.

This is deliberately NOT a naive balance clamp (audit V3): clamping a *balance* directly to
its bound would move one side of a transfer more than the other and trip the ledger's own
global zero-sum-of-balances assert -- so the SUT would catch that itself. Instead, both sides
of every affected op are shrunk to the SAME clamped effective amount, so the op stays
zero-sum and no assert in this file fires. Critically, the EVENT payload this file returns is
also rewritten to show the clamped (committed) amount, not the caller's original request --
matching the real, realistic shape of this class of bug: the event log looks entirely
self-consistent and successful on its own. The only way to see the discrepancy is to compare
what was actually committed (visible in the event) against what the original proposal
requested (visible on the harness's own copy of the proposal) -- exactly the check
sim_b2b/track_a.py's T1b performs.

Never imported by anything outside the negative-control test suite. Never used to modify
`B2B/` -- that directory is untouched; this is a wholly separate copy under `Sim/`.
"""
import json
import hashlib
import copy

def canonical(x) -> bytes:
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

        new_state = {
            "cell_id": cell_id,
            "params": {
                "neg_line_bp": params["neg_line_bp"],
                "pos_line_bp": params["pos_line_bp"],
                "velocity_window_s": params["velocity_window_s"],
                "velocity_max_cents": params["velocity_max_cents"],
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
        turnover = member.get("turnover_eur_cents")
        if not _is_strict_int(turnover) or turnover < 0:
            raise ValueError("turnover_eur_cents")
        credit_min = member.get("credit_min_cents")
        credit_max = member.get("credit_max_cents")
        if not _is_strict_int(credit_min) or not _is_strict_int(credit_max):
            raise ValueError("credit_min_cents")
        if not (credit_min <= 0 <= credit_max):
            raise ValueError("credit_min_cents")

        new_state["members"][member_id] = {
            "turnover_eur_cents": turnover,
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

        # N-02 PLANT: the real ledger computes the full-amount projected positions here and
        # raises if either breaches its bound. This copy instead silently shrinks the
        # effective amount to the smaller of the two sides' remaining headroom, and commits
        # that instead -- both sides still move by the identical (clamped) amount, so no
        # zero-sum assert anywhere in this file ever fires. `ob["amount_cents"]` (part of
        # `payload_copy`, and therefore of the returned event) is rewritten to the clamped
        # value too, so the event log looks entirely self-consistent on its own.
        debtor_headroom = get_projected(debtor) - d_mem["credit_min_cents"]
        creditor_headroom = c_mem["credit_max_cents"] - get_projected(creditor)
        effective_amount = min(amount, max(0, debtor_headroom), max(0, creditor_headroom))
        amount = effective_amount
        ob["amount_cents"] = effective_amount

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
        # N-02 PLANT: same silent-clamp shape as obligation_recorded above, applied here to
        # settlement -- shrink to the smaller side's headroom instead of raising, and rewrite
        # `payload_copy["amount_cents"]` (part of the returned event) to match what was
        # actually committed.
        debtor_headroom = d_mem["balance_cents"] - d_mem["credit_min_cents"]
        creditor_headroom = c_mem["credit_max_cents"] - c_mem["balance_cents"]
        effective_amount = min(amount, max(0, debtor_headroom), max(0, creditor_headroom))
        amount = effective_amount
        payload_copy["amount_cents"] = effective_amount
        d_mem["balance_cents"] -= amount
        c_mem["balance_cents"] += amount
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

    prev_seq = 0 if state is None else state["seq"]
    if new_state["seq"] != prev_seq + 1:
        raise ValueError("seq")

    if new_state["last_ts"] != ts:
        raise ValueError("last_ts")
    if new_state["head_hash"] != event_hash:
        raise ValueError("head_hash")

    return new_state, event

def create_cell(cell_id: str, params: dict, ratified_by: str, ts: int) -> tuple[dict, dict]:
    payload = {
        "cell_id": cell_id,
        "params": params,
        "ratified_by": ratified_by
    }
    return _apply(None, "cell_created", payload, ts)

def add_member(state: dict, member: dict, ratified_by: str, ts: int) -> tuple[dict, dict]:
    if not isinstance(member, dict):
        raise ValueError("member")
    member_id = member.get("id")
    if not isinstance(member_id, str) or not member_id:
        raise ValueError("id")
    turnover = member.get("turnover_eur_cents")
    if not _is_strict_int(turnover) or turnover < 0:
        raise ValueError("turnover_eur_cents")
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
        "turnover_eur_cents": turnover,
        "credit_min_cents": credit_min,
        "credit_max_cents": credit_max
    }
    payload = {
        "member": resolved_member,
        "ratified_by": ratified_by
    }
    return _apply(state, "member_added", payload, ts)

def update_member(state: dict, member_id: str, changes: dict, ratified_by: str, ts: int) -> tuple[dict, dict]:
    payload = {
        "member_id": member_id,
        "changes": changes,
        "ratified_by": ratified_by
    }
    return _apply(state, "member_updated", payload, ts)

def record_obligation(state: dict, obligation: dict, ts: int) -> tuple[dict, dict]:
    payload = {
        "obligation": obligation
    }
    return _apply(state, "obligation_recorded", payload, ts)

def apply_clearing(state: dict, proposal: dict, ratified_by: str, ts: int) -> tuple[dict, dict]:
    proposal_hash = hashlib.sha256(canonical(proposal)).hexdigest()
    payload = {
        "proposal": proposal,
        "proposal_hash": proposal_hash,
        "ratified_by": ratified_by
    }
    return _apply(state, "clearing_applied", payload, ts)

def settle_obligation(state: dict, obligation_id: str, amount_cents: int, ts: int) -> tuple[dict, dict]:
    payload = {
        "obligation_id": obligation_id,
        "amount_cents": amount_cents
    }
    return _apply(state, "obligation_settled", payload, ts)

def pause_cell(state: dict, ratified_by: str, ts: int) -> tuple[dict, dict]:
    payload = {
        "ratified_by": ratified_by
    }
    return _apply(state, "cell_paused", payload, ts)

def resume_cell(state: dict, ratified_by: str, ts: int) -> tuple[dict, dict]:
    payload = {
        "ratified_by": ratified_by
    }
    return _apply(state, "cell_resumed", payload, ts)

def to_clearing_input(state: dict) -> dict:
    state_cp = copy.deepcopy(state)
    members_list = []
    for m_id, m in state_cp["members"].items():
        members_list.append({
            "id": m_id,
            "turnover_eur_cents": m["turnover_eur_cents"],
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

def member_statement(state: dict, member_id: str) -> dict:
    if member_id not in state["members"]:
        raise ValueError(member_id)
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

def cell_metrics(state: dict) -> dict:
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
        "paused": state["params"]["paused"],
        "seq": state["seq"]
    }
