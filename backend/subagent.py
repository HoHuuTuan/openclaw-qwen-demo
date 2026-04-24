"""Sub-agent simulation for the optimized demo path."""

from __future__ import annotations

from dataclasses import dataclass

from .demo_data import KNOWLEDGE_ARTICLES


@dataclass(frozen=True)
class SubAgentResult:
    name: str
    summary: str
    source_paths: list[str]
    original_chars: int
    summary_chars: int


def run_research_subagent(query: str) -> SubAgentResult:
    """Return a concise summary instead of a full transcript.

    This models the optimization-guide idea that sub-agents should shield the
    main agent from bulky intermediate context.
    """

    source_paths = [article["path"] for article in KNOWLEDGE_ARTICLES]
    original = "\n\n".join(article["body"].strip() for article in KNOWLEDGE_ARTICLES)

    short_query = " ".join(query.split())[:180]
    summary = (
        f"Task focus: {short_query}. "
        "Long context is theoretical capacity, not a safe runtime budget. "
        "OpenClaw-style agents add prompt overhead from identity, tools, memory, "
        "history, retrieved knowledge, and sub-agent transcripts. Keep core "
        "prompts minimal, retrieve focused vault excerpts, prune stale context, "
        "and compact prior work before each model call."
    )

    return SubAgentResult(
        name="researcher",
        summary=summary,
        source_paths=source_paths,
        original_chars=len(original),
        summary_chars=len(summary),
    )
