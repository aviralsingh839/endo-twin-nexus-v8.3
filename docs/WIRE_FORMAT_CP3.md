# Wire format: `$CP3` and legacy `$CP2`

This is the canonical description of what the firmware sends and what the host
accepts. Everything else in `docs/` refers back to this file.

## Current format — `$CP3`

```
$CP3,ms,ir,red,ax,ay,az,gx,gy,gz,temp0,temp1,micRaw,micRms,micPitch,ecg,fsr,lux,roomT,hum,press,buttons,status,crc
```

24 comma-separated parts: the `$CP3` tag, 22 data fields, the XOR CRC.

| Field | Meaning | Typical source |
|---|---|---|
| `ms` | `millis()` at send time | firmware clock |
| `ir`, `red` | PPG raw channels | MAX30102 |
| `ax/ay/az`, `gx/gy/gz` | acceleration (g), angular rate (dps) | MPU6050 |
| `temp0` | **skin-contact temperature (°C)** | DS18B20 probe touching the skin |
| `temp1` | second probe, `nan` when only one is fitted | DS18B20 (optional) |
| `micRaw`, `micRms`, `micPitch` | microphone raw / RMS / pitch | MAX4466 (lab hub only) |
| `ecg` | ECG sample | AD8232 (lab hub only) |
| `fsr` | pressure sample | FSR divider (lab hub only) |
| `lux` | ambient light | BH1750 |
| `roomT`, `hum`, `press` | room temperature, humidity, pressure | BME280 |
| `buttons` | button bitmask | firmware |
| `status` | status bitfield (below) | firmware |
| `crc` | XOR CRC of everything before the final comma | firmware |

**Not fitted is not zero.** Every channel a board does not carry is sent as the
not-measured marker `-1` (`nan` for floating-point-only fields such as `temp1`).
The host stores `-1` as "not fitted" and never renders it as a physiological
zero. Firmware must not substitute a plausible-looking value for a channel it
does not have.

`status` bits (shared by every firmware):

| Bit | Meaning |
|---|---|
| 0 | PPG finger absent |
| 1 | PPG saturated |
| 2 | MPU6050 error |
| 3 | DS18B20 error (skin probe missing / disconnected / 85 °C power-on value) |
| 4 | GSR saturated — legacy CP2 recordings only, never set by current firmware |
| 5 | I2C error |
| 6 | Low signal quality |
| 7 | ECG leads off |
| 8 | BME280 error |
| 9 | OLED error (Mega hub only — kept distinct from bit 12) |
| 10 | Microphone low signal |
| 11 | FSR pressure artifact |
| 12 | Ambient light sensor error (ESP32-S3 wearable) |
| 13–15 | unused, must stay 0 |

## Why there is a new tag at all

`$CP2` carried a GSR (galvanic skin response) channel:

```
$CP2,ms,ir,red,ax,ay,az,gx,gy,gz,temp0,temp1,gsr,micRaw,micRms,micPitch,ecg,fsr,lux,roomT,hum,press,buttons,status,crc
```

GSR hardware is not used on this build and its code has been removed, so the
`gsr` field is gone and the frame is one field shorter. Rather than silently
redefine `$CP2` as a 23-part frame — which would corrupt every recording already
on disk — the format was given a new tag. `gsr.py` and its signal-processing
chain no longer exist in the active tree.

## Backwards compatibility

| Producer | Frame | Host behaviour |
|---|---|---|
| ESP32-S3 wearable (current) | `$CP3` | parsed as canonical; `gsr_raw = -1` (`NOT_MEASURED`) |
| Mega lab (current) | `$CP3` | parsed as canonical |
| ESP8266 sensor pod (current) | `$CP3` | parsed as canonical |
| Pre-change recordings, public-study imports | `$CP2` | still parsed, 25 parts, `gsr_raw` kept verbatim (e.g. 450) |
| Very old firmware | `$CP` | still parsed |

The Python parser (`src/serial_io/packet_parser.py`) accepts both widths; the
Android TCP clients (`android/*/wifi/EndoTwinTcpClient.kt`) accept both and also
expose which format a frame used. Field counts are enforced on both sides: a
`$CP2`-shaped payload relabelled `$CP3` is rejected instead of being misread.

The database keeps its nullable GSR columns and the `'gsr'` measurement type so
existing databases open unchanged; nothing writes to them any more.

## Verifying it

```bash
.venv/bin/python -m pytest tests/test_esp32s3_cp2_compatibility.py -q
```

That suite parses a real CP3 frame, rejects a mislabelled CP2 frame, checks the
legacy CP2 path still yields `gsr_raw == 450`, verifies CRC on both formats,
asserts the status-bit map, and confirms every active firmware emits `$CP3` with
no GSR code path.
