# Mobile Wearable + Doctor Sync

## Android patient app

The patient app now includes a BLE transport boundary:
- scan nearby BLE devices
- connect and discover notification characteristics
- receive raw notification payloads
- store raw payloads locally in Room
- create/end wear sessions
- record removal-for-bathing events
- reconnect with a new wear episode
- export a complete patient-scoped sync package

## Hardware-specific protocol

The current BLE implementation intentionally does not invent a service UUID, characteristic UUID or packet layout for the final wearable because the exact board/BLE hardware has not been fixed.

Once the hardware is finalized, configure:
- BLE service UUID
- notify/write characteristic UUID
- packet framing
- timestamp semantics
- checksum/CRC if used
- sample-rate declaration
- firmware version
- sensor availability flags

Then connect the transport to the existing board-specific packet parser.

## Doctor Desktop

The Doctor Desktop imports the patient package and merges:
- stable patient identity
- wear sessions
- raw BLE packets
- wearable lifecycle events
- feature vectors
- research labels/runs
- reports and other available patient-scoped metadata

DEMO_DATA and REAL labels are retained.
