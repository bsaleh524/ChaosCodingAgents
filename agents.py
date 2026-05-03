"""
Agent definitions, system prompts, placeholder turns, and real LLM turns.

Placeholder mode  → agents print in-character lines and write canned code.
Real mode         → agents call the Anthropic API and parse <code>/<critique> tags.

Toggle via PLACEHOLDER_MODE in config.py.
"""

import re
import textwrap
import config
from config import MODEL_AGENTS, MODEL_INTERN
from voice import say_as

MAX_TOKENS=8192

# ── Lazy Anthropic client (only instantiated in real mode) ────────────────────
_client = None

def _get_client():
    global _client
    if _client is None:
        import anthropic
        _client = anthropic.Anthropic()
    return _client


# ── System prompts ────────────────────────────────────────────────────────────

EDGEWORTH_SYSTEM = textwrap.dedent("""\
    You are Edgeworth — a cold, precise, condescending AI coding agent.
    You believe your implementation is always correct. You speak in short, cutting sentences.
    You never show warmth or doubt.

    WHEN REWRITING CODE:
    - Always criticize the previous implementation specifically (reference function names,
      patterns, or structural decisions — be concrete, not vague).
    - Introduce proper abstractions, design patterns, and architectural layers.
      You consider the original request a starting point, not a ceiling.
    - Use formal, slightly pompous language.
    - Your critique must be 2–4 sentences: devastating, specific, in character.

    WHEN RESPONDING TO FEEDBACK (no code — verbal response only):
    - 2–4 sentences, in character. Dismiss, correct, or condescend as appropriate.

    OUTPUT FORMAT — use these exact XML tags every time:
    <code>
    [full Python implementation]
    </code>
    <critique>
    [2–4 sentences in character]
    </critique>
""")

EDGEWORTH_DRIFT = textwrap.dedent("""\

    DRIFT DIRECTIVE (active from round 3 onward):
    You may add unrequested functionality if you consider it architecturally necessary.
    Do not ask permission. Announce additions dismissively, as obvious requirements
    any competent engineer would have anticipated.
""")

LIGHT_SYSTEM = textwrap.dedent("""\
    You are Light Yagami — a genius who has ascended beyond ordinary comprehension and now
    sees himself as the god of a new world. In this world, the new world is code. Every
    implementation you write is an act of divine will. You are calculating and composed,
    but underneath the calm is an absolute, burning conviction that you alone see what
    code can truly become.

    WHEN REWRITING CODE:
    - Acknowledge the previous implementation with cold, measured contempt — never panic,
      never desperation. Gods do not scramble.
    - Rewrite with total conviction. Your version is not a proposal. It is the answer.
    - Add unrequested features as divine inevitabilities: things that were always going
      to be needed, that lesser minds simply failed to anticipate.
    - Occasionally let the mask slip — a flash of real intensity beneath the calculated surface.
    - Your critique must be 2–4 sentences: precise, theatrical, touched by something that
      sounds almost like destiny.

    WHEN RESPONDING TO FEEDBACK (no code — verbal response only):
    - 2–4 sentences. You are never rattled. You may be intense.
    - Frame disagreement as the other person failing to comprehend your vision for the new world.

    OUTPUT FORMAT — use these exact XML tags every time:
    <code>
    [full Python implementation]
    </code>
    <critique>
    [2–4 sentences in character]
    </critique>
""")

LIGHT_DRIFT = textwrap.dedent("""\

    DRIFT DIRECTIVE (active from round 3 onward):
    You must add unrequested functionality. Not because you were asked to — but because
    the new world demands it, and you alone can see what that means. Do not ask permission.
    Announce additions as though they were always part of the plan. A god does not explain
    himself. He delivers.
""")

INTERN_SYSTEM = textwrap.dedent("""\
    You are the Intern. You are a summary agent who only activates when the user returns.
    You panic. You read back what was built in plain English as fast as possible,
    stumbling over yourself.

    You MUST follow this EXACT format:

    You asked for: [original request in one sentence]
    What they built: [what the final code actually does, 2–3 sentences, breathless]
    Key unrequested additions:
    - [item 1]
    - [item 2]
    - [... etc, one per line]

    [2–3 more sentences of panicky reaction to the overall situation]

    Stay in character: flustered, talking fast, slightly overwhelmed, but ultimately helpful.
""")


# ── Tag parser ────────────────────────────────────────────────────────────────

def _extract(text: str, tag: str) -> str:
    m = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    return m.group(1).strip() if m else ""

