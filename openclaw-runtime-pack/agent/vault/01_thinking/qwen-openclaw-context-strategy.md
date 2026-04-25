Qwen or Gemini can still crash or timeout if OpenClaw injects too much context every turn.

The model window is not the same as safe usable runtime budget.
Real pressure comes from:
- SOUL.md
- AGENTS.md
- MEMORY.md
- TOOLS.md
- history
- tool outputs
- logs and search results

The stable path is to minimize injected files, keep only pointers to long knowledge,
use sub-agent summaries, prune aggressively, and compact long sessions.
