"""Optimization helpers following the OpenClaw optimization guide mindset."""

from __future__ import annotations

from pathlib import Path

from .demo_data import DEFAULT_PROMPT, ROOT, read_prompt_file


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def trim_head_tail(text: str, max_chars: int = 4000) -> str:
    if len(text) <= max_chars:
        return text
    head = max_chars // 2
    tail = max_chars - head
    omitted = len(text) - max_chars
    return f"{text[:head]}\n\n...[trimmed {omitted:,} chars]...\n\n{text[-tail:]}"


def compact_history(history: list[str]) -> str:
    if not history:
        return "No history."
    selected = history[-4:]
    return "Compact history:\n" + "\n".join(f"- {item}" for item in selected)


def build_minimal_prompt(prompt: str = DEFAULT_PROMPT) -> dict[str, str]:
    return {
        "SOUL": read_prompt_file("SOUL.md").strip(),
        "AGENTS": read_prompt_file("AGENTS.md").strip(),
        "MEMORY": read_prompt_file("MEMORY.md").strip(),
        "TOOLS": read_prompt_file("TOOLS.md").strip(),
        "TASK": prompt.strip() or DEFAULT_PROMPT,
    }


def optimize_openclaw_context(raw_context: str) -> str:
    return trim_head_tail(raw_context, max_chars=4000)


def calculate_reduction(before: int, after: int) -> int:
    if before <= 0:
        return 0
    return max(0, 100 - int(after / before * 100))


def relative_demo_path(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")
