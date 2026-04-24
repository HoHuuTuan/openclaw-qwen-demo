# OpenClaw + Qwen Stable Context Demo

Local demo for this product message:

`The optimization solution prevents Qwen-side overload/crash risk by reducing OpenClaw context bloat enough for realistic prompts to complete successfully.`

The app does not use real API keys, does not call Qwen, and does not require the
real OpenClaw runtime. It simulates optimized OpenClaw-style context
construction, then returns a useful answer plus secondary stability details.

## Main Flow

1. User enters a realistic OpenClaw/Qwen task.
2. Backend builds an optimized context package.
3. Backend sends the optimized package through the Qwen-facing adapter.
4. UI shows the answer as the main output.
5. A collapsible `Stability details` panel shows estimated tokens, latency,
   crash-risk level, compacted context preview, and optimization steps.

If `QWEN_API_BASE_URL` is configured, `/api/ask` uses the HTTP adapter. If not,
the adapter falls back to a local mock answer so the demo still runs offline.
The old comparison endpoints remain available for experimentation, but the main
demo is now prompt-to-answer through the optimized Qwen path.

## Run Local

```bash
cd openclaw-qwen-demo
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.server:app --reload --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

## Run With Docker

```bash
docker compose up --build
```

Open:

```text
http://127.0.0.1:8000
```

## Primary API

```http
POST /api/ask
Content-Type: application/json

{
  "prompt": "Explain why a Qwen long-context setup can still become unstable if an agent framework injects too much redundant context."
}
```

Response shape:

```json
{
  "status": "ok",
  "prompt": "...",
  "answer": "...",
  "mode": "optimized-qwen-path",
  "stable": true,
  "metrics": {
    "estimated_tokens": 409,
    "crash_risk": "low",
    "latency_estimate": 845,
    "context_size_label": "optimized"
  },
  "context_preview": "...",
  "optimization_applied": [
    "minimal system prompt",
    "compact AGENTS instructions",
    "pointer-style memory references",
    "summarized sub-agent context",
    "pruned tools/context",
    "removed repeated context blocks"
  ],
  "notes": "Request completed through optimized context path.",
  "adapter": {
    "provider": "mock-qwen-adapter",
    "used_mock": true,
    "real_qwen_enabled": false
  }
}
```

## Where To Add Real Qwen Later

The optimized context is built in `backend/optimize.py`:

```text
simulate_optimized()
ask_with_optimized_context()
```

The Qwen-facing adapter is in `backend/qwen_client.py`.

To use a real Qwen-compatible endpoint, set:

```text
QWEN_API_BASE_URL=http://your-host/v1
QWEN_API_KEY=optional-key
QWEN_MODEL=qwen-model-name
```

`ask_with_optimized_context()` already routes through the adapter. If no base
URL is configured, the adapter returns the mock fallback answer.

## Secondary APIs

These remain for technical comparison/debugging:

```text
GET /api/health
GET /api/compare?prompt=...&mode=compare
POST /api/compare
GET /api/run/raw?prompt=...
GET /api/run/optimized?prompt=...
```
