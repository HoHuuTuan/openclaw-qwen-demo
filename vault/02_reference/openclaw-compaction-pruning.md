# OpenClaw Compaction and Pruning

Compaction converts long histories into compact state. Pruning removes
irrelevant or stale context before a model call.

An optimized OpenClaw-style runtime should maintain explicit budgets for:

- identity and operating rules
- active task
- retrieved knowledge
- tool descriptions
- memory
- sub-agent outputs
- response space

The optimization flow is:

1. Minimize SOUL / AGENTS / MEMORY / TOOLS.
2. Store long references in a vault.
3. Retrieve focused excerpts only.
4. Require sub-agent summaries.
5. Prune stale or low-priority sections.
6. Compact prior work into a short handoff.

This keeps the model call stable even when the underlying model advertises a
large context window.
