"""
CCA State Schema — replaces the Orchestrator class's instance variables.

Every field that Orchestrator stored as `self.X` becomes a field here.
The graph carries this dict through every node transition.
"""

from typing import TypedDict, Annotated, Optional
from langchain_core.messages import BaseMessage

# TODO 1 ─────────────────────────────────────────────────────────────────────
# Import the reducer you need for the conversation history fields.
# Hint: it lives in langgraph.graph.message and makes lists accumulate
#       (append) rather than replace on each node update.
#
# from ___ import ___


class CCAState(TypedDict):

    # ── Immutable inputs ──────────────────────────────────────────────────────
    # Set at invoke() time. No node should overwrite these.
    feature_request: str      # the original goal — never changes
    max_rounds: int           # how many E+L cycles to run

    # ── Turn tracking ─────────────────────────────────────────────────────────
    # Light increments this at the end of each round.
    round: int

    # ── Shared workspace ──────────────────────────────────────────────────────
    code: str                      # the latest code version
    last_critique: Optional[str]   # what the previous agent said

    # ── Per-agent conversation histories ──────────────────────────────────────
    # These need to ACCUMULATE across rounds, not be replaced.
    # A plain `list[BaseMessage]` would be replaced every time a node returns it.
    # You need to tell LangGraph to APPEND instead.
    #
    # TODO 2 ──────────────────────────────────────────────────────────────────
    # Complete the type annotation for edgeworth_history.
    # It holds a list of BaseMessage objects, and new messages should be
    # appended (not replaced) when a node returns this key.
    # Hint: use Annotated[___, ___] with your import from TODO 1.
    #
    edgeworth_history: ___

    # TODO 3 ──────────────────────────────────────────────────────────────────
    # Same thing for light_history.
    #
    light_history: ___
