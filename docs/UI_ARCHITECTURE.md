# ENDO-TWIN NEXUS UI Architecture

## Layers

1. **Domain/data** — existing ENDO-TWIN core, database, CP2 acquisition and research modules.
2. **Semantic presentation** — shared terminology for provenance, connection, device and sensor state.
3. **Platform UI** — Qt widgets, Compose screens and website components adapted to their native interaction model.
4. **Application navigation** — workstation/mobile/site-specific information architecture.

## Rule

Business/scientific logic stays below presentation. UI code should consume existing models/services rather than recreate physiology, packet parsing or disease logic.

## Provenance contract

Presentation code must be able to render LIVE, DEMO, MEASURED, DERIVED, MODEL and UNAVAILABLE without silently changing the underlying data.

## Hardware contract

Hardware screens consume board/device state and sensor inventory. They must not infer physical presence from a placeholder value. ESP8266 and ESP32-S3 are sensor-pod variants; Arduino Mega is a lab/bench controller.

## Performance

High-frequency streams must use bounded buffers, downsampling and background processing. Compose lists should remain lazy; Qt plots should avoid unbounded redraw history.
