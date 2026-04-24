"""Synthetic OpenClaw pipeline demonstrating raw vs optimized context pressure."""

from __future__ import annotations

import re

from .demo_data import (
    DEFAULT_PROMPT,
    CONVERSATION_HISTORY,
    LONG_TOOL_OUTPUT_SEED,
    RAW_AGENTS,
    RAW_MEMORY,
    RAW_SOUL,
    RAW_TOOLS,
    ROOT,
    VAULT_POINTERS,
    read_vault_file,
)
from .model_client import generate_response
from .optimize import (
    build_minimal_prompt,
    calculate_reduction,
    compact_history,
    estimate_tokens,
    trim_head_tail,
)
from .subagent import summarize_large_output


def _normalize_prompt(prompt: str | None) -> str:
    cleaned = " ".join((prompt or "").split())
    return cleaned or DEFAULT_PROMPT


def _prompt_profile(prompt: str) -> dict[str, int | list[str] | str]:
    terms = re.findall(r"[a-zA-Z0-9_+-]{3,}", prompt.lower())
    unique_terms = sorted(set(terms))
    topics = [
        keyword
        for keyword in ["qwen", "openclaw", "agent", "memory", "tools", "history", "vault", "sub-agent", "pruning", "compaction", "vllm", "latency", "timeout", "crash"]
        if keyword in prompt.lower()
    ]
    prompt_chars = len(prompt)
    pressure = 1 + min(8, max(1, prompt_chars // 80) + len(topics))
    return {
        "terms": unique_terms[:12],
        "topics": topics[:8],
        "prompt_chars": prompt_chars,
        "pressure": pressure,
        "topic_text": ", ".join(topics[:6]) if topics else "general",
    }


def _long_tool_output(prompt: str) -> str:
    profile = _prompt_profile(prompt)
    term_line = ", ".join(profile["terms"]) or "general runtime issue"
    block = (
        f"Prompt focus: {prompt}\n"
        f"Detected topics: {profile['topic_text']}\n"
        f"Key terms: {term_line}\n"
        f"{LONG_TOOL_OUTPUT_SEED}\n"
        "Repeated observation: the runtime keeps resending long system files, history, and logs.\n"
    )
    repeated = block * (520 + int(profile["pressure"]) * 45)
    max_chars = min(120_000, 78_000 + int(profile["pressure"]) * 4200)
    return repeated[:max_chars]


def build_raw_openclaw_context(prompt: str) -> dict[str, str]:
    profile = _prompt_profile(prompt)
    tool_output = _long_tool_output(prompt)
    history_seed = [
        *CONVERSATION_HISTORY,
        f"Prompt-specific concern: {prompt}",
        f"Detected runtime topics: {profile['topic_text']}.",
        f"Prompt length observed: {profile['prompt_chars']} chars.",
    ]
    history = "\n".join(f"- {item}" for item in history_seed * (10 + int(profile["pressure"])))
    return {
        "SOUL.md": (RAW_SOUL + f"\nPrompt pressure marker: {profile['topic_text']}.\n") * (34 + int(profile["pressure"]) * 3),
        "AGENTS.md": (RAW_AGENTS + f"\nPrompt branch expansion for: {prompt}\n") * (28 + int(profile["pressure"]) * 3),
        "MEMORY.md": (RAW_MEMORY + f"\nSticky memory tags: {', '.join(profile['terms']) or 'general'}\n") * (25 + int(profile["pressure"]) * 3),
        "TOOLS.md": (RAW_TOOLS + f"\nTool replay reason: {profile['topic_text']}\n") * (22 + int(profile["pressure"]) * 2),
        "history": history,
        "tool_outputs": tool_output,
        "logs_search_results": trim_head_tail(tool_output * 2, max_chars=95_000),
        "task": prompt,
    }


def build_optimized_openclaw_context(prompt: str) -> dict[str, str]:
    minimal = build_minimal_prompt(prompt)
    tool_output = _long_tool_output(prompt)
    subagent = summarize_large_output(tool_output)
    profile = _prompt_profile(prompt)
    compacted = compact_history(
        [
            *CONVERSATION_HISTORY[-3:],
            f"Active task: {prompt}",
            f"Focus topics: {profile['topic_text']}",
        ]
    )
    return {
        "SOUL.md": minimal["SOUL"],
        "AGENTS.md": minimal["AGENTS"],
        "MEMORY.md": minimal["MEMORY"],
        "TOOLS.md": minimal["TOOLS"],
        "history_summary": compacted,
        "subagent_summary": subagent.summary,
        "pruned_tool_context": trim_head_tail(tool_output, max_chars=1200),
        "task": minimal["TASK"],
    }


def _join_context(parts: dict[str, str]) -> str:
    return "\n\n".join(f"## {name}\n{content.strip()}" for name, content in parts.items())


def simulate_crash_risk(context: str) -> dict[str, str | int]:
    chars = len(context)
    tokens = estimate_tokens(context)
    if chars >= 180_000 or tokens >= 45_000:
        return {
            "status": "timeout_simulated",
            "crash_reason": "Prompt too large: prefill pressure and repeated runtime scaffolding would likely hang or timeout the Qwen backend.",
            "crash_risk": "critical",
        }
    if chars >= 80_000 or tokens >= 20_000:
        return {
            "status": "crash_risk",
            "crash_reason": "Context is bloated enough that OpenClaw-style overhead can push the backend into timeout/crash territory.",
            "crash_risk": "high",
        }
    return {
        "status": "safe",
        "crash_reason": "Context is small enough to stay in a stable operating range for the demo backend.",
        "crash_risk": "low",
    }


def simulate_latency(context: str) -> str:
    chars = len(context)
    seconds = max(0.4, chars / 280.0)
    if seconds >= 120:
        return f"{seconds:.1f}s"
    if seconds >= 1:
        return f"{seconds:.1f}s"
    return f"{int(seconds * 1000)}ms"


def run_raw_demo(prompt: str | None = None) -> dict:
    normalized = _normalize_prompt(prompt)
    raw_parts = build_raw_openclaw_context(normalized)
    raw_context = _join_context(raw_parts)
    risk = simulate_crash_risk(raw_context)
    before_chars = len(raw_context)
    tokens = estimate_tokens(raw_context)
    return {
        "mode": "raw",
        "status": risk["status"],
        "before_chars": before_chars,
        "after_chars": before_chars,
        "estimated_tokens": tokens,
        "estimated_latency": simulate_latency(raw_context),
        "crash_reason": risk["crash_reason"],
        "crash_risk": risk["crash_risk"],
        "prompt": normalized,
        "explanation": "Raw OpenClaw-style context overloaded the model backend.",
        "context_preview": trim_head_tail(raw_context, max_chars=3500),
    }


def run_optimized_demo(prompt: str | None = None) -> dict:
    normalized = _normalize_prompt(prompt)
    raw_parts = build_raw_openclaw_context(normalized)
    optimized_parts = build_optimized_openclaw_context(normalized)
    raw_context = _join_context(raw_parts)
    optimized_context = _join_context(optimized_parts)
    before_chars = len(raw_context)
    after_chars = len(optimized_context)
    model = generate_response(optimized_context)
    return {
        "mode": "optimized",
        "status": "success",
        "prompt": normalized,
        "before_chars": before_chars,
        "after_chars": after_chars,
        "reduction_percent": calculate_reduction(before_chars, after_chars),
        "estimated_tokens_before": estimate_tokens(raw_context),
        "estimated_tokens_after": estimate_tokens(optimized_context),
        "estimated_latency_before": simulate_latency(raw_context),
        "estimated_latency_after": simulate_latency(optimized_context),
        "crash_risk_before": simulate_crash_risk(raw_context)["crash_risk"],
        "crash_risk_after": simulate_crash_risk(optimized_context)["crash_risk"],
        "model_response": model["response"],
        "model_provider": model["provider"],
        "used_mock": model["used_mock"],
        "explanation": "Optimized context is small enough for the model backend.",
        "context_preview": trim_head_tail(optimized_context, max_chars=3500),
    }


def run_subagent_demo(prompt: str | None = None) -> dict:
    normalized = _normalize_prompt(prompt)
    tool_output = _long_tool_output(normalized)
    summary = summarize_large_output(tool_output)
    return {
        "mode": "subagent",
        "status": "success",
        "prompt": normalized,
        "raw_tool_output_chars": summary.raw_chars,
        "summary_chars": summary.summary_chars,
        "reduction_percent": summary.reduction_percent,
        "raw_tool_output_preview": summary.raw_preview,
        "subagent_summary": summary.summary,
        "explanation": "Sub-agent absorbs huge tool output and returns only a compact summary to the orchestrator.",
    }


def vault_strategy_payload() -> dict:
    entries = []
    for label, rel_path in VAULT_POINTERS.items():
        text = read_vault_file(rel_path)
        entries.append(
            {
                "label": label,
                "path": rel_path,
                "preview": trim_head_tail(text, max_chars=700),
            }
        )
    return {
        "mode": "vault",
        "memory_strategy": "MEMORY.md keeps only pointers to vault files instead of injecting long documents.",
        "entries": entries,
    }


def run_side_by_side_compare(prompt: str | None = None) -> dict:
    raw = run_raw_demo(prompt)
    optimized = run_optimized_demo(prompt)
    subagent = run_subagent_demo(prompt)
    return {
        "prompt": _normalize_prompt(prompt),
        "raw": raw,
        "optimized": optimized,
        "subagent": subagent,
        "comparison": {
            "raw_context_size": raw["before_chars"],
            "optimized_context_size": optimized["after_chars"],
            "token_estimate_raw": raw["estimated_tokens"],
            "token_estimate_optimized": optimized["estimated_tokens_after"],
            "reduction_percent": optimized["reduction_percent"],
            "crash_risk_raw": raw["crash_risk"],
            "crash_risk_optimized": optimized["crash_risk_after"],
            "model_response": optimized["model_response"],
        },
    }
