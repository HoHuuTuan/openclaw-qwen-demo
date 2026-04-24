"""FastAPI entrypoint for the OpenClaw + Qwen context optimization demo."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .fake_openclaw_pipeline import (
    run_optimized_demo,
    run_raw_demo,
    run_side_by_side_compare,
    run_subagent_demo,
    vault_strategy_payload,
)


ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT / "frontend"

app = FastAPI(
    title="OpenClaw + Qwen 120k Context Optimization Demo",
    version="2.0.0",
)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


class DemoRequest(BaseModel):
    prompt: str = ""


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/demo/raw")
def demo_raw(request: DemoRequest) -> dict:
    return run_raw_demo(request.prompt)


@app.post("/demo/optimized")
def demo_optimized(request: DemoRequest) -> dict:
    return run_optimized_demo(request.prompt)


@app.post("/demo/subagent")
def demo_subagent(request: DemoRequest) -> dict:
    return run_subagent_demo(request.prompt)


@app.get("/demo/vault")
def demo_vault() -> dict:
    return vault_strategy_payload()


@app.get("/demo/compare")
def demo_compare(prompt: str = "") -> dict:
    return run_side_by_side_compare(prompt)
