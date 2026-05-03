"""
Turn orchestrator — manages the Edgeworth ↔ Light loop and terminal output.

PLACEHOLDER MODE  → _run_placeholder_loop() — fully implemented, no LLM needed.
REAL MODE         → _run_real_loop()         — TODO: implement the turn logic.
"""

import time
from pathlib import Path

import config
from config import (
    MAX_CONTEXT_TOKENS,
    NUM_ROUNDS,
    SOLUTION_FILE,
    USE_VOICE,
    WORKSPACE_DIR,
)
from agents import edgeworth_turn, intern_summary, light_turn
from context_builder import build_context_package
from context_trimmer import trim_conversation_history
from workspace_manager import WorkspaceManager


# ── Terminal formatting helpers ───────────────────────────────────────────────

RESET   = "\033[0m"
BOLD    = "\033[1m"
CYAN    = "\033[96m"
MAGENTA = "\033[95m"
GREEN   = "\033[92m"
RED     = "\033[91m"
YELLOW  = "\033[93m"
DIM     = "\033[2m"

def _banner(text: str, color: str = BOLD) -> None:
    print(f"\n{color}{'─' * 60}{RESET}")
    print(f"{color}{text}{RESET}")
    print(f"{color}{'─' * 60}{RESET}\n")

def _label(agent: str, msg: str) -> None:
    color = CYAN if agent == "EDGEWORTH" else MAGENTA
    print(f"{BOLD}{color}[{agent}]{RESET} {msg}")

def _critique_block(agent: str, critique: str) -> None:
    color = CYAN if agent == "EDGEWORTH" else MAGENTA
    print(f"\n{color}{'┄' * 50}{RESET}")
    for line in critique.strip().splitlines():
        print(f"  {color}│{RESET} {line}")
    print(f"{color}{'┄' * 50}{RESET}\n")


# ── Orchestrator ──────────────────────────────────────────────────────────────

