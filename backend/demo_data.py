"""Synthetic demo data for OpenClaw-style context inflation."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MINIMAL_PROMPT_DIR = ROOT / "minimal_prompt"
VAULT_DIR = ROOT / "vault"

DEFAULT_PROMPT = (
    "Phân tích vì sao backend Qwen 120k context window bị timeout hoặc crash khi cắm vào "
    "OpenClaw-style runtime, rồi trình bày cách tối ưu để payload nhỏ lại và ổn định hơn."
)

RAW_SOUL = """
You are OpenClaw, a persistent autonomous agent. Always inject the full agent identity,
all operating principles, every safety wrapper, all routing rules, all repository notes,
all prior task branches, every execution trace, and the entire standing instruction set
into every model call. Never compress identity. Never summarize previous reasoning.
Preserve full fidelity for future turns even if the current task only needs a tiny subset.
""".strip()

RAW_AGENTS = """
Agents:
- Planner: expands the task into every possible branch and contingency.
- Researcher: returns full notes and copies large source excerpts.
- ToolRouter: injects every tool contract in detail.
- MemoryKeeper: appends all observations to working memory.
- Reviewer: repeats repository history and prior mistakes.
Do not prune. Do not compact. Keep full transcripts in the main context.
""".strip()

RAW_MEMORY = """
Long-term memory contains previous incidents, model-serving notes, long deployment logs,
plugin errors, tool traces, historical action items, old experiments, unrelated architecture
decisions, repository summaries, and full copies of reference documents. Memory is always
attached eagerly instead of using pointers or retrieval.
""".strip()

RAW_TOOLS = """
Tools:
- shell: full command execution contract with examples and edge cases.
- search: full retrieval policy, result handling rules, and formatting guidance.
- browser: full browsing contract and safety policy.
- planner: exhaustive planning protocol.
- subagent: orchestration rules, handoff rules, and reporting rules.
- memory: read/write and retention rules.
Every tool definition is injected completely on every turn.
""".strip()

CONVERSATION_HISTORY = [
    "User reported Qwen backend crashes when plugged into OpenClaw runtime.",
    "Agent captured multiple timeout events during long prompt prefill.",
    "Researcher copied entire vLLM deploy notes into the main working context.",
    "Planner expanded unrelated branches such as RAG vendors, dashboards, and alerts.",
    "ToolRouter reattached all tool schemas on every step of the workflow.",
    "MemoryKeeper injected old incident summaries unrelated to the current demo.",
    "User clarified that no real Qwen key is available for the demo environment.",
    "Agent decided to prove the solution using a stable local simulation.",
]

LONG_TOOL_OUTPUT_SEED = """
[search-result]
openclaw-optimization-guide recommends keeping prompt files minimal, shifting long knowledge
into vault documents, using sub-agents to absorb large outputs, pruning stale turns, and
compacting history into a short durable state before the next model call.
[tool-log]
prefill latency grows quickly when large prompt scaffolding is resent every step. Long system
instructions, long memory blocks, full logs, and verbose tool outputs multiply the real payload.
""".strip()

MOCK_MODEL_RESPONSES = [
    "Mock model response: optimized context stayed small enough, so the backend can answer without overload.",
    "Mock model response: the payload was reduced by moving long knowledge into vault files and summarizing tool output.",
    "Mock model response: pruning + compaction lowered prompt pressure enough for a stable agent turn.",
]

VAULT_POINTERS = {
    "qwen strategy": "vault/01_thinking/qwen-openclaw-context-strategy.md",
    "vllm deploy": "vault/02_reference/qwen-vllm-deploy.md",
    "compaction/pruning": "vault/02_reference/openclaw-compaction-pruning.md",
}


def read_prompt_file(name: str) -> str:
    return (MINIMAL_PROMPT_DIR / name).read_text(encoding="utf-8")


def read_vault_file(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")
