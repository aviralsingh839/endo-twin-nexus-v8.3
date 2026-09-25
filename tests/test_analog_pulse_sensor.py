"""Tests for V8.8 generic analog Pulse Sensor compatibility."""
import time
import numpy as np

from src.data_models import SensorSample
from src.serial_io.packet_parser import PacketParser, xor_crc_ascii
from src.signal_processing.ppg import PPGProcessor
from src.utils.quality import ppg_quality


def _cp2(payload_without_crc: str) -> str:
    return f"{payload_without_crc},{xor_crc_ascii(payload_without_crc):02X}"


def test_parser_marks_analog_pulse_packet():
    payload = "$CP2,1000,2048,-1,0,0,1,0,0,0,32.5,nan,450,0,0,0,-1,-1,-1,nan,nan,nan,0,4096"
    s = PacketParser().parse(_cp2(payload))
    assert s.ir == 2048
    assert s.red == -1
    assert s.ppg_input_type == "ANALOG_PULSE"
    assert s.source == "serial-mega-analog-pulse"
    assert s.status & (1 << 12)


def test_analog_pulse_quality_does_not_use_optical_threshold():
    x = 2000 + 180 * np.sin(2 * np.pi * 1.2 * np.arange(500) / 50.0)
    q = ppg_quality(x, red_values=None, motion_index=0.0, fs_hz=50.0, input_type="ANALOG_PULSE")
    assert q > 0.0


def test_analog_pulse_processor_disables_spo2():
    p = PPGProcessor(history_s=30, fs_hz=50, input_type="ANALOG_PULSE")
    t = np.arange(30.0, step=0.02)
    x = 2000 + 180*np.sin(2*np.pi*1.2*t)
    for ti, xi in zip(t, x):
        p.add_sample(ti, int(xi), -1)
    f = p.features()
    assert f["spo2_pct"] is None


def test_sensor_sample_keeps_backward_compatible_field_order():
    s = SensorSample(
        timestamp_s=time.time(), ms=1, ir=2000, red=-1,
        ax_g=0, ay_g=0, az_g=1, gx_dps=0, gy_dps=0, gz_dps=0,
        temp_c=32.5, gsr_raw=450, lux=-1
    )
    assert s.ppg_input_type == "OPTICAL_IR_RED"
