# ENDO-TWIN V8.5 — Build & Run

Start: `./START.sh`

Workstations:
```bash
./START.sh doctor
./START.sh patient-pc
```

Android:
```bash
./setup_android.sh
./build_apks.sh all
```

Outputs are copied to `DIST/android/`.

Phone connection:
Doctor Workstation → Mobile Link → address + 6-digit code.
Patient Android → Connect → Pair → Send latest session.

The bridge is trusted-LAN research infrastructure, not production clinical security.
