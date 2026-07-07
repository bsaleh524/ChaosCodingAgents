# LangGraph Migration: Future Work

Convert ChaosCodingAgents from the hand-rolled Anthropic SDK implementation to a LangChain + LangGraph architecture. This is an educational rewrite — the goal is to show what the same system looks like when built on standard frameworks.

---

## Background

The current project is intentionally hand-rolled: raw Anthropic SDK calls, a custom `Orchestrator` class managing the loop, manual history lists, and a regex parser for output tags. This is pedagogically correct for the YouTube tutorial — the plumbing IS the lesson.

This migration document covers the work to produce a **second implementation** alongside the original, showing the LangGraph equivalent. Do not delete the original — the before/after contrast is the content.

---

## Phase 1: Environment and Dependencies

**Files to create/modify:**
- `requirements-langgraph.txt` (new file, separate from original `requirements.txt`)

**Work:**
- Add `langchain-anthropic`, `langgraph`, `langchain-core`, `pydantic` to a new requirements file
- Keep the original `requirements.txt` unchanged — the original implementation stays

**Done when:** `pip install -r requirements-langgraph.txt` succeeds and `from langgraph.graph import StateGraph` imports cleanly.

---

## Phase 2: State Schema

**Files to create:**
- `langgraph_impl/state.py`

**Work:**
Define `CCAState(TypedDict)` replacing the `Orchestrator` instance variables:

```python
class CCAState(TypedDict):
    feature_request: str
    max_rounds: int
    round: int
    code: str
    last_critique: Optional[str]
    edgeworth_history: Annotated[list[BaseMessage], add_messages]
    light_history: Annotated[list[BaseMessage], add_messages]
```

**Mapping:**

| `Orchestrator` attribute | `CCAState` field |
|---|---|
| `self.feature_request` | `state["feature_request"]` |
| `self.rounds` | `state["max_rounds"]` |
| `self.rounds_completed` | `state["round"]` |
| `self.last_critique` | `state["last_critique"]` |
| `self.edgeworth_history` | `state["edgeworth_history"]` (with `add_messages` reducer) |
| `self.light_history` | `state["light_history"]` (with `add_messages` reducer) |

**Done when:** `CCAState` is importable and `from langgraph.graph.message import add_messages` works.

---

## Phase 3: Agent Nodes

**Files to create:**
- `langgraph_impl/nodes.py`

**Work:**
Convert `agents.py` functions to LangGraph node functions. Each node has signature `(state: CCAState) -> dict`.

### `edgeworth_node(state) -> dict`
- Replaces: `edgeworth_turn()` in `agents.py`
- Reuses: `EDGEWORTH_SYSTEM`, `EDGEWORTH_DRIFT` from `agents.py` (no changes needed)
- Reuses: `build_context_package()` from `context_builder.py` (no changes needed)
- Uses `ChatAnthropic.invoke()` instead of raw `client.messages.create()`
- Returns: `{"code": ..., "last_critique": ..., "edgeworth_history": [new_user_msg, ai_response]}`
- The `add_messages` reducer handles history appending automatically

### `light_node(state) -> dict`
- Replaces: `light_turn()` in `agents.py`
- Same pattern as `edgeworth_node`
- Also returns `"round": state["round"] + 1` — Light still increments the counter

### `intern_node(state) -> dict`
- Replaces: `intern_summary()` in `agents.py` and `orchestrator.summon_intern()`
- Single-shot LLM call, reuses `INTERN_SYSTEM` from `agents.py`
- Returns `{}` — terminal node

### `should_continue(state) -> str`
- Replaces: the `for` loop termination condition in `orchestrator._run_real_loop()`
- Returns `"edgeworth"` or `"intern"` based on `state["round"] > state["max_rounds"]`

**Note on context trimming:** `context_trimmer.py` is **replaced entirely** by the `add_messages` reducer plus `trim_messages()` from `langchain_core`. No manual trimming code needed. See the notebook for the pattern.

**Done when:** all four node functions are defined, importable, and individually testable with a mock state dict.

---

## Phase 4: Graph Assembly

**Files to create:**
- `langgraph_impl/graph.py`

**Work:**
Build and compile the `StateGraph`:

```python
graph = StateGraph(CCAState)
graph.add_node("edgeworth", edgeworth_node)
graph.add_node("light", light_node)
graph.add_node("intern", intern_node)
graph.set_entry_point("edgeworth")
graph.add_edge("edgeworth", "light")
graph.add_conditional_edges("light", should_continue, {
    "edgeworth": "edgeworth",
    "intern": "intern",
})
graph.add_edge("intern", END)

checkpointer = SqliteSaver.from_conn_string("cca_sessions.db")
cca_app = graph.compile(checkpointer=checkpointer)
```

