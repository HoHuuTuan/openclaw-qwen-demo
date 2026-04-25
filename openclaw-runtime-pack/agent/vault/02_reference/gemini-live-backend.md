Gemini 2.5 Flash is used as the live backend in the current demo because Qwen key is not available.

This does not change the context strategy.
It only swaps the model provider so the leader can see a stable live answer path:

optimized OpenClaw-style context -> Gemini 2.5 Flash -> used_mock=false when key exists

When Qwen key becomes available, only the provider/model setting changes.
The minimal prompt files, vault pointers, sub-agent summary, pruning, and compaction stay the same.
