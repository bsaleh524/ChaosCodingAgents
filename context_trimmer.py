"""
Trims agent conversation histories to stay within token limits.

As rounds accumulate, each agent's history grows. Without trimming,
you'll hit the model's context window. This module provides the strategy.
"""


def trim_conversation_history(
    history: list[dict],
    max_tokens: int,
    feature_request: str,
) -> list[dict]:
    """
    Returns a trimmed copy of `history` that fits within `max_tokens`.

    The trimmer must always preserve:
      - The first message (the original feature request / first user turn)
      - The most recent N exchanges

    Everything in the middle can be summarised, compressed, or dropped.

    Args:
        history:         List of {"role": "user"|"assistant", "content": str} dicts.
        max_tokens:      Soft upper bound on estimated tokens in the returned history.
        feature_request: The original feature request — always preserved if the
                         first message is dropped or summarised.

    Returns:
        A list of message dicts safe to pass directly to the Anthropic API.
    """

    # TODO [LEARNING]: As rounds accumulate, context grows and you'll hit token limits.
    # Implement a trimmer that summarises or drops older turns while preserving
    # the most recent exchanges and the original request. This is a real problem
    # in production agentic systems.
    #
    # The key invariant: the agent must always be able to see the original request
    # and the most recent state of the codebase. Those two things are non-negotiable.
    #
    # Uncomment the solution below when you're ready:

    # ── Step 1: Short-circuit if history is already small enough ─────────────
    # No point trimming if we're under budget. Check first to avoid unnecessary work.
    # Token estimation: dividing character count by 4 is a widely-used rough rule
    # (GPT/Claude tokenizers average ~4 chars per token in English code).
    #
    # def estimate_tokens(msgs: list[dict]) -> int:
    #     return sum(len(m["content"]) // 4 for m in msgs)  # sum token estimates across all messages
    #
    # if not history:                          # empty history — nothing to trim
    #     return history
    #
    # if estimate_tokens(history) <= max_tokens:   # already under budget — return as-is
    #     return history

    # ── Step 2: Identify which messages to always keep ───────────────────────
    # We anchor on two ends of the history:
    #   - history[0]   = first user message (the original feature request context)
    #                    Losing this means the agent forgets what it's building.
    #   - history[-4:] = last 2 full exchanges (user+assistant pairs)
    #                    Losing these means the agent loses immediate context.
    # Everything between them is the "droppable middle".
    #
    # first = history[:1]                      # always keep the very first message
    # tail  = history[-4:] if len(history) > 5 else history[1:]  # last 2 exchanges, skip first to avoid dupe

    # ── Step 3: Build the trimmed list and re-check ───────────────────────────
    # Combine anchor + tail, dropping the middle entirely.
    # If that's still too long (rare — means even 2 exchanges are huge),
    # fall back to just the tail so we at least have recent context.
    #
    # trimmed = first + tail                   # anchor + recent exchanges, middle dropped
    #
    # if estimate_tokens(trimmed) > max_tokens:    # still too big (very large exchanges)
    #     trimmed = tail                           # last resort: drop even the first message
    #
    # return trimmed

    pass
