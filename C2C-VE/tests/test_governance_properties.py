"""Property-based tests (hypothesis) for the Capa-6 sociocratic governance.

Maps to workflows/micorriza-politica/capa6/evals/tests.md P1-P7. Deterministic and offline.
The properties assert the structural walls hold for ANY input: the verdict is invariant to reputation
(unrepresentable), a single paramount objection ALWAYS blocks however many consent, a weighted /
duplicate / surveillance-shaped input is ALWAYS refused, no objector token ever surfaces, and the
function never crashes on scoped content.
"""
import importlib.util
from pathlib import Path

from hypothesis import given, settings, strategies as st

_MOD = Path(__file__).resolve().parent.parent / "src" / "governance" / "governance.py"
_spec = importlib.util.spec_from_file_location("governance", _MOD)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)
decide = mod.decide
GovernanceBreachError = mod.GovernanceBreachError

FORBIDDEN = ("score", "rating", "reputation", "rank", "blacklist", "ban",
             "penalty", "global_id", "dni")
WEIGHT = ("weight", "shares", "voting_power", "vote_count", "tally", "majority",
          "percent", "proxy", "seats", "quorum")
NOW = "2026-07-07T00:00:00Z"
SOON = "2026-08-01T00:00:00Z"


def walk_values(o):
    if isinstance(o, dict):
        for v in o.values():
            yield from walk_values(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk_values(v)
    else:
        yield o


def _req(dispositions, circle="c1"):
    return {"circle_id": circle, "proposal_id": "p1", "now": NOW,
            "expires_at": SOON, "dispositions": dispositions}


tokens = st.text(alphabet="abcdefghijk", min_size=1, max_size=5)


@st.composite
def consent_disp(draw, token):
    return {"token": token, "disposition": draw(st.sampled_from(["consent", "abstain"])),
            "circle_id": "c1"}


def _unique_tokens(n):
    return ["tok%d" % i for i in range(n)]


# P1/P2 — a single paramount objection ALWAYS blocks, however many consent
@settings(max_examples=200)
@given(st.integers(min_value=0, max_value=20))
def test_p2_one_paramount_always_blocks(n_consent):
    disps = [{"token": t, "disposition": "consent", "circle_id": "c1"}
             for t in _unique_tokens(n_consent)]
    disps.append({"token": "blocker", "disposition": "object", "circle_id": "c1",
                  "objection": {"paramount": True, "reason": "r"}})
    out = decide(_req(disps))
    assert out["verdict"] == "revisit"


# P1 — verdict invariant to token labels / order (no weighting path)
@settings(max_examples=150)
@given(st.lists(tokens, min_size=0, max_size=8, unique=True), st.booleans())
def test_p1_verdict_only_depends_on_paramount(toks, add_block):
    disps = [{"token": t, "disposition": "consent", "circle_id": "c1"} for t in toks]
    if add_block:
        disps.append({"token": "zzz-block", "disposition": "object", "circle_id": "c1",
                      "objection": {"paramount": True, "reason": "r"}})
    out = decide(_req(disps))
    assert out["verdict"] == ("revisit" if add_block else "adopted")


# P3 — a weighted-voice key at any depth is always refused
@settings(max_examples=100)
@given(st.integers(min_value=0, max_value=3), st.sampled_from(WEIGHT))
def test_p3_weight_always_refused(depth, key):
    node = {key: 3}
    for _ in range(depth):
        node = {"nest": node}
    r = _req([{"token": "t1", "disposition": "consent", "circle_id": "c1"}])
    r["extra"] = node
    try:
        decide(r)
        assert False, "should refuse weighted voice"
    except GovernanceBreachError:
        pass


# P4 — a duplicate token is always refused
@settings(max_examples=100)
@given(st.integers(min_value=2, max_value=6))
def test_p4_duplicate_token_refused(n):
    disps = [{"token": "same", "disposition": "consent", "circle_id": "c1"} for _ in range(n)]
    try:
        decide(_req(disps))
        assert False, "should refuse duplicate token"
    except GovernanceBreachError:
        pass


# P5 — no objector token ever surfaces
@settings(max_examples=150)
@given(st.lists(tokens, min_size=1, max_size=8, unique=True))
def test_p5_no_objector_token_out(toks):
    disps = []
    for i, t in enumerate(toks):
        if i == 0:
            disps.append({"token": t, "disposition": "object", "circle_id": "c1",
                          "objection": {"paramount": True, "reason": "reason-" + t}})
        else:
            disps.append({"token": t, "disposition": "consent", "circle_id": "c1"})
    out = decide(_req(disps))
    values = list(walk_values(out))
    for t in toks:
        assert t not in values  # tokens never surface; only reasons do


# P6 — surveillance refused at any depth
@settings(max_examples=100)
@given(st.integers(min_value=0, max_value=3), st.sampled_from(FORBIDDEN))
def test_p6_surveillance_refused_any_depth(depth, key):
    node = {key: 1}
    for _ in range(depth):
        node = {"nest": node}
    r = _req([{"token": "t1", "disposition": "consent", "circle_id": "c1"}])
    r["extra"] = node
    try:
        decide(r)
        assert False, "should refuse surveillance shape"
    except GovernanceBreachError:
        pass


# P7 — never crashes on scoped content (off-circle / expired), only envelope raises
@settings(max_examples=150)
@given(st.lists(tokens, min_size=0, max_size=8, unique=True))
def test_p7_never_crashes_on_scoped_content(toks):
    disps = []
    for i, t in enumerate(toks):
        circle = "c1" if i % 2 == 0 else "c2"                 # some off-circle
        exp = SOON if i % 3 else "2000-01-01T00:00:00Z"       # some expired
        disps.append({"token": t, "disposition": "consent", "circle_id": circle,
                      "expires_at": exp})
    out = decide(_req(disps))
    assert out["verdict"] in ("adopted", "revisit")
