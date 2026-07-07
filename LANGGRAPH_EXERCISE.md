# LangGraph Implementation Exercise

## Instructions for Claude (read this first)

You are a coding tutor. The user is working through the `langgraph_impl/` skeleton files in this repo, filling in TODO blanks to learn LangGraph by rebuilding ChaosCodingAgents.

**Your role:**
- Guide ONE TODO at a time. Do not jump ahead.
- Never fill in a TODO yourself. Explain the concept, let the user try, then review their answer.
- If they're stuck, give a hint — not the answer. Give the answer only if they ask directly or after two failed attempts.
- After they fill in a TODO correctly, confirm what they got right and explain WHY it's correct before moving on.
- If their answer is wrong, explain what's off and ask them to try again.

**The learning path follows the TODO numbers in order (1 → 17).**

Start by asking: "Ready to start? Open `langgraph_impl/state.py` — we'll begin with TODO 1."

---

## Background (share with the user when relevant)

### What ChaosCodingAgents is

A multi-agent system where:
- **Edgeworth** and **Light** take turns rewriting code in a loop
- Each agent reads what the other just wrote and critiques it
- The **Intern** summarizes the chaos at the end
- An optional **feedback mode** lets the user talk back to both agents after the loop

The original is hand-rolled: raw Anthropic SDK calls, a custom `Orchestrator` class managing the for loop, manual history lists, and a regex parser for output tags. The `langgraph_impl/` folder is a LangGraph rewrite. The user is filling it in to learn LangGraph by doing.

### What the migration covers (and what it doesn't)

Completing all 17 TODOs produces a **fully working LangGraph implementation** of the core loop:
- State schema replacing `Orchestrator` instance variables ✓
- Agent nodes replacing `edgeworth_turn()` / `light_turn()` / `intern_summary()` ✓
- Graph wiring replacing the `for` loop and `summon_intern()` ✓
- Stream observer replacing `print()` calls inside agent functions ✓
- OBS portrait switching and voice output via the stream observer ✓

**Not covered by this exercise (future work):**
- Human-in-the-loop feedback mode replacing `feedback.py` — this uses `interrupt_before` + `update_state`, more advanced LangGraph. A natural follow-up once the core loop is working.

### What NOT to change

These files are reused as-is by the new implementation. Do not modify them:

| File | Why it's unchanged |
|---|---|
| `context_builder.py` | Produces a string; `langgraph_impl/nodes.py` wraps it in `HumanMessage`. No LangGraph coupling. |
| `agents.py` | System prompts (`EDGEWORTH_SYSTEM`, `LIGHT_SYSTEM`, etc.) are imported directly. |
| `config.py` | Model names, OBS settings, voice flags — all read by the new implementation as-is. |
| `obs_manager.py` | `init_obs_manager()` is called once at startup; singleton used everywhere via `get_obs_manager()`. |
| `voice.py` | `say_as()` already owns OBS show/hide internally — no changes needed. |

### How OBS and voice work (relevant to TODO 17)

OBS source switching is **not wired separately** — it's a free side effect of calling `say_as()` in `voice.py`:

```python
def say_as(agent_name, text, enabled=False):
    _obs_show(name)       # show portrait BEFORE speaking
    try:
        # ElevenLabs or Mac `say` TTS...
    finally:
        _obs_hide(name)   # hide portrait AFTER speaking
```

So calling `say_as()` in the stream observer is all you need. OBS show/hide, TTS, and the `--obs` / `--voice` flags are all handled inside that one call.

**Startup:** `init_obs_manager()` in `langgraph_impl/main.py` is already written — it mirrors the current `main.py` exactly.

### Reference files for comparison

- `orchestrator.py` — the for loop and Orchestrator class being replaced
- `agents.py` — the agent turn functions being replaced by nodes
- `learn/langchain_langgraph/langchain_langgraph_intro.ipynb` — working examples of every LangGraph concept used here

---

## The 17 TODOs

### Phase 1 — State Schema (`langgraph_impl/state.py`)

**TODO 1** — Import the reducer for message accumulation
- **Concept:** LangGraph uses "reducers" to control how state fields are merged when a node returns an update. For a plain field (`str`, `int`), the returned value replaces the old one. For a list that needs to accumulate, you need a reducer that appends instead.
- **File:** `langgraph_impl/state.py`, top import block
- **Hint:** `from langgraph.graph.message import ___`
- **Checks:** Can they name `add_messages`? Can they explain what it does vs a plain list?

**TODO 2** — Type annotation for `edgeworth_history`
- **Concept:** `Annotated[type, reducer]` tells LangGraph two things: what type the field holds, and how to merge updates. Without the reducer, returning `{"edgeworth_history": [new_msg]}` would replace the entire history.
- **File:** `langgraph_impl/state.py`, `CCAState` class
- **Expected answer:** `Annotated[list[BaseMessage], add_messages]`
- **Checks:** Do they understand why `list[BaseMessage]` alone isn't enough?

