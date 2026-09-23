"""Arduino serial packet parsing.

Supported packets:

Canonical (current hardware - ESP32-S3 wearable, Mega lab, ESP8266 pod):
$CP3,ms,ir,red,ax,ay,az,gx,gy,gz,temp0,temp1,micRaw,micRms,micPitch,ecg,fsr,lux,roomT,hum,press,buttons,status,crc

Deprecated, still parsed so existing recordings keep loading:
$CP2,ms,ir,red,ax,ay,az,gx,gy,gz,temp0,temp1,gsr,micRaw,micRms,micPitch,ecg,fsr,lux,roomT,hum,press,buttons,status,crc
$CP,ms,ir,red,ax,ay,az,gx,gy,gz,tempC,gsr,lux,status,crc

CP3 differs from CP2 by exactly one field: the `gsr` channel was retired with the
GSR hardware, so the galvanic skin response reading no longer exists on the wire.
Legacy CP2 frames are still accepted, because recordings and public-study imports
made before the change contain them; their ``gsr_raw`` is preserved verbatim.

temp0 is skin temperature (DS18B20 in skin contact). mic/ECG/FSR remain explicit
missing-data markers on the wearable that are not fitted; they are decoded as
absent rather than as physiological zeros.

CRC is XOR of all characters in the payload before the final comma.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from src.data_models import SensorSample


class PacketParseError(ValueError):
    pass


#: Value stored where a channel exists in the format but is not measured by the
#: board that produced the frame. Never interpreted as a physiological reading.
NOT_MEASURED = -1


def xor_crc_ascii(text: str) -> int:
    c = 0
    for ch in text:
        c ^= ord(ch)
    return c & 0xFF


@dataclass
class PacketParser:
    require_crc: bool = True

    def parse(self, line: str) -> SensorSample:
        raw = line.strip()
        if not raw:
            raise PacketParseError("empty line")
        if raw.startswith("$CP3,"):
            return self._parse_cp3(raw)
        if raw.startswith("$CP2,"):
            return self._parse_cp2(raw)
        if raw.startswith("$CP,"):
            return self._parse_cp(raw)
        raise PacketParseError(f"bad prefix: {raw[:8]}")

    def _verify_crc(self, parts: list[str], expected_without_crc: int | None = None) -> None:
        if len(parts) < 2:
            raise PacketParseError("too few fields")
        payload = ",".join(parts[:-1])
        try:
            received_crc = int(parts[-1], 16)
        except ValueError as exc:
            raise PacketParseError("invalid crc field") from exc
        calc = xor_crc_ascii(payload)
        if self.require_crc and received_crc != calc:
            raise PacketParseError(f"crc mismatch: received={received_crc:02X} calc={calc:02X}")

    def _parse_cp(self, raw: str) -> SensorSample:
        parts = raw.split(",")
        if len(parts) != 15:
            raise PacketParseError(f"legacy $CP expected 15 fields, got {len(parts)}")
        self._verify_crc(parts)
        try:
            return SensorSample(
                timestamp_s=time.time(),
                ms=int(parts[1]),
                ir=int(float(parts[2])),
                red=int(float(parts[3])),
                ax_g=float(parts[4]),
                ay_g=float(parts[5]),
                az_g=float(parts[6]),
                gx_dps=float(parts[7]),
                gy_dps=float(parts[8]),
                gz_dps=float(parts[9]),
                temp_c=float(parts[10]),
                gsr_raw=int(float(parts[11])),
                lux=float(parts[12]),
                status=int(float(parts[13])),
                source="serial",
            )
        except (ValueError, IndexError) as exc:
            raise PacketParseError(f"numeric conversion failed: {exc}") from exc

    def _parse_cp3(self, raw: str) -> SensorSample:
        """Canonical frame: no GSR channel."""
        parts = raw.split(",")
        if len(parts) != 24:
            raise PacketParseError(f"enhanced $CP3 expected 24 fields, got {len(parts)}")
        self._verify_crc(parts)
        try:
            return SensorSample(
                timestamp_s=time.time(),
                ms=int(parts[1]),
                ir=int(float(parts[2])),
                red=int(float(parts[3])),
                ax_g=float(parts[4]),
                ay_g=float(parts[5]),
                az_g=float(parts[6]),
                gx_dps=float(parts[7]),
                gy_dps=float(parts[8]),
                gz_dps=float(parts[9]),
                temp_c=float(parts[10]),
                temp1_c=float(parts[11]),
                gsr_raw=NOT_MEASURED,          # retired with the GSR hardware
                mic_raw=int(float(parts[12])),
                mic_rms=float(parts[13]),
                mic_pitch_hz=float(parts[14]),
                ecg_raw=int(float(parts[15])),
                fsr_raw=int(float(parts[16])),
                lux=float(parts[17]),
                room_temp_c=float(parts[18]),
                humidity_pct=float(parts[19]),
                pressure_hpa=float(parts[20]),
                buttons=int(float(parts[21])),
                status=int(float(parts[22])),
                source="serial-usb",
            )
        except (ValueError, IndexError) as exc:
            raise PacketParseError(f"numeric conversion failed: {exc}") from exc

    def _parse_cp2(self, raw: str) -> SensorSample:
        """Deprecated frame retained for recordings made before GSR was retired."""
        parts = raw.split(",")
        if len(parts) != 25:
            raise PacketParseError(f"enhanced $CP2 expected 25 fields, got {len(parts)}")
        self._verify_crc(parts)
        try:
            return SensorSample(
                timestamp_s=time.time(),
                ms=int(parts[1]),
                ir=int(float(parts[2])),
                red=int(float(parts[3])),
                ax_g=float(parts[4]),
                ay_g=float(parts[5]),
                az_g=float(parts[6]),
                gx_dps=float(parts[7]),
                gy_dps=float(parts[8]),
                gz_dps=float(parts[9]),
                temp_c=float(parts[10]),
                temp1_c=float(parts[11]),
                gsr_raw=int(float(parts[12])),
                mic_raw=int(float(parts[13])),
                mic_rms=float(parts[14]),
                mic_pitch_hz=float(parts[15]),
                ecg_raw=int(float(parts[16])),
                fsr_raw=int(float(parts[17])),
                lux=float(parts[18]),
                room_temp_c=float(parts[19]),
                humidity_pct=float(parts[20]),
                pressure_hpa=float(parts[21]),
                buttons=int(float(parts[22])),
                status=int(float(parts[23])),
                source="serial-usb",
            )
        except (ValueError, IndexError) as exc:
            raise PacketParseError(f"numeric conversion failed: {exc}") from exc


def decode_status_flags(status: int) -> list[str]:
    """Decode the CP2 status word.

    The bit assignment is the wire contract shared by every firmware in
    ``hardware/``. Bit 9 is the Mega's OLED error; the ESP32-S3 wearable has no
    OLED and reports its ambient-light sensor error on bit 12 instead.

    Bit 4 (GSR saturated) is kept so pre-change CP2 recordings decode exactly as
    they always did. Current firmware never sets it: the GSR channel is retired.
    """
    labels = [
        "PPG finger absent",
        "PPG saturated",
        "MPU6050 error",
        "DS18B20 error",
        "GSR saturated (legacy CP2 only)",
        "I2C error",
        "Low signal quality",
        "ECG leads off",
        "BME280 error",
        "OLED error",
        "Microphone low signal",
        "FSR pressure artifact",
        "Ambient light sensor error",
    ]
    return [labels[i] for i in range(min(len(labels), 16)) if status & (1 << i)]
