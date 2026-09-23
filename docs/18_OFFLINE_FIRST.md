# 18 - Offline-First Design - V8.3+

## Principle
Core works without internet: patient records, sensor collection, signal processing, AI inference, ultrasound, reports, historical, local DB
Internet optional: provider directory, map tiles, updates, controlled sync

## Core Offline
- Patient records: LocalDatabase SQLite, no cloud
- Sensor collection: SerialManager, PacketParser $CP3, local processing
- Signal processing: Filtering, BaselineRemoval, ArtifactDetection, QualityControl, RealtimeFeatureExtractor local Python
- AI inference: ModelTrainer, ModelEvaluator, disease modules local sklearn, no API
- Ultrasound: local loading preprocessing quality checks segmentation inference if model local
- Reports: local generation ReportGenerator
- Historical: local DB queries
- Local DB: SQLite file

## Optional Internet
- Provider directory: list_providers, search_providers, get_nearby_providers local seeded demo, optional update from remote if available but not required
- Map: OSM directions URL https://www.openstreetmap.org/directions?from=&to= no API key, map tiles optional, list view works offline
- Updates: app updates optional, not required for core
- Controlled sync: deliberate sharing not automatic, patient-to-doctor export/import package, not automatic upload, user initiates

## Why Offline-First?
- Privacy: no cloud upload of private health data default
- Accessibility: works in low connectivity areas
- Class 11 project: no expensive cloud APIs
- Research: local-first

## Implementation
- Database: SQLite file DATA_DIR/chrono_twin_nexus_v8_3_plus.db
- No network calls in core analysis
- Provider network: local seeded demo providers, OSM URL generation no API key, offline-first
- Website: static HTML/CSS/JS, no private records, no backend required for core info
- Android: Kivy + local SQLite, APK via Buildozer, offline

## Testing No Internet
- Disconnect internet, run patient app, doctor app, sensor collection (demo mode), signal processing, AI inference, reports, historical - all should work
- Provider directory: should show seeded demo providers even offline
- Map: list view works offline, map tiles may not load but directions URL can be opened when online
