Decision tree:
1. If tool output is large, send it to a sub-agent and keep only the summary.
2. If long knowledge is needed, read the vault and inject only short excerpts.
3. If history grows, compact it before the next model call.
4. Keep the main orchestrator prompt minimal at all times.
