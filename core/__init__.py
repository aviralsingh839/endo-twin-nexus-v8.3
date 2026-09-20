"""
CHRONO-PCOS V8.3+ Core Module - Modular architecture wrapping V8.3 existing core.

Preserves ALL V8.3 functionality, provides clean imports for new ecosystem.

Structure:
core/
  signal_processing/ - wrappers around src/signal_processing
  sensors/ - wrappers around src/sensors + new unified interface
  features/ - wrappers around src/core/feature_extraction
  analysis/ - disease_modules, fusion, chrono-metabolic fingerprinting
  ai/ - AI/ML models, training, evaluation
  ultrasound/ - ultrasound pipeline
  chrono_metabolic/ - chrono-metabolic fingerprinting

This package re-exports V8.3 core for backward compatibility and new modular usage.
"""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Re-export V8.3 core modules for preservation
try:
    from src.core.feature_extraction import RealtimeFeatureExtractor
    from src.core.baseline_calibration import BaselineCalibrator
    from src.core.quality_control import SensorQualityControl
    from src.core.training import ModelTrainer
    from src.core.evaluation import ModelEvaluator
except ImportError:
    # Fallback if src not available
    RealtimeFeatureExtractor = None
    BaselineCalibrator = None
    SensorQualityControl = None
    ModelTrainer = None
    ModelEvaluator = None

try:
    from src.disease_modules import PCOSModule, SleepModule, CardiometabolicModule, AutonomicModule
except ImportError:
    PCOSModule = None
    SleepModule = None
    CardiometabolicModule = None
    AutonomicModule = None

try:
    from src.signal_processing import Filtering, BaselineRemoval, ArtifactDetection
except ImportError:
    Filtering = None
    BaselineRemoval = None
    ArtifactDetection = None

__all__ = [
    'RealtimeFeatureExtractor',
    'BaselineCalibrator',
    'SensorQualityControl',
    'ModelTrainer',
    'ModelEvaluator',
    'PCOSModule',
    'SleepModule',
    'CardiometabolicModule',
    'AutonomicModule',
    'Filtering',
    'BaselineRemoval',
    'ArtifactDetection',
]
