"""
Interactive feedback mode — activated after the Intern's summary.

Basem speaks (or types) feedback. Both agents respond in character.
Agents can react to each other's responses across rounds.

Press  f + Enter  →  record/type feedback
Press  q + Enter  →  exit feedback mode
"""

import time
import config
from config import USE_VOICE, MODEL_AGENTS
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

_LIGHT_FEEDBACK_PLACEHOLDER = [
    "Your feedback is noted. I had already considered it and moved past it "
    "before you finished speaking. The implementation stands.",

    "You question the additions. That is because you cannot yet see what they are for. "
    "You will. The new world does not reveal itself all at once.",

    "Edgeworth thinks I overreached. You may feel the same. "
    "I find it interesting that mediocrity always recognizes itself in the presence of something greater.",
]

_EDGEWORTH_FEEDBACK_REACTS = [
    "Light's response confirms what I already suspected: "
    "he has mistaken grandiosity for competence. The architecture is still wrong.",

    "I'll refrain from dignifying that with a full reply. "
    "Note that my structure still stands. Light's theatrics change nothing technically.",
]

_LIGHT_FEEDBACK_REACTS = [
    "Edgeworth calls it wrong. He would. "
    "Men who cannot see the destination always criticize the vehicle.",

    "He is still talking about architecture. "
    "I am talking about what this code will become. We are not having the same conversation.",
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
        other = "Light" if agent_name == "EDGEWORTH" else "Edgeworth"
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
    light_history: list[dict],
    previous_responses: dict[str, str] | None = None,
) -> tuple[str, str]:
    """
    Sends feedback to both agents and returns (edgeworth_reply, light_reply).

    Each agent receives: the feedback text, their own conversation history,
    and optionally what the other agent said in the previous feedback round.

    # TODO [LEARNING]: Route feedback to both agents independently.
    # Each should receive: the feedback text, their own conversation history,
    # and their personality prompt. Consider whether showing one agent's reply
    # to the other before they respond changes the dynamic — it would in a
    # real multi-agent setup.
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
    # from agents import EDGEWORTH_SYSTEM, LIGHT_SYSTEM  # import both personality prompts

    # ── Step 2: Call Edgeworth with his history + the feedback ───────────────
    # _real_feedback_response() handles the API call, appends to history, returns reply text.
    # We pass Edgeworth's OWN history so their context threads stay separate.
    # other_agent_response lets Edgeworth react to what Light said last round, if anything.
    #
    # e_reply = _real_feedback_response(
    #     agent_name="EDGEWORTH",
    #     system_prompt=EDGEWORTH_SYSTEM,
    #     history=edgeworth_history,
    #     feedback_text=feedback_text,
    #     other_agent_response=(
    #         previous_responses.get("light") if previous_responses else None
    #     ),
    # )

    # ── Step 3: Call Light with his history + the feedback ───────────────────
    # Exact same pattern but with Light's system prompt and history.
    # Light sees what Edgeworth said last round — not what he just said.
    # This is the fan-out: one input → two separate, independent agent calls.
    #
    # l_reply = _real_feedback_response(
    #     agent_name="LIGHT",
    #     system_prompt=LIGHT_SYSTEM,
    #     history=light_history,
    #     feedback_text=feedback_text,
    #     other_agent_response=(
    #         previous_responses.get("edgeworth") if previous_responses else None
    #     ),
    # )

    # ── Step 4: Return both replies ───────────────────────────────────────────
    # Histories were already updated inside _real_feedback_response, so future
    # calls to either agent will include this exchange automatically.
    #
    # return e_reply, l_reply
    """
    pass


# ── Feedback mode UI ──────────────────────────────────────────────────────────

def run_feedback_mode(
    edgeworth_history: list[dict],
    light_history: list[dict],
    use_voice: bool = USE_VOICE,
) -> None:
    from orchestrator import (
        BOLD, CYAN, DIM, MAGENTA, RED, RESET,
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
        if config.PLACEHOLDER_MODE:
            idx = min(feedback_round - 1, 2)
            e_reply = _EDGEWORTH_FEEDBACK_PLACEHOLDER[idx]
            l_reply = _LIGHT_FEEDBACK_PLACEHOLDER[idx]
            if feedback_round > 1 and previous_responses:
                e_reply = _EDGEWORTH_FEEDBACK_REACTS[min(feedback_round - 2, 1)]
                l_reply = _LIGHT_FEEDBACK_REACTS[min(feedback_round - 2, 1)]
        else:
            result = route_feedback_to_agents(
                feedback_text,
                edgeworth_history,
                light_history,
                previous_responses,
            )
            if result is None:
                print(f"{RED}  route_feedback_to_agents() not yet implemented — see feedback.py TODO.{RED}\n")
                continue
            e_reply, l_reply = result

        # ── Print + speak ─────────────────────────────────────────────────────
        _label("EDGEWORTH", "")
        print(f"  {CYAN}{e_reply}{RESET}\n")
        say_as("EDGEWORTH", e_reply, enabled=use_voice)
        time.sleep(0.3)

        _label("LIGHT", "")
        print(f"  {MAGENTA}{l_reply}{RESET}\n")
        say_as("LIGHT", l_reply, enabled=use_voice)

        previous_responses = {"edgeworth": e_reply, "light": l_reply}
        print()
