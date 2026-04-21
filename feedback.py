"""
Interactive feedback mode — activated after the Intern's summary.

Basem speaks (or types) feedback. Both agents respond in character.
Agents can react to each other's responses across rounds.

Press  f + Enter  →  record/type feedback
Press  q + Enter  →  exit feedback mode
"""

import time
from config import PLACEHOLDER_MODE, USE_VOICE, MODEL_AGENTS
from voice import listen, say_as


# ── Placeholder feedback responses ────────────────────────────────────────────

_EDGEWORTH_FEEDBACK_PLACEHOLDER = [
    "Your concern about readability is noted and summarily dismissed. "
    "Clarity is for people who can't be bothered to understand proper engineering.",

    "I appreciate that you're trying to give feedback, but what you've described "
    "is simply how correct software is structured. The confusion is on your end.",

    "If the solution feels over-engineered, that's a reflection of the problem's "
    "actual complexity — which you may not have fully appreciated when you wrote the request.",
]

_SPARKS_FEEDBACK_PLACEHOLDER = [
    "THANK YOU. Finally someone gets it. "
    "Edgeworth's version was a masterclass in solving the wrong problem elegantly.",

    "Okay okay okay — so what you're saying is you want it simpler? "
    "I can do simpler. I already made it simpler. Did nobody look at my version??",

    "I knew the batch processing was a good call. "
    "I KNEW it. Edgeworth said it was scope creep but look — LOOK — it's useful.",
]

_EDGEWORTH_FEEDBACK_REACTS = [
    "Sparks' response confirms what I already knew: "
    "enthusiasm without discipline produces exactly this kind of chaos.",

    "I'll refrain from dignifying that with a full reply. "
    "Note that my architecture still stands. Sparks' excitement changes nothing structurally.",
]

_SPARKS_FEEDBACK_REACTS = [
    "Can you BELIEVE him?? 'Dismissed.' "
    "That's not a rebuttal, that's just — that's just being rude with extra steps.",

    "He literally just said the confusion is on your end. "
    "I'm sorry, but wow. Okay. Fine. I'm fine.",
]


# ── Real feedback responses ───────────────────────────────────────────────────

def _real_feedback_response(
    agent_name: str,
    system_prompt: str,
    history: list[dict],
    feedback_text: str,
    other_agent_response: str | None,
) -> str:
    import anthropic
    client = anthropic.Anthropic()

    content = f"USER FEEDBACK: {feedback_text}"
    if other_agent_response:
        other = "Sparks" if agent_name == "EDGEWORTH" else "Edgeworth"
        content += f"\n\n{other.upper()} JUST SAID:\n{other_agent_response}"
        content += "\n\nRespond to the feedback (and optionally to what they said). 2–4 sentences, in character. No code."
    else:
        content += "\n\nRespond in character. 2–4 sentences. No code rewrites."

    msgs = history + [{"role": "user", "content": content}]
    resp = client.messages.create(
        model=MODEL_AGENTS,
        max_tokens=512,
        system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
        messages=msgs,
    )
    reply = resp.content[0].text.strip()
    history.append({"role": "user", "content": content})
    history.append({"role": "assistant", "content": reply})
    return reply


