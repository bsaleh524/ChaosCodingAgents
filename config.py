from pathlib import Path

# ── Mode flags ────────────────────────────────────────────────────────────────
PLACEHOLDER_MODE = True   # Set False to enable real Anthropic LLM calls
USE_VOICE = False          # Set True to enable Mac `say` TTS

# ── Turn loop ─────────────────────────────────────────────────────────────────
NUM_ROUNDS = 6             # One round = one Edgeworth turn + one Sparks turn

# ── Paths ─────────────────────────────────────────────────────────────────────
WORKSPACE_DIR = Path("workspace")
SOLUTION_FILE = "solution.py"

# ── Models ────────────────────────────────────────────────────────────────────
MODEL_AGENTS = "claude-sonnet-4-6"
MODEL_INTERN  = "claude-haiku-4-5-20251001"

# ── Token budget for context trimmer ─────────────────────────────────────────
MAX_CONTEXT_TOKENS = 8_000
