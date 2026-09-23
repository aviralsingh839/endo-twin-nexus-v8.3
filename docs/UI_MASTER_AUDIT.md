# ENDO-TWIN NEXUS — UI Master Audit

## Scope

Audit target: `ui/endo-twin-nexus-professional-redesign`.

The repository is a multi-surface research platform: PySide6 desktop workstations, native Kotlin/Compose Patient and Doctor Android clients, a static research website, launcher/control-center tooling, and hardware/network workflows.

## Product-wide constraints

- Preserve the canonical CP2 packet contract and parser.
- Preserve DEMO/LIVE separation and provenance labels.
- Preserve patient-scoped data access and research-only wording.
- Do not invent unavailable sensors or clinical validation.
- Keep ESP8266, ESP32-S3 and Mega hardware identities explicit where relevant.
- Do not rewrite scientific/core/data architecture merely to change presentation.

## UI surfaces

| Surface | Technology | Primary UX role | Current direction |
|---|---|---|---|
| Doctor Workstation | PySide6/Qt | Dense research/clinical workspace | Light clinical shell, navy rail, compact data panels |
| Patient Workstation | PySide6/Qt | Personal longitudinal view | Same semantic tokens, lower cognitive load |
| Patient Android | Kotlin + Compose | Personal mobile companion | Mobile-native, calm, patient-scoped |
| Doctor Android | Kotlin + Compose | Mobile research/clinical companion | Dense but touch-safe |
| Website | HTML/CSS/JS | Public research/product explanation | Product-grade research site |
| Launcher | PySide6 | Engineering control center | Explicit command/build state |
| Hardware UX | Desktop + Android | Device setup/diagnostics | Device-first, truthful availability |

## Required information architecture

Desktop primary navigation: Overview, Patients, Live Monitor, Analysis, Research, Hardware, Models, Reports, Studies, Data, Settings, Diagnostics.

Mobile navigation must prioritize the user's task instead of mirroring the desktop sidebar. Secondary functions belong in contextual navigation/drawers/bottom sheets.

## Reusable component inventory

MetricCard, StatusBadge, DeviceCard, SensorCard, ConnectionBadge, SignalQuality, MiniTrend, FullTimeSeriesChart, WaveformChart, PatientRow, PatientHeader, Timeline, ActivityFeed, DataTable, FilterBar, SearchBox, EmptyState, LoadingState, ErrorState, ConfirmationDialog, BottomSheet, Toast, Tooltip, SectionHeader, Breadcrumbs, Tabs, CommandPanel, HealthIndicator, ProvenanceBadge.

## Visual debt identified

- Older website copy still contains legacy CHRONO-PCOS/V8.3-era references in deep sections.
- Website header/hero need a stricter product hierarchy and less generic marketing-card behavior.
- Some desktop helpers still contain legacy dark/purple pill semantics even though the workstation is light.
- Android themes need explicit semantic tokens for surface hierarchy, state, provenance and compact controls instead of relying only on Material defaults.
- Launcher status presentation must remain tied to actual process exit state; visual polish must not mask build failures.
- Hardware UI needs a single sensor availability vocabulary: Present, Connected, Streaming, Quality, Last Value, Error, Unavailable.

## Files to preserve unless a concrete UI reason exists

Scientific core, database, CP2 parser/network readers, model registry, acquisition services, test fixtures, protocol code and safety/guardrail logic.

## Validation checklist

- Python syntax/import checks
- Existing pytest suite
- Patient Gradle build when Android SDK/JDK are available
- Doctor Gradle build when Android SDK/JDK are available
- Website static checks/browser smoke test
- Launcher startup/command exit-state verification
- Hardware protocol/CP2 parser compatibility checks
- Responsive review at 320/375/390/430/768/1024/1280/1440/1920 widths

## Audit conclusion

The redesign should be treated as a product-system implementation, not a palette swap. The common semantic layer is now the contract for subsequent screen-level work.
