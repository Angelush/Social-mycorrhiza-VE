from pathlib import Path

import pytest

from sim_b2b.adapter import B2BAdapter

B2B_ROOT = Path(__file__).resolve().parent.parent.parent / "B2B-VE"

_PARAMS = {
    "moneda": "USD",            # D1: mono-moneda por célula, sin default
    "sal_seudonimo": "sim-ve-sal",  # D3: sal obligatoria en toda célula
    "neg_line_bp": 100,
    "pos_line_bp": 1000,
    "velocity_window_s": 3600,
    "velocity_max_cents": 10_000_000,
}


def _fresh_cell() -> B2BAdapter:
    adapter = B2BAdapter(B2B_ROOT)
    adapter.create_cell("cell-1", dict(_PARAMS), ratified_by="ops", ts=0)
    adapter.add_member({"id": "A", "turnover_cents": 10_000_000}, ratified_by="ops", ts=0)
    adapter.add_member({"id": "B", "turnover_cents": 10_000_000}, ratified_by="ops", ts=0)
    return adapter


def test_adapter_pins_real_sut_with_git_commit():
    adapter = B2BAdapter(B2B_ROOT)
    assert len(adapter.pin.content_hash) == 64
    assert adapter.pin.git_commit is not None
    assert len(adapter.pin.git_commit) == 40


def test_two_instances_pin_identically():
    a1 = B2BAdapter(B2B_ROOT)
    a2 = B2BAdapter(B2B_ROOT)
    assert a1.pin.content_hash == a2.pin.content_hash


def test_full_chain_against_real_sut():
    # clear() only cancels CYCLES: a lone A->B edge has nothing to net against and
    # passes through unchanged, so this needs a genuine 2-cycle (A->B, B->A) for
    # apply_clearing to actually reduce anything (mirrors evals/tests.md B-04).
    adapter = _fresh_cell()
    adapter.record_obligation({"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 10_000}, ts=1)
    adapter.record_obligation({"id": "o2", "debtor": "B", "creditor": "A", "amount_cents": 10_000}, ts=1)

    proposal = adapter.run_clearing()
    assert proposal["net_positions"] == {"A": 0, "B": 0}
    assert proposal["metrics"]["cycles_cancelled"] == 1
    assert adapter.cell_metrics()["open_obligations"] == 2  # run_clearing must not touch state

    event = adapter.apply_clearing(proposal, ratified_by="ops", ts=2)
    assert event["kind"] == "clearing_applied"
    assert adapter.cell_metrics()["open_obligations"] == 0  # apply_clearing did


def test_adapter_never_swallows_a_real_rejection():
    adapter = _fresh_cell()
    with pytest.raises(ValueError):
        # C: not a member -> the real ledger rejects this; the adapter must not catch it
        adapter.record_obligation({"id": "o1", "debtor": "A", "creditor": "C", "amount_cents": 10_000}, ts=1)


def test_reapplying_a_proposal_raises_and_propagates():
    adapter = _fresh_cell()
    adapter.record_obligation({"id": "o1", "debtor": "A", "creditor": "B", "amount_cents": 10_000}, ts=1)
    proposal = adapter.run_clearing()
    adapter.apply_clearing(proposal, ratified_by="ops", ts=2)
    with pytest.raises(ValueError):
        adapter.apply_clearing(proposal, ratified_by="ops", ts=3)


def test_member_statement_is_read_only():
    adapter = _fresh_cell()
    before = adapter.member_statement("A", "comite_credito")
    adapter.member_statement("A", "comite_credito")
    after = adapter.member_statement("A", "comite_credito")
    assert before == after
