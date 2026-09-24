"""Reusable ESP32-S3 / wearable connection state model for ENDO-TWIN NEXUS.

Transport adapters can feed this controller with state updates. The controller
keeps connection semantics consistent across desktop/Kivy/native UI layers.
It does not manufacture sensor measurements.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Optional


class DeviceConnectionState(str, Enum):
    DISCONNECTED = "disconnected"
    SCANNING = "scanning"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


@dataclass
class DeviceConnectionSnapshot:
    state: DeviceConnectionState = DeviceConnectionState.DISCONNECTED
    device_name: Optional[str] = None
    firmware: Optional[str] = None
    transport: Optional[str] = None
    endpoint: Optional[str] = None
    last_packet_time: Optional[float] = None
    packets_received: int = 0
    error: Optional[str] = None
    updated_at: float = field(default_factory=time.time)

    @property
    def connected(self) -> bool:
        return self.state is DeviceConnectionState.CONNECTED

    @property
    def last_packet_age_s(self) -> Optional[float]:
        if self.last_packet_time is None:
            return None
        return max(0.0, time.time() - self.last_packet_time)


class DeviceConnectionController:
    """Small UI-agnostic state controller shared by connection surfaces."""

    def __init__(self) -> None:
        self.snapshot = DeviceConnectionSnapshot()

    def scan_started(self) -> DeviceConnectionSnapshot:
        self.snapshot.state = DeviceConnectionState.SCANNING
        self.snapshot.error = None
        self.snapshot.updated_at = time.time()
        return self.snapshot

    def connecting(
        self,
        *,
        device_name: str | None = None,
        transport: str | None = None,
        endpoint: str | None = None,
    ) -> DeviceConnectionSnapshot:
        self.snapshot.state = DeviceConnectionState.CONNECTING
        self.snapshot.device_name = device_name or self.snapshot.device_name
        self.snapshot.transport = transport or self.snapshot.transport
        self.snapshot.endpoint = endpoint or self.snapshot.endpoint
        self.snapshot.error = None
        self.snapshot.updated_at = time.time()
        return self.snapshot

    def connected(
        self,
        *,
        device_name: str | None = None,
        firmware: str | None = None,
        transport: str | None = None,
        endpoint: str | None = None,
    ) -> DeviceConnectionSnapshot:
        self.snapshot.state = DeviceConnectionState.CONNECTED
        self.snapshot.device_name = device_name or self.snapshot.device_name
        self.snapshot.firmware = firmware or self.snapshot.firmware
        self.snapshot.transport = transport or self.snapshot.transport
        self.snapshot.endpoint = endpoint or self.snapshot.endpoint
        self.snapshot.error = None
        self.snapshot.updated_at = time.time()
        return self.snapshot

    def packet_received(self) -> DeviceConnectionSnapshot:
        self.snapshot.packets_received += 1
        self.snapshot.last_packet_time = time.time()
        self.snapshot.updated_at = self.snapshot.last_packet_time
        if self.snapshot.state in {
            DeviceConnectionState.CONNECTING,
            DeviceConnectionState.RECONNECTING,
        }:
            self.snapshot.state = DeviceConnectionState.CONNECTED
        return self.snapshot

    def reconnecting(self, error: str | None = None) -> DeviceConnectionSnapshot:
        self.snapshot.state = DeviceConnectionState.RECONNECTING
        self.snapshot.error = error
        self.snapshot.updated_at = time.time()
        return self.snapshot

    def failed(self, error: str) -> DeviceConnectionSnapshot:
        self.snapshot.state = DeviceConnectionState.ERROR
        self.snapshot.error = error
        self.snapshot.updated_at = time.time()
        return self.snapshot

    def disconnected(self) -> DeviceConnectionSnapshot:
        self.snapshot.state = DeviceConnectionState.DISCONNECTED
        self.snapshot.updated_at = time.time()
        return self.snapshot