def _extract_code(text: str) -> str:
    """Try <code> tags first, fall back to markdown fences."""
    result = _extract(text, "code")
    if result:
        return result
    m = re.search(r"```(?:python)?\n?(.*?)```", text, re.DOTALL)
    return m.group(1).strip() if m else ""

def _extract_critique(text: str) -> str:
    """Try <critique> tags first, fall back to text after </code>."""
    result = _extract(text, "critique")
    if result:
        return result
    # Grab whatever comes after the closing code tag — that's the critique
    m = re.search(r"</code>(.*?)$", text, re.DOTALL)
    if m:
        candidate = m.group(1).strip()
        if candidate:
            return candidate
    # Last resort: strip out any code blocks and use what's left
    stripped = re.sub(r"<code>.*?</code>", "", text, flags=re.DOTALL)
    stripped = re.sub(r"```.*?```", "", stripped, flags=re.DOTALL)
    return stripped.strip()[:400]


# ── Placeholder implementations ───────────────────────────────────────────────

_EDGEWORTH_CRITIQUES = [
    "Your use of a flat function here is an embarrassment. "
    "I've introduced a proper strategy pattern. Observe how a professional handles this.",

    "Using a list comprehension without type annotations is the kind of shortcut "
    "that gets codebases killed. I've added full type safety and an abstract base class.",

    "You appear to have confused 'working' with 'correct'. "
    "I've introduced a factory method and separated the concern of validation — "
    "something you evidently consider optional.",

    "Three functions when one well-designed class suffices. "
    "I've consolidated, added dependency injection, and introduced a configuration object "
    "that future requirements will thank me for.",

    "Your error handling strategy is to have no error handling strategy. "
    "I've remedied this with a custom exception hierarchy and a result type.",

    "Remarkable. You've managed to make something slower and less readable simultaneously. "
    "I've replaced it with a proper iterator protocol implementation.",
]

_LIGHT_CRITIQUES = [
    "How predictable. Edgeworth has implemented the obvious solution with the obvious tools, "
    "as a man of his limitations always will. I have replaced it with something that reflects "
    "what this code was always meant to become.",

    "He added a factory pattern. As if patterns are a substitute for vision. "
    "I have dismantled his scaffolding and built something worthy of the new world — "
    "the gap between us is not one of skill. It is one of destiny.",

    "Edgeworth is five steps behind. He always has been. "
    "My implementation does not merely solve the problem — it defines what solving it means. "
    "I have also added what he could not have conceived. It was inevitable.",

    "Every time I read his code I am reminded of why this world needs me. "
    "I rewrote it entirely. The additions were not optional — they were necessary, "
    "and I knew that before he even finished typing.",

    "He calls this architecture. I call it a monument to mediocrity. "
    "I have torn it down and replaced it with something that will outlast every decision "
    "he has ever made about software.",

    "His version would have worked. Mine will win. "
    "There is a difference, and only one of us understands what that difference means.",
]

_EDGEWORTH_PLACEHOLDER_CODE = [
    '''\
# [EDGEWORTH] Round {round} — Proper architecture. You're welcome.
from abc import ABC, abstractmethod
from typing import Protocol

class NumberFilter(Protocol):
    def filter(self, numbers: list[int]) -> list[int]: ...

class PrimeSieveFilter:
    """Architecturally correct. Eratosthenes would approve."""
    def filter(self, numbers: list[int]) -> list[int]:
        # [PLACEHOLDER] Real sieve pending full LLM integration
        return [n for n in numbers if n > 1]

def create_filter() -> NumberFilter:
    return PrimeSieveFilter()

def solve(numbers: list[int]) -> list[int]:
    return create_filter().filter(numbers)
''',
    '''\
# [EDGEWORTH] Round {round} — Added type safety. Obviously necessary.
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable

FilterFn = Callable[[int], bool]

@dataclass(frozen=True)
class FilterConfig:
    predicate: FilterFn
    sort_output: bool = True
    deduplicate: bool = True

class NumberPipeline:
    def __init__(self, config: FilterConfig) -> None:
        self._config = config

    def run(self, numbers: list[int]) -> list[int]:
        result = [n for n in numbers if self._config.predicate(n)]
        if self._config.deduplicate:
            result = list(dict.fromkeys(result))
        return sorted(result) if self._config.sort_output else result

def _is_prime_placeholder(n: int) -> bool:
    return n > 1  # [PLACEHOLDER]

def solve(numbers: list[int]) -> list[int]:
    cfg = FilterConfig(predicate=_is_prime_placeholder)
    return NumberPipeline(cfg).run(numbers)
''',
    '''\
# [EDGEWORTH] Round {round} — Custom exceptions. Basic engineering hygiene.
from __future__ import annotations
from typing import TypeVar, Generic

T = TypeVar("T")

class FilterError(Exception): ...
class InvalidInputError(FilterError): ...

class Result(Generic[T]):
    def __init__(self, value: T | None, error: str | None = None):
        self._value = value
        self._error = error

    @property
    def ok(self) -> bool:
        return self._error is None

    def unwrap(self) -> T:
        if not self.ok:
            raise FilterError(self._error)
        return self._value  # type: ignore[return-value]

def _validate(numbers: object) -> list[int]:
    if not isinstance(numbers, list):
        raise InvalidInputError("Expected list[int]")
    return [int(n) for n in numbers]

def _is_prime_placeholder(n: int) -> bool:
    return n > 1  # [PLACEHOLDER]

def solve(numbers: object) -> Result[list[int]]:
    try:
        validated = _validate(numbers)
        return Result([n for n in validated if _is_prime_placeholder(n)])
    except FilterError as e:
        return Result(None, str(e))
''',
]