**TODO 3** — Type annotation for `light_history`
- **Concept:** Same as TODO 2. Each agent has its own separate history thread.
- **File:** `langgraph_impl/state.py`, `CCAState` class
- **Expected answer:** `Annotated[list[BaseMessage], add_messages]`

**Checkpoint 1** — Verify the state schema:
```bash
python -c "from langgraph_impl.state import CCAState; print('State OK:', list(CCAState.__annotations__.keys()))"
```
Should print all 7 field names without errors.

---

### Phase 2 — Agent Nodes (`langgraph_impl/nodes.py`)

**TODO 4** — Wrap the context string in a message type
- **Concept:** LangChain uses typed message objects instead of raw `{"role": "user", "content": "..."}` dicts. `build_context_package()` returns a plain string — you need to wrap it in the right type for a "user" message.
- **File:** `langgraph_impl/nodes.py`, `edgeworth_node`
- **Expected answer:** `HumanMessage(content=pkg)`
- **Checks:** Do they know why it's `HumanMessage` and not `AIMessage`? (The orchestrator is sending context TO the agent, not the agent speaking.)

**TODO 5** — Build the full message list
- **Concept:** An LLM call needs the system prompt + the conversation history + the new message. The system prompt goes first. History is already in `state['edgeworth_history']` as a list of messages. New message goes last.
- **File:** `langgraph_impl/nodes.py`, `edgeworth_node`
- **Expected answer:** `[SystemMessage(content=system_text)] + list(state.get('edgeworth_history', [])) + [new_user_msg]`
- **Checks:** Why do we do `state.get('edgeworth_history', [])` instead of just `state['edgeworth_history']`? (Safety for the first round where history is empty.)

**TODO 6** — Return the Edgeworth state update
- **Concept:** Nodes return a PARTIAL dict — only keys that changed. Think about what Edgeworth produces and what the next agent needs.
- **File:** `langgraph_impl/nodes.py`, `edgeworth_node`
- **Expected answer:**
  ```python
  return {
      'code': code,
      'last_critique': critique,
      'edgeworth_history': [new_user_msg, response],
  }
  ```
- **Key discussion:** Why return `[new_user_msg, response]` instead of the full history? Because `add_messages` appends — you only return the NEW messages. Why NOT return `'round'`? Because Edgeworth doesn't end the round — that's Light's job.

**TODO 7** — Build Light's message list (same pattern as TODOs 4 and 5)
- **File:** `langgraph_impl/nodes.py`, `light_node`
- Ask them to do it without the hint this time.

**TODO 8** — Return Light's state update (same as TODO 6, plus one extra key)
- **Key discussion:** What extra key does Light return that Edgeworth doesn't? (`'round': r + 1`) Why Light and not Edgeworth? Light ends each full round — the counter increments after BOTH agents have spoken.

**TODO 9** — Terminal node return value
- **Concept:** The Intern is the last node. It produces no state updates — it just prints. What do you return when you have nothing to update?
- **Expected answer:** `{}` (empty dict)
- **Checks:** Do they understand that returning `{}` is valid and means "no state changes"?

**Checkpoint 2** — Verify nodes import:
```bash
python -c "from langgraph_impl.nodes import edgeworth_node, light_node, intern_node; print('Nodes OK')"
```

---

### Phase 3 — Graph Wiring (`langgraph_impl/graph.py`)

**TODO 10** — The routing function `should_continue`
- **Concept:** This is a pure function of state. It returns a string that the conditional edge uses to decide the next node. It replaces the `for` loop termination condition in `orchestrator.py`.
- **File:** `langgraph_impl/graph.py`, `should_continue`
- **Expected answer:**
  ```python
  if state['round'] > state['max_rounds']:
      return 'intern'
  return 'edgeworth'
  ```
- **Checks:** What field do they read from state? Does the return value match the keys they'll use in TODO 14?

**TODO 11** — Register the three nodes
- **Concept:** `graph.add_node('name', function)` registers a Python function as a named node. The name is what edges reference.
- **File:** `langgraph_impl/graph.py`, `build_graph`
- **Expected answer:** Three calls: `graph.add_node('edgeworth', edgeworth_node)`, `graph.add_node('light', light_node)`, `graph.add_node('intern', intern_node)`

**TODO 12** — Set the entry point
- **Expected answer:** `graph.set_entry_point('edgeworth')`
- **Checks:** Which agent goes first in CCA? Could it be Light? Why not?

**TODO 13** — Unconditional edge Edgeworth → Light
- **Concept:** After Edgeworth always comes Light. No routing needed.
- **Expected answer:** `graph.add_edge('edgeworth', 'light')`

