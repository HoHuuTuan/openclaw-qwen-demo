"""Build raw and optimized OpenClaw-style prompts."""

from __future__ import annotations

from .demo_data import (
    RAW_AGENTS,
    RAW_MEMORY,
    RAW_SOUL,
    RAW_TOOLS,
    read_prompt_file,
)
from .optimize import (
    build_subagent_summary,
    build_vault_pointer_context,
    compact_demo_history,
    synthetic_large_tool_output,
    trim_head_tail,
)


def join_context(parts: dict[str, str]) -> str:
    return "\n\n".join(f"## {name}\n{content.strip()}" for name, content in parts.items())


def build_raw_context_parts(user_message: str) -> dict[str, str]:
    large_output = synthetic_large_tool_output(user_message)
    return {
        "SOUL.md": (RAW_SOUL + "\n") * 40,
        "AGENTS.md": (RAW_AGENTS + "\n") * 34,
        "MEMORY.md": (RAW_MEMORY + "\n") * 32,
        "TOOLS.md": (RAW_TOOLS + "\n") * 26,
        "history": (compact_demo_history(user_message) + "\n") * 18,
        "raw_tool_output": large_output,
        "task": user_message,
    }


def build_optimized_context_parts(user_message: str) -> dict[str, str]:
    large_output = synthetic_large_tool_output(user_message)
    return {
        "SOUL.md": read_prompt_file("SOUL.md"),
        "AGENTS.md": read_prompt_file("AGENTS.md"),
        "MEMORY.md": read_prompt_file("MEMORY.md"),
        "TOOLS.md": read_prompt_file("TOOLS.md"),
        "history_summary": compact_demo_history(user_message),
        "vault_pointers": build_vault_pointer_context(),
        "subagent_summary": build_subagent_summary(large_output),
        "pruned_tool_excerpt": trim_head_tail(large_output, max_chars=950),
        "task": user_message,
        "instruction": "Answer the user using only the optimized context. Be concise and practical.",
    }


def build_raw_context(user_message: str) -> str:
    return join_context(build_raw_context_parts(user_message))


def build_optimized_prompt(user_message: str) -> str:
    return join_context(build_optimized_context_parts(user_message))
