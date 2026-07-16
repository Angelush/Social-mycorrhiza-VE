from __future__ import annotations

import networkx as nx


def generate_trade_graph(
    n_firms: int, seed: int, m: int = 2
) -> dict[str, tuple[str, ...]]:
    # Hypothesis: real B2B trade networks resemble Barabási–Albert graphs; swap if a validated model is found.
    g = nx.barabasi_albert_graph(n_firms, m, seed=seed)

    result = {}
    for i in range(n_firms):
        firm_id = f"firm_{i:04d}"
        if i in g:
            neighbors = sorted([f"firm_{nbr:04d}" for nbr in g.neighbors(i)])
            result[firm_id] = tuple(neighbors)
        else:
            result[firm_id] = ()

    return result