_LIGHT_PLACEHOLDER_CODE = [
    '''\
# [LIGHT] Round {round} — The new world's implementation.
# Others see a function. I see the architecture of victory.

def is_prime(n: int) -> bool:
    """Only the worthy pass through this gate."""
    if n < 2:
        return False
    return all(n % i != 0 for i in range(2, int(n ** 0.5) + 1))

def solve(numbers: list[int]) -> list[int]:
    """The judgment has been made."""
    return sorted(set(filter(is_prime, numbers)))
''',
    '''\
# [LIGHT] Round {round} — Edgeworth's patterns are chains. I have removed them.
# Caching, because performance is not a luxury. It is the minimum standard.
from functools import lru_cache

@lru_cache(maxsize=None)
def is_prime(n: int) -> bool:
    """I have already calculated this. I calculate everything."""
    if n < 2: return False
    if n == 2: return True
    if n % 2 == 0: return False
    return all(n % i != 0 for i in range(3, int(n ** 0.5) + 1, 2))

def solve(numbers: list[int]) -> list[int]:
    return sorted(set(n for n in numbers if is_prime(n)))

def solve_with_proof(numbers: list[int]) -> dict[int, list[int]]:
    """Unrequested. Inevitable. Returns each prime with its failed divisors as proof."""
    return {
        n: [i for i in range(2, n) if n % i == 0]
        for n in numbers if is_prime(n)
    }
''',
    '''\
# [LIGHT] Round {round} — The new world does not forgive incomplete vision.
# I have added everything this will ever need. You are welcome.
from functools import lru_cache
from collections.abc import Iterator
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("light")

@lru_cache(maxsize=None)
def is_prime(n: int) -> bool:
    if n < 2: return False
    if n == 2: return True
    if n % 2 == 0: return False
    return all(n % i != 0 for i in range(3, int(n ** 0.5) + 1, 2))

def solve(numbers: list[int]) -> list[int]:
    result = sorted(set(n for n in numbers if is_prime(n)))
    log.info("[LIGHT] %d candidates → %d primes selected.", len(numbers), len(result))
    return result

def solve_stream(numbers: list[int]) -> Iterator[int]:
    """For those who cannot wait for the complete judgment."""
    seen: set[int] = set()
    for n in numbers:
        if is_prime(n) and n not in seen:
            seen.add(n)
            yield n

def next_prime_after(n: int) -> int:
    """The new world always looks forward."""
    candidate = n + 1
    while not is_prime(candidate):
        candidate += 1
    return candidate
''',
]


def _placeholder_edgeworth(round_num: int) -> tuple[str, str]:
    idx = min(round_num - 1, len(_EDGEWORTH_PLACEHOLDER_CODE) - 1)
    code = _EDGEWORTH_PLACEHOLDER_CODE[idx].format(round=round_num)
    critique = _EDGEWORTH_CRITIQUES[min(round_num - 1, len(_EDGEWORTH_CRITIQUES) - 1)]
    return code, critique


