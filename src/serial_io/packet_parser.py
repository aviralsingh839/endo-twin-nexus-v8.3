"""Arduino serial packet parsing - V8.4 Shoulder+Forearm build.

Supported packets:

Legacy UNO:
$CP,ms,ir,red,ax,ay,az,gx,gy,gz,tempC,gsr,lux,status,crc

Enhanced Mega / wearable V8.4:
$CP2,ms,ir,red,ax,ay,az,gx,gy,gz,temp0,temp1,gsr,micRaw,micRms,micPitch,ecg,fsr,lux,roomT,hum,press,buttons,status,crc

V8.4 hardware map:
- I2C bus SDA=8 SCL=9: MPU6050/2060 (shoulder), BME280 (room temp/hum/press), BH1750 (lux)
- Pulse S=40 analog (forearm) -> ir field, red=-1
- DS18B20 DATA=6 (forearm skin temp) -> temp0
- GSR optional -> gsr_raw
- BME280 -> roomT, hum, press
- BH1750 -> lux

V8.8 analog-pulse compatibility:
- When status bit 12 (ST_PPG_ANALOG) is set, ir = ADC pulse waveform.
- red = -1 because no optical red channel.
- Do NOT infer SpO2 from analog pulse.

CRC is XOR of all characters in the payload before the final comma.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from src.data_models import SensorSample


class PacketParseError(ValueError):
    pass


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
                ppg_input_type="OPTICAL_IR_RED",
                source="serial",
            )
        except (ValueError, IndexError) as exc:
            raise PacketParseError(f"numeric conversion failed: {exc}") from exc

    def _parse_cp2(self, raw: str) -> SensorSample:
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
                ppg_input_type=("ANALOG_PULSE" if (int(float(parts[23])) & (1 << 12)) else "OPTICAL_IR_RED"),
                source=("serial-mega-analog-pulse" if (int(float(parts[23])) & (1 << 12)) else "serial-mega"),
            )
        except (ValueError, IndexError) as exc:
            raise PacketParseError(f"numeric conversion failed: {exc}") from exc


def decode_status_flags(status: int) -> list[str]:
    labels = [
        "Pulse sensor absent / no finger",
        "Pulse sensor saturated / clipped",
        "MPU6050/2060 error (shoulder IMU)",
        "DS18B20 error (forearm skin temp)",
        "GSR saturated",
        "I2C bus error (SDA=8 SCL=9)",
        "Low signal quality",
        "ECG leads off (unused)",
        "BME280 error (shoulder env)",
        "OLED error (unused)",
        "Microphone low signal (unused)",
        "FSR pressure artifact (unused)",
        "Analog Pulse Sensor active (forearm GPIO40)",
        "Analog Pulse Sensor invalid ADC",
        "BH1750 error (shoulder lux)",
        "Reserved / future",
    ]
    return [labels[i] for i in range(min(len(labels), 16)) if status & (1 << i)]


def decode_hardware_health(status: int) -> dict:
    """Return per-sensor health dict for live dashboard."""
    return {
        "pulse": not (status & (1<<0) or status & (1<<1) or status & (1<<13)),
        "mpu": not (status & (1<<2)),
        "ds18": not (status & (1<<3)),
        "gsr": not (status & (1<<4)),
        "i2c": not (status & (1<<5)),
        "bme280": not (status & (1<<8)),
        "bh1750": not (status & (1<<14)),
        "analog_active": bool(status & (1<<12)),
    }