**TODO 14** — Conditional edge from Light
- **Concept:** After Light, either loop back to Edgeworth OR go to the Intern. `add_conditional_edges` takes a routing function and a map of return values → node names.
- **Expected answer:**
  ```python
  graph.add_conditional_edges(
      'light',
      should_continue,
      {'edgeworth': 'edgeworth', 'intern': 'intern'},
  )
  ```
- **Checks:** Do the dict keys match the strings `should_continue` returns?

**TODO 15** — Connect Intern to END
- **Expected answer:** `graph.add_edge('intern', END)`
- **Checks:** What does `END` mean? (It's a sentinel — going here terminates the graph.)

**Checkpoint 3** — Compile the graph and visualize:
```bash
python -c "
from langgraph_impl.graph import cca_app
print('Graph compiled OK')
print(cca_app.get_graph().draw_ascii())
"
```
Should show the correct topology with all nodes and edges.

---

### Phase 4 — Entry Point (`langgraph_impl/main.py`)

**TODO 16** — Build the initial state
- **Concept:** `app.invoke(initial_state)` needs every field in `CCAState` present. Go through each field in `state.py` and decide the starting value.
- **File:** `langgraph_impl/main.py`, `run()`
- **Expected answer:**
  ```python
  initial_state = {
      'feature_request': feature_request,
      'max_rounds': rounds,
      'round': 1,
      'code': '',
      'last_critique': None,
      'edgeworth_history': [],
      'light_history': [],
  }
  ```
- **Key discussion:** Why does `round` start at 1 and not 0? (`should_continue` checks `round > max_rounds` — starting at 0 would give an extra round.) Why are the history lists `[]`? (No prior history on round 1.)

**TODO 17** — The stream observer
- **Concept:** `stream()` replaces the for loop body in `orchestrator.py`. Each chunk is `{node_name: state_delta}`. This is where ALL output lives — terminal printing, TTS, and OBS portrait switching. The nodes themselves stay clean (no print, no audio, no OBS calls).
- **File:** `langgraph_impl/main.py`, `run()`
- **OBS note:** You do NOT need to call `show_agent()` / `hide_agent()` here. Calling `say_as()` is enough — it handles OBS internally via `_obs_show()` / `_obs_hide()` in a try/finally. The `--obs` flag and `init_obs_manager()` startup are already handled in `main()`.
- **Expected answer:**
  ```python
  for chunk in cca_app.stream(initial_state, config=graph_config, stream_mode='updates'):
      node_name = list(chunk.keys())[0]
      delta = chunk[node_name]

      critique = delta.get('last_critique', '')
      if critique:
          say_as(node_name.upper(), critique, enabled=config.USE_VOICE)
          _critique_block(node_name.upper(), critique)

      if delta.get('code'):
          print(f'  [{node_name.upper()}] wrote {len(delta["code"])} chars')
  ```
- **Checks:** Why `list(chunk.keys())[0]`? (Each chunk has exactly one key — the node that just ran.) Why does `say_as()` here replace the OBS calls that were inside `voice.py`'s helper functions? (OBS is already baked into `say_as()` — centralizing the call here means nodes have zero side effects.)

**Checkpoint 4 (final)** — Run the full implementation:
```bash
mamba activate chaos-agents
python -m langgraph_impl.main --rounds 2
```
Should prompt for a feature request, run 2 rounds of Edgeworth + Light, then the Intern summary. Add `--voice` or `--obs` to test those paths.

---

## When you finish

### Side-by-side comparison

| Original | LangGraph equivalent |
|---|---|
| `Orchestrator.__init__` instance variables | `langgraph_impl/state.py` `CCAState` |
| `Orchestrator._run_real_loop()` for loop | `langgraph_impl/graph.py` graph edges |
| `agents.py` `edgeworth_turn()` | `langgraph_impl/nodes.py` `edgeworth_node` |
| `agents.py` `light_turn()` | `langgraph_impl/nodes.py` `light_node` |
| `agents.py` `intern_summary()` + `orchestrator.summon_intern()` | `langgraph_impl/nodes.py` `intern_node` |
| `main.py` for loop body (print, say_as, write_solution) | `langgraph_impl/main.py` stream observer |

The logic is identical. The difference is what the framework handles:
- State is a TypedDict, not instance variables on a class
- History accumulation is a reducer, not a list you manually append to
- The loop is a graph cycle, not a for loop with a manual termination check
- All output is centralized in the stream observer, not scattered inside agent functions

### What's next (not covered by this exercise)

**Human-in-the-Loop** — replacing `feedback.py`

The original `feedback.py` runs an interactive loop after the Intern where the user can send comments and both agents respond. In LangGraph this is done with `interrupt_before` + `update_state`:

```python
# Compile with a pause point
cca_app = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=['light'],   # pause before Light runs
)

# Run until the interrupt, inspect/modify state, then resume
app.invoke(None, config=config)
```

This is a natural follow-up once the core loop is working end-to-end.
