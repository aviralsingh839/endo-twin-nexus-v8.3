# Firmware Guide

## Responsibilities
Sensor initialization → availability check → sampling → timestamping → packet encoding → integrity check → serial transport → explicit error state.

Every packet should carry a protocol version and sequence counter. The desktop parser must be able to detect gaps and reject malformed frames.

## Required behavior
- Do not substitute sensor values after a disconnect.
- Preserve packet gaps in stored data.
- Report actual sampling rate rather than assuming the configured target was achieved.
- Keep firmware version with every acquisition session.

The existing Arduino reader and packet parser remain the compatibility path until new wearable firmware is introduced.