**Done when:** `cca_app.compile()` succeeds and `cca_app.get_graph().draw_ascii()` shows the correct topology.

---

## Phase 5: Entry Point

**Files to create:**
- `langgraph_impl/main.py`

**Work:**
Replace `main.py` CLI + `orchestrator.run()` + `orchestrator.summon_intern()` with a `cca_app.invoke()` call. The new entry point:

1. Parses CLI args (same interface: `--rounds`, `--no-placeholder`)
2. Gets the feature request (same `_get_feature_request()` logic)
3. Builds initial state
4. Calls `cca_app.invoke(initial_state, config={"configurable": {"thread_id": session_id}})`
5. Prints the final result

**Note on `USE_VOICE` / `USE_OBS`:** These are side effects inside the original agent functions (`say_as()`, `obs_manager`). In the LangGraph version, these can remain as side effects inside the nodes — LangGraph does not restrict node side effects.

**Done when:** `python langgraph_impl/main.py` runs a full session end-to-end with real LLM calls.

---

## Phase 5.5: OBS WebSocket Integration

**Files involved:**
- `obs_manager.py` — no changes needed
- `voice.py` — no changes needed
- `langgraph_impl/main.py` — startup init (same as current `main.py`)
- `langgraph_impl/main.py` stream observer — where `say_as()` moves (see Phase 7)

### Current architecture (important to understand before migrating)

OBS show/hide is not called directly by agent functions — it is **owned by `say_as()` in `voice.py`**:

```python
def say_as(agent_name: str, text: str, enabled: bool = False) -> None:
    _obs_show(name)          # show portrait BEFORE speaking
    try:
        # ... ElevenLabs or Mac `say` TTS ...
    finally:
        _obs_hide(name)      # hide portrait AFTER speaking (even on error)
```

`_obs_show()` / `_obs_hide()` call `get_obs_manager()` (the module-level singleton) and toggle the OBS source visibility for that agent's portrait. This means OBS behavior is a free side effect of calling `say_as()` — you don't wire OBS separately.

The startup sequence in the current `main.py`:
```python
if args.obs:
    config.USE_OBS = True
    from obs_manager import init_obs_manager
    init_obs_manager()     # TCP probe → WebSocket connect → sets _obs_manager singleton
```

### What changes in the LangGraph version

**Startup init — no change.** Call `init_obs_manager()` in `langgraph_impl/main.py` before `cca_app.invoke()` or `cca_app.stream()`, same as the current `main.py`. The singleton is then available globally via `get_obs_manager()`.

**Per-turn source switching — depends on where `say_as()` is called.**

The LangGraph version has two options:

#### Option A: Keep `say_as()` as a node side effect (minimal migration work)

Leave `say_as()` calls inside `edgeworth_node` and `light_node`, same as the current `agents.py` pattern. OBS show/hide comes along automatically. No changes to `obs_manager.py` or `voice.py`.

Downside: nodes have side effects, making them harder to test in isolation.

#### Option B: Move `say_as()` to the stream observer (recommended for Phase 7)

In the Phase 7 stream observer in `langgraph_impl/main.py`, call `say_as()` when a node emits a critique. OBS show/hide still comes along automatically — it's baked into `say_as()`.

```python
from voice import say_as

for chunk in cca_app.stream(initial_state, stream_mode="updates"):
    node_name = list(chunk.keys())[0]
    delta = chunk[node_name]

    critique = delta.get("last_critique", "")
    if critique:
        # say_as() internally calls _obs_show() → TTS → _obs_hide()
        say_as(node_name.upper(), critique, enabled=config.USE_VOICE)
        print(f"\n[{node_name.upper()}] {critique}\n")
```

This keeps nodes pure (no audio/OBS side effects) and centralizes all output — terminal printing, TTS, and OBS source switching — in one place.

### Config fields (no changes needed)

All OBS config is read from `config.py` by `obs_manager.py` and `voice.py` directly:

| Field | Purpose |
|---|---|
| `USE_OBS` | Gate — set to `True` by `--obs` CLI flag |
| `OBS_HOST` / `OBS_PORT` / `OBS_PASSWORD` | WebSocket connection details |
| `OBS_SCENE` | OBS scene that contains the agent source items |
| `EDGEWORTH_OBS_SOURCE` | Name of the Edgeworth portrait source in OBS |
| `LIGHT_OBS_SOURCE` | Name of the Light portrait source in OBS |
| `INTERN_OBS_SOURCE` | Name of the Intern portrait source in OBS |

