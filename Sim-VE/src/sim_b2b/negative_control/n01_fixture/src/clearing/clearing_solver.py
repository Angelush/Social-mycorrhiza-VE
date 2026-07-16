"""N-01 negative-control copy of B2B-VE/src/clearing/clearing_solver.py — DELIBERATELY BROKEN.

Full copy of the real VE solver with exactly two surgical changes, each marked "# N-01 PLANT"
at the point it differs from ../../../../../B2B-VE/src/clearing/clearing_solver.py:
(1) the cycle-cancellation loop silently under-reduces the LAST edge of each cancelled cycle
by one cent (the actual conservation breach); (2) the solver's own `post_net != pre_net`
self-check is disabled, so the corrupted proposal returns as if valid. TS.1: re-derived from
the VE SUT — same plant as the upstream Sim fixture, re-applied to the VE source (which
carries D1/TB.8b: `moneda` required in the input and conserved in the proposal; the plant
does not touch that path, so the corrupted proposal still carries a legal `moneda`).

Never imported by anything outside the negative-control test suite. Never used to modify
`B2B-VE/` — that directory is untouched; this is a wholly separate copy under `Sim-VE/`.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple

Edge = Tuple[str, str]  # (debtor, creditor)

# D1 (TB.8b) — mono-moneda por célula; el símbolo se deriva, jamás se hardcodea (C-d1.6).
# Duplicado a propósito respecto al mapa del ledger: el solver no importa el ledger y no debe
# (D9 los separó); el anti-drift lo fija un test de igualdad de los dos mapas.
_SIMBOLO = {"USD": "$", "VES": "Bs."}


def _validate(data: dict) -> Tuple[str, str, List[dict], List[dict]]:
    if not isinstance(data, dict):
        raise ValueError("input must be a dict")
    cell_id = data.get("cell_id")
    if not isinstance(cell_id, str) or not cell_id:
        raise ValueError("missing or invalid cell_id")
    # D1 — sin default: un default sería la configuración que nadie revisa (F-d3.1) y el
    # defecto del «€» seguiría vivo para todo llamador que no la pase. EUR no es válido.
    moneda = data.get("moneda")
    if moneda not in _SIMBOLO:
        raise ValueError("missing or invalid moneda")
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
        for field in ("turnover_cents", "credit_min_cents", "credit_max_cents"):
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
    return cell_id, moneda, members, obligations


def _net_positions(member_ids, obligations) -> Dict[str, int]:
    """net = sum(incoming) - sum(outgoing), every member present (default 0)."""
    net = {mid: 0 for mid in member_ids}
    for o in obligations:
        net[o["creditor"]] += o["amount_cents"]
        net[o["debtor"]] -= o["amount_cents"]
    return net


def _find_cycle(weights: Dict[Edge, int]) -> List[str] | None:
    """Return a directed cycle as [n0, n1, ..., n0] or None. Deterministic:
    iterates nodes and neighbours in sorted order so the same graph always
    yields the same cycle (M3 / AC4)."""
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
        # iterative DFS with an explicit neighbour index
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
                if cst == GREY:  # back-edge -> cycle
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
    cell_id, moneda, members, obligations = _validate(data)
    member_ids = [m["id"] for m in members]

    pre_net = _net_positions(member_ids, obligations)

    # Collapse parallel debtor->creditor edges; remember component obligations
    # (id, original_amount) in ascending-id order for deterministic back-alloc.
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

    # Back-allocate each edge's total reduction across its obligations, capping
    # every obligation at its own amount (ascending id order). This is the fix
    # over the naive draft, which over-reduced the first parallel obligation.
    settlements: List[dict] = []
    for e in sorted(reduced_per_edge):
        remaining = reduced_per_edge[e]
        for oid, amt in components[e]:
            if remaining <= 0:
                break
            take = min(remaining, amt)
            settlements.append({"obligation_id": oid, "reduce_by_cents": take})
            remaining -= take
        if remaining != 0:  # should never happen: total reduction <= edge total
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
        # D1 (TB.8b) — la propuesta que el comité ratifica declara en qué unidad habla;
        # el render no puede derivar lo que el resultado no lleva.
        "moneda": moneda,
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


def render_report(result: dict) -> str:
    cell_id = result["cell_id"]
    metrics = result["metrics"]
    settlements = result["settlements"]
    residual_obligations = result["residual_obligations"]
    net_positions = result["net_positions"]
    credit_flags = result["credit_flags"]
    audit_trace = result["audit_trace"]

    # D1/C-d1.6 (TB.8b) — el símbolo se deriva del campo `moneda` de la propuesta. El «€»
    # hardcodeado de upstream era una mentira en cuanto la unidad de cuenta dejó de ser el
    # euro, y esta propuesta la lee el comité para RATIFICAR.
    simbolo = _SIMBOLO[result["moneda"]]

    def format_cents(cents: int) -> str:
        sign = "-" if cents < 0 else ""
        a = abs(cents)
        return f"{sign}{a // 100}.{a % 100:02d} {simbolo}"

    lines = []
    lines.append(f"# Settlement proposal — {cell_id}")

    lines.append("")
    lines.append("## Metrics")
    lines.append(f"- gross debt before: {format_cents(metrics['gross_debt_before_cents'])}")
    lines.append(f"- gross debt after: {format_cents(metrics['gross_debt_after_cents'])}")
    lines.append(f"- reduction: {metrics['reduction_pct']}%")
    lines.append(f"- cycles cancelled: {metrics['cycles_cancelled']}")

    lines.append("")
    lines.append("## Settlements")
    if settlements:
        for s in settlements:
            lines.append(f"- {s['obligation_id']}: reduce by {format_cents(s['reduce_by_cents'])}")
    else:
        lines.append("- none")

    lines.append("")
    lines.append("## Residual obligations")
    if residual_obligations:
        for o in residual_obligations:
            lines.append(f"- {o['debtor']} \u2192 {o['creditor']}: {format_cents(o['amount_cents'])}")
    else:
        lines.append("- none")

    lines.append("")
    lines.append("## Net positions")
    for mid in sorted(net_positions):
        lines.append(f"- {mid}: {format_cents(net_positions[mid])}")

    lines.append("")
    lines.append("## Credit flags")
    if credit_flags:
        for mid in credit_flags:
            lines.append(f"- {mid}")
    else:
        lines.append("- none")

    lines.append("")
    lines.append("## Audit trace")
    if audit_trace:
        for entry in audit_trace:
            cycle_str = " \u2192 ".join(entry["cycle"])
            lines.append(f"- cycle {cycle_str}: {format_cents(entry['min_edge_cents'])}")
    else:
        lines.append("- none")

    return "\n".join(lines) + "\n"
