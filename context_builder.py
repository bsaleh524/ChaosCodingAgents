"""
Builds the context package passed from one agent to the next.

This is the core of multi-agent communication — what you include here
determines how well agents coordinate.
"""


def build_context_package(
    feature_request: str,
    codebase: dict[str, str],
    previous_critique: str | None,
    agent_name: str,
    round_num: int,
) -> str:
    """
    Formats a single user message to send to the next agent.
    The message must give the agent everything it needs to:
      (a) know the original goal,
      (b) know what code currently exists,
      (c) know what the previous agent thought of it.

    Returns a formatted string ready to append to the agent's conversation history.
    """

    # TODO [LEARNING]: Build the context package passed to the next agent.
    # It should include the original feature request, the full current codebase,
    # and the previous agent's critique. This is the core of multi-agent
    # communication — what you include here determines how well agents coordinate.
    #
    # Once you implement this, the agents will start actually responding to each other.
    # That moment of real coordination is the payoff.
    #
    # Uncomment the solution below when you're ready:

    # ── Step 1: Flatten the codebase dict into a readable string ─────────────
    # The codebase is {filename: contents}. We want to show every file clearly
    # so the agent can see the full picture, not just one file.
    # We label each file with === markers so the agent knows where one ends and the next begins.
    #
    codebase_str = "\n\n".join(
        f"=== {fname} ===\n{contents}" # f-string: label + file contents
        for fname, contents in codebase.items() # iterate every file in the workspace
    )

    # ── Step 2: Handle the first-round case ──────────────────────────────────
    # On round 1 there is no previous critique yet — previous_critique will be None.
    # We need to handle that gracefully so the agent knows this is a clean slate.
    # A clear instruction is better than sending the word "None" to the model.
    #
    critique_selection = (
        previous_critique # use the real critque if it exists
        if previous_critique # Truthiness check: None or "" both fall through
        else "None - this is round 1. Write your first implementation."
    )

    # ── Step 3: Assemble the full context string ──────────────────────────────
    # This is the single string passed as a "user" message in the agent's
    # conversation history. The model reads this and uses it to decide what to write.
    #
    # The order matters: goal first, then current state, then criticism.
    # That mirrors how a human developer would think: "what do I need to build,
    # what's already there, and what's wrong with it?"
    #
    return (
        f"FEATURE REQUEST:\n{feature_request}\n\n"              # the original goal - never changes
        f"CURRENT CODEBASE:\n{codebase_str}\n\n"                # what's in the workspace right now
        f"PREVIOUS AGENT'S CRITIQUE:\n{critique_selection}\n\n" # what the other agent complained about
        f"ROUND: {round_num}\n"                                 # lets the agent know how far along we are
        f"YOUR TURN: {agent_name}"                              # explcitit instruction on who is acting
    )
