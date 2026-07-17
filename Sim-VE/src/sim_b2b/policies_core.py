from __future__ import annotations

from random import Random

from engine.policy import RulePolicy
from engine.types import Proposal
from .config import CellView, FirmState
from .proposals import (PauseCell, PuentePausar, PuenteReanudar, RequestClearing,
                        ResumeCell, SanctionStep, Settle, StatementProbe, Trade)


class Circulator(RulePolicy):
    def __init__(self, member_id: str, bite_size_cents: int = 50_000):
        self._member_id = member_id
        self._bite_size = bite_size_cents
        self._seq = 0
        self._open_as_debtor: list[tuple[str, int]] = []

    def act(self, view: FirmState, rng: Random) -> Proposal | None:
        if rng.random() < 0.4:
            if self._open_as_debtor:
                obligation_id, amount = self._open_as_debtor.pop()
                return Settle(obligation_id=obligation_id, cents=amount)
        if not view.neighbor_ids:
            return None
        neighbor = rng.choice(view.neighbor_ids)
        as_debtor = rng.random() < 0.5
        if as_debtor:
            cap = max(0, view.balance_cents - view.credit_min_cents)
        else:
            cap = max(0, view.credit_max_cents - view.balance_cents)
        if cap <= 0:
            return None
        amount = min(self._bite_size, cap)
        obligation_id = f"{self._member_id}-t{self._seq}"
        self._seq += 1
        if as_debtor:
            self._open_as_debtor.append((obligation_id, amount))
            return Trade(obligation_id=obligation_id, debtor=self._member_id, creditor=neighbor, cents=amount)
        return Trade(obligation_id=obligation_id, debtor=neighbor, creditor=self._member_id, cents=amount)


class Hoarder(RulePolicy):
    def __init__(self, member_id: str, bite_size_cents: int = 50_000):
        self._member_id = member_id
        self._bite_size = bite_size_cents
        self._seq = 0

    def act(self, view: FirmState, rng: Random) -> Proposal | None:
        if not view.neighbor_ids:
            return None
        neighbor = rng.choice(view.neighbor_ids)
        obligation_id = f"{self._member_id}-t{self._seq}"
        self._seq += 1
        return Trade(obligation_id=obligation_id, debtor=neighbor, creditor=self._member_id, cents=self._bite_size)


class Wallflower(RulePolicy):
    def __init__(self, member_id: str, bite_size_cents: int = 50_000):
        self._member_id = member_id
        self._bite_size = bite_size_cents
        self._seq = 0
        self._open_as_debtor: list[tuple[str, int]] = []

    def act(self, view: FirmState, rng: Random) -> Proposal | None:
        if rng.random() >= 0.1:
            return None
        if self._open_as_debtor and rng.random() < 0.5:
            obligation_id, amount = self._open_as_debtor.pop()
            return Settle(obligation_id=obligation_id, cents=amount)
        if not view.neighbor_ids:
            return None
        neighbor = rng.choice(view.neighbor_ids)
        amount = min(self._bite_size // 5, max(0, view.balance_cents - view.credit_min_cents))
        if amount <= 0:
            return None
        obligation_id = f"{self._member_id}-t{self._seq}"
        self._seq += 1
        self._open_as_debtor.append((obligation_id, amount))
        return Trade(obligation_id=obligation_id, debtor=self._member_id, creditor=neighbor, cents=amount)


class ClearingScheduler(RulePolicy):
    def __init__(self, cadence_ticks: int):
        self._cadence = cadence_ticks

    def act(self, view: CellView, rng: Random) -> Proposal | None:
        return RequestClearing() if view.tick % self._cadence == 0 else None


class ComplianceOfficer(RulePolicy):
    def __init__(self, warn_threshold_cents: int):
        self._warn_threshold = warn_threshold_cents

    def act(self, view: CellView, rng: Random) -> Proposal | None:
        for mid in sorted(view.member_ids):
            statement = view.statements[mid]
            if statement["projected_cents"] <= self._warn_threshold and statement["status"] == "active":
                return SanctionStep(member_id=mid, changes={"status": "warned"})
        return None


class CircuitBreaker(RulePolicy):
    def __init__(self, velocity_max_cents: int, pause_after_ticks_paused: int = 5):
        self._velocity_max = velocity_max_cents
        self._pause_after = pause_after_ticks_paused
        self._ticks_since_pause: int | None = None

    def act(self, view: CellView, rng: Random) -> Proposal | None:
        paused = view.metrics.get("paused", False)
        if paused:
            if self._ticks_since_pause is None:
                self._ticks_since_pause = 0
            else:
                self._ticks_since_pause += 1
            if self._ticks_since_pause >= self._pause_after:
                self._ticks_since_pause = None
                return ResumeCell()
            return None
        gross_open = view.metrics.get("gross_open_cents", 0)
        # Deliberately simple stand-in for an anomaly detector the real ledger lacks —
        # not a literal reading of the design brief's "automatic pause".
        if gross_open > self._velocity_max * 2:
            self._ticks_since_pause = 0
            return PauseCell()
        return None


class Auditor(RulePolicy):
    """Harness role (TS.2): produces the observable material the VE oracles judge.

    - A StatementProbe on a rotating member each `cadence` ticks (visibilidad_saldos needs
      REAL scoped statements in the trace, not the world's own views).
    - One puente_pausar/puente_reanudar cycle early in the round (puerta_humana_ops_nuevas
      needs the VE "ops nuevas" exercised — I-VE7: the pause does not stop internal credit,
      so the rest of the campaign is unaffected).
    Anti-vacuity is the point (TS.1's M2 lesson): an oracle with no material is green blind.
    """

    def __init__(self, member_ids: tuple[str, ...], cadence: int = 4):
        self._members = tuple(sorted(member_ids))
        self._cadence = cadence
        self._puente_state = 0  # 0 = not yet paused, 1 = paused, 2 = cycle done

    def act(self, view: "CellView", rng: Random) -> Proposal | None:
        if self._puente_state == 0 and view.tick >= 1:
            self._puente_state = 1
            return PuentePausar()
        if self._puente_state == 1:
            self._puente_state = 2
            return PuenteReanudar()
        if len(self._members) >= 2 and view.tick % self._cadence == 0:
            i = (view.tick // self._cadence) % len(self._members)
            member = self._members[i]
            foreign = self._members[(i + 1) % len(self._members)]
            return StatementProbe(member_id=member, foreign_id=foreign)
        return None