def route_feedback_to_agents(
    feedback_text: str,
    edgeworth_history: list[dict],
    sparks_history: list[dict],
    previous_responses: dict[str, str] | None = None,
) -> tuple[str, str]:
    """
    Sends Basem's feedback to both agents and returns (edgeworth_reply, sparks_reply).

    Each agent receives: the feedback text, their own conversation history,
    and optionally what the other agent said in the previous feedback round.

    # TODO [LEARNING]: Route feedback to both agents independently.
    # Each should receive: the feedback text, their own conversation history,
    # and their personality prompt. Consider whether showing one agent's reply
    # to the other before they respond changes the dynamic — it would in a
    # real multi-agent setup.
    #
    # Hint: This function should:
    #   1. Format a user message for each agent containing the feedback
    #      (and optionally the other agent's previous response from `previous_responses`)
    #   2. Call the Anthropic API for each agent using their respective system prompts
    #      (import EDGEWORTH_SYSTEM and SPARKS_SYSTEM from agents.py)
    #   3. Return (edgeworth_response, sparks_response) as plain text strings
    #   4. Append both responses to their respective histories so future turns
    #      and future feedback rounds have context
    #
    # Fan-out pattern: one input → two independent recipients → two independent replies.
    # Each agent maintains its own thread; neither knows what the other is thinking
    # until you pass `previous_responses` from the previous round.
    # That choice — synchronous vs. independent — changes the dynamic significantly.
    #
    # Uncomment the solution below when you're ready:

    # ── Step 1: Import the personality prompts ────────────────────────────────
    # Each agent needs its own system prompt so it stays in character.
    # These live in agents.py alongside the rest of the agent definitions.
    #
    # from agents import EDGEWORTH_SYSTEM, SPARKS_SYSTEM  # import both personality prompts

    # ── Step 2: Call Edgeworth with his history + the feedback ───────────────
    # _real_feedback_response() is already implemented above — it handles the
    # API call, appends to history, and returns the reply text.
    # We pass Edgeworth's OWN history (not Sparks') so their context threads stay separate.
    # other_agent_response lets Edgeworth react to what Sparks said last round, if anything.
    #
    # e_reply = _real_feedback_response(
    #     agent_name="EDGEWORTH",                                      # used to label the "other" agent in the prompt
    #     system_prompt=EDGEWORTH_SYSTEM,                              # Edgeworth's personality
    #     history=edgeworth_history,                                   # Edgeworth's own conversation thread
    #     feedback_text=feedback_text,                                 # what Basem just said
    #     other_agent_response=(                                       # what Sparks said last round (or None)
    #         previous_responses.get("sparks") if previous_responses else None
    #     ),
    # )

    # ── Step 3: Call Sparks with her history + the feedback ──────────────────
    # Exact same pattern as Edgeworth but with Sparks' system prompt and history.
    # Sparks sees what Edgeworth said last round (if anything) — not what he just said.
    # Both agents are called independently, so neither waits on the other.
    # This is the "fan-out": one input triggers two separate, parallel agent calls.
    #
    # s_reply = _real_feedback_response(
    #     agent_name="SPARKS",                                         # used to label the "other" agent in the prompt
    #     system_prompt=SPARKS_SYSTEM,                                 # Sparks' personality
    #     history=sparks_history,                                      # Sparks' own conversation thread
    #     feedback_text=feedback_text,                                 # same feedback Basem gave
    #     other_agent_response=(                                       # what Edgeworth said last round (or None)
    #         previous_responses.get("edgeworth") if previous_responses else None
    #     ),
    # )

    # ── Step 4: Return both replies ───────────────────────────────────────────
    # The caller (run_feedback_mode) prints and speaks both replies in order.
    # Histories were already updated inside _real_feedback_response, so future
    # calls to either agent will include this exchange automatically.
    #
    # return e_reply, s_reply

    pass


# ── Feedback mode UI ──────────────────────────────────────────────────────────

def run_feedback_mode(
    edgeworth_history: list[dict],
    sparks_history: list[dict],
    use_voice: bool = USE_VOICE,
) -> None:
    from orchestrator import (
        BOLD, CYAN, DIM, RED, RESET, YELLOW,
        _banner, _label,
    )

    _banner("[ FEEDBACK MODE ]  f = speak/type feedback   q = exit", BOLD + CYAN)

    previous_responses: dict[str, str] | None = None
    feedback_round = 0

    while True:
        cmd = input(f"{BOLD}> {RESET}").strip().lower()

        if cmd in ("q", "quit", "exit"):
            print(f"{DIM}Exiting feedback mode.{RESET}\n")
            break

        if cmd not in ("f", "feedback", ""):
            print(f"  {DIM}Commands: f (feedback) | q (quit){RESET}")
            continue

        # ── Gather feedback ───────────────────────────────────────────────────
        if use_voice:
            print(f"  {CYAN}Recording...{RESET}")
            feedback_text = listen()
        else:
            feedback_text = input("  Feedback: ").strip()

        if not feedback_text:
            continue

        feedback_round += 1
        print(f"\n{DIM}[Routing feedback to both agents...]{RESET}\n")

        # ── Get responses ─────────────────────────────────────────────────────
        if PLACEHOLDER_MODE:
            idx = min(feedback_round - 1, 2)
            e_reply = _EDGEWORTH_FEEDBACK_PLACEHOLDER[idx]
            s_reply = _SPARKS_FEEDBACK_PLACEHOLDER[idx]
            if feedback_round > 1 and previous_responses:
                e_reply = _EDGEWORTH_FEEDBACK_REACTS[min(feedback_round - 2, 1)]
                s_reply = _SPARKS_FEEDBACK_REACTS[min(feedback_round - 2, 1)]
        else:
            result = route_feedback_to_agents(
                feedback_text,
                edgeworth_history,
                sparks_history,
                previous_responses,
            )
            if result is None:
                print(f"{RED}  route_feedback_to_agents() not yet implemented — see feedback.py TODO.{RESET}\n")
                continue
            e_reply, s_reply = result

        # ── Print + speak ─────────────────────────────────────────────────────
        _label("EDGEWORTH", "")
        print(f"  {CYAN}{e_reply}{RESET}\n")
        say_as("EDGEWORTH", e_reply, enabled=use_voice)
        time.sleep(0.3)

        _label("SPARKS", "")
        print(f"  {YELLOW}{s_reply}{RESET}\n")
        say_as("SPARKS", s_reply, enabled=use_voice)

        previous_responses = {"edgeworth": e_reply, "sparks": s_reply}
        print()
