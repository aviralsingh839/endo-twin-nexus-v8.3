# 14 - Care Discovery - V8.3+

## Overview
FIND CARE map/list distance/specialty/address/opening hours/services/contact/directions/verification status example Nearby ABC Women's Clinic 1.2km Gynecology Verified [View][Directions]. Provider directory separate from private records.

## Provider Directory
- Separate from private patient records
- Table providers: provider_id, name, type doctor/clinic/lab/supply, specialty, address, latitude, longitude, distance_km, opening_hours, services_json, contact_info, verification_status verified/pending/unverified/demo, is_demo
- Verification statuses: verified/pending/unverified/demo never falsely label real doctor/clinic verified prototype allow demo clearly marked
- Seeded 4 demo providers all demo status is_demo 1 clearly marked Demo Provider
  - Dr Priya Sharma (Demo) 1.2km Gynecology 123 Health Street Mon-Sat 9AM-6PM PCOS Consultation Gynecology Ultrasound demo@example.com +91 90000 00001
  - ABC Women's Clinic (Demo) 2.1km Gynecology & Obstetrics 456 Care Avenue Mon-Sun 8AM-8PM Gynecology Ultrasound Lab Tests PCOS Screening clinic-demo@example.com +91 90000 00002
  - City Diagnostic Lab (Demo) 3.5km Pathology 789 Lab Road Mon-Sat 7AM-7PM Hormone Tests Blood Tests Ultrasound lab-demo@example.com +91 90000 00003
  - Health Monitoring Supplies (Demo) 0.8km Medical Supplies 321 Supply Street Mon-Sat 9AM-9PM Sensor Accessories Monitoring Equipment Menstrual Care supply-demo@example.com +91 90000 00004

## CareDiscoveryEngine
- find_nearby latitude 28.6692 longitude 77.4538 radius 10km type filter doctor/clinic/lab/supply verified_only bool -> List[Provider]
- search query -> List[Provider] name specialty address LIKE
- get_provider_details provider_id -> Provider dict
- get_directions_url from_lat from_lon to_lat to_lon -> OSM https://www.openstreetmap.org/directions?from=lat,lon&to=lat,lon no API key offline-first
- list_by_type -> grouped doctor/clinic/lab/supply
- as_card_text Provider -> card text with View Directions Contact buttons, Demo badge if demo

## Map/List
- Map: would use OSM tiles, offline-first, optional internet for tiles
- List: distance, specialty, address, hours, services, contact, verification
- Directions: OSM directions URL, no API key

## Supply Discovery
- Separate section sensor accessories/monitoring equipment/menstrual-care/general supplies
- No prescription-drug sales, no auto medication, no treatment decisions
- Table supplies: supply_id, name, category sensor/accessory/menstrual/monitoring, description, provider_id, price, availability
- Seeded 5 supplies: MAX30102 450, MPU6050 250, DS18B20 150, Wrist Band 200, Menstrual Care Kit 300
- SupplyDiscoveryEngine: list_supplies category filter, search_supplies query, get_categories -> list categories

## Why Separate?
Provider directory is public info, patient records private, Do NOT upload private health to public website, local-first, offline core works without internet, optional internet provider directory/map/updates/controlled sync.

## Testing
Care discovery search, nearby, directions OSM, list_by_type, supply list/search/categories.
