"""Synthetic live stream for UI demonstration only - V8.4 Shoulder+Forearm model.

This is NOT a dataset and must not be used to train/validate medical models.
It simulates:
- Shoulder: MPU6050/2060 motion, BME280 room temp/hum/press, BH1750 lux
- Forearm: analog pulse sensor (GPIO40) + DS18B20 skin temp (GPIO6)
- Optional GSR

Smooth 50Hz output for live dashboard testing.
"""
from __future__ import annotations

import math
import time

import numpy as np
from PySide6.QtCore import QObject, QTimer, Signal

from src.data_models import SensorSample


class DemoSensorStream(QObject):
    sample_received = Signal(object)
    state_changed = Signal(str)
    error_received = Signal(str)

    def __init__(self, fs_hz: float = 50.0, parent=None):
        super().__init__(parent)
        self.fs_hz = fs_hz
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.t0 = time.time()
        self.i = 0
        self.rng = np.random.default_rng(7)
        self.mode = "rest"
        # Env state
        self.bme_temp = 25.2
        self.bme_hum = 48.0
        self.bme_press = 1008.5
        self.lux_base = 180.0

    def start(self) -> None:
        self.t0 = time.time()
        self.i = 0
        self.timer.start(int(1000 / self.fs_hz))
        self.state_changed.emit("demo-running-v8.4-shoulder-forearm")

    def stop(self) -> None:
        self.timer.stop()
        self.state_changed.emit("demo-stopped")

    def write_command(self, command: str) -> None:
        pass

    def _tick(self) -> None:
        now = time.time()
        t = now - self.t0
        # Cycle rest, stress, movement every 2 minutes
        phase = int(t // 120) % 3
        if phase == 0:
            hr = 72 + 3 * math.sin(2 * math.pi * t / 35)
            motion = 0.02
            gsr = 420 + 15 * math.sin(2 * math.pi * t / 50)
        elif phase == 1:
            hr = 90 + 5 * math.sin(2 * math.pi * t / 25)
            motion = 0.04
            gsr = 600 + 70 * abs(math.sin(2 * math.pi * t / 11))
        else:
            hr = 105 + 8 * math.sin(2 * math.pi * t / 20)
            motion = 0.35
            gsr = 520 + 40 * math.sin(2 * math.pi * t / 16)

        pulse_freq = hr / 60.0
        # Analog pulse sensor: 0..4095 ADC, ~ mid 1800 + pulse waveform
        # Real analog pulse sensor has inverted/offset waveform, simulate
        base = 1850
        pulse_wave = 280 * math.sin(2 * math.pi * pulse_freq * t) + 90 * math.sin(2 * math.pi * 2 * pulse_freq * t + 0.3)
        # Dicrotic notch slight
        pulse_wave += 25 * math.sin(2 * math.pi * 3 * pulse_freq * t + 0.7)
        analog_pulse = int(max(0, min(4095, base + pulse_wave + self.rng.normal(0, 8))))

        # MPU6050 shoulder mount - relatively stable vs wrist
        ax = self.rng.normal(0, motion*0.6)
        ay = self.rng.normal(0, motion*0.6)
        az = 1.0 + self.rng.normal(0, motion*0.4)
        gx = self.rng.normal(0, motion * 15)
        gy = self.rng.normal(0, motion * 15)
        gz = self.rng.normal(0, motion * 15)

        # DS18B20 forearm skin temp: 32-34C, circadian variation
        skin_temp = 32.8 + 0.4 * math.sin(2 * math.pi * t / (24*3600) - 1.0) + 0.15*math.sin(2*math.pi*t/120) + self.rng.normal(0, 0.03)

        # BME280 shoulder: room temp, hum, press with slow drift
        self.bme_temp += self.rng.normal(0, 0.005)
        self.bme_temp = np.clip(self.bme_temp, 22.0, 28.0)
        # humidity inversely correlated with temp slightly
        self.bme_hum += self.rng.normal(0, 0.02) - 0.01*(self.bme_temp-25)
        self.bme_hum = np.clip(self.bme_hum, 35, 65)
        self.bme_press += self.rng.normal(0, 0.02)
        self.bme_press = np.clip(self.bme_press, 1000, 1020)

        # BH1750 lux: shoulder ambient, varies with movement/orientation
        lux = self.lux_base + 80*math.sin(2*math.pi*t/240) + 30*math.sin(2*math.pi*t/17) + self.rng.normal(0, 3)
        if phase == 2: # movement causes lux variation as shoulder moves
            lux += 20*self.rng.normal(0, 1)
        lux = max(1, lux)

        sample = SensorSample(
            timestamp_s=now,
            ms=int(t * 1000),
            ir=analog_pulse,  # analog pulse raw
            red=-1,
            ax_g=float(ax),
            ay_g=float(ay),
            az_g=float(az),
            gx_dps=float(gx),
            gy_dps=float(gy),
            gz_dps=float(gz),
            temp_c=float(skin_temp),  # DS18B20 forearm
            gsr_raw=int(gsr + self.rng.normal(0, 8)),
            lux=float(lux),  # BH1750 shoulder
            ecg_raw=-1,
            mic_raw=-1,
            mic_rms=0.0,
            mic_pitch_hz=0.0,
            fsr_raw=-1,
            temp1_c=float('nan'),
            room_temp_c=float(self.bme_temp),
            humidity_pct=float(self.bme_hum),
            pressure_hpa=float(self.bme_press),
            buttons=0,
            status=(1<<12),  # analog pulse active
            ppg_input_type="ANALOG_PULSE",
            source="demo-v8.4-shoulder-forearm",
        )
        self.i += 1
        self.sample_received.emit(sample)
