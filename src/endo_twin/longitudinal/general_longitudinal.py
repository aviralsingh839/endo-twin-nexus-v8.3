"""
General Longitudinal Engine - No PCOS assumptions
Core scientific story is NOT today's number, it is personal baseline → time series → change → persistence → recovery → context
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import time

class GeneralLongitudinalEngine:
    """General longitudinal engine - personal baseline → time series → change → persistence → recovery → context"""
    
    def __init__(self):
        self.timelines: Dict[str, List[Dict]] = {}
    
    def get_timeline(self, patient_id: str) -> Dict[str, Any]:
        """Get longitudinal timeline for patient - GENERAL"""
        if patient_id in self.timelines:
            events = self.timelines[patient_id]
            return {
                "patient_id": patient_id,
                "events": events,
                "count": len(events),
                "description": "Chronological timeline - sensor session, symptom entry, clinical entry, imaging, analysis, model run, report generated",
                "core_story": "Personal baseline → time series → change → persistence → recovery → context - NOT today's number",
                "visualizations": "daily, weekly, monthly longitudinal where data supports, never fabricate trends"
            }
        return {
            "patient_id": patient_id,
            "events": [],
            "count": 0,
            "description": "No timeline yet",
            "core_story": "Personal baseline → time series → change → persistence → recovery → context"
        }
    
    def add_event(self, patient_id: str, event_type: str, title: str, description: str = "", data: Dict = None):
        if patient_id not in self.timelines:
            self.timelines[patient_id] = []
        
        event = {
            "event_id": f"EVT-{int(time.time()*1000)}",
            "patient_id": patient_id,
            "event_type": event_type,
            "title": title,
            "description": description,
            "timestamp": time.time(),
            "data": data or {}
        }
        self.timelines[patient_id].append(event)
        return event
