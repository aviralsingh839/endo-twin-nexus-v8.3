"""Care Discovery System - FIND CARE

Similar to map/list discovery like food-delivery or petrol-pump finder.

User can discover:
- nearby participating doctors
- nearby clinics
- relevant healthcare facilities
- participating laboratories
- relevant product/supply providers

Provides:
- map
- list view
- distance
- specialty
- address
- opening hours
- services
- contact information
- directions
- verification status

IMPORTANT: Do not mix directory with private medical records.
Provider-directory information is separate from patient health data.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Dict, List, Optional

from database.database import LocalDatabase


@dataclass
class Provider:
    provider_id: str
    name: str
    type: str  # doctor, clinic, lab, supply
    specialty: str
    address: str
    latitude: float
    longitude: float
    distance_km: float
    opening_hours: str
    services: List[str]
    contact_info: str
    verification_status: str  # verified, pending, unverified, demo
    is_demo: bool

    def as_card_text(self) -> str:
        verified_badge = {
            "verified": "✓ Verified",
            "pending": "⏳ Pending Verification",
            "unverified": "Unverified",
            "demo": "Demo Provider"
        }.get(self.verification_status, self.verification_status)

        return f"""
{self.name}
{self.distance_km:.1f} km • {self.specialty}
{verified_badge}
{self.address}
Hours: {self.opening_hours}
Services: {', '.join(self.services[:3])}
Contact: {self.contact_info}
[View] [Directions] [Contact]
"""


class CareDiscoveryEngine:
    """Care discovery - map and list view."""

    def __init__(self, db: Optional[LocalDatabase] = None):
        self.db = db or LocalDatabase()

    def find_nearby(self, latitude: float = 28.6692, longitude: float = 77.4538,
                    radius_km: float = 10.0, provider_type: Optional[str] = None,
                    verified_only: bool = False) -> List[Provider]:
        """Find nearby providers."""
        raw_providers = self.db.get_nearby_providers(latitude, longitude, radius_km)

        if provider_type:
            raw_providers = [p for p in raw_providers if p["type"] == provider_type]

        if verified_only:
            raw_providers = [p for p in raw_providers if p["verification_status"] == "verified"]

        providers = []
        for p in raw_providers:
            try:
                services = json.loads(p["services_json"]) if p["services_json"] else []
            except:
                services = []

            providers.append(Provider(
                provider_id=p["provider_id"],
                name=p["name"],
                type=p["type"],
                specialty=p["specialty"] or "",
                address=p["address"] or "",
                latitude=p["latitude"] or 0.0,
                longitude=p["longitude"] or 0.0,
                distance_km=p["distance_km"] or 0.0,
                opening_hours=p["opening_hours"] or "",
                services=services,
                contact_info=p["contact_info"] or "",
                verification_status=p["verification_status"],
                is_demo=bool(p["is_demo"])
            ))

        return sorted(providers, key=lambda x: x.distance_km)

    def search(self, query: str) -> List[Provider]:
        """Search providers by name, specialty, address."""
        raw = self.db.search_providers(query)
        providers = []
        for p in raw:
            try:
                services = json.loads(p["services_json"]) if p["services_json"] else []
            except:
                services = []
            providers.append(Provider(
                provider_id=p["provider_id"],
                name=p["name"],
                type=p["type"],
                specialty=p["specialty"] or "",
                address=p["address"] or "",
                latitude=p["latitude"] or 0.0,
                longitude=p["longitude"] or 0.0,
                distance_km=p["distance_km"] or 0.0,
                opening_hours=p["opening_hours"] or "",
                services=services,
                contact_info=p["contact_info"] or "",
                verification_status=p["verification_status"],
                is_demo=bool(p["is_demo"])
            ))
        return providers

    def get_provider_details(self, provider_id: str) -> Optional[Provider]:
        """Get detailed provider info."""
        providers = self.db.list_providers()
        for p in providers:
            if p["provider_id"] == provider_id:
                try:
                    services = json.loads(p["services_json"]) if p["services_json"] else []
                except:
                    services = []
                return Provider(
                    provider_id=p["provider_id"],
                    name=p["name"],
                    type=p["type"],
                    specialty=p["specialty"] or "",
                    address=p["address"] or "",
                    latitude=p["latitude"] or 0.0,
                    longitude=p["longitude"] or 0.0,
                    distance_km=p["distance_km"] or 0.0,
                    opening_hours=p["opening_hours"] or "",
                    services=services,
                    contact_info=p["contact_info"] or "",
                    verification_status=p["verification_status"],
                    is_demo=bool(p["is_demo"])
                )
        return None

    def get_directions_url(self, provider: Provider, from_lat: Optional[float] = None, from_lon: Optional[float] = None) -> str:
        """Generate directions URL - uses open street map for offline-first, no Google API required."""
        # Use OSM for offline-first, no API key
        if from_lat and from_lon:
            return f"https://www.openstreetmap.org/directions?from={from_lat},{from_lon}&to={provider.latitude},{provider.longitude}"
        return f"https://www.openstreetmap.org/?mlat={provider.latitude}&mlon={provider.longitude}#map=16/{provider.latitude}/{provider.longitude}"

    def list_by_type(self) -> Dict[str, List[Provider]]:
        """List providers grouped by type."""
        all_providers = self.find_nearby()
        grouped: Dict[str, List[Provider]] = {"doctor": [], "clinic": [], "lab": [], "supply": []}
        for p in all_providers:
            if p.type in grouped:
                grouped[p.type].append(p)
        return grouped


class SupplyDiscoveryEngine:
    """Supply discovery - health monitoring supplies."""

    def __init__(self, db: Optional[LocalDatabase] = None):
        self.db = db or LocalDatabase()

    def list_supplies(self, category: Optional[str] = None) -> List[Dict]:
        """List supplies - sensor accessories, monitoring equipment, menstrual care, general supplies."""
        return self.db.list_supplies(category)

    def search_supplies(self, query: str) -> List[Dict]:
        """Search supplies."""
        all_supplies = self.db.list_supplies()
        query_lower = query.lower()
        return [s for s in all_supplies if query_lower in s["name"].lower() or query_lower in s["description"].lower()]

    def get_categories(self) -> List[str]:
        """Get supply categories."""
        supplies = self.db.list_supplies()
        categories = list(set(s["category"] for s in supplies))
        return categories
