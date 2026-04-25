# Gemini Live Backend

This demo uses Gemini 2.5 Flash as the live backend because no Qwen key is available yet.

Gemini is not the core claim. It is a practical replacement so the leader can type questions and see a real optimized runtime flow. The backend owns the key through `GEMINI_API_KEY`; the frontend never receives or calls the key directly.

If `GEMINI_API_KEY` is missing, or if the request fails because of quota or network issues, the backend returns a mock answer. The context optimization metrics are still real for the synthetic OpenClaw-style prompt, so the demo does not fail during presentation.
