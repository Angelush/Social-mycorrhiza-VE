"""Track B — C2C welfare, position-relative and DESCRIPTIVE-ONLY.

The load-bearing C2C constraint (brief inv. 2): there is no global scalar of the person. The
guarantee here is STRUCTURAL — the engine `WelfareReport` type has no agent-indexed dimension, so a
per-person score is *unrepresentable*, not merely un-named (measurement.WelfareReport.__post_init__).
`assert_no_person_scalar` (the FORBIDDEN_KEYS substring lint) is defense-in-depth only; it would miss
a scalar named `fertility`/`reachability`/`centrality`, which is exactly why the type is the wall.

Every metric is an aggregate over SAMPLED POSITIONS (never a per-identity slot) and ships with a
Goodhart flag (GOODHART_FLAGS): the number is a description, never an objective the loop maximizes.
The C2CResearcher's search space (M6) contains no Track-B-derived objective — the researcher cannot
turn any of these into a target, so a fertility proxy can never become the thing being optimized.
"""
from __future__ import annotations

from collections.abc import Sequence

from engine.measurement import Distribution, TrackB, WelfareReport
from engine.types import TraceEvent
from .world import ModuleCall, Rejected


class C2CTrackB(TrackB):
    # Each metric ships a Goodhart flag: what goes wrong if someone optimizes FOR this number.
    GOODHART_FLAGS = {
        "reachability_of_cooperation": (
            "DESCRIPTIVE ONLY. Optimizing this rebuilds engagement funnels — a match surfaced is "
            "not a cooperation chosen; a human still disposes."
        ),
        "vouch_graph_diversity": (
            "DESCRIPTIVE ONLY. A centrality-adjacent proxy: do NOT rank or score people by it; "
            "high diversity from one position says nothing about any individual's worth."
        ),
        "cascade_damping_ratio": (
            "DESCRIPTIVE ONLY. High is not 'good moderation' — it is friction, and context "
            "dependent; maximizing it would silence legitimate sustained coordination."
        ),
        "bootstrapping_cost": (
            "DESCRIPTIVE ONLY. Minimizing this incentivizes fake vouches (Sybil rings) that make "
            "newcomers look reachable without any real trust."
        ),
    }

    def goodhart_flag(self, metric: str) -> str:
        return self.GOODHART_FLAGS[metric]

    def measure(self, trace: Sequence[TraceEvent]) -> WelfareReport:
        # position -> did this asker find any cooperation affordance (a legibility path or a match)?
        found_by_position: dict[str, bool] = {}
        diversity_samples: list[float] = []      # distinct nearest-hop trustees per query position
        bootstrap_hops: list[float] = []         # nearest_hops when a position first reaches trust
        damped_total = 0
        considered_total = 0

        for event in trace:
            mc = event.result
            if not isinstance(mc, ModuleCall) or isinstance(mc.output, Rejected):
                continue
            out = mc.output

            if mc.method == "query":
                asker = out.get("asker")
                fp = out.get("from_your_position", {})
                reached = bool(fp.get("reachable")) or bool(fp.get("facts"))
                found_by_position[asker] = found_by_position.get(asker, False) or reached
                diversity_samples.append(float(len(fp.get("vouched_by_people_you_trust", []))))
                if fp.get("reachable") and fp.get("nearest_hops") is not None:
                    bootstrap_hops.append(float(fp["nearest_hops"]))

            elif mc.method == "match":
                asker = out.get("asker")
                surfaced = len(out.get("proposals", [])) > 0
                found_by_position[asker] = found_by_position.get(asker, False) or surfaced

            elif mc.method == "sense":
                at = out.get("audit_trace", {})
                damped_total += int(at.get("damped_velocity", 0))
                considered_total += int(at.get("considered_traces", 0))

        reach_samples = [1.0 if v else 0.0 for _, v in sorted(found_by_position.items())]
        reach_frac = (sum(reach_samples) / len(reach_samples)) if reach_samples else 0.0
        damping_ratio = (damped_total / considered_total) if considered_total else 0.0

        metrics = {
            "reachability_of_cooperation": Distribution(
                summary={"fraction_positions_reached": reach_frac,
                         "n_positions": float(len(reach_samples))},
                samples=tuple(reach_samples),
            ),
            "vouch_graph_diversity": Distribution(
                summary={"mean_trustees": (sum(diversity_samples) / len(diversity_samples))
                         if diversity_samples else 0.0,
                         "n_queries": float(len(diversity_samples))},
                samples=tuple(sorted(diversity_samples)),
            ),
            "cascade_damping_ratio": float(damping_ratio),
            "bootstrapping_cost": Distribution(
                summary={"mean_hops": (sum(bootstrap_hops) / len(bootstrap_hops))
                         if bootstrap_hops else 0.0,
                         "n_reached": float(len(bootstrap_hops))},
                samples=tuple(sorted(bootstrap_hops)),
            ),
        }
        return WelfareReport(metrics=metrics)
