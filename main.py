"""
Chaos Coding Agents — entry point.

Usage:
    python main.py
    python main.py --rounds 4 --voice
    python main.py --elevenlabs
    python main.py --no-placeholder --rounds 3
"""

import argparse
import sys
import threading
from datetime import datetime
from pathlib import Path

import config
from config import NUM_ROUNDS, USE_VOICE, WORKSPACE_DIR
from orchestrator import Orchestrator
from feedback import run_feedback_mode


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Chaos Coding Agents")
    p.add_argument("--rounds", type=int, default=NUM_ROUNDS,
                   help="Number of rounds (default %(default)s)")
    p.add_argument("--voice", action="store_true", default=USE_VOICE,
                   help="Enable voice output via Mac `say`")
    p.add_argument("--elevenlabs", action="store_true", default=False,
                   help="Use ElevenLabs TTS instead of Mac `say` (requires ELEVENLABS_API_KEY)")
    p.add_argument("--no-placeholder", dest="no_placeholder", action="store_true",
                   help="Disable placeholder mode — use real Anthropic LLM calls")
    p.add_argument("--sync", action="store_true", default=False,
                   help="Run loop in main thread (no interrupt support) — easier to debug")
    return p.parse_args()


def _get_feature_request(use_voice: bool) -> str:
    print("  Feature request:")
    if use_voice:
        print("  \033[2mPress Enter to speak, or just type and press Enter.\033[0m")
        choice = input("  [Enter = speak | type to skip mic] > ").strip()
        if choice == "":
            from voice import listen
            print()
            return listen()
        return choice
    return input("  > ").strip()


def print_header() -> None:
    print("\033[1m\033[92m")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║            C H A O S   C O D I N G   A G E N T S        ║")
    print("║        Edgeworth  ×  Light Yagami  ×  The Intern        ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print("\033[0m")


def main() -> None:
    args = parse_args()

    # Apply CLI overrides to config (must use config.X so all modules see the change)
    if args.no_placeholder:
        config.PLACEHOLDER_MODE = False
    if args.voice or args.elevenlabs:
        config.USE_VOICE = True
    if args.elevenlabs:
        config.USE_ELEVENLABS = True
        if not config.ELEVENLABS_API_KEY:
            print("\033[91m[ERROR] --elevenlabs requires ELEVENLABS_API_KEY to be set.\033[0m")
            print("  export ELEVENLABS_API_KEY=your_key_here")
            sys.exit(1)

    print_header()

    use_voice = args.voice or args.elevenlabs or config.USE_VOICE
    feature_request = _get_feature_request(use_voice)
    if not feature_request:
        print("No feature request provided. Exiting.")
        sys.exit(1)

    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = WORKSPACE_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n  \033[2mSession workspace: {session_dir}\033[0m")

    orchestrator = Orchestrator(
        feature_request=feature_request,
        rounds=args.rounds,
        use_voice=use_voice,
        workspace_dir=session_dir,
    )

    if args.sync:
        # Synchronous mode — runs in main thread, fully debuggable, no interrupt support
        print("\n  \033[2m[SYNC MODE] Running in main thread. Breakpoints work normally.\033[0m\n")
        orchestrator.run()
    else:
        # ── Run the turn loop in a thread so Enter interrupts it ──────────────
        print("\n  \033[2mPress Enter at any time to interrupt and summon the Intern early.\033[0m\n")

        loop_thread = threading.Thread(target=orchestrator.run, daemon=True)
        loop_thread.start()

        interrupted = _wait_for_enter_or_finish(loop_thread, orchestrator)

        if interrupted:
            orchestrator.stop_event.set()
            loop_thread.join(timeout=3)
            print("\n\033[91m[SYSTEM] Interrupted — summoning the Intern.\033[0m")

    # ── Intern summary ────────────────────────────────────────────────────────
    orchestrator.summon_intern()

    # ── Feedback mode ─────────────────────────────────────────────────────────
    run_feedback_mode(
        edgeworth_history=orchestrator.edgeworth_history,
        light_history=orchestrator.light_history,
        use_voice=use_voice,
    )


def _wait_for_enter_or_finish(thread: threading.Thread, orchestrator: Orchestrator) -> bool:
    import select
    while thread.is_alive():
        rlist, _, _ = select.select([sys.stdin], [], [], 0.2)
        if rlist:
            sys.stdin.readline()
            return True
    return False


if __name__ == "__main__":
    main()
