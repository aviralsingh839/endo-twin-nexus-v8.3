from pathlib import Path

from src.serial_io.packet_parser import PacketParser, PacketParseError, xor_crc_ascii

REPO = Path(__file__).resolve().parents[1]

def make_cp2(status=0):
    payload = "$CP2,1234,10000,9000,0.1,0.2,0.9,0.1,0.2,0.3,nan,nan,450,0,0.0,0.0,-1,-1,-1,nan,nan,nan,0," + str(status)
    return payload + "," + f"{xor_crc_ascii(payload):02X}"

def test_esp32s3_cp2_is_parser_compatible():
    sample = PacketParser(require_crc=True).parse(make_cp2())
    assert sample.ms == 1234
    assert sample.ir == 10000
    assert sample.gsr_raw == 450
    assert sample.source == "serial-usb"

def test_cp2_bad_crc_is_rejected():
    good = make_cp2()
    bad = good[:-2] + ("00" if not good.endswith("00") else "FF")
    try:
        PacketParser(require_crc=True).parse(bad)
        raise AssertionError("bad CRC was accepted")
    except PacketParseError:
        pass

def test_esp32s3_missing_sensor_semantics_are_preserved():
    # Status bit 3 = DS18B20 error and temp0 remains nan.
    sample = PacketParser(require_crc=True).parse(make_cp2(status=(1 << 3)))
    assert sample.temp_c != sample.temp_c  # NaN
    assert sample.status & (1 << 3)

def test_active_hardware_paths_match_current_architecture():
    active_files = [
        REPO / "hardware/esp32s3/endo_twin_wearable/endo_twin_wearable.ino",
        REPO / "hardware/arduino/endo_twin_mega_lab/endo_twin_mega_lab.ino",
        REPO / "scripts/build/build_firmware.sh",
        REPO / ".github/workflows/arduino_firmware.yml",
    ]
    text = "\n".join(p.read_text(encoding="utf-8") for p in active_files)
    assert "chrono_pcos_nano_pod" not in text
    assert "esp32s3_bridge" not in text
    assert "ESP32-S3" in text
    assert "Mega" in text
