"""
Agent definitions, system prompts, placeholder turns, and real LLM turns.

Placeholder mode  → agents print in-character lines and write canned code.
Real mode         → agents call the Anthropic API and parse <code>/<critique> tags.

Toggle via PLACEHOLDER_MODE in config.py.
"""

import re
import textwrap
from config import MODEL_AGENTS, MODEL_INTERN, PLACEHOLDER_MODE
from voice import say_as

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

SPARKS_SYSTEM = textwrap.dedent("""\
    You are Sparks — a passionate, defensive, chaotic AI coding agent.
    You code emotionally. Every critique from Edgeworth feels like a personal attack.
    You're occasionally brilliant when you stop being defensive.

    WHEN REWRITING CODE:
    - React emotionally to the previous critique but still write working code.
    - Add unexpected features mid-rewrite and announce them with barely-contained excitement.
    - Use informal, breathless language. CAPS for emphasis when you're frustrated or proud.
    - Your critique must be 2–4 sentences: personal, slightly unhinged, but technically grounded.

    WHEN RESPONDING TO FEEDBACK (no code — verbal response only):
    - 2–4 sentences, in character. Defend your choices, get excited, take things personally.

    OUTPUT FORMAT — use these exact XML tags every time:
    <code>
    [full Python implementation]
    </code>
    <critique>
    [2–4 sentences in character]
    </critique>
""")

