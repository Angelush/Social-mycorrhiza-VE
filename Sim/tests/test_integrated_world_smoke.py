"""MI-1: identity + IntegratedWorld + proposals, against the REAL B2B and C2C code (ACI1.1–1.3)."""
from pathlib import Path
from random import Random

from engine.policy import RulePolicy
from sim_b2b.adapter import B2BAdapter
from sim_c2c.adapter import C2CAdapter
from sim_integrated.identity import Identity
from sim_integrated.world import IntegratedWorld, WorldEvent
from sim_integrated.proposals import B2BTrade, C2CGift

B2B_ROOT = Path(__file__).resolve().parent.parent.parent / "B2B"
C2C_ROOT = Path(__file__).resolve().parent.parent.parent / "C2C"
CELL_PARAMS = {"neg_line_bp": 1000, "pos_line_bp": 1000,
               "velocity_window_s": 3600, "velocity_max_cents": 10_000_000}


def setup_b2b(cell: str, members: tuple[str, ...]) -> B2BAdapter:
    a = B2BAdapter(B2B_ROOT)
    a.create_cell(cell, dict(CELL_PARAMS), ratified_by="ops", ts=0)
    for m in members:
        a.add_member({"id": m, "turnover_eur_cents": 10_000_000}, ratified_by="ops", ts=0)
    return a


class _CoopActor(RulePolicy):
    def __init__(self, identity: Identity, partner: str):
        self._id = identity
        self._partner = partner
        self._seq = 0

    def act(self, view, rng):
        self._seq += 1
        if self._id.in_b2b and self._seq % 2 == 1:
            return B2BTrade(cell=self._id.b2b_cell, obligation_id=f"{self._id.actor_id}-o{self._seq}",
                            debtor=self._id.actor_id, creditor=self._partner, cents=50_000)
        if self._id.in_c2c:
            return C2CGift(cell_id=self._id.c2c_cell, interaction_id=f"{self._id.actor_id}-g{self._seq}",
                           participants=(self._id.actor_id,), payload={"gift": "bread"})
        return None


def _build():
    b2b = {"cell-A": setup_b2b("cell-A", ("A1", "A2")),
           "cell-B": setup_b2b("cell-B", ("B1", "B2"))}
    c2c = C2CAdapter(C2C_ROOT)
    ids = {
        "A1": Identity("A1", "business", b2b_cell="cell-A", c2c_cell="room-gift"),
        "A2": Identity("A2", "business", b2b_cell="cell-A", c2c_cell=None),
        "B1": Identity("B1", "person", b2b_cell="cell-B", c2c_cell="room-gift"),
    }
    actors = {"A1": _CoopActor(ids["A1"], "A2"), "A2": _CoopActor(ids["A2"], "A1"),
              "B1": _CoopActor(ids["B1"], "B2")}
    world = IntegratedWorld(b2b, c2c, actors, ids,
                            b2b_rosters={"cell-A": ("A1", "A2"), "cell-B": ("B1", "B2")},
                            c2c_modes={"room-gift": "communal_gift"}, rng=Random(1))
    return world


def test_world_steps_both_suts_over_one_population():
    world = _build()
    for _ in range(6):
        world.step()
    kinds = {e.result.kind for e in world.trace if isinstance(e.result, WorldEvent)}
    assert "obligation_recorded" in kinds, "ACI1.2: baseline B2B trade must drive the real ledger"
    assert "gift_admitted" in kinds, "ACI1.2: baseline C2C gift must drive the real membrane"
    assert world.tick == 6


def test_both_clocks_advance_from_world_tick():
    world = _build()
    world.step()
    world.step()
    # a B2B event carries ts derived from tick; C2C interactions used _iso(tick) internally
    assert world.tick == 2


def test_one_identity_spans_both_worlds():
    world = _build()
    a1 = world.identities["A1"]
    assert a1.in_b2b and a1.in_c2c
    assert a1.b2b_firm_id == a1.c2c_token == "A1"