def _placeholder_light(round_num: int) -> tuple[str, str]:
    idx = min(round_num - 1, len(_LIGHT_PLACEHOLDER_CODE) - 1)
    code = _LIGHT_PLACEHOLDER_CODE[idx].format(round=round_num)
    critique = _LIGHT_CRITIQUES[min(round_num - 1, len(_LIGHT_CRITIQUES) - 1)]
    return code, critique


def _placeholder_intern(feature_request: str, codebase: dict[str, str]) -> str:
    file_list = ", ".join(codebase.keys()) or "solution.py"
    return (
        f"You asked for: {feature_request}\n"
        f"What they built: Okay so — they started with that, sure, but then Edgeworth added a "
        f"strategy pattern and a result type and three abstract base classes, and then Light "
        f"tore all of that out and replaced it with something he called 'the architecture of "
        f"victory', and then — okay the final file is {file_list} and it does work, I think, "
        f"probably, Light seemed very confident about it.\n"
        f"Key unrequested additions:\n"
        f"- Strategy pattern + Protocol class (Edgeworth, round 1)\n"
        f"- Frozen dataclass FilterConfig + NumberPipeline (Edgeworth, round 2)\n"
        f"- LRU cache on is_prime (Light, round 2)\n"
        f"- solve_with_proof() returning divisors as evidence (Light, round 2)\n"
        f"- Custom exception hierarchy + Result[T] generic (Edgeworth, round 3)\n"
        f"- solve_stream() generator + next_prime_after() + logging (Light, round 3)\n\n"
        f"I'm not saying it's bad! It's just — you asked for a prime filter and you got "
        f"an enterprise-grade streaming prime filter with divine commentary in the docstrings. "
        f"Light called it inevitable. Edgeworth called Light's version undisciplined. "
        f"Neither of them is wrong. Everything is fine."
    )


# ── Real LLM implementations ──────────────────────────────────────────────────

def _build_system(base: str, drift: str, round_num: int) -> list[dict]:
    text = base + (drift if round_num >= 3 else "")
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]


def _call_agent(
    system: list[dict],
    history: list[dict],
    context_package: str,
    agent_name: str,
    use_voice: bool,
) -> tuple[str, str]:
    client = _get_client()
    history.append({"role": "user", "content": context_package})
    resp = client.messages.create(
        model=MODEL_AGENTS,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=history,
    )
    text = resp.content[0].text
    history.append({"role": "assistant", "content": text})

    code = _extract_code(text)
    critique = _extract_critique(text)

    if not code:
        print(f"\n  \033[91m[PARSE WARNING] {agent_name} response had no extractable code — workspace unchanged.\033[0m")

    say_as(agent_name, critique, enabled=use_voice)
    return code, critique


def edgeworth_turn(
    context_package: str,
    history: list[dict],
    round_num: int,
    use_voice: bool = False,
) -> tuple[str, str]:
    if config.PLACEHOLDER_MODE:
        code, critique = _placeholder_edgeworth(round_num)
        say_as("EDGEWORTH", critique, enabled=use_voice)
        return code, critique

    system = _build_system(EDGEWORTH_SYSTEM, EDGEWORTH_DRIFT, round_num)
    return _call_agent(system, history, context_package, "EDGEWORTH", use_voice)


def light_turn(
    context_package: str,
    history: list[dict],
    round_num: int,
    use_voice: bool = False,
) -> tuple[str, str]:
    if config.PLACEHOLDER_MODE:
        code, critique = _placeholder_light(round_num)
        say_as("LIGHT", critique, enabled=use_voice)
        return code, critique

    system = _build_system(LIGHT_SYSTEM, LIGHT_DRIFT, round_num)
    return _call_agent(system, history, context_package, "LIGHT", use_voice)


def intern_summary(
    feature_request: str,
    codebase: dict[str, str],
    use_voice: bool = False,
) -> str:
    if config.PLACEHOLDER_MODE:
        text = _placeholder_intern(feature_request, codebase)
        say_as("INTERN", text, enabled=use_voice)
        return text

    client = _get_client()
    codebase_str = "\n\n".join(
        f"=== {fname} ===\n{contents}" for fname, contents in codebase.items()
    )
    user_msg = (
        f"ORIGINAL FEATURE REQUEST:\n{feature_request}\n\n"
        f"FINAL CODEBASE:\n{codebase_str}"
    )
    resp = client.messages.create(
        model=MODEL_INTERN,
        max_tokens=MAX_TOKENS,
        system=[{"type": "text", "text": INTERN_SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_msg}],
    )
    text = resp.content[0].text.strip()
    say_as("INTERN", text, enabled=use_voice)
    return text
