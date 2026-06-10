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
for chunk in cca_app.stream(initial_state, stream_mode="updates"):
    node_name = list(chunk.keys())[0]
    delta = chunk[node_name]
    # Print critique, code length, round number in a single place
```

This is cosmetic but important for the tutorial — it shows that observability moves from inside agents to the graph boundary.

**Done when:** terminal output from the LangGraph version matches the original's visual style (colored banners, critique blocks) but is driven from the `stream()` observer rather than from inside nodes.

---

## What NOT to change

- `context_builder.py` — reuse as-is. It produces a string; wrap it in `HumanMessage`. No framework coupling.
- `agents.py` system prompts (`EDGEWORTH_SYSTEM`, `LIGHT_SYSTEM`, etc.) — reuse as-is.
- `config.py` model names and flags — reuse as-is.
- `voice.py`, `obs_manager.py` — side effects inside nodes; no changes needed.
- `workspace_manager.py` — keep as a side effect in `edgeworth_node` / `light_node` if disk writes are desired.

---

## Suggested Tutorial Structure

The migration makes a natural 2-part tutorial:

1. **Part A (existing):** Build the hand-rolled version. Understand the problem deeply. This IS `ChaosCodingAgents` as it stands.
2. **Part B (this migration):** Rebuild it with LangGraph. Compare each piece. The before/after is the lesson.

The `learn/langchain_langgraph/langchain_langgraph_intro.ipynb` notebook is the companion material for Part B.
