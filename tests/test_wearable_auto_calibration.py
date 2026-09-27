from __future__ import annotations

import math
import time

import numpy as np

from src.core.raw_calibration import RawAutoCalibrator
from src.data_models import SensorSample
from src.serial_io.packet_parser import PacketParser, xor_crc_ascii
from src.signal_processing.analog_ppg import AnalogPPGProcessor
from src.disease_modules.pcos_complications import PCOSComplicationContextEngine


def _sample(**kw):
    data = dict(
        timestamp_s=time.time(), ms=1, ir=-1, red=-1,
        ax_g=0.01, ay_g=-0.01, az_g=1.01,
        gx_dps=0.2, gy_dps=-0.1, gz_dps=0.1,
        temp_c=float("nan"), gsr_raw=1600, lux=120.0,
        analog_ppg_raw=2048.0, room_temp_c=29.0,
        humidity_pct=45.0, pressure_hpa=1008.0,
    )
    data.update(kw)
    return SensorSample(**data)


def test_cp3_packet_parser_round_trip():
    payload = "$CP3,123,2050,1600,0.01,-0.01,1.01,0.2,-0.1,0.1,29.0,45.0,1008.0,120.0,0"
    line = f"{payload},{xor_crc_ascii(payload):02X}"
    sample = PacketParser(require_crc=True).parse(line)
    assert sample.analog_ppg_raw == 2050.0
    assert sample.gsr_raw == 1600
    assert sample.room_temp_c == 29.0


def test_calibrator_ready_and_transform():
    cal = RawAutoCalibrator(warmup_s=0.0, min_samples=20)
    for i in range(60):
        cal.update(_sample(ms=i, analog_ppg_raw=2048 + 3 * math.sin(i / 5), gsr_raw=1600 + (i % 3)))
    assert cal.ready_fraction >= 0.75
    z = cal.transform_value("analog_ppg_raw", 2050)
    assert z is not None and abs(float(z)) < 3.0


def test_analog_ppg_has_bounded_quality_and_hr():
    p = AnalogPPGProcessor(fs_hz=20)
    start = time.time()
    for i in range(20 * 25):
        t = i / 20.0
        pulse = 2048 + 500 * math.sin(2 * math.pi * 1.2 * t)
        p.add_sample(start + t, pulse)
    f = p.features(motion_index=0.0)
    assert f["hr_bpm"] is None or 60 <= f["hr_bpm"] <= 90
    assert 0.0 <= f["ppg_quality"] <= 1.0


def test_complications_are_context_not_probability():
    engine = PCOSComplicationContextEngine()
    rows = engine.evaluate({"age_years": 25, "bmi": 24.0}, None)
    assert rows
    assert all("probability" not in str(r).lower() for r in rows)