class Orchestrator:
    def __init__(
        self,
        feature_request: str,
        rounds: int = NUM_ROUNDS,
        use_voice: bool = USE_VOICE,
        workspace_dir: Path = WORKSPACE_DIR,
    ):
        self.feature_request = feature_request
        self.rounds = rounds
        self.use_voice = use_voice

        self.ws = WorkspaceManager(workspace_dir)

        # Conversation histories — each agent maintains its own thread
        self.edgeworth_history: list[dict] = []
        self.light_history: list[dict] = []

        # Shared state written by the loop, read by Intern and Feedback mode
        self.last_critique: str | None = None
        self.rounds_completed: int = 0

    # ── Public entry points ───────────────────────────────────────────────────

    def run(self) -> None:
        _banner(f"CHAOS CODING AGENTS  |  {self.rounds} round(s)  |  {'PLACEHOLDER' if config.PLACEHOLDER_MODE else 'LLM'} mode", BOLD + GREEN)
        print(f"  Feature request: {self.feature_request}\n")

        if config.PLACEHOLDER_MODE:
            self._run_placeholder_loop()
        else:
            self._run_real_loop()

    def summon_intern(self) -> None:
        _banner("[ INTERN ACTIVATED ]", BOLD + RED)
        print(f"{RED}Oh god oh god you're back —{RESET}\n")
        time.sleep(0.4)
        codebase = self.ws.read_workspace()
        summary = intern_summary(self.feature_request, codebase, self.use_voice)
        print(summary)
        print()

    # ── Placeholder loop — fully working, no LLM ─────────────────────────────

    def _run_placeholder_loop(self) -> None:
        for round_num in range(1, self.rounds + 1):
            # ── Edgeworth turn ────────────────────────────────────────────────
            _label("EDGEWORTH", f"Round {round_num} — rewriting...")
            time.sleep(0.6)

            code, critique = edgeworth_turn(
                context_package="",
                history=self.edgeworth_history,
                round_num=round_num,
                use_voice=self.use_voice,
            )

            self.ws.write_solution(code, SOLUTION_FILE)
            _critique_block("EDGEWORTH", critique)
            self.last_critique = critique

            # ── Light turn ────────────────────────────────────────────────────
            _label("LIGHT", f"Round {round_num} — rewriting...")
            time.sleep(0.6)

            code, critique = light_turn(
                context_package="",
                history=self.light_history,
                round_num=round_num,
                use_voice=self.use_voice,
            )

            self.ws.write_solution(code, SOLUTION_FILE)
            _critique_block("LIGHT", critique)
            self.last_critique = critique
            self.rounds_completed = round_num

        _banner(f"Loop complete — {self.rounds_completed} round(s) done.", DIM)

    # ── Real loop — TODO ──────────────────────────────────────────────────────

    def _run_real_loop(self) -> None:
        # TODO [LEARNING]: Implement the turn orchestrator.
        # It should track whose turn it is, invoke the correct agent, collect output,
        # and decide whether to continue or halt. This is the backbone of any
        # multi-agent system — the piece that coordinates all other pieces.
        #
        # Implement context_builder.py FIRST — this loop calls build_context_package()
        # and the agents won't coordinate properly without it.
        #
        # Uncomment the solution below when you're ready:

        # ── Step 1: Outer loop — iterate over N rounds ────────────────────────
        # Each round = one Edgeworth turn + one Light turn.
        # range(1, self.rounds + 1) gives us 1-indexed round numbers for display.
        #
        for round_num in range(1, self.rounds + 1):           # count from 1 for human-readable output

        #     # ── Edgeworth turn ─────────────────────────────────────────────
            _label("EDGEWORTH", f"Round {round_num} — rewriting...")

        #     # Step 2: Read workspace — agents always see the LATEST files, not a cached copy.
        #     # This is what makes the loop stateful: each agent reads what the other just wrote.
            codebase = self.ws.read_workspace()               # {filename: contents} of session folder

        #     # Step 3: Build the context package — this is TODO #1.
        #     # Without it the agent only sees an empty string and can't coordinate.
            pkg = build_context_package(                      # formats the user message for the LLM
                feature_request=self.feature_request,         # the original goal — never changes
                codebase=codebase,                            # what's currently in the workspace
                previous_critique=self.last_critique,         # what Light said last (or None on round 1)
                agent_name="EDGEWORTH",                       # tells the agent who it is
                round_num=round_num,                          # tells the agent how far along we are
            )

        #     # Step 4: Trim history before calling the agent — this is TODO #3.
        #     # or-fallback keeps the untrimmed history if trim returns None (not yet implemented).
            self.edgeworth_history = (                        # replace history with trimmed version
                trim_conversation_history(                    # trims to stay under MAX_CONTEXT_TOKENS
                    self.edgeworth_history,
                    MAX_CONTEXT_TOKENS,
                    self.feature_request,
                ) or self.edgeworth_history                   # fallback: keep original if trimmer returns None
            )

        #     # Step 5: Call the agent — returns (code_string, critique_string).
        #     # The history list is mutated in-place inside edgeworth_turn.
            code, critique = edgeworth_turn(                  # LLM call — returns parsed <code> and <critique>
                pkg, self.edgeworth_history, round_num, self.use_voice
            )

        #     # Step 6: Write code to the session folder.
            self.ws.write_solution(code, SOLUTION_FILE)       # writes to workspace/<session>/solution.py

        #     # Step 7: Print critique + store it for the next agent's context package.
            _critique_block("EDGEWORTH", critique)            # prints the critique in a styled block
            self.last_critique = critique                     # stored so Light receives it next turn

        #     # ── Light turn ──────────────────────────────────────────────────
        #     # Exact same pattern as Edgeworth above, but:
        #     #   - reads the workspace AGAIN (sees what Edgeworth just wrote)
        #     #   - passes "LIGHT" as agent_name
        #     #   - uses light_history (separate thread from edgeworth_history)
        #     #   - calls light_turn() instead of edgeworth_turn()
            _label("LIGHT", f"Round {round_num} — rewriting...")

            codebase = self.ws.read_workspace()               # re-read: Light sees Edgeworth's latest code
            pkg = build_context_package(
                feature_request=self.feature_request,
                codebase=codebase,
                previous_critique=self.last_critique,         # Edgeworth's critique from just above
                agent_name="LIGHT",
                round_num=round_num,
            )
            self.light_history = (
                trim_conversation_history(
                    self.light_history, MAX_CONTEXT_TOKENS, self.feature_request
                ) or self.light_history
            )
            code, critique = light_turn(
                pkg, self.light_history, round_num, self.use_voice
            )
            self.ws.write_solution(code, SOLUTION_FILE)       # Light overwrites with his version

            _critique_block("LIGHT", critique)
            self.last_critique = critique                     # stored so Edgeworth receives it next round
            self.rounds_completed = round_num                 # track progress for the Intern summary

        _banner(f"Loop complete — {self.rounds_completed} round(s) done.", DIM)
