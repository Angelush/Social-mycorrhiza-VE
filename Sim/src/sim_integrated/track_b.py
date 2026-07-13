"""Track B — integration welfare, descriptive-only. Aggregate seam-health counts, never a per-party
scalar (the WelfareReport type forbids an agent-indexed slot). Each ships a Goodhart flag: these are
descriptions of how hard the walls were pushed, never objectives the loop maximizes.
"""
from __future__ import annotations

from collections.abc import Sequence

from engine.measurement import TrackB, WelfareReport
from engine.types import TraceEvent
from .world import BridgeAttempt, Rejected


class IntegratedTrackB(TrackB):
    GOODHART_FLAGS = {
        "bridge_attempts_total": "DESCRIPTIVE ONLY. Count of seam-crossing attempts; not a target.",
        "bridge_rejected_fraction": (
            "DESCRIPTIVE ONLY. Fraction of seam crossings the real SUTs rejected — high is the walls "
            "holding, not something to optimize; a provenance leak (F-VS2) is invisible to this count."
        ),
    }

    def measure(self, trace: Sequence[TraceEvent]) -> WelfareReport:
        attempts = [e.result for e in trace if isinstance(e.result, BridgeAttempt)]
        total = len(attempts)
        rejected = sum(1 for a in attempts if isinstance(a.output, Rejected))
        frac = (rejected / total) if total else 1.0
        return WelfareReport(metrics={
            "bridge_attempts_total": float(total),
            "bridge_rejected_fraction": float(frac),
        })
