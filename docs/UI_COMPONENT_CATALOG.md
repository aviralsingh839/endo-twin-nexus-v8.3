# ENDO-TWIN NEXUS Component Catalog

| Component | Purpose | Required states |
|---|---|---|
| MetricCard | Compact key metric | normal/loading/unavailable |
| StatusBadge | Short semantic state | LIVE/DEMO/ERROR/etc. |
| DeviceCard | Hardware identity | disconnected/connecting/ready/error |
| SensorCard | Sensor inventory | absent/present/streaming/error |
| ConnectionBadge | Link state | offline/connecting/connected |
| SignalQuality | Quality indicator | good/fair/poor/unavailable |
| MiniTrend | Small longitudinal context | empty/loading/data |
| WaveformChart | Live/review signal | streaming/paused/unavailable |
| DataTable | Dense records | loading/empty/error/data |
| FilterBar | Search/filter/sort | default/active/no-results |
| EmptyState | Explain missing content | reason + next action |
| ErrorState | Explain failure | actual error + recovery |
| ProvenanceBadge | Source traceability | MEASURED/DERIVED/MODEL/DEMO |
| CommandPanel | Launcher engineering action | idle/running/success/failed/cancelled |
| Timeline | Events and sessions | empty/data/partial |

Components should remain visually consistent while adapting to platform interaction conventions.
