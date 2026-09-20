"""Sensors wrappers - preserve V8.3 serial_io + new unified interface"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.serial_io.packet_parser import PacketParser
    from src.serial_io.serial_manager import SerialManager
except ImportError:
    PacketParser = None
    SerialManager = None

__all__ = ['PacketParser', 'SerialManager']
