# Qwen OpenClaw Context Strategy

Qwen 120k has a large advertised context window, but an OpenClaw runtime can still crash or time out when it injects too much material every turn.

The problem is context bloat: long SOUL/AGENTS/MEMORY/TOOLS files, uncompressed history, raw tool output, search logs, and copied vault documents all add prefill cost. The model limit is not the only limit. Runtime latency, gateway timeout, memory pressure, and provider quotas can fail before the theoretical window is reached.

The fix is to keep the working prompt small from the start. Minimal prompt files stay injected. Long knowledge remains in vault. MEMORY.md stores pointers. Large tool output is summarized by a sub-agent. History is compacted. Low value context is pruned before the backend call.
