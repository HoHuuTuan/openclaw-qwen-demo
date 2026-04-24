"""Local FastAPI server for the OpenClaw/Qwen optimization demo."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .optimize import ask_with_optimized_context, compare_modes, simulate_optimized, simulate_raw


ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT / "frontend"

app = FastAPI(
    title="OpenClaw Qwen Context Optimization Demo",
    description="Local-only simulation. No API keys. No real OpenClaw runtime.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


class DemoRequest(BaseModel):
    prompt: str = ""
    mode: str = "compare"


class AskRequest(BaseModel):
    prompt: str


@app.get("/")
def index() -> FileResponse:
    return FileResponse(
        FRONTEND_DIR / "index.html",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "runtime": "local simulation"}


@app.post("/api/ask")
def ask(request: AskRequest) -> dict:
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Vui lòng nhập prompt.")
    return ask_with_optimized_context(request.prompt)


@app.get("/api/run/raw")
def run_raw(prompt: str = "") -> dict:
    raw = simulate_raw(prompt)
    return raw.__dict__ | {"sections": [section.__dict__ for section in raw.sections]}


@app.get("/api/run/optimized")
def run_optimized(prompt: str = "") -> dict:
    optimized = simulate_optimized(prompt)
    return optimized.__dict__ | {
        "sections": [section.__dict__ for section in optimized.sections]
    }


@app.get("/api/compare")
def compare(prompt: str = "", mode: str = "compare") -> dict:
    return compare_modes(prompt=prompt, mode=mode)


@app.post("/api/compare")
def compare_post(request: DemoRequest) -> dict:
    return compare_modes(prompt=request.prompt, mode=request.mode)
