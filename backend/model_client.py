"""Model client with mock-by-default behavior and optional Ollama fallback."""

from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any
from urllib import error, request

from .demo_data import MOCK_MODEL_RESPONSES


def mock_generate(prompt: str) -> dict[str, Any]:
    normalized = " ".join(prompt.split())
    digest = int(hashlib.md5(normalized.encode("utf-8")).hexdigest()[:8], 16)
    template = MOCK_MODEL_RESPONSES[digest % len(MOCK_MODEL_RESPONSES)]
    task_match = re.search(r"##\s*task\s+(.+?)(?:\s+## |\Z)", prompt, re.DOTALL | re.IGNORECASE)
    task_text = " ".join(task_match.group(1).split()) if task_match else normalized
    excerpt = task_text[:180] + ("..." if len(task_text) > 180 else "")
    return {
        "provider": "mock",
        "used_mock": True,
        "response": f"{template}\n\nPrompt đang hỏi: {excerpt}",
    }


def _ollama_urls() -> list[str]:
    explicit = os.getenv("OLLAMA_URL", "").strip()
    if explicit:
        return [explicit]
    return [
        "http://host.docker.internal:11434/api/generate",
        "http://localhost:11434/api/generate",
    ]


def generate_response(prompt: str) -> dict[str, Any]:
    if os.getenv("USE_OLLAMA", "").lower() != "true":
        return mock_generate(prompt)

    payload = {
        "model": os.getenv("OLLAMA_MODEL", "qwen2.5:3b"),
        "prompt": prompt,
        "stream": False,
    }
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}

    for url in _ollama_urls():
        req = request.Request(url=url, data=body, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=25) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except (error.URLError, error.HTTPError, TimeoutError, json.JSONDecodeError):
            continue

        text = str(raw.get("response", "")).strip()
        if text:
            return {
                "provider": "ollama",
                "used_mock": False,
                "response": text,
            }

    fallback = mock_generate(prompt)
    fallback["provider"] = "mock-fallback-after-ollama-error"
    return fallback
