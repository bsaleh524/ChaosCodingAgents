import os
from pathlib import Path

# ── Mode flags ────────────────────────────────────────────────────────────────
PLACEHOLDER_MODE = True   # Set False to enable real Anthropic LLM calls
USE_VOICE = False          # Set True to enable Mac `say` TTS
USE_ELEVENLABS = False     # Set True (or pass --elevenlabs) to use ElevenLabs TTS

# ── Turn loop ─────────────────────────────────────────────────────────────────
NUM_ROUNDS = 6             # One round = one Edgeworth turn + one Light turn

# ── Paths ─────────────────────────────────────────────────────────────────────
WORKSPACE_DIR = Path("workspace")
SOLUTION_FILE = "solution.py"

# ── Models ────────────────────────────────────────────────────────────────────
MODEL_AGENTS = "claude-sonnet-4-6"
MODEL_INTERN  = "claude-haiku-4-5-20251001"

# ── Token budget for context trimmer ─────────────────────────────────────────
MAX_CONTEXT_TOKENS = 8_000

# ── ElevenLabs TTS ────────────────────────────────────────────────────────────
ELEVENLABS_API_KEY    = os.environ.get("ELEVENLABS_API_KEY", "")
EDGEWORTH_VOICE_ID    = "JBFqnCBsd6RMkjVDRZzb"
LIGHT_VOICE_ID        = "SOYHLrjzK2X1ezoPC6cr"

# ── OBS WebSockets ────────────────────────────────────────────────────────────
USE_OBS              = False
OBS_HOST             = "localhost"
OBS_PORT             = 4455
OBS_PASSWORD         = os.environ.get("OBS_WS_PASSWORD", "")
OBS_SCENE            = "Default"   # match your OBS scene name exactly
EDGEWORTH_OBS_SOURCE = "Edgeworth"              # OBS source name for Edgeworth image
LIGHT_OBS_SOURCE     = "Light Yagami"           # OBS source name for Light image
INTERN_OBS_SOURCE    = "Intern"                 # OBS source name for Intern image
