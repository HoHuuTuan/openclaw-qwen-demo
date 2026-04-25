"""Synthetic data used to show context pressure without calling Qwen."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MINIMAL_PROMPT_DIR = ROOT / "minimal_prompt"

DEFAULT_PROMPT = (
    "Vì sao OpenClaw làm Qwen 120k bị timeout, và bản optimized runtime live chat này giải quyết thế nào?"
)

RAW_SOUL = """
You are OpenClaw with a very large persistent identity. Inject all principles, safety notes,
prior project details, operating style, edge cases, old assumptions, and complete runtime policy
into every request even when the user asks a small question.
""".strip()

RAW_AGENTS = """
Planner expands every branch. Researcher copies complete references. ToolRouter includes every
tool contract. MemoryKeeper attaches every memory. Reviewer repeats past incidents. Do not prune,
compact, summarize, or route large output away from the main prompt.
""".strip()

RAW_MEMORY = """
Long-term memory eagerly includes incidents, deploy notes, old experiments, full references,
unrelated architecture choices, copied logs, search results, and previous task transcripts.
""".strip()

RAW_TOOLS = """
Tools: shell, search, browser, subagent, vault, compact, memory, planner, verifier. Include every
schema, example, warning, approval rule, and result formatting rule on every model call.
""".strip()

CONVERSATION_HISTORY = [
    "Qwen backend crash/timeout happened when OpenClaw sent too much context.",
    "No real Qwen key is available in this demo environment.",
    "Gemini 2.5 Flash is used only as a live backend replacement.",
    "The fix is context optimization before the model call.",
    "Raw tool output must be summarized by a sub-agent.",
    "Long notes stay in vault and MEMORY.md keeps pointers.",
]

LONG_TOOL_OUTPUT_SEED = """
[tool-output]
The optimization guide recommends minimal prompt files, pointer-based memory, vault storage for
long knowledge, sub-agent summaries for large tool output, history compaction, and pruning before
the next model call. Repeating raw logs increases prefill cost and can turn a large context window
into a slow or unstable runtime.
""".strip()

MOCK_MODEL_RESPONSES = [
    "Optimized context stayed small, so the backend can answer without overload.",
    "Long knowledge was moved into vault pointers and only a short excerpt was injected.",
    "Sub-agent summary, pruning, and compaction reduced prompt pressure before the model call.",
]

VAULT_POINTERS = {
    "qwen strategy": "vault/01_thinking/qwen-openclaw-context-strategy.md",
    "gemini backend": "vault/02_reference/gemini-live-backend.md",
    "pruning/compaction": "vault/02_reference/openclaw-compaction-pruning.md",
}


def read_prompt_file(name: str) -> str:
    return (MINIMAL_PROMPT_DIR / name).read_text(encoding="utf-8")


def read_vault_file(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")
