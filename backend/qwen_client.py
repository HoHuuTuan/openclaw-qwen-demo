"""Backward-compatible wrapper around the demo model client."""

from __future__ import annotations

from .model_client import generate_response


def complete(prompt: str) -> dict:
    return generate_response(prompt)
