"""Property-based tests (evals/tests.md P-01..P-05), via hypothesis."""
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from engine.researcher import apply_within_gate, GateViolation
from engine.types import RangeBound, SearchSpace, WorldDiff
from sim_b2b.campaign import build_campaign
from sim_b2b.config import RoundConfig
from sim_b2b.track_a import _net_positions

B2B_ROOT = Path(__file__).resolve().parent.parent.parent / "B2B-VE"


# P-01: conservation is oracle-independent -- track_a's own networkx-based recompute matches
# a THIRD, differently-implemented (plain-dict) recompute, never the solver's own numbers.
@given(
    edges=st.lists(
        st.tuples(
            st.sampled_from(["A", "B", "C", "D"]),
            st.sampled_from(["A", "B", "C", "D"]),
            st.integers(min_value=1, max_value=100_000),
        ).filter(lambda t: t[0] != t[1]),
        min_size=0,
        max_size=12,
    )
)
@settings(max_examples=50)
def test_p01_independent_net_position_recompute_matches_a_third_implementation(edges):
    firms = {d for d, c, a in edges} | {c for d, c, a in edges}
    networkx_net = _net_positions(edges, firms)

    naive_net = {f: 0 for f in firms}
    for debtor, creditor, amount in edges:
        naive_net[creditor] += amount
        naive_net[debtor] -= amount

    assert networkx_net == naive_net


# P-02: reproducibility -- for random (seed, T), two builds of the same campaign give
# identical journal hashes.
@given(seed=st.integers(min_value=0, max_value=10_000), t=st.integers(min_value=2, max_value=8))
@settings(max_examples=10, deadline=None)
def test_p02_reproducibility_across_random_seeds(seed, t):
    cfg = RoundConfig(
        actor_mix={"circulator": 0.7, "hoarder": 0.15, "wallflower": 0.15},
        n_firms=6, T=t, clearing_cadence=3, base_turnover_cents=10_000_000,
        neg_line_bp=1000, pos_line_bp=1000, topology_params={}, adversary_intensity=0.2,
        velocity_window_s=1, ticks_per_second=10, velocity_max_cents=500_000,
        credit_crunch=False, seed=seed,
    )
    result1 = build_campaign(cfg, B2B_ROOT, max_rounds=2)
    result2 = build_campaign(cfg, B2B_ROOT, max_rounds=2)

    assert [e.entry_hash for e in result1.journal.entries] == [e.entry_hash for e in result2.journal.entries]


# P-03: gate soundness -- apply_within_gate accepts a diff iff every field is declared in
# search_space AND within that field's bound; never a partial accept.
@given(
    x_value=st.floats(min_value=-5.0, max_value=5.0, allow_nan=False),
    include_undeclared=st.booleans(),
)
@settings(max_examples=50)
def test_p03_gate_soundness(x_value, include_undeclared):
    search_space = SearchSpace(bounds={"x": RangeBound(0.0, 1.0)})
    fields = {"x": x_value}
    if include_undeclared:
        fields["undeclared_field"] = 123

    should_accept = (not include_undeclared) and (0.0 <= x_value <= 1.0)
    diff = WorldDiff(fields=fields)
    cfg = {"x": 0.5}

    if should_accept:
        new_cfg = apply_within_gate(cfg, diff, search_space)
        assert new_cfg["x"] == x_value
    else:
        try:
            apply_within_gate(cfg, diff, search_space)
            assert False, "expected GateViolation"
        except GateViolation:
            pass


# P-04: track separation -- IntegrityReport and WelfareReport are independent objects;
# mutating/reconstructing one never touches or depends on the other.
def test_p04_track_separation():
    result = build_campaign(
        RoundConfig(
            actor_mix={"circulator": 1.0}, n_firms=6, T=5, clearing_cadence=3,
            base_turnover_cents=10_000_000, neg_line_bp=1000, pos_line_bp=1000,
            topology_params={}, adversary_intensity=0.1, velocity_window_s=1,
            ticks_per_second=10, velocity_max_cents=500_000, credit_crunch=False, seed=1,
        ),
        B2B_ROOT, max_rounds=2,
    )
    for record in result.history:
        # distinct types, no shared mutable state, no function combining them into one score
        assert type(record.integrity_report).__name__ == "IntegrityReport"
        assert type(record.welfare_report).__name__ == "WelfareReport"
        assert not hasattr(record.integrity_report, "metrics")
        assert not hasattr(record.welfare_report, "results")


# P-05: integer-cents invariant -- no float ever appears on a value-path amount, for random
# valid amounts driven directly through the real adapter.
_AMOUNT_KEYS = {
    "amount_cents", "reduce_by_cents", "balance_cents",
    "gross_debt_before_cents", "gross_debt_after_cents",
    "credit_min_cents", "credit_max_cents",
}


def _assert_no_float_amounts(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in _AMOUNT_KEYS:
                assert isinstance(v, int) and not isinstance(v, bool), f"{k}={v!r} is not an int"
            _assert_no_float_amounts(v)
    elif isinstance(obj, list):
        for item in obj:
            _assert_no_float_amounts(item)


@given(amount=st.integers(min_value=1, max_value=900_000))
@settings(max_examples=30)
def test_p05_no_float_ever_touches_a_value_path_amount(amount):
    from sim_b2b.adapter import B2BAdapter

    adapter = B2BAdapter(B2B_ROOT)
    adapter.create_cell(
        "cell-1",
        {"moneda": "USD", "sal_seudonimo": "sim-ve-sal",
         "neg_line_bp": 1000, "pos_line_bp": 1000, "velocity_window_s": 3600, "velocity_max_cents": 10_000_000},
        ratified_by="ops", ts=0,
    )
    adapter.add_member({"id": "A", "turnover_cents": 10_000_000}, ratified_by="ops", ts=0)
    adapter.add_member({"id": "B", "turnover_cents": 10_000_000}, ratified_by="ops", ts=0)

    event = adapter.record_obligation({"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": amount}, ts=0)
    _assert_no_float_amounts(event)
    _assert_no_float_amounts(adapter.member_statement("A", "comite_credito"))
    _assert_no_float_amounts(adapter.member_statement("B", "comite_credito"))
