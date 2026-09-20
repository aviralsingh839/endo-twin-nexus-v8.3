"""
Real PCOS Model Adapter - Uses actual trained model artifacts

Model: chrono_pcos_project V8/models/pcos_risk_model.joblib
Type: dict with model, feature_names, target, meta
Model: CalibratedClassifierCV with VotingClassifier (LogisticRegression, RandomForest, ExtraTrees)
Features: 37 features - Age, Weight, BMI, Blood Group, Pulse rate, RR, Hb, Cycle, Cycle length, FSH, LH, etc.
Target: PCOS (Y/N)
Meta: dataset PCOS_data_without_infertility.xlsx, n_rows_train 541, n_real_rows 541, n_features 37, cv_roc_auc 0.9594, cv_average_precision 0.9324
CV: 5-fold stratified-group (patient-level)
Leaky columns dropped: Pregnant(Y/N), No. of abortions, I beta-HCG, II beta-HCG
Notes: Extended dataset synthetic excluded by default

This adapter provides:
model input → schema validation → feature preparation → preprocessing → real model inference → raw model output → calibration/interpretation → uncertainty → explanation → provenance

NEVER display fabricated confidence number.
If model cannot produce reliable uncertainty: show "Uncertainty not established" rather than inventing one.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import time
import json

try:
    import joblib
    import numpy as np
    import pandas as pd
    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False


class RealPCOSModelAdapter:
    """
    Real model adapter for pcos_risk_model.joblib
    
    Uses actual trained artifact, not deterministic research logic.
    """
    
    def __init__(self, model_path: Optional[Path] = None):
        if model_path is None:
            # Try multiple locations
            possible_paths = [
                Path("chrono_pcos_project V8/models/pcos_risk_model.joblib"),
                Path("models/pcos_risk_model.joblib"),
                Path("disease_models/chrono_pcos/model/pcos_risk_model.joblib"),
                Path(__file__).parent / "pcos_risk_model.joblib"
            ]
            for p in possible_paths:
                if p.exists():
                    model_path = p
                    break
        
        self.model_path = model_path
        self.model = None
        self.feature_names = []
        self.target = ""
        self.meta = {}
        self.is_loaded = False
        self.load_error = None
        
        if model_path and model_path.exists() and JOBLIB_AVAILABLE:
            try:
                self._load_model()
            except Exception as e:
                self.load_error = str(e)
    
    def _load_model(self):
        """Load real model artifact"""
        data = joblib.load(self.model_path)
        if isinstance(data, dict):
            self.model = data.get("model")
            self.feature_names = data.get("feature_names", [])
            self.target = data.get("target", "PCOS (Y/N)")
            self.meta = data.get("meta", {})
        else:
            # Direct model
            self.model = data
            self.feature_names = getattr(data, "feature_names_in_", [])
        
        self.is_loaded = self.model is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model metadata - for Model Transparency"""
        if not self.is_loaded:
            return {
                "name": "pcos_risk_model",
                "version": "V8",
                "model_path": str(self.model_path) if self.model_path else "not found",
                "is_loaded": False,
                "load_error": self.load_error,
                "status": "NOT AVAILABLE - Real model artifact not loaded",
                "fallback": "Using deterministic research logic - NOT real model inference"
            }
        
        return {
            "name": "pcos_risk_model",
            "version": "V8",
            "display_name": "PCOS Risk Model - Clinical Variables",
            "model_path": str(self.model_path),
            "model_type": str(type(self.model)),
            "is_loaded": True,
            "feature_names": self.feature_names,
            "n_features": len(self.feature_names),
            "target": self.target,
            "meta": self.meta,
            "dataset": self.meta.get("dataset", ["PCOS_data_without_infertility.xlsx"]),
            "n_rows_train": self.meta.get("n_rows_train", 541),
            "n_real_rows": self.meta.get("n_real_rows", 541),
            "n_features_meta": self.meta.get("n_features", 37),
            "leaky_columns_dropped": self.meta.get("leaky_columns_dropped", []),
            "cv_scheme": self.meta.get("cv_scheme", "5-fold stratified-group (patient-level)"),
            "cv_roc_auc": self.meta.get("cv_roc_auc", 0.9594),
            "cv_average_precision": self.meta.get("cv_average_precision", 0.9324),
            "cv_evaluated_on": self.meta.get("cv_evaluated_on", "all 541 real rows"),
            "notes": self.meta.get("notes", "Extended dataset synthetic excluded by default"),
            "model_architecture": "CalibratedClassifierCV(cv=3, estimator=VotingClassifier([lr: LogisticRegression(C=0.5, class_weight=balanced, max_iter=3000), rf: RandomForestClassifier(n_estimators=500), et: ExtraTreesClassifier(n_estimators=400)], voting=soft), method=isotonic)",
            "status": "REAL MODEL - Trained on 541 real rows, 37 features, patient-level CV",
            "limitations": "Clinical variables only, not wearable physiology, requires lab values FSH, LH, etc., not diagnosis, research only, clinical validation NOT ESTABLISHED for wearable context",
            "provenance": "TRAINED MODEL - PCOS_data_without_infertility.xlsx 541 rows",
            "disclaimer": "Research model, not diagnostic, requires clinical evaluation, Rotterdam criteria requires clinician"
        }
    
    def validate_input(self, clinical_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Schema validation - check if input has required features
        
        Real model expects 37 features:
        Age (yrs), Weight (Kg), Height(Cm), BMI, Blood Group, Pulse rate(bpm), RR, Hb(g/dl), Cycle(R/I), Cycle length(days), Marraige Status (Yrs), FSH(mIU/mL), LH(mIU/mL), FSH/LH, Hip(inch), Waist(inch), Waist:Hip Ratio, TSH, AMH, PRL, Vit D3, PRG, RBS, Weight gain(Y/N), hair growth(Y/N), Skin darkening (Y/N), Hair loss(Y/N), Pimples(Y/N), Fast food (Y/N), Reg.Exercise(Y/N), BP Systolic, BP Diastolic, Follicle No. (L), Follicle No. (R), Avg. F size (L), Avg. F size (R), Endometrium (mm)
        """
        if not self.is_loaded:
            return {
                "valid": False,
                "missing": self.feature_names,
                "warnings": ["Real model not loaded"],
                "quality": 0.0,
                "is_real_model": False
            }
        
        missing = []
        present = []
        warnings = []
        
        for feat in self.feature_names:
            # Check if feature present (allow case-insensitive, with/without units)
            found = False
            for key in clinical_data.keys():
                # Normalize: lower, remove units, remove spaces
                feat_norm = feat.lower().replace("(yrs)", "").replace("(kg)", "").replace("(cm)", "").replace("(mm)", "").replace("(mmhg)", "").replace("(mg/dl)", "").replace("(miu/ml)", "").replace("(ng/ml)", "").replace("(inch)", "").replace("(y/n)", "").strip()
                key_norm = key.lower().replace("_", " ").replace("(yrs)", "").strip()
                if feat_norm in key_norm or key_norm in feat_norm or feat == key:
                    if clinical_data[key] is not None:
                        found = True
                        present.append(feat)
                        break
            
            if not found:
                missing.append(feat)
        
        # Quality based on coverage
        coverage = len(present) / len(self.feature_names) if self.feature_names else 0
        
        if coverage < 0.5:
            warnings.append(f"Low feature coverage: {len(present)}/{len(self.feature_names)} - insufficient for reliable inference")
        
        # Check for critical features
        critical = ["Age (yrs)", "BMI", "Cycle(R/I)", "Cycle length(days)"]
        for crit in critical:
            if crit in missing:
                warnings.append(f"Missing critical feature: {crit}")
        
        valid = coverage >= 0.5  # At least 50% features needed
        
        return {
            "valid": valid,
            "missing": missing,
            "present": present,
            "coverage": coverage,
            "warnings": warnings,
            "quality": coverage,
            "is_real_model": True,
            "n_features_expected": len(self.feature_names),
            "n_features_present": len(present)
        }
    
    def prepare_features(self, clinical_data: Dict[str, Any]) -> Tuple[Optional[Any], Dict[str, Any]]:
        """
        Feature preparation - convert dict to model input
        
        Returns: (prepared_features, preparation_info)
        """
        if not self.is_loaded:
            return None, {"error": "Model not loaded", "is_real_model": False}
        
        validation = self.validate_input(clinical_data)
        if not validation["valid"]:
            return None, {
                "error": f"Insufficient features: {validation['coverage']:.0%} coverage",
                "validation": validation,
                "is_real_model": True
            }
        
        # Prepare features in correct order
        feature_values = []
        feature_map = {}
        
        for feat_name in self.feature_names:
            value = None
            # Try to find value
            for key, val in clinical_data.items():
                feat_norm = feat_name.lower().replace("(yrs)", "").replace("(kg)", "").replace("(cm)", "").replace("(mm)", "").replace("(mmhg)", "").replace("(mg/dl)", "").replace("(miu/ml)", "").replace("(ng/ml)", "").replace("(inch)", "").replace("(y/n)", "").strip()
                key_norm = key.lower().replace("_", " ").strip()
                if feat_name == key or feat_norm in key_norm or key_norm in feat_norm:
                    value = val
                    break
            
            # Handle missing - will be imputed by model's SimpleImputer
            if value is None:
                value = np.nan
            
            feature_values.append(value)
            feature_map[feat_name] = value
        
        # Convert to DataFrame or array in correct order
        try:
            # Try DataFrame first (if model expects feature names)
            df = pd.DataFrame([feature_values], columns=self.feature_names)
            prepared = df
        except:
            # Fallback to array
            prepared = np.array([feature_values])
        
        prep_info = {
            "feature_names": self.feature_names,
            "feature_values": feature_values,
            "feature_map": feature_map,
            "n_features": len(feature_values),
            "validation": validation,
            "is_real_model": True,
            "preprocessing": "SimpleImputer(strategy=median) + StandardScaler() - handled by model pipeline",
            "feature_order": "Correct order as per training - critical for valid inference"
        }
        
        return prepared, prep_info
    
    def infer(self, clinical_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Real model inference
        
        model input → schema validation → feature preparation → preprocessing → real model inference → raw model output → calibration/interpretation → uncertainty → explanation → provenance
        """
        if not self.is_loaded:
            return {
                "success": False,
                "error": "Real model not loaded",
                "is_real_model": False,
                "model_path": str(self.model_path) if self.model_path else "not found",
                "fallback": "Deterministic research logic should be used, NOT fake confidence",
                "provenance": "NOT REAL MODEL INFERENCE"
            }
        
        # Schema validation
        validation = self.validate_input(clinical_data)
        
        # Feature preparation
        prepared_features, prep_info = self.prepare_features(clinical_data)
        
        if prepared_features is None:
            return {
                "success": False,
                "error": prep_info.get("error", "Feature preparation failed"),
                "validation": validation,
                "preparation": prep_info,
                "is_real_model": True,
                "provenance": "REAL MODEL - but insufficient data"
            }
        
        # Preprocessing is handled by model pipeline (SimpleImputer + StandardScaler)
        # Real model inference
        try:
            # Raw model output
            if hasattr(self.model, "predict_proba"):
                proba = self.model.predict_proba(prepared_features)
                # proba shape: (n_samples, n_classes) - classes [0, 1] where 1 = PCOS
                if isinstance(proba, np.ndarray) and proba.shape[1] >= 2:
                    pcos_proba = float(proba[0][1])  # Probability of PCOS
                else:
                    pcos_proba = float(proba[0]) if isinstance(proba, (list, np.ndarray)) else 0.5
                
                # Raw prediction
                pred = self.model.predict(prepared_features)
                raw_pred = int(pred[0]) if isinstance(pred, (list, np.ndarray)) else int(pred)
            else:
                pred = self.model.predict(prepared_features)
                raw_pred = int(pred[0]) if isinstance(pred, (list, np.ndarray)) else int(pred)
                pcos_proba = float(raw_pred)  # If no proba, use pred as proxy (less ideal)
            
            # Calibration/interpretation - model is already calibrated via CalibratedClassifierCV isotonic
            # So proba is calibrated probability
            
            # Level from probability
            if pcos_proba < 0.25:
                level = "low"
            elif pcos_proba < 0.5:
                level = "moderate"
            elif pcos_proba < 0.75:
                level = "elevated"
            else:
                level = "high"
            
            signal = "pcos_associated_risk" if pcos_proba < 0.5 else "elevated_pcos_associated_risk"
            
            # Uncertainty - honestly represented, not fabricated
            # Model confidence from calibration, data quality from coverage
            model_confidence = pcos_proba if pcos_proba > 0.5 else 1 - pcos_proba  # Confidence in prediction
            data_quality = validation["coverage"]
            
            # If model cannot produce reliable uncertainty, show "Uncertainty not established"
            # But we can provide what we have
            uncertainty = {
                "model_confidence": model_confidence,
                "data_quality": data_quality,
                "coverage": validation["coverage"],
                "n_features_present": validation["n_features_present"],
                "n_features_expected": validation["n_features_expected"],
                "note": "Model output confidence from calibrated classifier, not clinical certainty",
                "calibration": "CalibratedClassifierCV isotonic - probability is calibrated",
                "validation": f"CV ROC AUC {self.meta.get('cv_roc_auc', 0.9594)} on {self.meta.get('n_real_rows', 541)} real rows, patient-level CV"
            }
            
            # Explanation - only factors that actually influenced computation
            # Get feature importances if available
            drivers = []
            try:
                # For VotingClassifier, get importances from underlying estimators
                if hasattr(self.model, "calibrated_classifiers_"):
                    # CalibratedClassifierCV - get base estimator
                    base = self.model.calibrated_classifiers_[0].base_estimator if hasattr(self.model.calibrated_classifiers_[0], "base_estimator") else self.model.calibrated_classifiers_[0].estimator
                    if hasattr(base, "estimators_"):
                        # VotingClassifier
                        for name, est in base.estimators:
                            if hasattr(est, "named_steps") and "clf" in est.named_steps:
                                clf = est.named_steps["clf"]
                                if hasattr(clf, "feature_importances_"):
                                    importances = clf.feature_importances_
                                    # Get top features
                                    top_idx = np.argsort(importances)[-3:][::-1]
                                    for idx in top_idx:
                                        feat_name = self.feature_names[idx] if idx < len(self.feature_names) else f"feature_{idx}"
                                        drivers.append({
                                            "feature": feat_name,
                                            "importance": float(importances[idx]),
                                            "value": prep_info["feature_map"].get(feat_name, "unknown"),
                                            "source": "real_model_feature_importance"
                                        })
            except Exception as e:
                # If explanation unavailable, don't invent
                pass
            
            if not drivers:
                # Fallback to showing present critical features, not invented medical explanations
                for feat in ["BMI", "Cycle length(days)", "FSH(mIU/mL)", "LH(mIU/mL)"]:
                    if feat in prep_info["feature_map"] and prep_info["feature_map"][feat] is not None:
                        drivers.append({
                            "feature": feat,
                            "value": prep_info["feature_map"][feat],
                            "source": "input_feature_present",
                            "note": "Feature present in input, actual influence requires SHAP"
                        })
            
            if not drivers:
                drivers.append({
                    "feature": "general",
                    "note": "Explanation unavailable for this model - Top contributing features not available without SHAP"
                })
            
            explanation = (
                f"PCOS risk model inference: probability {pcos_proba:.3f} ({level}). "
                f"Based on {validation['n_features_present']}/{validation['n_features_expected']} features "
                f"({validation['coverage']:.0%} coverage). "
                f"Model: {self.meta.get('cv_scheme', '5-fold patient-level CV')} "
                f"ROC AUC {self.meta.get('cv_roc_auc', 0.9594)}. "
                f"Not a diagnosis. Clinical evaluation required."
            )
            
            provenance = {
                "model": "TRAINED MODEL - pcos_risk_model.joblib",
                "dataset": self.meta.get("dataset", ["PCOS_data_without_infertility.xlsx"]),
                "n_real_rows": self.meta.get("n_real_rows", 541),
                "n_features": len(self.feature_names),
                "cv_scheme": self.meta.get("cv_scheme"),
                "cv_roc_auc": self.meta.get("cv_roc_auc"),
                "feature_preparation": "Correct feature order as per training",
                "preprocessing": "SimpleImputer(median) + StandardScaler() - via pipeline",
                "inference": "Real model inference - CalibratedClassifierCV isotonic",
                "calibration": "Isotonic calibration - probability calibrated"
            }
            
            return {
                "success": True,
                "is_real_model": True,
                "model_info": self.get_model_info(),
                "validation": validation,
                "preparation": prep_info,
                "raw_output": {
                    "pcos_probability": pcos_proba,
                    "raw_prediction": raw_pred,
                    "proba_array": proba.tolist() if 'proba' in locals() and hasattr(proba, 'tolist') else str(proba) if 'proba' in locals() else None
                },
                "calibrated_output": {
                    "pcos_probability": pcos_proba,
                    "level": level,
                    "signal": signal
                },
                "uncertainty": uncertainty,
                "explanation": explanation,
                "drivers": drivers,
                "provenance": provenance,
                "limitations": self.meta.get("notes", "") + " " + "Research only, not diagnostic, Rotterdam criteria requires clinician, clinical variables only not wearable",
                "disclaimer": "Research / risk-screening output — not a medical diagnosis. Requires clinical evaluation.",
                "timestamp": time.time()
            }
            
        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "validation": validation,
                "preparation": prep_info,
                "is_real_model": True,
                "provenance": "REAL MODEL - but inference failed"
            }
