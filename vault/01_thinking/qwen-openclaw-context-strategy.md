Qwen 120k context window is only the theoretical upper bound of the model.

Inside an OpenClaw-style runtime, the usable context is smaller because every turn may also carry:
- prompt identity files
- agent routing rules
- memory blocks
- tool specs
- history
- logs and search results
- output budget

The stable strategy is to treat context as scarce.
Keep prompt files tiny, store long knowledge in vault documents, retrieve only short excerpts,
and make sub-agents return summaries instead of full transcripts.
