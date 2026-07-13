"""N-01 negative-control copy of B2B/src/clearing/clearing_solver.py — DELIBERATELY BROKEN.

This is a full copy of the real clearing solver with exactly two surgical changes, each
marked "# N-01 PLANT" at the point it differs from the real source in
../../../../B2B/src/clearing/clearing_solver.py:

1. The cycle-cancellation loop reduces every edge in a cancelled cycle by the SAME amount
   `m` EXCEPT the last edge, which is silently under-reduced by one cent. This is not a
   symmetric, conservation-preserving reduction: a genuine cycle-cancellation must reduce
   every edge around a closed loop by the identical amount, or some firm's net position
   necessarily changes (audit V2/ST6 — this is the actual conservation breach the harness's
   independent oracle must catch).
2. The solver's own `post_net != pre_net` self-check, which would normally catch exactly
   this kind of corruption and raise before returning, is disabled — so the corrupted
   proposal is returned as if it were valid, with no exception at all.

Never imported by anything outside the negative-control test suite. Never used to modify
`B2B/` — that directory is untouched; this is a wholly separate copy under `Sim/`.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple

Edge = Tuple[str, str]  # (debtor, creditor)


def _validate(data: dict) -> Tuple[str, List[dict], List[dict]]:
    if not isinstance(data, dict):
        raise ValueError("input must be a dict")
    cell_id = data.get("cell_id")
    if not isinstance(cell_id, str) or not cell_id:
        raise ValueError("missing or invalid cell_id")
    members = data.get("members", [])
    if not isinstance(members, list):
        raise ValueError("members must be a list")
    for m in members:
        if not isinstance(m, dict):
            raise ValueError("member must be a dict")
        if "id" not in m:
            raise ValueError("member missing id")
        mid = m["id"]
        if not isinstance(mid, str) or not mid:
            raise ValueError(f"member {mid} invalid id")
        for field in ("turnover_eur_cents", "credit_min_cents", "credit_max_cents"):
            if field not in m:
                raise ValueError(f"member {mid} missing field '{field}'")
            val = m[field]
            if not isinstance(val, int) or isinstance(val, bool):
                raise ValueError(f"member {mid} {field} must be int")
        if not (m["credit_min_cents"] <= 0 <= m["credit_max_cents"]):
            raise ValueError(f"member {mid} invalid credit bounds")
    member_ids = {m["id"] for m in members}
    if len(member_ids) != len(members):
        raise ValueError("duplicate member id")
    obligations = data.get("obligations", [])
    if not isinstance(obligations, list):
        raise ValueError("obligations must be a list")
    seen_obl = set()
    for o in obligations:
        if not isinstance(o, dict):
            raise ValueError("obligation must be a dict")
        for field in ("id", "debtor", "creditor", "amount_cents"):
            if field not in o:
                raise ValueError(f"obligation missing field '{field}'")
        oid = o["id"]
        if not isinstance(oid, str) or not oid:
            raise ValueError(f"obligation {oid} invalid id")
        if not isinstance(o["debtor"], str):
            raise ValueError(f"obligation {oid} debtor must be str")
        if not isinstance(o["creditor"], str):
            raise ValueError(f"obligation {oid} creditor must be str")
        if oid in seen_obl:
            raise ValueError(f"duplicate obligation id: {oid}")
        seen_obl.add(oid)
        amt = o["amount_cents"]
        if not isinstance(amt, int) or isinstance(amt, bool):
            raise ValueError(f"obligation {oid} amount must be int cents")
        if amt <= 0:
            raise ValueError(f"obligation {oid} amount must be > 0")
        if o["debtor"] == o["creditor"]:
            raise ValueError(f"self-loop obligation: {oid}")
        if o["debtor"] not in member_ids or o["creditor"] not in member_ids:
            raise ValueError(f"obligation {oid} references unknown member")
    return cell_id, members, obligations


def _net_positions(member_ids, obligations) -> Dict[str, int]:
    net = {mid: 0 for mid in member_ids}
    for o in obligations:
        net[o["creditor"]] += o["amount_cents"]
        net[o["debtor"]] -= o["amount_cents"]
    return net


def _find_cycle(weights: Dict[Edge, int]) -> List[str] | None:
    adj: Dict[str, List[str]] = defaultdict(list)
    for (d, c) in weights:
        adj[d].append(c)
    for d in adj:
        adj[d].sort()

    WHITE, GREY, BLACK = 0, 1, 2
    color: Dict[str, int] = {}
    stack: List[str] = []

    nodes = sorted({n for e in weights for n in e})

    def visit(start: str) -> List[str] | None:
        frames: List[Tuple[str, int]] = [(start, 0)]
        color[start] = GREY
        stack.append(start)
        while frames:
            node, i = frames[-1]
            neigh = adj.get(node, [])
            if i < len(neigh):
                frames[-1] = (node, i + 1)
                nxt = neigh[i]
                cst = color.get(nxt, WHITE)
                if cst == GREY:
                    idx = stack.index(nxt)
                    return stack[idx:] + [nxt]
                if cst == WHITE:
                    color[nxt] = GREY
                    stack.append(nxt)
                    frames.append((nxt, 0))
            else:
                color[node] = BLACK
                stack.pop()
                frames.pop()
        return None

    for n in nodes:
        if color.get(n, WHITE) == WHITE:
            cyc = visit(n)
            if cyc is not None:
                return cyc
    return None


def clear(data: dict) -> dict:
    cell_id, members, obligations = _validate(data)
    member_ids = [m["id"] for m in members]

    pre_net = _net_positions(member_ids, obligations)

    weights: Dict[Edge, int] = {}
    components: Dict[Edge, List[Tuple[str, int]]] = {}
    for o in obligations:
        e = (o["debtor"], o["creditor"])
        weights[e] = weights.get(e, 0) + o["amount_cents"]
        components.setdefault(e, []).append((o["id"], o["amount_cents"]))
    for e in components:
        components[e].sort(key=lambda t: t[0])

    gross_before = sum(weights.values())
    reduced_per_edge: Dict[Edge, int] = defaultdict(int)
    audit_trace: List[dict] = []
    cycles_cancelled = 0

    while True:
        cycle = _find_cycle(weights)
        if cycle is None:
            break
        edges = [(cycle[i], cycle[i + 1]) for i in range(len(cycle) - 1)]
        m = min(weights[e] for e in edges)
        # N-01 PLANT: every edge in the cycle must be reduced by the identical amount `m`
        # for the cancellation to preserve net positions. The last edge is silently under-
        # reduced by one cent instead, breaking that symmetry (audit V2/ST6's exact target).
        for i, e in enumerate(edges):
            reduce_amt = m if i < len(edges) - 1 else max(0, m - 1)
            weights[e] -= reduce_amt
            reduced_per_edge[e] += reduce_amt
            if weights[e] == 0:
                del weights[e]
        audit_trace.append({"cycle": list(cycle), "min_edge_cents": m})
        cycles_cancelled += 1

    settlements: List[dict] = []
    for e in sorted(reduced_per_edge):
        remaining = reduced_per_edge[e]
        for oid, amt in components[e]:
            if remaining <= 0:
                break
            take = min(remaining, amt)
            settlements.append({"obligation_id": oid, "reduce_by_cents": take})
            remaining -= take
        if remaining != 0:
            raise ValueError(f"back-allocation residue on edge {e}")

    residual = [
        {"debtor": d, "creditor": c, "amount_cents": w}
        for (d, c), w in weights.items()
    ]
    residual.sort(key=lambda o: (o["debtor"], o["creditor"]))

    post_net = _net_positions(member_ids, residual)
    # N-01 PLANT: the real solver raises here on `post_net != pre_net`. That self-check is
    # exactly what would catch the corruption planted above -- disabling it is what makes
    # this plant SILENT (ST6: a plant the SUT catches for you tests its own self-defence,
    # not the independent oracle). No conservation check remains in this copy at all.

    gross_after = sum(weights.values())
    if gross_after > gross_before:
        raise ValueError("debt increased: impossible result")

    credit_flags = [
        m["id"] for m in members
        if not (m["credit_min_cents"] <= post_net[m["id"]] <= m["credit_max_cents"])
    ]

    reduction_pct = (
        round((gross_before - gross_after) / gross_before * 100.0, 6)
        if gross_before else 0.0
    )

    return {
        "cell_id": cell_id,
        "settlements": settlements,
        "residual_obligations": residual,
        "metrics": {
            "gross_debt_before_cents": gross_before,
            "gross_debt_after_cents": gross_after,
            "reduction_pct": reduction_pct,
            "cycles_cancelled": cycles_cancelled,
        },
        "net_positions": post_net,
        "credit_flags": credit_flags,
        "audit_trace": audit_trace,
    }
