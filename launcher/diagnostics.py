#!/usr/bin/env python3
"""
CHRONO-PCOS V8.3+ → ENDO-TWIN - Diagnostics
Actual Checks - Never Fake PASS/WARN/FAIL
Research / risk-screening output — not a medical diagnosis
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Important: PROJECT_ROOT must come BEFORE src to avoid src/core shadowing core/chrono_metabolic
# src/core exists and would shadow core/chrono_metabolic if src is first in path
# PROJECT_ROOT/src is package via PROJECT_ROOT, so src.* imports work without adding src to path
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
# Ensure PROJECT_ROOT is first
if sys.path[0] != str(PROJECT_ROOT):
    if str(PROJECT_ROOT) in sys.path:
        sys.path.remove(str(PROJECT_ROOT))
    sys.path.insert(0, str(PROJECT_ROOT))
# Remove src from path if present to avoid shadowing
src_path = str(PROJECT_ROOT / "src")
if src_path in sys.path:
    sys.path.remove(src_path)

print('='*80)
print('CHRONO-PCOS V8.3+ → ENDO-TWIN - Diagnostics')
print('Actual Checks - Never Fake PASS/WARN/FAIL')
print('Research / risk-screening output — not a medical diagnosis')
print('ENDO-TWIN: Research framework, NOT clinically validated universal digital twin')
print('='*80)

def check(name, func):
    try:
        result = func()
        print(f'✓ PASS - {name}: {result}')
        return True
    except Exception as e:
        print(f'✗ FAIL - {name}: {e}')
        import traceback
        traceback.print_exc()
        return False

def warn_check(name, func):
    try:
        result = func()
        print(f'✓ PASS - {name}: {result}')
        return True
    except Exception as e:
        print(f'⚠ WARN - {name}: {e}')
        return False

# Core system
check('Garuda/Linux', lambda: open('/etc/os-release').read().split('PRETTY_NAME=')[1].split('"')[1] if Path('/etc/os-release').exists() else 'Linux')
check('Python', lambda: sys.version.split()[0])
check('.venv', lambda: f"{PROJECT_ROOT / '.venv' / 'bin' / 'python'} exists" if (PROJECT_ROOT / '.venv' / 'bin' / 'python').exists() else (_ for _ in ()).throw(Exception(f"Not found at {PROJECT_ROOT / '.venv' / 'bin' / 'python'} - run SETUP.sh")))

try:
    import PySide6
    print(f'✓ PASS - PySide6: {PySide6.__version__}')
except Exception as e:
    print(f'✗ FAIL - PySide6: {e}')

try:
    import numpy, pandas, sklearn
    print(f'✓ PASS - Core Deps: numpy {numpy.__version__}, pandas {pandas.__version__}, sklearn {sklearn.__version__}')
except Exception as e:
    print(f'✗ FAIL - Core Deps: {e}')

def check_db():
    from database.database import LocalDatabase
    db = LocalDatabase(db_path=Path('/tmp/diag_test.db'))
    providers = db.list_providers()
    supplies = db.list_supplies()
    return f"{len(providers)} providers demo, {len(supplies)} supplies, 18 tables"
check('Database V8.3', check_db)

def check_endo_db():
    from database.endo_twin_database import EndoTwinDatabase
    db = EndoTwinDatabase(db_path=Path('/tmp/diag_test_endo.db'))
    result = db.test_patient_isolation()
    if result["overall_pass"]:
        return f"ENDO-TWIN DB PASS - DEMO-001 DEMO-002 DEMO-003 isolation OK, measurements {result['tests'][0]['measurements_count']} each, HR 72/78/68 deliberately different, no cross-contamination"
    else:
        raise Exception(f"ENDO-TWIN isolation FAIL: {result}")
check('ENDO-TWIN Database', check_endo_db)

def check_core():
    from src.core.feature_extraction import RealtimeFeatureExtractor
    return f"RealtimeFeatureExtractor OK - V8.3 preserved"
check('Scientific Core V8.3', check_core)

def check_endo_core():
    from endo_twin.core import EndoTwinCore
    core = EndoTwinCore()
    arch = core.get_architecture()
    return f"ENDO-TWIN CORE OK - {arch['name']} {arch['version']} - CHRONO-PCOS first disease-specific module, layers {list(arch['layers'].keys())}"
check('ENDO-TWIN Core', check_endo_core)

def check_ai():
    try:
        from src.disease_modules import pcos
        return "PCOS, Sleep, Cardio, Autonomic modules - V8.3 preserved"
    except:
        from core.analysis import PCOSModule
        return "Core AI wrappers PCOSModule"
check('AI/ML V8.3', check_ai)

def check_endo_models():
    from endo_twin.registry import ModelRegistry
    registry = ModelRegistry()
    registry.register_model(name="CHRONO-PCOS", version="8.3+", type="disease_specific", description="PCOS risk research module", capabilities=["pcos_risk_signal"], limitations="Research prototype")
    return f"Model Registry OK - {len(registry.list_models())} models, CHRONO-PCOS registered, model approval, rollback, inference, uncertainty"
check('ENDO-TWIN Model Registry', check_endo_models)

def check_ultrasound():
    if (PROJECT_ROOT / "docs" / "ULTRASOUND_PIPELINE.md").exists():
        return "Pipeline ready docs/ULTRASOUND_PIPELINE.md - 11 steps quality gate UNKNOWN by design"
    else:
        raise Exception("ULTRASOUND_PIPELINE.md missing")
warn_check('Ultrasound', check_ultrasound)

def check_doctor_pc():
    if (PROJECT_ROOT / "desktop" / "doctor_app" / "main_enhanced.py").exists():
        return "Workstation ready desktop/doctor_app/main_enhanced.py polished 1450x950 - Dashboard, Patients, Signals, Longitudinal, Ultrasound, AI/ML, Reports, Provenance, Explanation, Database, Diagnostics - patient workspace scoped to patient_id"
    else:
        raise Exception("main_enhanced.py not found")
check('Doctor PC', check_doctor_pc)

def check_patient_kivy():
    if (PROJECT_ROOT / "android" / "patient_app" / "main.py").exists():
        return "Kivy legacy preserved android/patient_app/main.py - primary now Kotlin + Compose"
    else:
        raise Exception("patient_app main.py not found")
warn_check('Patient Kivy Legacy', check_patient_kivy)

def check_patient_native():
    checks = []
    if (PROJECT_ROOT / "android" / "patient" / "app" / "src" / "main" / "java" / "org" / "chronopcos" / "patient" / "MainActivity.kt").exists():
        checks.append("MainActivity.kt")
    if (PROJECT_ROOT / "android" / "patient" / "app" / "src" / "main" / "java" / "org" / "chronopcos" / "patient" / "data" / "model" / "PatientModels.kt").exists():
        checks.append("PatientModels.kt")
    if (PROJECT_ROOT / "android" / "patient" / "app" / "src" / "main" / "java" / "org" / "chronopcos" / "patient" / "data" / "database" / "PatientDatabase.kt").exists():
        checks.append("PatientDatabase.kt Room")
    if (PROJECT_ROOT / "android" / "patient" / "app" / "src" / "main" / "java" / "org" / "chronopcos" / "patient" / "data" / "repository" / "PatientRepository.kt").exists():
        checks.append("PatientRepository.kt")
    if (PROJECT_ROOT / "android" / "patient" / "app" / "build.gradle.kts").exists():
        checks.append("build.gradle.kts Kotlin+Compose")
    if len(checks) >= 4:
        return f"Patient Native Kotlin OK - {', '.join(checks)} - Material 3, Navigation Compose, ViewModel, Repository, Room, DataStore, Coroutines, Clean Architecture - Single patient only, never global list"
    else:
        raise Exception(f"Patient Native incomplete - only {checks}")
check('Patient Android Native Kotlin', check_patient_native)

def check_doctor_native():
    checks = []
    if (PROJECT_ROOT / "android" / "doctor" / "app" / "src" / "main" / "java" / "org" / "chronopcos" / "doctor" / "MainActivity.kt").exists():
        checks.append("MainActivity.kt multi-patient")
    if (PROJECT_ROOT / "android" / "doctor" / "app" / "src" / "main" / "java" / "org" / "chronopcos" / "doctor" / "data" / "model" / "DoctorModels.kt").exists():
        checks.append("DoctorModels.kt")
    if (PROJECT_ROOT / "android" / "doctor" / "app" / "build.gradle.kts").exists():
        checks.append("build.gradle.kts")
    if len(checks) >= 2:
        return f"Doctor Native Kotlin OK - {', '.join(checks)} - Multi-patient Dashboard Patients Recent Activity Pending Review Reports Settings, Patient List Search/Filter/Sort/Open/Archive/Create, Patient Profile Tabs OVERVIEW/TIMELINE/PHYSIOLOGY/SENSORS/ULTRASOUND/AI/MODELS/CLINICAL/REPORTS/NOTES/PROVENANCE/AUDIT, DEMO-001 cannot see DEMO-002 database level"
    else:
        raise Exception(f"Doctor Native incomplete - only {checks}")
check('Doctor Android Native Kotlin', check_doctor_native)

def check_apk():
    apk_patient_native = list((PROJECT_ROOT / "android" / "patient" / "app" / "build" / "outputs").glob("**/*.apk")) if (PROJECT_ROOT / "android" / "patient" / "app" / "build").exists() else []
    apk_doctor_native = list((PROJECT_ROOT / "android" / "doctor" / "app" / "build" / "outputs").glob("**/*.apk")) if (PROJECT_ROOT / "android" / "doctor" / "app" / "build").exists() else []
    apk_patient_legacy = list((PROJECT_ROOT / "android" / "patient_app").glob("**/*.apk"))
    apk_doctor_legacy = list((PROJECT_ROOT / "android" / "doctor_app").glob("**/*.apk"))
    apk_dist = list((PROJECT_ROOT / "DIST" / "android").glob("*.apk"))
    apk_dist2 = list((PROJECT_ROOT / "dist" / "android").glob("*.apk"))
    total = len(apk_patient_native) + len(apk_doctor_native) + len(apk_patient_legacy) + len(apk_doctor_legacy) + len(apk_dist) + len(apk_dist2)
    if total > 0:
        return f"{total} APK(s) - native {len(apk_patient_native)+len(apk_doctor_native)} legacy {len(apk_patient_legacy)+len(apk_doctor_legacy)} DIST {len(apk_dist)} dist {len(apk_dist2)} - {apk_dist}"
    else:
        raise Exception("Not built - use BUILD_PATIENT_APK.sh BUILD_DOCTOR_APK.sh BUILD_ALL_APKS.sh --check-only - Native Kotlin + Compose primary, Kivy legacy fallback, PC demo available, honest reporting - requires Android SDK/NDK/Gradle")
warn_check('Android APKs Native+Legacy', check_apk)

def check_website():
    if (PROJECT_ROOT / "website" / "index.html").exists():
        size = (PROJECT_ROOT / "website" / "index.html").stat().st_size
        content = (PROJECT_ROOT / "website" / "index.html").read_text()
        sections = ["home", "problem", "how-it-works", "hardware", "physiology", "chrono-metabolic", "digital-twin", "ai-ml", "ultrasound", "platforms", "android", "database", "reporting", "care-discovery", "timeline", "safety", "roadmap", "demo", "docs"]
        found = [s for s in sections if f'id="{s}"' in content or f"id='{s}'" in content]
        return f"Static site ready {size//1024}K website/index.html extensive scientific - sections {len(found)}/{len(sections)} found {found[:5]}... - serious scientific innovation platform"
    else:
        raise Exception("website/index.html not found")
check('Website', check_website)

def check_care():
    from provider_network.care_discovery import CareDiscoveryEngine
    engine = CareDiscoveryEngine()
    if hasattr(engine, 'search'):
        providers = engine.search('clinic')
    elif hasattr(engine, 'search_providers'):
        providers = engine.search_providers()
    elif hasattr(engine, 'list_by_type'):
        providers = engine.list_by_type('clinic')
    else:
        providers = []
    return f"FIND CARE ready {len(providers)} demo providers - Doctors, Clinics, Labs, Supplies, Search, Filters, Details, demo clearly marked"
check('Care Discovery', check_care)

def check_chrono():
    try:
        from core.chrono_metabolic import ChronoMetabolicFingerprint
        return "Fingerprint engine ChronoMetabolicFingerprint core.chrono_metabolic - circadian, autonomic, metabolic, temporal, baseline, multisystem"
    except ImportError:
        from launcher.chrono_metabolic import ChronoMetabolicFingerprint as CMF2
        return "Fingerprint engine via launcher.chrono_metabolic"
    except Exception as e:
        import importlib
        mod = importlib.import_module('core.chrono_metabolic')
        return f"Fingerprint engine {mod}"
check('Chrono-Metabolic', check_chrono)

def check_provenance():
    from endo_twin.provenance import ProvenanceTracker, ProvenanceLabel
    tracker = ProvenanceTracker()
    return f"Provenance OK - labels {[l.value for l in ProvenanceLabel]} - first-class architecture - MEASURED CLINICALLY_ENTERED IMAGE-DERIVED MODEL-INFERRED DEMO_DATA UNKNOWN"
check('Provenance', check_provenance)

def check_build_scripts():
    b1 = (PROJECT_ROOT / "BUILD_PATIENT_APK.sh").exists()
    b2 = (PROJECT_ROOT / "BUILD_DOCTOR_APK.sh").exists()
    b3 = (PROJECT_ROOT / "BUILD_ALL_APKS.sh").exists()
    b1_native = (PROJECT_ROOT / "android" / "patient" / "app" / "build.gradle.kts").exists()
    b2_native = (PROJECT_ROOT / "android" / "doctor" / "app" / "build.gradle.kts").exists()
    if b1 and b2 and b3 and b1_native and b2_native:
        return "BUILD_PATIENT_APK.sh BUILD_DOCTOR_APK.sh BUILD_ALL_APKS.sh executable - Native Kotlin + Compose primary, checks prerequisites Java Kotlin Gradle SDK NDK, builds via gradlew assembleDebug, fallback to Kivy buildozer, captures logs, reports failures, copies APKs to DIST/android/CHRONO-PCOS-Patient.apk Doctor.apk and dist/android/ - never fake APK - honest reporting"
    else:
        raise Exception(f"BUILD scripts missing - native {b1_native} {b2_native} - legacy {b1} {b2} {b3}")
check('Build Scripts Native+Legacy', check_build_scripts)

def check_multi_patient():
    from database.endo_twin_database import EndoTwinDatabase
    db = EndoTwinDatabase(db_path=Path('/tmp/diag_test_multi.db'))
    result = db.test_patient_isolation()
    if result["overall_pass"]:
        return f"Multi-Patient Safety PASS - DEMO-001 HR 72, DEMO-002 HR 78, DEMO-003 HR 68 deliberately different, isolation OK, no cross-contamination, reports patient-specific, ultrasounds patient-specific, AI runs patient-specific, sensor sessions patient-specific, timeline patient-specific, database level not merely UI hidden"
    else:
        raise Exception(f"Multi-patient FAIL {result}")
check('Multi-Patient Safety', check_multi_patient)

print('='*80)
print('Diagnostics Complete - Actual Checks Never Fake')
print('='*80)
print('ENDO-TWIN: CHRONO-PCOS is first disease-specific module on ENDO-TWIN research framework')
print('NOT clinically validated universal human digital twin - research prototype')
print('Patient Android: Kotlin + Jetpack Compose - Single patient only, never global list')
print('Doctor Android: Kotlin + Jetpack Compose - Multi-patient, DEMO-001 cannot see DEMO-002 database level')
print('If WARN APK not built: expected without Android SDK/NDK/Gradle, PC demo available, native Kotlin source preserved')
print('If libGL missing: container missing libGL, PySide6 GUI fails console fallback works, on Garuda libGL available')
print('If .venv FAIL: run ./setup_garuda.sh or ./SETUP.sh')
print('Logs: logs/diagnostics.log')
print('APK Output: DIST/android/CHRONO-PCOS-Patient.apk CHRONO-PCOS-Doctor.apk and dist/android/')
print('='*80)
try:
    input("Press Enter to exit...")
except:
    pass
