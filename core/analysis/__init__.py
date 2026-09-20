"""Analysis - disease modules, fusion, chrono-metabolic"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.disease_modules.pcos_module import PCOSModule
    from src.disease_modules.sleep_module import SleepModule
    from src.disease_modules.cardiometabolic_module import CardiometabolicModule
    from src.disease_modules.autonomic_module import AutonomicModule
    from src.fusion.multimodal_fusion import MultimodalFusion
    from src.explainability.shap_explainer import ShapExplainer
except ImportError:
    PCOSModule = None
    SleepModule = None
    CardiometabolicModule = None
    AutonomicModule = None
    MultimodalFusion = None
    ShapExplainer = None

__all__ = ['PCOSModule','SleepModule','CardiometabolicModule','AutonomicModule','MultimodalFusion','ShapExplainer']
