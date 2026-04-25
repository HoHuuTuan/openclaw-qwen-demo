# OpenClaw Compaction And Pruning

Compaction turns previous turns into a short durable state: what the user wants, what decisions were made, what constraints matter, and what remains open.

Pruning removes context that does not help the next model call: repeated logs, old branches, full schemas, stale search results, and raw tool output already summarized elsewhere.

Together they keep each model request close to the active task. This is why a smaller optimized prompt can be more stable than a huge raw prompt even on a model with a large context window.
