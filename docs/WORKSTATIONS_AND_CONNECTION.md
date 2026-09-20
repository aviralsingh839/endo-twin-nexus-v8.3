# ENDO-TWIN V8.5 — Workstations & Connection

## Doctor PC
`./START.sh doctor` — multi-patient workstation, bridge **7777**.

## Patient PC
`./START.sh patient-pc` — single-patient workstation, bridge **7778**.

## Phone → Doctor PC
Doctor → Mobile Link → copy address + code.
Patient Android → Connect → enter endpoint/code → Pair → Send latest session.

Received packages are stored in `data/bridge/inbox/`.

Both devices must reach the workstation on the same trusted LAN. The bridge is research infrastructure, not production security.
