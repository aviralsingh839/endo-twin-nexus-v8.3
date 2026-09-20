"""
ENDO-TWIN Main App - General Platform

ENDO-TWIN is the platform, CHRONO-PCOS is its first disease-specific model.
"""

try:
    from .main_app import EndoTwinMainApp, EndoTwinMainWindow, main
except ImportError:
    from .main_app import EndoTwinMainApp, main
    EndoTwinMainWindow = None

__all__ = ["EndoTwinMainApp", "EndoTwinMainWindow", "main"]
