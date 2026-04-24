"""Demo fixtures for the OpenClaw + Qwen context overload simulation.

The strings here are intentionally synthetic. They model the shape of a
real agent runtime prompt without requiring OpenClaw, Qwen, or API keys.
"""

from __future__ import annotations


CONTEXT_WINDOW_TOKENS = 120_000
SAFE_RUNTIME_BUDGET_TOKENS = 36_000


USER_TASK = (
    "Investigate why Qwen with a 120k context window crashes or times out "
    "when connected to an OpenClaw-style agent runtime, then propose a stable "
    "optimization strategy for production-like usage."
)


RAW_SOUL = """
You are OpenClaw, a persistent autonomous software agent. You must keep every
policy, memory, tool contract, prior decision, repository note, stack trace,
conversation branch, and speculative plan available at all times. Never drop
context. Always include full agent identity, operating principles, routing
rules, task history, previous summaries, tool descriptions, execution traces,
and retrieved documents in the next model call.
"""


RAW_AGENTS = """
Agents:
- Planner: expands tasks into exhaustive plans.
- Researcher: reads all documents and returns full notes.
- Coder: reads every file before changing code.
- Reviewer: receives the complete repository history.
- MemoryKeeper: appends every observation to long-term memory.
- ToolRouter: includes every tool schema in every turn.
Each agent returns verbose reasoning, full source excerpts, all failed paths,
and every possible future branch. No agent is allowed to summarize.
"""


RAW_MEMORY = """
Long-term memory includes previous deployment logs, historical incident notes,
all model serving experiments, all vLLM flags, all OpenClaw prompt variants,
all team retrospectives, all TODOs, all unrelated architecture notes, and
complete copies of reference documents. Memory is injected eagerly.
"""


RAW_TOOLS = """
Tools:
- shell: full operating system command execution contract with examples.
- browser: full web navigation contract with detailed policies.
- file_search: recursive repository search contract.
- vector_retriever: full knowledge-base retrieval contract.
- planner: long-running planning interface.
- subagent_spawn: sub-agent orchestration contract.
All tool docs are injected completely even when a task only needs one tool.
"""


KNOWLEDGE_ARTICLES = [
    {
        "title": "Qwen 120k Context Strategy",
        "path": "vault/01_thinking/qwen-openclaw-context-strategy.md",
        "body": """
Qwen long-context models can expose very large theoretical windows. In an
agent runtime, the usable window is smaller because the runtime adds hidden
overhead: system prompt, tool schemas, memory, agent routing instructions,
retrieved documents, scratchpads, safety wrappers, intermediate observations,
and output budget. A 120k context window is not a guarantee that 120k tokens
of arbitrary prompt bloat will run quickly or reliably.

The stable approach is to design context as a scarce runtime resource. Keep
SOUL, AGENTS, MEMORY, and TOOLS minimal. Move long reference knowledge into a
vault and retrieve only the narrow passages needed by the task. Ask sub-agents
to return short structured summaries, not full transcripts. Prune stale turns
and compact previous work into durable summaries. Keep the active prompt below
a safe operating budget rather than aiming for the model maximum.
""",
    },
    {
        "title": "Qwen vLLM Deploy Notes",
        "path": "vault/02_reference/qwen-vllm-deploy.md",
        "body": """
When serving long-context Qwen models through vLLM-like infrastructure, latency
and memory pressure rise with prompt length. Large prefill phases can dominate
request time. If the agent runtime repeatedly resends huge system prompts,
tool schemas, and memory blocks, each step pays the cost again. Production
setups should monitor prompt tokens, prefill latency, KV cache pressure,
timeout counts, and model-server queue depth.

For demos, use estimated metrics instead of real keys. This keeps the example
safe, reproducible, and vendor-neutral while still showing the operational
lesson: context size is a reliability variable.
""",
    },
    {
        "title": "OpenClaw Compaction and Pruning",
        "path": "vault/02_reference/openclaw-compaction-pruning.md",
        "body": """
Compaction converts long interaction histories into compact state. Pruning
removes irrelevant or stale context before a model call. A healthy agent
runtime has explicit context budgets for identity, active task, retrieved
knowledge, tool specs, memory, sub-agent outputs, and response space.

An optimized OpenClaw-style runtime should inject only the minimal operating
prompt, retrieve focused vault excerpts, require sub-agent summaries, remove
irrelevant history, and compact remaining state into a short handoff.
""",
    },
]


CONVERSATION_HISTORY = [
    "User asked for a demo proving that larger context windows do not remove the need for context discipline.",
    "Agent explored a simulated OpenClaw prompt with large SOUL, AGENTS, MEMORY, and TOOLS blocks.",
    "Research sub-agent returned full deployment notes instead of a concise summary.",
    "Planner expanded every possible branch, including unrelated model-serving options.",
    "Reviewer warned that repeated full-context injection can trigger timeout risk.",
    "User clarified that no real API keys or OpenClaw runtime should be required.",
    "Agent decided to create a local FastAPI and static UI demonstration.",
]


def repeated_block(label: str, body: str, repeat: int) -> str:
    """Build a synthetic long prompt section."""

    chunks = []
    for index in range(1, repeat + 1):
        chunks.append(f"## {label} copy {index}\n{body.strip()}")
    return "\n\n".join(chunks)


def scaled_repeat(base: int, pressure: float) -> int:
    return max(1, round(base * pressure))


def build_raw_context(
    user_task: str = USER_TASK,
    pressure: float = 1.0,
    task_notes: str = "",
) -> dict[str, str]:
    """Return intentionally bloated prompt sections."""

    vault_dump = "\n\n".join(
        f"# {article['title']}\n{article['body'].strip()}" for article in KNOWLEDGE_ARTICLES
    )
    history_dump = "\n".join(f"- {item}" for item in CONVERSATION_HISTORY)

    return {
        "SOUL": repeated_block("SOUL", RAW_SOUL, scaled_repeat(75, pressure)),
        "AGENTS": repeated_block("AGENTS", RAW_AGENTS, scaled_repeat(80, pressure)),
        "MEMORY": repeated_block("MEMORY", RAW_MEMORY + "\n" + history_dump, scaled_repeat(90, pressure)),
        "TOOLS": repeated_block("TOOLS", RAW_TOOLS, scaled_repeat(70, pressure)),
        "KNOWLEDGE": repeated_block("KNOWLEDGE", vault_dump, scaled_repeat(65, pressure)),
        "SUBAGENTS": repeated_block(
            "SUBAGENT FULL TRANSCRIPT",
            "Researcher transcript: " + " ".join(article["body"].strip() for article in KNOWLEDGE_ARTICLES),
            scaled_repeat(55, pressure),
        ),
        "TASK_ANALYSIS": task_notes,
        "TASK": user_task,
    }


def build_minimal_context(
    user_task: str = USER_TASK,
    task_notes: str = "",
) -> dict[str, str]:
    """Return compact operating prompt sections used by the optimized mode."""

    return {
        "SOUL": "Operate as a focused local demo agent. Treat context as scarce. Prefer concise state.",
        "AGENTS": "Use one planner and one researcher. Sub-agents must return structured summaries only.",
        "MEMORY": "Remember only the active objective, latest decision, and unresolved risk.",
        "TOOLS": "Use local simulation tools only. No real OpenClaw runtime. No real API keys.",
        "TASK_ANALYSIS": task_notes,
        "TASK": user_task,
    }
