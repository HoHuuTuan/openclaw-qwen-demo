"""Sub-agent simulation for compressing large tool output."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SubagentSummary:
    raw_chars: int
    summary_chars: int
    reduction_percent: int
    raw_preview: str
    summary: str


def summarize_large_output(tool_output: str) -> SubagentSummary:
    stripped = " ".join(tool_output.split())
    raw_chars = len(tool_output)
    prompt_focus = ""
    match = re.search(r"Prompt focus:\s*(.+?)\s*(?:\[search-result\]|\[tool-log\]|Repeated observation:)", tool_output, re.DOTALL)
    if match:
        prompt_focus = " ".join(match.group(1).split())[:180]
    sentences = [
        "Sub-agent summary:",
        "The raw tool output was too large to keep in the main OpenClaw turn.",
        "Most of the content repeated the same warning: long prompt scaffolding inflates prefill cost.",
        "The actionable result is to keep minimal prompt files, move long notes to vault, and return only compact findings.",
        "This summary is what the main orchestrator should keep instead of the full 80k-120k char transcript.",
    ]
    if prompt_focus:
        sentences.append(f"Current prompt focus: {prompt_focus}.")
    if raw_chars > 90_000:
        sentences.append("The observed raw output was well into the danger zone for timeout and backend instability.")
    summary = " ".join(sentences)
    summary_chars = len(summary)
    reduction = max(0, 100 - int(summary_chars / max(1, raw_chars) * 100))
    return SubagentSummary(
        raw_chars=raw_chars,
        summary_chars=summary_chars,
        reduction_percent=reduction,
        raw_preview=stripped[:600],
        summary=summary,
    )
