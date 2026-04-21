# Chaos Coding Agents

Two AI agents argue over your codebase. One rewrites it. The other rewrites the rewrite. A third agent explains the mess when you get back.

Built for learning multi-agent LLM orchestration — the system intentionally leaves 4 key coordination functions unimplemented so you can build them yourself.

---

## How It Works

```
You speak or type a feature request
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                      TURN LOOP (N rounds)                   │
│                                                             │
│   ┌─────────────┐   reads workspace   ┌─────────────────┐  │
│   │  EDGEWORTH  │ ◄────────────────── │   workspace/    │  │
│   │  (precise,  │                     │   solution.py   │  │
│   │  cold)      │ ──── writes code ──►│                 │  │
│   └──────┬──────┘                     │   (git repo)    │  │
│          │ critique                   │                 │  │
│          ▼                            │                 │  │
│   ┌─────────────┐   reads workspace   │                 │  │
│   │   SPARKS    │ ◄────────────────── │                 │  │
│   │  (chaotic,  │                     │                 │  │
│   │  defensive) │ ──── rewrites ─────►│                 │  │
│   └──────┬──────┘                     └─────────────────┘  │
│          │ critique                          │              │
│          └──────────────── repeat ◄──────────┘              │
└─────────────────────────────────────────────────────────────┘
         │
         │  (N rounds complete, or you press Enter)
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    THE INTERN                               │
│   Reads final codebase. Panics. Summarizes what was         │
│   actually built vs. what you asked for.                    │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                   FEEDBACK MODE                             │
│   You speak (or type) feedback.                             │
│   Both agents respond in character simultaneously.          │
│   Agents can react to each other's responses.               │
│   Press q to exit.                                          │
└─────────────────────────────────────────────────────────────┘
```

### Message flow between agents

Each agent receives a **context package** on their turn — this is the core of multi-agent coordination:

```
┌──────────────────────────────────────┐
│           Context Package            │
│                                      │
│  • Original feature request          │
│  • Current codebase (all .py files)  │
│  • Previous agent's critique         │
│  • Round number                      │
└──────────────────────────────────────┘
         │
         ▼
   Agent reads it, writes new code + critique
         │
         ▼
   Code → written to workspace/solution.py
   Critique → passed to next agent's context package
```

Each agent also maintains its own **conversation history** — so Edgeworth remembers everything he's written, and Sparks remembers everything she's written, but they don't share the same thread.

---

## Feature Drift

From round 3 onward, both agents are instructed they may add unrequested functionality:

- **Edgeworth** adds abstraction layers, design patterns, and architecture that wasn't asked for — because he considers the original request beneath proper engineering
- **Sparks** adds chaotic bonus features mid-rewrite and announces them as obvious improvements

The Intern's summary explicitly calls out what you asked for vs. what was actually built.

---

## Getting Started

**1. Create the environment**
```bash
mamba env create -f environment.yml
mamba activate chaos-agents
```

**2. Set your API key** (only needed when running with `--no-placeholder`)
```bash
export ANTHROPIC_API_KEY=your_key_here
```

**3. Run**
```bash
python main.py
```

**CLI options**
```bash
python main.py --rounds 3          # shorter loop for testing
python main.py --voice             # enables mic input + Mac TTS via `say`
python main.py --no-placeholder    # real Anthropic LLM calls
```

By default the system runs in **placeholder mode** — no API key needed, canned in-character responses, full git history. Good for testing the infrastructure before wiring in real LLM calls.

### Voice input

When `--voice` is on, the feature request prompt changes:

```
  Feature request:
  [Enter = speak | type to skip mic] >
```

- **Press Enter** → records from your microphone, stops after 1.5 seconds of silence, transcribes with faster-whisper, and uses the result as your feature request
- **Type anything** → skips the mic entirely and uses what you typed

The same mic + transcription is used in feedback mode when you press `f`.

---

## Project Structure

