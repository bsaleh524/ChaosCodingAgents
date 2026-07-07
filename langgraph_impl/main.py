"""
LangGraph entry point — replaces orchestrator.py + main.py.

The Orchestrator class and its for loop are gone.
State management, turn routing, and loop termination live in graph.py.
This file handles: CLI args, startup, initial state, and the stream observer.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
from datetime import datetime

import config
from orchestrator import _critique_block, _banner, BOLD, GREEN, DIM
from voice import say_as

from .graph import cca_app


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='CCA — LangGraph version')
    p.add_argument('--rounds', type=int, default=config.NUM_ROUNDS)
    p.add_argument('--voice', action='store_true', default=config.USE_VOICE)
    p.add_argument('--elevenlabs', action='store_true', default=False)
    p.add_argument('--obs', action='store_true', default=False)
    return p.parse_args()


def _get_feature_request() -> str:
    print('  Feature request:')
    return input('  > ').strip()


def run(feature_request: str, rounds: int) -> None:
    session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    graph_config = {'configurable': {'thread_id': session_id}}

    # TODO 16 ─────────────────────────────────────────────────────────────────
    # Build the initial state dict.
    #
    # Every field declared in CCAState must be present here.
    # Open langgraph_impl/state.py and go through each field.
    # Ask yourself: what is a sensible starting value for each one?
    #
    # Two things to think hard about:
    #   - What value should `round` start at?
    #   - What value should the history fields start with? (They're lists.)
    #
    initial_state = {
        ___
    }

    _banner(f'CHAOS CODING AGENTS  |  LangGraph  |  {rounds} round(s)', BOLD + GREEN)
    print(f'  Feature request: {feature_request}\n')

    # TODO 17 ─────────────────────────────────────────────────────────────────
    # Write the stream observer.
    #
    # cca_app.stream() yields one chunk per node transition.
    # Each chunk is a dict: {node_name: state_delta}
    # state_delta contains only the keys that node returned.
    #
    # For each chunk you need to:
    #   1. Get the node name and state delta out of the chunk
    #   2. If the delta has a 'last_critique', print it and speak it
    #      (say_as() handles OBS show/hide automatically)
    #   3. If the delta has 'code', you can print a brief progress note
    #
    # Hint for unpacking: chunk is {node_name: delta}, and there's always
    # exactly one key per chunk.
    #
    for chunk in cca_app.stream(initial_state, config=graph_config, stream_mode='updates'):
        ___

    _banner(f'Done — session {session_id}', DIM)


def main() -> None:
    args = parse_args()

    if args.voice or args.elevenlabs:
        config.USE_VOICE = True
    if args.elevenlabs:
        config.USE_ELEVENLABS = True
    if args.obs:
        config.USE_OBS = True
        from obs_manager import init_obs_manager
        init_obs_manager()

    feature_request = _get_feature_request()
    if not feature_request:
        print('No feature request. Exiting.')
        sys.exit(1)

    run(feature_request, args.rounds)


if __name__ == '__main__':
    main()
