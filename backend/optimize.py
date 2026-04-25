"""Runtime context optimization helpers for the live chat demo."""

from __future__ import annotations

from .demo_data import CONVERSATION_HISTORY, LONG_TOOL_OUTPUT_SEED, VAULT_POINTERS, read_vault_file
from .subagent import summarize_large_output


OPTIMIZATION_STEPS = [
    "minimal prompt files",
    "vault pointers",
    "sub-agent summary",
    "pruning",
    "compaction",
]


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def trim_head_tail(text: str, max_chars: int = 3500) -> str:
    if len(text) <= max_chars:
        return text
    head = max_chars // 2
    tail = max_chars - head
    omitted = len(text) - max_chars
    return f"{text[:head]}\n\n...[trimmed {omitted} chars]...\n\n{text[-tail:]}"


def compact_history(messages: list[str]) -> str:
    if not messages:
        return "History: none."
    recent = messages[-5:]
    return "Compact history:\n" + "\n".join(f"- {item}" for item in recent)


def build_subagent_summary(large_output: str) -> str:
    return summarize_large_output(large_output).summary


def build_vault_pointer_context() -> str:
    lines = ["Vault pointers, not full documents:"]
    for label, path in VAULT_POINTERS.items():
        lines.append(f"- {label}: {path}")
    return "\n".join(lines)


def _short_vault_excerpt() -> str:
    path = VAULT_POINTERS["pruning/compaction"]
    return trim_head_tail(read_vault_file(path), max_chars=750)


def _join_context(parts: dict[str, str]) -> str:
    return "\n\n".join(f"## {name}\n{content.strip()}" for name, content in parts.items())


def optimize_context(raw_context: str, user_message: str) -> str:
    from .prompt_builder import build_optimized_context_parts

    parts = build_optimized_context_parts(user_message)
    parts["vault_excerpt"] = _short_vault_excerpt()
    return _join_context(parts)


def calculate_reduction(before: int, after: int) -> int:
    if before <= 0:
        return 0
    return max(0, min(100, round((1 - after / before) * 100)))


def crash_risk_for_context(text: str) -> str:
    chars = len(text)
    tokens = estimate_tokens(text)
    if chars > 90_000 or tokens > 22_500:
        return "high"
    if chars > 35_000 or tokens > 8_750:
        return "medium"
    return "low"


def context_budget(before_context: str, after_context: str) -> dict[str, int | str]:
    before = len(before_context)
    after = len(after_context)
    return {
        "before_chars": before,
        "after_chars": after,
        "tokens_before": estimate_tokens(before_context),
        "tokens_after": estimate_tokens(after_context),
        "reduction_percent": calculate_reduction(before, after),
        "crash_risk": "low",
    }


def synthetic_large_tool_output(user_message: str) -> str:
    seed = (
        f"User task: {user_message}\n"
        f"{LONG_TOOL_OUTPUT_SEED}\n"
        "Repeated note: full logs and raw search output should not be injected into the main model call.\n"
    )
    return (seed * 900)[:95_000]


def compact_demo_history(user_message: str) -> str:
    return compact_history([*CONVERSATION_HISTORY, f"Current user question: {user_message}"])
