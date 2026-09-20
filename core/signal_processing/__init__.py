"""Signal processing wrappers - preserve V8.3 src/signal_processing"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.signal_processing.filtering import Filtering
    from src.signal_processing.baseline import BaselineRemoval
    from src.signal_processing.artifact import ArtifactDetection
except ImportError:
    Filtering = None
    BaselineRemoval = None
    ArtifactDetection = None

__all__ = ['Filtering', 'BaselineRemoval', 'ArtifactDetection']
