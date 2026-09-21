"""Dependency-free convention for future disease-model discovery.

Entry points may be added by packaged modules, but ENDO-TWIN can still operate
without installed plugins. Discovery errors are isolated per plugin.
"""
from __future__ import annotations

from importlib import metadata
from typing import Iterable, List, Any


def discover_disease_models(group: str = "endo_twin.disease_models") -> List[Any]:
    discovered: List[Any] = []
    try:
        entries = metadata.entry_points()
        entries = entries.select(group=group) if hasattr(entries, "select") else entries.get(group, [])
    except Exception:
        return discovered
    for entry in entries:
        try:
            discovered.append(entry.load())
        except Exception:
            continue
    return discovered
