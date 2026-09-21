from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    from pydantic import BaseModel, ConfigDict, Field
except ImportError:  # Keep current prototype runnable before optional install.
    BaseModel = object  # type: ignore[misc,assignment]
    ConfigDict = dict  # type: ignore[misc,assignment]
    Field = lambda default=None, **_: default  # type: ignore[misc,assignment]


if BaseModel is object:
    class PatientSchema:  # pragma: no cover - dependency-gated compatibility shim
        def __init__(self, **data: Any) -> None:
            self.__dict__.update(data)
else:
    class PatientSchema(BaseModel):
        model_config = ConfigDict(extra="forbid")
        patient_id: str = Field(min_length=1)
        display_name: Optional[str] = None
        enabled_disease_models: List[str] = Field(default_factory=list)
        extensions: Dict[str, Any] = Field(default_factory=dict)


if BaseModel is object:
    class MeasurementSchema:
        def __init__(self, **data: Any) -> None:
            self.__dict__.update(data)
else:
    class MeasurementSchema(BaseModel):
        model_config = ConfigDict(extra="forbid")
        patient_id: str = Field(min_length=1)
        session_id: Optional[str] = None
        measurement_type: str = Field(min_length=1)
        value: Optional[float] = None
        unit: Optional[str] = None
        quality: float = Field(ge=0.0, le=1.0)
        provenance: str = Field(min_length=1)
        source: Optional[str] = None
        confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)



if BaseModel is object:
    class FeatureSchema:
        def __init__(self, **data: Any) -> None:
            self.__dict__.update(data)
else:
    class FeatureSchema(BaseModel):
        model_config = ConfigDict(extra="forbid")
        patient_id: str = Field(min_length=1)
        timestamp: float
        name: str = Field(min_length=1)
        value: Optional[float] = None
        category: str = Field(min_length=1)
        source: str = Field(min_length=1)
        sensor: Optional[str] = None
        quality: float = Field(ge=0.0, le=1.0)
        provenance: str = Field(min_length=1)
        algorithm_version: Optional[str] = None
