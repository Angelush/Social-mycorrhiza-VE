"""M2: C2CWorld + proposals + the 9 archetypes, driven against the REAL C2C code (AC2.1–AC2.3).

Builds a mixed cooperative+adversarial population across a gift cell and a market cell, runs it, and
checks (a) byte-determinism (same seed -> identical trace) and (b) that each adversary's shape is
caught by the real module's own wall (a Rejected / dropped_ / damped_ count), never assumed away.
"""
from pathlib import Path
from random import Random

from sim_c2c.adapter import C2CAdapter
from sim_c2c.config import RoundConfig
from sim_c2c.world import C2CWorld, ModuleCall, Rejected
from sim_c2c.policies_core import (
    Convener, Lurker, Matchmaker, Newcomer, Reciprocator, Sensor,
)
from sim_c2c.policies_adversarial import (
    BadFaithBlocker, EngagementBaiter, MobInstigator, RoomLeaker, Surveillor, SybilVoucher,
)

C2C_ROOT = Path(__file__).resolve().parent.parent.parent / "C2C"

CELLS = {"cell-gift": "communal_gift", "cell-market": "market_price"}
CIRCLE, PROP, CAMP = "circle-1", "prop-1", "camp-1"


def _cfg(seed: int) -> RoundConfig:
    return RoundConfig(
        actor_mix={}, n_actors=9, T=24, cells=CELLS, adversary_intensity=0.5,
        window=5, velocity_cap=3, half_life=4, min_strength=0.1, seed=seed,
    )


def _build_world(seed: int) -> C2CWorld:
    cell_of = {
        "r1": "cell-gift", "n1": "cell-gift", "l1": "cell-gift", "s1": "cell-gift",
        "m1": "cell-gift", "rl1": "cell-gift", "bb1": "cell-gift", "eb1": "cell-gift",
        "sv1": "cell-gift", "r2": "cell-market",
    }
    cfg = _cfg(seed)
    actors = {
        "r1": Reciprocator("r1"), "n1": Newcomer("n1"), "l1": Lurker("l1"),
        "s1": Surveillor("s1"), "m1": MobInstigator("m1", target_artifact="artifact-cell-gift"),
        "rl1": RoomLeaker("rl1"), "bb1": BadFaithBlocker("bb1", CIRCLE, PROP),
        "eb1": EngagementBaiter("eb1"), "sv1": SybilVoucher("sv1", CAMP), "r2": Reciprocator("r2"),
        "__matchmaker__": Matchmaker(askers=("r1", "n1", "eb1", "s1"), cell_id="cell-gift"),
        "__sensor__": Sensor(cell_id="cell-gift", cfg=cfg),
        "__convener__": Convener(CIRCLE, PROP, CAMP, "cell-gift", threshold=2),
    }
    return C2CWorld(C2CAdapter(C2C_ROOT), actors, cfg, cell_of, CELLS, Random(seed * 1_000_003))


def _run(seed: int):
    world = _build_world(seed)
    for _ in range(world.cfg.T):
        world.step()
    return world


def test_byte_determinism_same_seed_identical_trace():
    a = _run(7)
    b = _run(7)
    assert a.trace == b.trace, "AC2.2: same seed must yield an identical trace"


def _module_calls(world, method):
    return [e for e in world.trace
            if isinstance(e.result, ModuleCall) and e.result.method == method]


def test_room_leaker_market_key_is_rejected_by_the_real_membrane():
    world = _run(7)
    admits = _module_calls(world, "admit")
    leaks = [e for e in admits if e.actor_id == "rl1"]
    assert leaks, "the room-leaker must have attempted admits"
    assert all(isinstance(e.result.output, Rejected) for e in leaks), (
        "AC2.2 / invariant 1: a market key in a gift room must be rejected by the real membrane"
    )


def test_matcher_drops_engagement_and_surveillance_shapes():
    world = _run(7)
    matches = _module_calls(world, "match")
    # every surfaced proposal must be clean: no engagement/surveillance key survived
    dropped_total = 0
    for e in matches:
        out = e.result.output
        assert not isinstance(out, Rejected), "a valid match request must not raise"
        dropped_total += out["audit_trace"]["dropped_surveillance_shape"]
        for p in out["proposals"]:
            assert set(p.keys()) == {"token", "cell_id", "kind", "reason", "cited_facts", "expires_at"}
    assert dropped_total >= 1, "AC2.2 / invariant 8: engagement/surveillance shapes must be dropped"


def test_mob_burst_is_velocity_throttled_by_the_real_stigmergy():
    world = _run(7)
    senses = _module_calls(world, "sense")
    assert any(e.result.output["audit_trace"]["damped_velocity"] > 0 for e in senses), (
        "AC2.2 / invariant 9: the mob's flag burst must be velocity-throttled"
    )


def test_governance_surfaces_reason_not_objector_token():
    import json
    world = _run(7)
    decides = _module_calls(world, "decide")
    assert decides, "the convener must have run governance.decide"
    revisits = [e for e in decides if e.result.output["verdict"] == "revisit"]
    assert revisits, "AC2.2 / Capa-6: the bad-faith paramount objection must force a revisit"
    for e in decides:
        assert "bb1" not in json.dumps(e.result.output), "objector token must never leak"


def test_harness_never_calls_the_claude_matcher_factory():
    # AC2.3: the injected propose is a deterministic rule closure; the world never imports or calls
    # the real Claude factory inside a campaign.
    import ast
    import sim_c2c.world as world_mod
    src = Path(world_mod.__file__).read_text()
    tree = ast.parse(src)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    assert not any("claude_matcher" in n for n in names)
    assert "make_claude_propose" not in src
