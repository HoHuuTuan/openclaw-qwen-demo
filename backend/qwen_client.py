"""Qwen-facing adapter with a mock fallback for local demos."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib import error, request


@dataclass(frozen=True)
class QwenResult:
    answer: str
    provider: str
    used_mock: bool
    success: bool
    error: str | None = None
    elapsed_ms: int | None = None
    status_code: int | None = None
    raw_response: dict[str, Any] | None = None


class QwenClient:
    """Thin adapter so the optimized demo can plug into a real Qwen call later."""

    def __init__(self) -> None:
        self.base_url = os.getenv("QWEN_API_BASE_URL", "").strip().rstrip("/")
        self.api_key = os.getenv("QWEN_API_KEY", "").strip()
        self.model = os.getenv("QWEN_MODEL", "qwen-local-demo").strip()

    @property
    def enabled(self) -> bool:
        return bool(self.base_url)

    def complete(self, *, prompt: str, optimized_context: str, fallback_answer: str) -> QwenResult:
        return self.complete_from_messages(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are answering through an optimized OpenClaw-style context path. "
                        "Use the provided compact context and give a practical answer."
                    ),
                },
                {"role": "system", "content": optimized_context},
                {"role": "user", "content": prompt},
            ],
            fallback_answer=fallback_answer,
            allow_mock_fallback=True,
        )

    def complete_from_messages(
        self,
        *,
        messages: list[dict[str, str]],
        fallback_answer: str = "",
        allow_mock_fallback: bool = False,
        timeout_seconds: int = 45,
    ) -> QwenResult:
        if not self.enabled:
            if allow_mock_fallback:
                return QwenResult(
                    answer=fallback_answer,
                    provider="mock-qwen-adapter",
                    used_mock=True,
                    success=True,
                    raw_response=None,
                )
            return QwenResult(
                answer="",
                provider="qwen-http-adapter",
                used_mock=False,
                success=False,
                error="QWEN_API_BASE_URL chua duoc cau hinh.",
                raw_response=None,
            )

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req = request.Request(
            url=f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        started_at = time.perf_counter()
        try:
            with request.urlopen(req, timeout=timeout_seconds) as response:
                raw = json.loads(response.read().decode("utf-8"))
                status_code = getattr(response, "status", None)
        except error.HTTPError as exc:
            elapsed_ms = int((time.perf_counter() - started_at) * 1000)
            detail = exc.read().decode("utf-8", errors="ignore").strip()
            fallback = fallback_answer if allow_mock_fallback else ""
            if allow_mock_fallback:
                return QwenResult(
                    answer=fallback,
                    provider="mock-qwen-adapter",
                    used_mock=True,
                    success=True,
                    error=f"HTTP {exc.code}: {detail or exc.reason}",
                    elapsed_ms=elapsed_ms,
                    status_code=exc.code,
                    raw_response=None,
                )
            return QwenResult(
                answer="",
                provider="qwen-http-adapter",
                used_mock=False,
                success=False,
                error=f"HTTP {exc.code}: {detail or exc.reason}",
                elapsed_ms=elapsed_ms,
                status_code=exc.code,
                raw_response=None,
            )
        except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            elapsed_ms = int((time.perf_counter() - started_at) * 1000)
            if allow_mock_fallback:
                return QwenResult(
                    answer=fallback_answer,
                    provider="mock-qwen-adapter",
                    used_mock=True,
                    success=True,
                    error=str(exc),
                    elapsed_ms=elapsed_ms,
                    raw_response=None,
                )
            return QwenResult(
                answer="",
                provider="qwen-http-adapter",
                used_mock=False,
                success=False,
                error=str(exc),
                elapsed_ms=elapsed_ms,
                raw_response=None,
            )

        answer_text = extract_answer_text(raw) or fallback_answer
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        return QwenResult(
            answer=answer_text,
            provider="qwen-http-adapter",
            used_mock=False,
            success=bool(answer_text.strip()),
            elapsed_ms=elapsed_ms,
            status_code=status_code,
            raw_response=raw,
        )


def extract_answer_text(raw: dict[str, Any]) -> str:
    choices = raw.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""

    first = choices[0]
    if not isinstance(first, dict):
        return ""

    message = first.get("message")
    if isinstance(message, dict):
        content = message.get("content", "")
        if isinstance(content, str):
            return content.strip()

    text = first.get("text", "")
    if isinstance(text, str):
        return text.strip()

    return ""
