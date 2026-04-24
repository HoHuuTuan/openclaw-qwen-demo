# Qwen + OpenClaw Context Strategy

Qwen long-context models can expose large theoretical context windows, such as
120k tokens. In an agent runtime, usable context is smaller because the runtime
adds overhead before the user task reaches the model.

Typical overhead includes SOUL/identity prompts, agent routing instructions,
tool schemas, long-term memory, retrieved documents, prior turns, scratchpads,
sub-agent outputs, safety wrappers, and reserved response tokens.

The practical strategy is to treat context as a scarce runtime resource:

- Keep SOUL, AGENTS, MEMORY, and TOOLS minimal.
- Move long-lived knowledge into a vault.
- Retrieve only task-relevant excerpts.
- Require sub-agents to return summaries, not transcripts.
- Prune stale context before each model call.
- Compact completed work into short durable state.

The goal is not to fill the 120k window. The goal is to stay far below the
timeout and reliability cliff.
