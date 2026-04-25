"""FastAPI entrypoint for the optimized runtime live chat demo."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .model_client import active_model, active_provider, generate_answer, has_gemini_key
from .optimize import OPTIMIZATION_STEPS, context_budget, optimize_context
from .prompt_builder import build_raw_context
from .vault import vault_pointer_items


ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT / "frontend"
CONFIG_PATH = ROOT / "config" / "openclaw_gemini_optimized.json"

app = FastAPI(
    title="OpenClaw + Gemini Optimized Runtime Live Chat Demo",
    version="3.1.0",
)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {
        "ok": True,
        "gemini_key_present": has_gemini_key(),
        "provider": active_provider(),
        "model": active_model(),
    }


@app.post("/chat")
def chat(request: ChatRequest) -> dict:
    message = " ".join(request.message.split()) or "Explain how OpenClaw avoids context overload."
    raw_context = build_raw_context(message)
    optimized_prompt = optimize_context(raw_context, message)
    model = generate_answer(optimized_prompt)
    return {
        "answer": model["answer"],
        "provider": model["provider"],
        "model": model["model"],
        "used_mock": model["used_mock"],
        "warning": model.get("warning"),
        "context": context_budget(raw_context, optimized_prompt),
        "optimization_steps": OPTIMIZATION_STEPS,
    }


@app.get("/strategy")
def strategy() -> dict:
    return {
        "summary": "Demo now uses Gemini 2.5 Flash live when GEMINI_API_KEY is available.",
        "why_large_windows_still_crash": (
            "Qwen 120k or Gemini can still timeout when an agent runtime injects long prompt files, "
            "uncompacted history, raw logs, large tool output, and full vault documents into every turn. "
            "A large context window does not remove prefill cost, gateway timeout, or memory pressure."
        ),
        "optimized_runtime": (
            "Demo now uses Gemini 2.5 Flash live when GEMINI_API_KEY is available. "
            "Gemini replaces Qwen only for live backend demonstration. The backend sends only the optimized prompt: "
            "minimal prompt files, MEMORY pointers, short vault excerpts, sub-agent summaries, pruning, and compaction."
        ),
        "transfer_to_qwen": (
            "The context optimization strategy transfers to Qwen when Qwen key is available. "
            "When Qwen is ready, only provider/model changes; the optimized runtime strategy stays the same."
        ),
        "vault": vault_pointer_items(),
    }


@app.get("/config/openclaw")
def openclaw_config() -> FileResponse:
    return FileResponse(CONFIG_PATH, media_type="application/json")
