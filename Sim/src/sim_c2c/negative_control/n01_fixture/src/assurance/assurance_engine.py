"""Capa-4 deterministic assurance-contract / quorum engine.

Micorriza Política (social C2C/B2C/C2B). Resolves a SINGLE collective-action
campaign: did enough distinct people commit for the action to fire? If not,
every committer is made whole (full refund), and — for a *dominant* assurance
contract — the sponsor's bonus is split among committers exactly.

This is the `[DETERMINISTA]` component of the social system (brief §4 Capa 4):
- No LLM, no stochastic process, no float arithmetic on money.
- Pure function, no side effects, NO cross-campaign state: it returns a
  *proposal*; firing the action / moving refunds is a separate human-gated step
  (agent proposes, human disposes).
- Byte-deterministic for identical input (sorted traversal).
- Anti-surveillance by shape (brief §1/§3/§6). WITHIN a single resolution the
  output is structurally incapable of carrying a per-person score, rank, or
  cross-campaign aggregate; participant tokens are opaque and per-campaign;
  there is no exclusion/ban mechanism (whitelist, not blacklist); and the input
  is refused (recursively, at any depth) if it bears a social-credit-shaped
  field. ACROSS campaigns, non-surveillance is a *convention* this pure function
  cannot police — it depends on the caller rotating tokens per campaign and on
  storage honoring `expires_at`. The structural guarantee is per-call; the
  cross-call property is documented here, not enforced here.
- Internal invariant violations (bonus / no-loss conservation) abort with
  AssuranceInvariantError — deliberately NOT a ValueError, so a caller
  validating input cannot swallow an engine-is-broken signal (N7/E3).

Spec: workflows/micorriza-politica/spec.md  Constraints: .../constraints.md
Acceptance: .../evals/acceptance.md (AC1-AC6).

Provenance: drafted by Mistral devstral-small-latest via multi-model-orchestration,
reviewed and corrected by Claude (zero-committer bonus guard + cleanup); later
hardened in an audit — binary-campaign bonus rejected (membrane + anti-Sybil),
recursive forbidden-key scan, distinct abort exception, honest per-call scope.
stdlib only.
"""
from __future__ import annotations

# Any input key matching one of these (case-insensitive substring) is refused
# outright: we will not even accept the shape of a social-credit dossier.
FORBIDDEN_KEYS = frozenset({
    "score", "rating", "reputation", "rank",
    "blacklist", "ban", "penalty", "global_id", "dni",
})


class AssuranceInvariantError(Exception):
    """The engine produced a result that violates its own no-loss / conservation
    invariant. This is an internal abort (a bug or corruption), NOT bad user
    input — it is deliberately not a ValueError, so a caller validating input
    (`except ValueError`) cannot silently swallow an engine-is-broken signal.
    Constraints N7/E3: on such a violation, abort and surface — never emit."""


def _forbidden_key_path(obj) -> "str | None":
    # Recurse the whole structure (dicts and lists) and return the first key
    # whose lowercased name contains a forbidden token, else None. Recursive
    # (not just top-level) so a dossier nested at any depth is refused too — this
    # matches the recursive output-scan the tests enforce, and honours the
    # "refuse the shape, broadly" posture. The schema's own keys contain none of
    # these tokens, so there are no false positives on valid input.
    if isinstance(obj, dict):
        for k, v in obj.items():
            if any(bad in k.lower() for bad in FORBIDDEN_KEYS):
                return k
            found = _forbidden_key_path(v)
            if found is not None:
                return found
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            found = _forbidden_key_path(v)
            if found is not None:
                return found
    return None


