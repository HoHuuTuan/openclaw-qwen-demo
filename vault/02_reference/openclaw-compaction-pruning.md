Compaction converts long history into a short durable summary.
Pruning removes low-value context before the next model call.

In practice:
- keep only the active goal
- keep only the latest decision
- keep only the unresolved risk
- trim head/tail of long noisy outputs
- hand large tool output to a sub-agent and keep the summary

This is how an OpenClaw-style runtime stays far below the dangerous prompt size zone.
