# Firmware guide

Firmware responsibilities:
1. Initialize sensors.
2. Verify sensor availability.
3. Sample raw channels at configured rates.
4. Timestamp frames.
5. Encode packets with version + sequence fields and integrity checking.
6. Report sensor errors instead of substituting values.
7. Recover from transient serial/device failures where safe.

The existing serial packet parser/Arduino reader remains the reference implementation until a hardware-specific firmware package is introduced.
