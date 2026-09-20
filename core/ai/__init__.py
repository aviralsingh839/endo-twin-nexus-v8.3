"""AI/ML wrappers"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.core.training import ModelTrainer
    from src.core.evaluation import ModelEvaluator
except ImportError:
    ModelTrainer = None
    ModelEvaluator = None

__all__ = ['ModelTrainer','ModelEvaluator']
