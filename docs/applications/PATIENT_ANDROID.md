# ENDO-TWIN Patient Android V8.6

Native Kotlin + Jetpack Compose.

The Android app remains patient-scoped and supports the existing Connect workflow. Build metadata is 8.6.0.

The current phone-to-workstation transport is deliberately **DEMO_DATA**. Real-device live sensor ingestion is not claimed here. The canonical live USB sensor processing path is the desktop workstation runtime.

Mobile connection:
Doctor Workstation → Mobile Link → endpoint + pairing code
Patient Android → Connect → Pair → Send latest session.
