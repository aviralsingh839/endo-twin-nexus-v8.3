"""Global configuration for CHRONO-TWIN NEXUS V8.3.

Conservative defaults - this is an educational research prototype,
not a medical device.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

# V8.3 branding
APP_VERSION = "8.3.0"
APP_VERSION_LABEL = "V8.3, Modular Multimodal Longitudinal Health Platform (research prototype, not clinically validated)"
APP_NAME = "CHRONO-TWIN NEXUS"
APP_TAGLINE = "Sense • Understand • Track • Personalize"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
MODEL_DIR = PROJECT_ROOT / "models"
LOG_DIR = DATA_DIR / "raw"

# Legacy reference
LEGACY_V81_ROOT = PROJECT_ROOT / "chrono_pcos_project V8"

SERIAL_BAUD = 115200
SERIAL_TIMEOUT_S = 0.2
RECONNECT_RETRY_S = 3.0
STALE_DATA_TIMEOUT_S = 6.0
WIFI_BRIDGE_DEFAULT_PORT = 7777

# Baseline
BASELINE_CAPTURE_S = 300.0
BASELINE_MIN_SAMPLES = 60
BASELINE_MIN_DAYS = 3  # minimum days for stable longitudinal baseline
BASELINE_ROLLING_WINDOW_DAYS = 14
BASELINE_CONFIDENCE_MIN_OBS = 30

# Feature logging
FEATURE_LOG_INTERVAL_S = 10.0

# Sampling targets
PPG_FS_HZ = 50.0
IMU_FS_HZ = 50.0
GSR_FS_HZ = 10.0
TEMP_FS_HZ = 1.0

# HR limits
MIN_HR_BPM = 35.0
MAX_HR_BPM = 210.0
MIN_IBI_S = 60.0 / MAX_HR_BPM
MAX_IBI_S = 60.0 / MIN_HR_BPM

# Signal quality
MIN_IR_FINGER_PRESENT = 5000
MAX_ADC_18BIT = 262143
PPG_SATURATION_MARGIN = 4000

# Risk thresholds - research signals, not diagnosis
RISK_LOW = 25.0
RISK_MEDIUM = 50.0
RISK_HIGH = 75.0

# Longitudinal engine
LONGITUDINAL_WINDOW_SHORT_H = 24
LONGITUDINAL_WINDOW_MEDIUM_H = 72
LONGITUDINAL_WINDOW_LONG_H = 168  # 7 days
PERSISTENCE_MIN_POINTS = 3
PERSISTENCE_MIN_HOURS = 12
TREND_SLOPE_THRESHOLD = 0.5
RECOVERY_THRESHOLD = 0.3

# Physiology defaults when personal baseline unavailable
DEFAULT_RESTING_HR = 72.0
DEFAULT_RMSSD_MS = 42.0
DEFAULT_SKIN_TEMP_C = 32.5
DEFAULT_GSR_RAW = 450.0
DEFAULT_ACTIVITY = 0.10
DEFAULT_SLEEP_DURATION_H = 7.5

# Dashboard timing
UI_PLOT_HISTORY_S = 180
RISK_UPDATE_INTERVAL_S = 2.0
FEATURE_UPDATE_INTERVAL_S = 1.0
TREND_PLOT_DAYS = 90

# Disease modules enabled by default
ENABLED_MODULES = ["pcos", "sleep", "cardiometabolic", "autonomic"]

# Future modules placeholder
FUTURE_MODULES = ["thyroid", "renal", "hepatic", "infectious", "oncology", "neurodegenerative"]


@dataclass
class UserProfile:
    """Non-sensitive user inputs. No names or identifiers."""

    age_years: float = 17.0
    bmi: float | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    waist_cm: float | None = None
    systolic_bp: float | None = None
    diastolic_bp: float | None = None
    cycle_day: int | None = None
    usual_cycle_length_days: int | None = None
    days_since_last_period: int | None = None
    years_post_menarche: float | None = None
    cycle_irregular: bool | None = None
    glucose_mg_dl: float | None = None
    glucose_context: str = "unknown"
    time_since_meal_min: float | None = None
    # V8.3 additions
    sex: str | None = None  # for module gating, optional
    smoking_status: str | None = None
    family_history: List[str] = field(default_factory=list)


DEFAULT_PROFILE = UserProfile()


# Data labeling constants - NEVER mix silently
DATA_LABEL_REAL = "REAL"
DATA_LABEL_SYNTHETIC = "SYNTHETIC"
DATA_LABEL_SIMULATED = "SIMULATED"
DATA_LABEL_PUBLIC = "PUBLIC DATASET"
DATA_LABEL_USER = "USER-ENTERED"

# Provenance labels
PROVENANCE_MEASURED = "MEASURED"
PROVENANCE_PATIENT_REPORTED = "PATIENT-REPORTED"
PROVENANCE_CLINICALLY_ENTERED = "CLINICALLY-ENTERED"
PROVENANCE_IMAGE_DERIVED = "IMAGE-DERIVED"
PROVENANCE_MODEL_INFERRED = "MODEL-INFERRED"
PROVENANCE_UNKNOWN = "UNKNOWN"
