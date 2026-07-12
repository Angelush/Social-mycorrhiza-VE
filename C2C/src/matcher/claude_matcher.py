"""Capa-3 Claude-backed proposer — the injectable stochastic core behind matcher.match().

This module provides `make_claude_propose(...)`, which returns a `propose(context) -> list[dict]`
callable backed by Claude via the Anthropic SDK. It is the ONLY place the network/keys are
touched, and it is imported LAZILY: `anthropic` is imported inside the factory, never at module
top, so `src/matcher/matcher.py` (the deterministic wrapper) and the whole test suite stay
importable and runnable offline with a stub.

The model is a Tool-assistant capped at PROPOSAL level (architecture.md, FWK-030): it is handed
only the sanitized, eligible context the wrapper built, and it returns a bounded list of proposed
matches. It has NO tool that connects, notifies, ranks, or persists. Whatever it returns is
validated/bounded/canonically-sorted and dropped-if-bad by the deterministic wrapper — the model
is never trusted (see matcher.py). This client is a thin adapter; the guardrail lives in matcher.py.

Model choice: `claude-sonnet-5` — a proposal-appropriate tier for bounded offer/need/goal matching
(cost-conscious; the wrapper, not the model, is the correctness surface). Override via `model=`.

Provenance: written by Claude (claude-api skill), guardrailed by src/matcher/matcher.py.
"""

# The strict output schema the model must return. A person-scalar / engagement field cannot even
# be requested here — and if the model smuggles one anyway, matcher.py's scan drops that proposal.
_PROPOSAL_SCHEMA = {
    "type": "object",
    "properties": {
        "proposals": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "token": {"type": "string"},
                    "kind": {
                        "type": "string",
                        "enum": ["offer_meets_need", "shared_goal", "translation"],
                    },
                    "reason": {"type": "string"},
                },
                "required": ["token", "kind", "reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["proposals"],
    "additionalProperties": False,
}

_SYSTEM = (
    "You are the proposal-only core of a prosocial matcher (Micorriza Capa 3). "
    "You are given an asker's declared offers/needs/goals and a list of candidates who have "
    "CONSENTED to be surfaced, each with their own declared offers/needs/goals and cell_id. "
    "Propose a bounded list of candidate matches, each with a short human-readable reason a human "
    "will read before deciding whether to reach out. Kinds: 'offer_meets_need' (your offer meets "
    "their need or vice-versa), 'shared_goal' (you share a goal), 'translation' (a need bridged "
    "across two of the asker's own contexts). Rules you MUST follow: propose only candidates that "
    "appear in the given context (never invent a token); NEVER emit any score, rating, rank, "
    "reputation, or engagement/click/relevance number about anyone; the ORDER of your list carries "
    "no meaning (a downstream wrapper re-sorts it); your objective is cooperation initiated, never "
    "engagement. Propose, do not impose — a human disposes."
)


def make_claude_propose(model: str = "claude-sonnet-5", max_proposals_hint: int = 10,
                        client=None):
    """Return a `propose(context) -> list[dict]` callable backed by Claude.

    Lazily imports `anthropic` (never at module top). The returned callable is what you inject as
    the second argument to `matcher.match(request, propose)`. It returns raw proposals; the
    deterministic wrapper validates, drops, canonically-sorts, and bounds them.

    Args:
        model: Claude model id (proposal-appropriate tier).
        max_proposals_hint: soft hint to the model; the wrapper enforces the hard `max_proposals`.
        client: an optional pre-built Anthropic client (mainly for tests that want to inject a
            fake SDK client without importing anthropic).
    """
    def propose(context: dict) -> list:
        nonlocal client
        if client is None:
            import anthropic  # lazy — no network/keys unless this callable is actually invoked
            client = anthropic.Anthropic()

        import json
        user = (
            "Propose up to " + str(max_proposals_hint) + " matches for this asker.\n\n"
            + json.dumps(context, sort_keys=True, ensure_ascii=False)
        )
        # Structured output pins the shape; adaptive thinking per claude-api defaults.
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=_SYSTEM,
            messages=[{"role": "user", "content": user}],
            output_config={"format": {"type": "json_schema", "schema": _PROPOSAL_SCHEMA}},
        )
        text = next((b.text for b in response.content if getattr(b, "type", None) == "text"), "")
        try:
            parsed = json.loads(text)
        except (ValueError, TypeError):
            return []  # a wrapper that gets [] simply surfaces nothing — never a crash
        proposals = parsed.get("proposals") if isinstance(parsed, dict) else None
        return proposals if isinstance(proposals, list) else []

    return propose
