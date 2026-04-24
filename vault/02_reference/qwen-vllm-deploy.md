When Qwen is served through a local vLLM or Ollama-like stack, long prompts make prefill slower
and increase memory pressure.

For a demo, the important lesson is not vendor setup details. The key lesson is operational:
large repeated prompt scaffolding creates latency spikes, queueing, and timeout risk.

That is why the demo keeps model access optional and stable mock mode as the default.