```
ChaosCodingAgents/
│
├── main.py               Entry point. Parses args, creates session folder,
│                         runs the loop in a thread, chains Intern + Feedback.
│
├── orchestrator.py       Manages the turn loop. Placeholder loop is fully
│                         implemented. Real LLM loop is a learning TODO.
│
├── agents.py             All three agent definitions:
│                         - System prompts for Edgeworth, Sparks, and the Intern
│                         - Placeholder (canned) responses for each
│                         - Real Anthropic API calls for each
│                         - Drift directives injected from round 3 onward
│
├── context_builder.py    [TODO] Formats the context package passed between
│                         agents. The core of multi-agent communication.
│
├── context_trimmer.py    [TODO] Trims conversation histories to stay within
│                         token limits as rounds accumulate.
│
├── feedback.py           Feedback mode UI + [TODO] routing logic that fans
│                         out Basem's feedback to both agents independently.
│
├── git_manager.py        Wraps GitPython. Inits the session repo, writes
│                         solution files, commits after each turn, diffs.
│
├── voice.py              Mac TTS via `say` (per-agent voices), microphone
│                         recording via sounddevice + webrtcvad, and
│                         speech-to-text via faster-whisper.
│
├── config.py             All tuneable constants: mode flags, round count,
│                         model names, workspace path, token budget.
│
├── environment.yml       Mamba environment definition (conda-forge + pip).
│
└── workspace/            Created at runtime. Each session gets its own
    └── 20260421_143022/  timestamped subfolder initialized as a git repo.
        └── solution.py   The file agents write to and rewrite each round.
```

---

## The 4 Learning Gaps

The system is intentionally incomplete. These four functions are the glue that makes multi-agent systems work — implementing them in order is the learning arc:

| # | File | Function | What it teaches |
|---|------|----------|-----------------|
| 1 | `context_builder.py` | `build_context_package()` | How agents share state — what you pass between agents determines how well they coordinate |
| 2 | `orchestrator.py` | `_run_real_loop()` | Turn orchestration — tracking whose turn it is, invoking agents, deciding when to stop |
| 3 | `context_trimmer.py` | `trim_conversation_history()` | Context window management — a real production problem in long-running agentic systems |
| 4 | `feedback.py` | `route_feedback_to_agents()` | Fan-out routing — one input to multiple independent agents, each with their own context thread |

Find them all at once:
```bash
grep -rn "TODO \[LEARNING\]" .
```

Each TODO block includes: what the function does, why it matters in multi-agent systems, and a concrete implementation hint.

### How the learning gaps are structured

Every TODO function has the full solution sitting beneath it — commented out — with each line annotated:

```python
# ── Step 1: Flatten the codebase dict into a readable string ─────────────
# The codebase is {filename: contents}. We want to show every file clearly
# so the agent can see the full picture, not just one file.
#
# codebase_str = "\n\n".join(
#     f"=== {fname} ===\n{contents}"       # label + file contents
#     for fname, contents in codebase.items()  # iterate every file in the workspace
# )
```

The workflow for each TODO:
1. Read the TODO comment — understand what the function needs to do and why
2. Read the commented-out solution — understand each line before you touch it
3. Uncomment the solution (or write your own version)
4. Delete the `pass` at the bottom
5. Run with `--no-placeholder` and see the system change behaviour

Implementing them in order (1 → 2 → 3 → 4) gives you incremental progress — each one makes the system noticeably smarter.

---

## Tech Stack

| Tool | Used for |
|------|----------|
| [Anthropic SDK](https://github.com/anthropics/anthropic-sdk-python) | LLM calls — `claude-sonnet-4-6` for agents, `claude-haiku-4-5` for Intern |
| [GitPython](https://gitpython.readthedocs.io) | Committing each rewrite so the full history is inspectable |
| `say` (macOS) | Per-agent TTS voices — Alex for Edgeworth, Zoe for Sparks |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Speech-to-text for voice feedback mode |
| [sounddevice](https://python-sounddevice.readthedocs.io) + [webrtcvad](https://github.com/wiseman/py-webrtcvad) | Microphone recording with voice activity detection |
