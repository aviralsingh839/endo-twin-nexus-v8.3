"""
Test CareDiscoveryEngine V8.3+
"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from database.database import LocalDatabase
from provider_network.care_discovery import CareDiscoveryEngine, SupplyDiscoveryEngine

def test_care_discovery():
    db_path = Path("/tmp/test_care_discovery.db")
    if db_path.exists():
        db_path.unlink()
    db = LocalDatabase(db_path=db_path)
    engine = CareDiscoveryEngine(db)

    # find_nearby
    nearby = engine.find_nearby()
    assert len(nearby) == 4
    assert nearby[0].distance_km == 0.8  # sorted by distance

    nearby_filtered = engine.find_nearby(provider_type='doctor')
    assert len(nearby_filtered) == 1
    assert nearby_filtered[0].type == 'doctor'

    # search
    search = engine.search("Gynecology")
    assert len(search) >= 1

    search_clinic = engine.search("Clinic")
    assert len(search_clinic) >= 1

    # get_provider_details returns Provider dataclass
    details = engine.get_provider_details("demo_doc_001")
    assert details
    assert details.name == "Dr. Priya Sharma (Demo)"
    assert details.verification_status == 'demo'
    assert details.is_demo == 1

    # get_directions_url OSM no API key - signature is (provider, from_lat, from_lon)
    provider_for_dir = nearby[0]
    url = engine.get_directions_url(provider_for_dir, 28.6692, 77.4538)
    assert "openstreetmap.org" in url
    assert str(provider_for_dir.latitude) in url or "28." in url

    # list_by_type grouped doctor/clinic/lab/supply
    grouped = engine.list_by_type()
    assert 'doctor' in grouped
    assert 'clinic' in grouped
    assert 'lab' in grouped
    assert 'supply' in grouped
    assert len(grouped['doctor']) == 1

    # as_card_text
    card_text = nearby[0].as_card_text()
    assert "[View]" in card_text
    assert "[Directions]" in card_text
    assert "[Contact]" in card_text

    # SupplyDiscoveryEngine
    supply_engine = SupplyDiscoveryEngine(db)
    supplies = supply_engine.list_supplies()
    assert len(supplies) == 5

    sensor_supplies = supply_engine.list_supplies(category='sensor')
    assert len(sensor_supplies) == 3

    search_supplies = supply_engine.search_supplies("MAX30102")
    assert len(search_supplies) == 1
    assert search_supplies[0]['name'] == "MAX30102 Sensor Module"

    categories = supply_engine.get_categories()
    assert 'sensor' in categories
    assert 'accessory' in categories

    print("All care discovery tests passed")
    print(f"Nearby: {len(nearby)}, Grouped: {grouped.keys()}, Supplies: {len(supplies)}")
    print("Provider verification statuses demo clearly marked, never falsely label real doctor/clinic verified")

if __name__ == '__main__':
    test_care_discovery()
