"""Small vault access layer for the demo."""

from __future__ import annotations

from .demo_data import VAULT_POINTERS, read_vault_file
from .optimize import trim_head_tail


def vault_pointer_items() -> list[dict[str, str]]:
    return [
        {
            "label": label,
            "path": path,
            "excerpt": trim_head_tail(read_vault_file(path), max_chars=650),
        }
        for label, path in VAULT_POINTERS.items()
    ]
