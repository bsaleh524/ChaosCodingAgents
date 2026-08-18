"""Terminal formatting helpers — colors, banners, and per-agent critique blocks."""

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
