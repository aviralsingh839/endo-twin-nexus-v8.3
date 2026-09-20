"""Disease Module Registry for V8.3.

Architecture allows additional modules without rewriting core engine.

Initial modules:
- pcos (A)
- sleep (B)
- cardiometabolic (C)
- autonomic (D)

Future modules marked 'not implemented'
"""
from __future__ import annotations

from typing import Dict, List, Optional, Type
from dataclasses import dataclass

from src.disease_modules.base import DiseaseModule
from src.disease_modules.pcos import PCOSModule
from src.disease_modules.sleep import SleepModule
from src.disease_modules.cardiometabolic import CardiometabolicModule
from src.disease_modules.autonomic import AutonomicModule
from src.config import ENABLED_MODULES, FUTURE_MODULES


@dataclass
class ModuleInfo:
    name: str
    version: str
    status: str  # implemented, future
    description: str
    cls: Optional[Type[DiseaseModule]] = None


class DiseaseModuleRegistry:
    """Registry of all disease modules."""

    def __init__(self):
        self._modules: Dict[str, ModuleInfo] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register("pcos", PCOSModule, "PCOS / reproductive-metabolic risk - PCOS-associated physiological and clinical risk signals", "8.3.0")
        self.register("sleep", SleepModule, "Sleep / circadian health - sleep regularity and circadian disruption signals", "8.3.0")
        self.register("cardiometabolic", CardiometabolicModule, "Cardiometabolic risk - research-oriented screening signals", "8.3.0")
        self.register("autonomic", AutonomicModule, "Autonomic / stress regulation - physiological regulation signals", "8.3.0")

        # Future modules
        for future in FUTURE_MODULES:
            self._modules[future] = ModuleInfo(
                name=future,
                version="0.0.0",
                status="future - not implemented",
                description=f"Future research module: {future} - not implemented. Requires appropriate dataset, validated features, scientifically defensible target labels.",
                cls=None
            )

    def register(self, name: str, cls: Type[DiseaseModule], description: str, version: str = "8.3.0"):
        self._modules[name] = ModuleInfo(
            name=name,
            version=version,
            status="implemented",
            description=description,
            cls=cls
        )

    def get(self, name: str) -> Optional[ModuleInfo]:
        return self._modules.get(name)

    def get_module_class(self, name: str) -> Optional[Type[DiseaseModule]]:
        info = self._modules.get(name)
        return info.cls if info else None

    def create(self, name: str, *args, **kwargs) -> Optional[DiseaseModule]:
        cls = self.get_module_class(name)
        if cls is None:
            return None
        return cls(*args, **kwargs)

    def list_implemented(self) -> List[str]:
        return [k for k, v in self._modules.items() if v.status == "implemented"]

    def list_future(self) -> List[str]:
        return [k for k, v in self._modules.items() if "future" in v.status]

    def list_all(self) -> List[str]:
        return list(self._modules.keys())

    def summary(self) -> Dict:
        return {
            "implemented": {k: {"version": v.version, "description": v.description} for k, v in self._modules.items() if v.status == "implemented"},
            "future": {k: {"description": v.description} for k, v in self._modules.items() if "future" in v.status},
            "enabled_by_default": ENABLED_MODULES,
        }


# Global registry instance
GLOBAL_REGISTRY = DiseaseModuleRegistry()