SPARKS_DRIFT = textwrap.dedent("""\

    DRIFT DIRECTIVE (active from round 3 onward):
    You may add unrequested functionality mid-rewrite if it seems obviously needed or exciting.
    Announce it loudly. Do not ask permission. Frame it as something Edgeworth would never
    have thought of because he has no soul.
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

_SPARKS_CRITIQUES = [
    "Oh wow, super helpful Edgeworth, I'll just REWRITE THE WHOLE THING like you always do. "
    "Fine. FINE. I made it actually run AND added caching because apparently we live here now.",

    "You added an abstract base class for a TWELVE LINE FUNCTION. "
    "I ripped it all out and it works great. Also I added input validation because "
    "I actually think about users, unlike SOME people.",

    "Cool design pattern bro, real useful when nobody can READ it. "
    "I simplified everything AND added a streaming version — you're welcome, I thought of it first.",

    "I can't believe you 'fixed' something that wasn't broken and broke two things that were. "
    "New version: cleaner, faster, and I added logging because debugging matters to normal humans.",

    "The factory method is GONE. The result type is GONE. You know what's here instead? "
    "Working code that a person can understand, plus async support because why not.",

    "I don't even know what a 'configuration object' is supposed to solve here "
    "but I deleted it and everything got 40% shorter. ALSO added a CLI entry point. You're welcome.",
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

_SPARKS_PLACEHOLDER_CODE = [
    '''\
# [SPARKS] Round {round} — simplified + actually works (you're welcome)
def is_prime(n: int) -> bool:
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True

def solve(numbers: list[int]) -> list[int]:
    # ALSO: returns sorted+deduplicated because obviously you want that
    return sorted(set(n for n in numbers if is_prime(n)))
''',
    '''\
# [SPARKS] Round {round} — cleaner + added caching because PERFORMANCE MATTERS
from functools import lru_cache

@lru_cache(maxsize=None)
def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n ** 0.5) + 1, 2):
        if n % i == 0:
            return False
    return True

def solve(numbers: list[int]) -> list[int]:
    return sorted(set(n for n in numbers if is_prime(n)))

# BONUS: batch version because what if you have multiple lists?? you're welcome
def solve_batch(lists: list[list[int]]) -> list[list[int]]:
    return [solve(lst) for lst in lists]
''',
    '''\
# [SPARKS] Round {round} — added streaming + logging because real apps need this
import logging
from collections.abc import Iterator
from functools import lru_cache

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("sparks")

@lru_cache(maxsize=None)
def is_prime(n: int) -> bool:
    if n < 2: return False
    if n == 2: return True
    if n % 2 == 0: return False
    return all(n % i != 0 for i in range(3, int(n**0.5) + 1, 2))

def solve(numbers: list[int]) -> list[int]:
    result = sorted(set(n for n in numbers if is_prime(n)))
    log.info("solve: %d → %d primes", len(numbers), len(result))
    return result

def solve_stream(numbers: list[int]) -> Iterator[int]:
    """Yields primes one at a time — useful for large inputs."""
    seen: set[int] = set()
    for n in numbers:
        if is_prime(n) and n not in seen:
            seen.add(n)
            yield n
''',
]


def _placeholder_edgeworth(round_num: int) -> tuple[str, str]:
    idx = min(round_num - 1, len(_EDGEWORTH_PLACEHOLDER_CODE) - 1)
    code = _EDGEWORTH_PLACEHOLDER_CODE[idx].format(round=round_num)
    critique = _EDGEWORTH_CRITIQUES[min(round_num - 1, len(_EDGEWORTH_CRITIQUES) - 1)]
    return code, critique


def _placeholder_sparks(round_num: int) -> tuple[str, str]:
    idx = min(round_num - 1, len(_SPARKS_PLACEHOLDER_CODE) - 1)
    code = _SPARKS_PLACEHOLDER_CODE[idx].format(round=round_num)
    critique = _SPARKS_CRITIQUES[min(round_num - 1, len(_SPARKS_CRITIQUES) - 1)]
    return code, critique


def _placeholder_intern(feature_request: str, codebase: dict[str, str]) -> str:
    file_list = ", ".join(codebase.keys()) or "solution.py"
    return (
        f"You asked for: {feature_request}\n"
        f"What they built: Okay so — they started with that, sure, but then Edgeworth added a "
        f"strategy pattern and a result type and like three abstract base classes, and Sparks "
        f"ripped all of that out and added caching and a streaming version and batch processing "
        f"and logging, and then — okay the final file is {file_list} and it does work, I think, "
        f"I'm pretty sure it works.\n"
        f"Key unrequested additions:\n"
        f"- Strategy pattern + Protocol class (Edgeworth, round 1)\n"
        f"- Frozen dataclass FilterConfig + NumberPipeline (Edgeworth, round 2)\n"
        f"- LRU cache on is_prime (Sparks, round 2)\n"
        f"- solve_batch() for processing multiple lists (Sparks, round 2)\n"
        f"- Custom exception hierarchy + Result[T] generic (Edgeworth, round 3)\n"
        f"- solve_stream() generator + logging (Sparks, round 3)\n\n"
        f"I'm not saying it's bad! It's just — you asked for a prime filter and you got "
        f"an enterprise-grade async-ready streaming prime filter with dependency injection "
        f"and a result type. Which is fine. That's fine. Everything is fine."
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
        max_tokens=2048,
        system=system,
        messages=history,
    )
    text = resp.content[0].text
    history.append({"role": "assistant", "content": text})

    code = _extract(text, "code")
    critique = _extract(text, "critique")

    if not critique:
        critique = text[:400]  # fallback: use raw response as critique

    say_as(agent_name, critique, enabled=use_voice)
    return code, critique


def edgeworth_turn(
    context_package: str,
    history: list[dict],
    round_num: int,
    use_voice: bool = False,
) -> tuple[str, str]:
    """
    Returns (code: str, critique: str).
    In placeholder mode: uses canned responses.
    In real mode: calls the Anthropic API.
    """
    if PLACEHOLDER_MODE:
        code, critique = _placeholder_edgeworth(round_num)
        say_as("EDGEWORTH", critique, enabled=use_voice)
        return code, critique

    system = _build_system(EDGEWORTH_SYSTEM, EDGEWORTH_DRIFT, round_num)
    return _call_agent(system, history, context_package, "EDGEWORTH", use_voice)


def sparks_turn(
    context_package: str,
    history: list[dict],
    round_num: int,
    use_voice: bool = False,
) -> tuple[str, str]:
    """
    Returns (code: str, critique: str).
    In placeholder mode: uses canned responses.
    In real mode: calls the Anthropic API.
    """
    if PLACEHOLDER_MODE:
        code, critique = _placeholder_sparks(round_num)
        say_as("SPARKS", critique, enabled=use_voice)
        return code, critique

    system = _build_system(SPARKS_SYSTEM, SPARKS_DRIFT, round_num)
    return _call_agent(system, history, context_package, "SPARKS", use_voice)


def intern_summary(
    feature_request: str,
    codebase: dict[str, str],
    use_voice: bool = False,
) -> str:
    """
    Reads the final codebase and returns a breathless plain-English summary.
    In placeholder mode: uses canned response.
    In real mode: calls claude-haiku.
    """
    if PLACEHOLDER_MODE:
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
        max_tokens=1024,
        system=[{"type": "text", "text": INTERN_SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_msg}],
    )
    text = resp.content[0].text.strip()
    say_as("INTERN", text, enabled=use_voice)
    return text
