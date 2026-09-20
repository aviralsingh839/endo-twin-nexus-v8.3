"""Ultrasound wrappers - preserve V8.3 ultrasound pipeline"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ultrasound modules may exist in src or elsewhere
# Preserve existing functionality, don't fake

__all__ = []
