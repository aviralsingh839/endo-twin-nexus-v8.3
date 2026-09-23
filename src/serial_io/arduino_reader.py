"""Threaded PySerial reader for Arduino packets with auto-reconnect."""
from __future__ import annotations
import threading, time
from typing import Optional
try:
    import serial
    from serial.tools import list_ports
except Exception:
    serial = None
    list_ports = None
from PySide6.QtCore import QObject, Signal
from src.config import RECONNECT_RETRY_S, SERIAL_BAUD, SERIAL_TIMEOUT_S, STALE_DATA_TIMEOUT_S
from src.data_models import SensorSample
from src.serial_io.packet_parser import PacketParseError, PacketParser

class _SerialStaleError(Exception):
    """Raised when no data arrives for longer than the stale timeout."""

class ArduinoReader(QObject):
    sample_received=Signal(object)
    error_received=Signal(str)
    state_changed=Signal(str)
    ack_received=Signal(str)
    def __init__(self,port:str,baud:int=SERIAL_BAUD,require_crc:bool=True,parent=None):
        super().__init__(parent); self.port=port; self.baud=baud; self.require_crc=require_crc
        self._thread:Optional[threading.Thread]=None; self._stop=threading.Event(); self._serial=None
        self.parser=PacketParser(require_crc=require_crc)
    @staticmethod
    def available_ports()->list[str]:
        return [] if list_ports is None else [p.device for p in list_ports.comports()]
    def start(self):
        if self._thread and self._thread.is_alive(): return
        self._stop.clear(); self._thread=threading.Thread(target=self._run,daemon=True); self._thread.start()
    def stop(self):
        self._stop.set()
        if self._serial is not None:
            try:self._serial.close()
            except Exception:pass
        self.state_changed.emit("stopped")
    def write_command(self,command:str):
        if self._serial is None:return
        if not command.endswith("\n"):command+="\n"
        try:self._serial.write(command.encode("ascii",errors="ignore")); self._serial.flush()
        except Exception as exc:self.error_received.emit(f"Serial write failed: {exc}")
    def _run(self):
        if serial is None:self.error_received.emit("pyserial is not installed"); return
        while not self._stop.is_set():
            try:
                self._serial=serial.Serial(self.port,self.baud,timeout=min(float(SERIAL_TIMEOUT_S),0.05),write_timeout=0.20)
                time.sleep(0.55)
                self.state_changed.emit(f"connected:{self.port}")
                self._read_loop()
            except _SerialStaleError:self.error_received.emit(f"Serial link to {self.port} went silent; reconnecting...")
            except Exception as exc:self.error_received.emit(f"Serial connection problem on {self.port}: {exc}")
            finally:
                try:
                    if self._serial is not None:self._serial.close()
                except Exception:pass
                self._serial=None
            if self._stop.is_set():break
            self.state_changed.emit("reconnecting")
            deadline=time.time()+RECONNECT_RETRY_S
            while time.time()<deadline and not self._stop.is_set():time.sleep(0.1)
        self.state_changed.emit("stopped")
    def _read_loop(self):
        assert self._serial is not None
        last_data=time.time()
        while not self._stop.is_set():
            try:
                line=self._serial.readline().decode("ascii",errors="replace").strip()
                if not line:
                    if time.time()-last_data>STALE_DATA_TIMEOUT_S: raise _SerialStaleError()
                    continue
                if line.startswith("$ACK"):
                    # Firmware command acknowledgements ("$ACK,PONG,00") share the
                    # serial link with measurement frames. They are informational;
                    # feeding them to the frame parser reported them as errors.
                    self.ack_received.emit(line)
                    continue
                sample:SensorSample=self.parser.parse(line); last_data=time.time(); self.sample_received.emit(sample)
            except PacketParseError as exc:self.error_received.emit(f"Packet parse error: {exc}")
            except Exception as exc:
                if isinstance(exc,_SerialStaleError): raise
                self.error_received.emit(f"Serial read error: {exc}"); raise
