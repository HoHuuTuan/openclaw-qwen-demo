# Qwen vLLM Deploy Notes

This demo does not run vLLM or call Qwen. It uses local estimates to communicate
the operational lesson.

In real model serving, long prompts increase prefill time and memory pressure.
If an agent runtime sends the same large prompt, tool definitions, and memory
blocks on every step, each step pays that cost again. Large prompts can also
increase queue depth and timeout probability.

Useful production metrics include:

- prompt tokens
- output tokens
- prefill latency
- decode latency
- timeout count
- KV cache pressure
- model-server queue depth
- retry count

For a safe demo, estimated metrics are enough to show the pattern without any
keys or infrastructure.
