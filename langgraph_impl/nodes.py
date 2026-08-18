"""
LangGraph node functions — one per agent.

Each node signature is: (state: CCAState) -> dict
The returned dict is a PARTIAL state update — only the keys you include are changed.
Keys you don't return stay at their current values.
"""

import sys
import os
import re
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from context_builder import build_context_package
from agents import EDGEWORTH_SYSTEM, EDGEWORTH_DRIFT, LIGHT_SYSTEM, LIGHT_DRIFT, INTERN_SYSTEM
from .state import CCAState

AGENT_MODEL = 'claude-sonnet-4-6'
INTERN_MODEL = 'claude-haiku-4-5-20251001'


def _extract(text: str, tag: str) -> str:
    m = re.search(rf'<{tag}>(.*?)</{tag}>', text, re.DOTALL)
    return m.group(1).strip() if m else ''


# ── Edgeworth node ─────────────────────────────────────────────────────────────

def edgeworth_node(state: CCAState) -> dict:
    r = state['round']
    system_text = EDGEWORTH_SYSTEM + (EDGEWORTH_DRIFT if r >= 3 else '')

    pkg = build_context_package(
        feature_request=state['feature_request'],
        codebase={'solution.py': state.get('code', '')},
        previous_critique=state.get('last_critique'),
        agent_name='EDGEWORTH',
        round_num=r,
    )

    # TODO 4 ──────────────────────────────────────────────────────────────────
    # Wrap `pkg` (a plain string) in the correct LangChain message type.
    # This is a message from the "user" (the orchestrator giving context to the agent).
    # Hint: you imported message types at the top of this file.
    #
    new_user_msg = HumanMessage(content=pkg)

    # TODO 5 ──────────────────────────────────────────────────────────────────
    # Build the full message list to pass to the LLM.
    # It needs three parts in order:
    #   1. A system message with Edgeworth's personality + drift directive
    #   2. The existing conversation history for this agent
    #   3. The new user message you just built above
    #
    # Note: existing history comes from state — it's already a list of messages.
    #
    all_msgs = [SystemMessage(content=system_text)] +\
        state.get('edgeworth_history', []) + [new_user_msg]

    model = ChatAnthropic(model=AGENT_MODEL, max_tokens=8192)
    response = model.invoke(all_msgs)

    code = _extract(response.content, 'code')
    critique = _extract(response.content, 'critique')

    # TODO 6 ──────────────────────────────────────────────────────────────────
    # Return the partial state update.
    # Think through each key:
    #   - What did Edgeworth produce that the workspace needs?
    #   - What does Light need to see from Edgeworth before his turn?
    #   - How do you add the new messages to the history WITHOUT replacing it?
    #     (Return the new messages — the reducer handles the append.)
    #
    return {
        'code': code,
        'last_critique': critique,
        'edgeworth_history': [new_user_msg, response]
    }


# ── Light node ─────────────────────────────────────────────────────────────────

def light_node(state: CCAState) -> dict:
    r = state['round']
    system_text = LIGHT_SYSTEM + (LIGHT_DRIFT if r >= 3 else '')

    pkg = build_context_package(
        feature_request=state['feature_request'],
        codebase={'solution.py': state.get('code', '')},
        previous_critique=state.get('last_critique'),
        agent_name='LIGHT',
        round_num=r,
    )

    # TODO 7 ──────────────────────────────────────────────────────────────────
    # Same pattern as edgeworth_node TODOs 4 and 5.
    # Build new_user_msg and all_msgs for Light's LLM call.
    # Note: use state['light_history'], not edgeworth_history.
    #
    new_user_msg = HumanMessage(content=pkg)
    all_msgs = [SystemMessage(content=system_text)] +\
        state.get('light_history', []) + [new_user_msg]

    model = ChatAnthropic(model=AGENT_MODEL, max_tokens=8192)
    response = model.invoke(all_msgs)

    code = _extract(response.content, 'code')
    critique = _extract(response.content, 'critique')

    # TODO 8 ──────────────────────────────────────────────────────────────────
    # Return the partial state update — same keys as Edgeworth, PLUS one more.
    # Light is the one who ends a round. What counter needs to increment here,
    # and who is responsible for incrementing it?
    #
    return {
        'code': code,
        'last_critique': critique,
        'light_history': [new_user_msg, response],
        'round': r+1
    }


# ── Intern node (terminal) ─────────────────────────────────────────────────────

def intern_node(state: CCAState) -> dict:
    print('\n[INTERN] Oh god oh god you\'re back —')

    model = ChatAnthropic(model=INTERN_MODEL, max_tokens=2048)
    response = model.invoke([
        SystemMessage(content=INTERN_SYSTEM),
        HumanMessage(content=(
            f'ORIGINAL FEATURE REQUEST:\n{state["feature_request"]}\n\n'
            f'FINAL CODE:\n{state.get("code", "")}'
        )),
    ])
    print(response.content)

    # TODO 9 ──────────────────────────────────────────────────────────────────
    # What should the terminal node return?
    # The Intern doesn't produce code or a critique.
    # Returning nothing at all is a valid answer — what does that look like?
    #
    return {'intern_summary': response.content}
