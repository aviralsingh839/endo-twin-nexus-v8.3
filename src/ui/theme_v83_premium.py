"""Compatibility shim: the active ENDO-TWIN visual system lives in theme.py.

Keeping this importable prevents older screens from drifting into a second
visual language while the project is migrated to the unified design system.
"""
from src.ui.theme import *  # noqa: F401,F403
