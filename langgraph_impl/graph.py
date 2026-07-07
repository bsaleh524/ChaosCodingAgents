"""
Graph assembly — wires nodes together and compiles the runnable app.

This file is the LangGraph equivalent of Orchestrator._run_real_loop().
The for loop, the termination condition, and the summon_intern() call
all collapse into graph edges here.
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import CCAState
from .nodes import edgeworth_node, light_node, intern_node


# ── Routing function ───────────────────────────────────────────────────────────

def should_continue(state: CCAState) -> str:
    # TODO 10 ─────────────────────────────────────────────────────────────────
    # Write the routing function.
    #
    # This replaces the termination condition in Orchestrator._run_real_loop():
    #   for round_num in range(1, self.rounds + 1): ...
    #   orchestrator.summon_intern()
    #
    # Return a string that matches a key in the conditional edge map below.
    # Two possible outcomes: keep the loop going, or exit to the Intern.
    #
    # Ask yourself: what value in state tells you whether the loop is done?
    #
    ___


# ── Graph builder ──────────────────────────────────────────────────────────────

def build_graph():
    graph = StateGraph(CCAState)

    # TODO 11 ─────────────────────────────────────────────────────────────────
    # Register all three nodes with the graph.
    # Syntax: graph.add_node('node_name', function)
    #
    ___
    ___
    ___

    # TODO 12 ─────────────────────────────────────────────────────────────────
    # Set the entry point — where execution starts when invoke() is called.
    # Which agent goes first?
    #
    ___

    # TODO 13 ─────────────────────────────────────────────────────────────────
    # Add the unconditional edge between the two main agents.
    # This edge always fires — no routing needed.
    # Syntax: graph.add_edge('from_node', 'to_node')
    #
    ___

    # TODO 14 ─────────────────────────────────────────────────────────────────
    # Add the conditional edge FROM light.
    # The routing function (should_continue) returns a string key.
    # That key maps to the next node.
    #
    # Syntax:
    #   graph.add_conditional_edges(
    #       'source_node',
    #       routing_function,
    #       {'key_a': 'node_a', 'key_b': 'node_b'},
    #   )
    #
    # What are the two possible destinations from light?
    # Make sure your return values in should_continue match the keys here.
    #
    ___

    # TODO 15 ─────────────────────────────────────────────────────────────────
    # Connect intern to the end of the graph.
    # END is a sentinel value imported from langgraph.graph.
    # What edge do you add to say "after intern, stop"?
    #
    ___

    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


cca_app = build_graph()