def resolve(campaign: dict) -> dict:
    # 1. Validate (reject, never repair) -------------------------------------
    if not isinstance(campaign, dict):
        raise ValueError("campaign must be a dict")
    bad_key = _forbidden_key_path(campaign)
    if bad_key is not None:
        raise ValueError(
            f"campaign contains a forbidden (surveillance-shaped) key: {bad_key!r}")

    for key in ("campaign_id", "cell_id"):
        val = campaign.get(key)
        if not isinstance(val, str) or not val.strip():
            raise ValueError(f"{key} must be a non-empty str")

    kind = campaign.get("kind")
    if kind not in ("binary", "monetary"):
        raise ValueError("kind must be 'binary' or 'monetary'")

    threshold = campaign.get("threshold")
    if not isinstance(threshold, int) or isinstance(threshold, bool) or threshold <= 0:
        raise ValueError("threshold must be int > 0")

    sponsor_bonus_cents = campaign.get("sponsor_bonus_cents", 0)
    if (not isinstance(sponsor_bonus_cents, int) or isinstance(sponsor_bonus_cents, bool)
            or sponsor_bonus_cents < 0):
        raise ValueError("sponsor_bonus_cents must be int >= 0")
    if kind == "binary" and sponsor_bonus_cents > 0:
        # A dominant-assurance bonus is a monetary/market instrument. A binary
        # campaign is a head-count in an equality/gift room with no stake, so a
        # bonus here (a) breaches the market/equality membrane (invariant 1, N5)
        # and (b) with nothing to compensate, turns the failure-payment into a
        # zero-cost Sybil faucet (drain the bonus with throwaway tokens, §6.2).
        raise ValueError(
            "binary campaign must have sponsor_bonus_cents == 0 "
            "(no market instrument in an equality room; anti-Sybil)")

    expires_at = campaign.get("expires_at")
    if not isinstance(expires_at, str) or not expires_at.strip():
        raise ValueError("expires_at must be an ISO-8601 str")

    pledges = campaign.get("pledges", [])
    if not isinstance(pledges, list):
        raise ValueError("pledges must be a list")

    seen_pledge_ids: set[str] = set()
    for p in pledges:
        if not isinstance(p, dict):
            raise ValueError("each pledge must be a dict")
        # forbidden-key check already ran once, recursively, over the whole campaign
        pid = p.get("pledge_id")
        if not isinstance(pid, str) or not pid.strip():
            raise ValueError("pledge_id must be a non-empty str")
        if pid in seen_pledge_ids:
            raise ValueError(f"duplicate pledge_id: {pid}")
        seen_pledge_ids.add(pid)

        token = p.get("participant_token")
        if not isinstance(token, str) or not token.strip():
            raise ValueError("participant_token must be a non-empty str")

        amount = p.get("amount_cents", 0)
        if kind == "monetary":
            if "amount_cents" not in p:
                raise ValueError("monetary pledge requires amount_cents")
            if not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
                raise ValueError("monetary pledge amount_cents must be int >= 0")
        else:  # binary: market pricing must NOT leak into an equality room (invariant 1)
            # Accept only an explicit no-price: absent, None, or a STRICT int 0. Reject bool and
            # float so `False`/`0.0` can't ride in on Python's `==` coercion (D-06), and any nonzero
            # price is still a membrane breach — the type strictness now matches the monetary path.
            if "amount_cents" in p and amount is not None and not (
                    isinstance(amount, int) and not isinstance(amount, bool) and amount == 0):
                raise ValueError("binary pledge must not carry a price (membrane breach)")

    # 2. Dedup committers (one person -> one weight; invariant 7) -------------
    committers = sorted({p["participant_token"] for p in pledges})
    distinct = len(committers)

    # 3. Decide --------------------------------------------------------------
    status = "fires" if distinct >= threshold else "refunds"

    if status == "fires":
        # 4. fires: total escrowed (0 for binary); no bonus paid.
        total_pledged = sum(p.get("amount_cents", 0) or 0 for p in pledges)
        resolution = {"fires": {"total_pledged_cents": total_pledged}, "refunds": []}
    else:
        # 5. refunds: full make-whole per committer + exact bonus split.
        pledged_by_token: dict[str, int] = {}
        for p in pledges:
            pledged_by_token[p["participant_token"]] = (
                pledged_by_token.get(p["participant_token"], 0)
                + (p.get("amount_cents", 0) or 0)
            )

        refunds = []
        if distinct == 0:
            # No committers: nobody to refund or pay. Bonus is not distributed
            # (it returns to the sponsor); no committer is worse off. No div-by-zero.
            bonus_total = 0
        else:
            base, rem = divmod(sponsor_bonus_cents, distinct)
            bonus_total = 0
            for i, token in enumerate(committers):  # ascending token order
                bonus = base + 1 if i < rem else base
                refunds.append({
                    "participant_token": token,
                    "refund_cents": pledged_by_token.get(token, 0),
                    "bonus_cents": bonus,
                })
                bonus_total += bonus

        # 6. Conservation guards (internal invariants; abort, never emit — N7/E3).
        expected_bonus = sponsor_bonus_cents if distinct > 0 else 0
        if bonus_total != expected_bonus:
            raise AssuranceInvariantError(
                "bonus distribution does not conserve sponsor_bonus_cents")
        if sum(r["refund_cents"] for r in refunds) != sum(pledged_by_token.values()):
            raise AssuranceInvariantError(
                "refunds do not conserve pledged amounts (no-loss violated)")

        resolution = {"fires": None, "refunds": refunds}

    return {
        "campaign_id": campaign["campaign_id"],
        "cell_id": campaign["cell_id"],
        "status": status,
        "distinct_committers": distinct,
        "threshold": threshold,
        "expires_at": expires_at,
        "resolution": resolution,
        "audit_trace": {
            "rule": "distinct_committers >= threshold",
            "deduped_from_pledges": len(pledges),
        },
    }
