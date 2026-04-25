"""Gemini 2.5 Flash client with safe mock fallback."""

from __future__ import annotations

import os
from typing import Any


GEMINI_MODEL = "gemini-2.5-flash"
MOCK_MODEL = "mock-optimized-context"
MISSING_KEY_WARNING = "GEMINI_API_KEY/GOOGLE_API_KEY is missing; using mock fallback."


def get_gemini_api_key() -> str | None:
    """Prefer GEMINI_API_KEY, then GOOGLE_API_KEY."""
    return os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip() or None


def has_gemini_key() -> bool:
    return get_gemini_api_key() is not None


def active_provider() -> str:
    return "gemini" if has_gemini_key() else "mock"


def active_model() -> str:
    return GEMINI_MODEL if has_gemini_key() else MOCK_MODEL


def _safe_error_message(exc: Exception) -> str:
    message = str(exc) or type(exc).__name__
    api_key = get_gemini_api_key()
    if api_key:
        message = message.replace(api_key, "[redacted]")
    return message[:300]


def _mock_answer(warning: str) -> dict[str, Any]:
    return {
        "answer": (
            "Mock fallback only. Add GEMINI_API_KEY to enable Gemini live mode. "
            "The optimized-context pipeline still ran: minimal prompt files, vault pointers, "
            "sub-agent summary, pruning, and compaction were applied before the mock response."
        ),
        "provider": "mock",
        "model": MOCK_MODEL,
        "used_mock": True,
        "warning": warning,
    }


def generate_answer(prompt: str) -> dict[str, Any]:
    api_key = get_gemini_api_key()
    if not api_key:
        return _mock_answer(MISSING_KEY_WARNING)

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        answer = (response.text or "").strip()
        if not answer:
            raise RuntimeError("Gemini returned an empty response.")
        return {
            "answer": answer,
            "provider": "gemini",
            "model": GEMINI_MODEL,
            "used_mock": False,
            "warning": None,
        }
    except Exception as exc:  # noqa: BLE001 - demo must never crash if Gemini fails.
        safe_message = _safe_error_message(exc)
        return _mock_answer(f"Gemini API failed: {safe_message}")
