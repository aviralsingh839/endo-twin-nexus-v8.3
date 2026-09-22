# V8.7 Unified Workstation

The new launcher is one desktop window containing:

1. Patient workspace — live physiology, signal quality, patient context and the CHRONO-PCOS research index.
2. Doctor workspace — local patient registry, Add Patient, edit clinical context and shared patient selection.
3. Prototype Lab — packet rate, PING/LED/BEEP commands, 15-second module acceptance test and export.
4. Settings — fixed session mode and USB/ESP transport information.

The startup dialog offers DEMO or LIVE. LIVE can use the Mega over USB or the ESP8266 bridge over TCP port 7777.

The research index is only calculated after a disease-specific evidence gate is satisfied. Wearable signals are contextual physiology; they are not treated as a standalone PCOS/PCOD diagnosis.

Prototype PASS means software received and processed plausible channel data. It does not prove physical attachment, calibration or clinical accuracy.