`langgraph_impl/main.py` imports `config` directly — these fields are already available with no changes.

### Graceful degradation (preserve current behavior)

`init_obs_manager()` in `obs_manager.py` already handles all failure cases:
- `obs-websocket-py` not installed → prints warning, returns `None`
- OBS not running (TCP probe fails) → prints warning, returns `None`
- WebSocket handshake fails → prints warning, `_obs_manager` stays `None`

`_obs_show()` / `_obs_hide()` in `voice.py` both guard with `if obs:` — so if `init_obs_manager()` returned `None`, all OBS calls are no-ops. This behavior is preserved for free.

**Done when:** `python langgraph_impl/main.py --obs` shows each agent's portrait in OBS for the duration of their TTS output, matching the original behavior. `python langgraph_impl/main.py` (without `--obs`) runs cleanly with no OBS calls.

---

## Phase 6: Human-in-the-Loop (replaces `feedback.py`)

**Files to modify:**
- `langgraph_impl/graph.py` (add `interrupt_before`)
- `langgraph_impl/main.py` (add feedback loop using `app.update_state()` + `app.invoke(None, config)`)

**Work:**
Replace `run_feedback_mode()` in `feedback.py` with LangGraph's native human-in-the-loop:

```python
# Compile with interrupt
cca_app = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["light"],  # pause before Light runs
)

# In main.py: after Edgeworth runs, pause for human input
# Human can modify state["last_critique"] before Light sees it
# Resume with app.invoke(None, config=config)
```

The fan-out behavior from `feedback.py` (both agents responding to feedback independently) can be modeled as a subgraph or as a separate `feedback_graph` invoked from the main loop.

**Done when:** the LangGraph implementation supports interactive pause + resume between Edgeworth and Light turns.

---

## Phase 7: Streaming + Observability

**Work:**
Replace the inline `print()` calls in each agent function with a single `stream()` observer in `main.py`:

```python
from voice import say_as

for chunk in cca_app.stream(initial_state, stream_mode="updates"):
    node_name = list(chunk.keys())[0]
    delta = chunk[node_name]

    critique = delta.get("last_critique", "")
    code = delta.get("code", "")

    if critique:
        # say_as() internally calls _obs_show() → TTS → _obs_hide()
        # so OBS portrait switching and voice output both happen here
        say_as(node_name.upper(), critique, enabled=config.USE_VOICE)
        _critique_block(node_name.upper(), critique)   # reuse the styled print from orchestrator.py

    if code:
        print(f"  [{node_name.upper()}] wrote {len(code)} chars")
```

This is important for the tutorial — it shows that observability (printing, TTS, OBS) moves from inside individual agent functions to a single boundary in `main.py`. Nodes become pure: they make LLM calls and return state updates, nothing else.

**Done when:** terminal output from the LangGraph version matches the original's visual style (colored banners, critique blocks) but is driven from the `stream()` observer rather than from inside nodes.

---

## What NOT to change

- `context_builder.py` — reuse as-is. It produces a string; wrap it in `HumanMessage`. No framework coupling.
- `agents.py` system prompts (`EDGEWORTH_SYSTEM`, `LIGHT_SYSTEM`, etc.) — reuse as-is.
- `config.py` model names and flags — reuse as-is.
- `obs_manager.py` — no changes needed. `init_obs_manager()` is called once at startup; the singleton is used everywhere via `get_obs_manager()`.
- `voice.py` — no changes needed. `say_as()` already owns OBS show/hide internally via `_obs_show()` / `_obs_hide()`. In Option B (recommended), `say_as()` moves from inside nodes to the stream observer in `main.py` — the file itself is untouched.
- `workspace_manager.py` — keep as a side effect in `edgeworth_node` / `light_node` if disk writes are desired.

---

## Suggested Tutorial Structure

The migration makes a natural 2-part tutorial:

1. **Part A (existing):** Build the hand-rolled version. Understand the problem deeply. This IS `ChaosCodingAgents` as it stands.
2. **Part B (this migration):** Rebuild it with LangGraph. Compare each piece. The before/after is the lesson.

The `learn/langchain_langgraph/langchain_langgraph_intro.ipynb` notebook is the companion material for Part B.
