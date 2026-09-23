"""Wire-format tests for the ESP32-S3 wearable frames.

The wearable emits the canonical ``$CP3`` frame. ``$CP2`` is still accepted so
recordings and study imports made before the GSR hardware was retired keep
loading, but current firmware never produces it: CP3 is CP2 with the ``gsr``
field removed.
"""
from pathlib import Path

from src.serial_io.packet_parser import (
    NOT_MEASURED,
    PacketParser,
    PacketParseError,
    decode_status_flags,
    xor_crc_ascii,
)

REPO = Path(__file__).resolve().parents[1]

# Field order of each frame, as documented in src/serial_io/packet_parser.py.
CP3_FIELDS = ("ms,ir,red,ax,ay,az,gx,gy,gz,temp0,temp1,micRaw,micRms,micPitch,ecg,fsr,"
              "lux,roomT,hum,press,buttons,status")
CP2_FIELDS = ("ms,ir,red,ax,ay,az,gx,gy,gz,temp0,temp1,gsr,micRaw,micRms,micPitch,ecg,fsr,"
              "lux,roomT,hum,press,buttons,status")


def make_cp3(status=0, mic=0, ecg=-1, fsr=-1, buttons=0):
    payload = ("$CP3,1234,10000,9000,0.1,0.2,0.9,0.1,0.2,0.3,32.5,nan,"
               f"{mic},0.0,0.0,{ecg},{fsr},-1,nan,nan,nan,{buttons},{status}")
    return payload + "," + f"{xor_crc_ascii(payload):02X}"


def make_cp2(status=0):
    payload = ("$CP2,1234,10000,9000,0.1,0.2,0.9,0.1,0.2,0.3,nan,nan,450,"
               "0,0.0,0.0,-1,-1,-1,nan,nan,nan,0," + str(status))
    return payload + "," + f"{xor_crc_ascii(payload):02X}"


def test_cp3_is_parser_compatible():
    sample = PacketParser(require_crc=True).parse(make_cp3())
    assert sample.ms == 1234
    assert sample.ir == 10000
    assert sample.temp_c == 32.5
    assert sample.source == "serial-usb"


def test_cp3_carries_no_gsr_reading():
    """The retired channel must not reappear as a physiological value."""
    sample = PacketParser(require_crc=True).parse(make_cp3())
    assert sample.gsr_raw == NOT_MEASURED


def test_cp3_field_count_is_enforced():
    # A CP2 payload relabelled as CP3 must not be silently accepted.
    with_cp2_shape = make_cp2().replace("$CP2", "$CP3")
    try:
        PacketParser(require_crc=True).parse(with_cp2_shape)
    except PacketParseError:
        return
    raise AssertionError("a frame with the wrong field count was accepted")


def test_cp2_still_parses_for_existing_recordings():
    sample = PacketParser(require_crc=True).parse(make_cp2())
    assert sample.gsr_raw == 450      # legacy value preserved verbatim
    assert sample.source == "serial-usb"


def test_crc_is_verified_on_both_formats():
    for good in (make_cp3(), make_cp2()):
        bad = good[:-2] + ("00" if not good.endswith("00") else "FF")
        try:
            PacketParser(require_crc=True).parse(bad)
            raise AssertionError(f"bad CRC was accepted: {bad[:20]}")
        except PacketParseError:
            pass


def test_missing_sensor_semantics_are_preserved():
    # Status bit 3 = skin-temperature probe missing/unusable.
    sample = PacketParser(require_crc=True).parse(make_cp3(status=(1 << 3)))
    assert sample.status & (1 << 3)


def test_status_bit_9_stays_the_mega_oled_bit():
    """The S3's light error lives on bit 12 so bit 9 keeps decoding as OLED."""
    assert decode_status_flags(1 << 9) == ["OLED error"]
    assert decode_status_flags(1 << 12) == ["Ambient light sensor error"]
    # bit 4 is still decoded for legacy CP2 frames, and current firmware never sets it
    assert decode_status_flags(1 << 4) == ["GSR saturated (legacy CP2 only)"]


FIRMWARES = (
    "hardware/esp32s3/endo_twin_wearable/endo_twin_wearable.ino",
    "hardware/arduino/endo_twin_mega_lab/endo_twin_mega_lab.ino",
    "hardware/arduino/chrono_pcos_mega_firmware/chrono_pcos_mega_firmware.ino",
    "hardware/esp8266/endo_twin_sensor_pod/endo_twin_sensor_pod.ino",
)


def test_every_active_firmware_emits_cp3_without_a_gsr_path():
    for relative in FIRMWARES:
        text = (REPO / relative).read_text(encoding="utf-8")
        assert '"$CP3,' in text or '"$CP3," +' in text, f"{relative} does not emit the canonical CP3 frame"
        assert "analogRead(GSR" not in text, f"{relative} still reads a GSR pin"
        assert "gsrRaw" not in text, f"{relative} still holds a GSR variable"
        assert "ST_GSR_SAT=" not in text.replace(" ", ""), f"{relative} still defines a GSR status bit"


def test_every_firmware_builds_the_23_field_cp3_body():
    """CP3 is 24 comma-separated parts: the tag plus 22 data fields plus the CRC.

    The Arduino builds count commas directly because snprintf frames pad absent
    channels with literals, so counting ``%`` conversions undercounts.
    """
    import re

    for relative in FIRMWARES:
        text = (REPO / relative).read_text(encoding="utf-8")
        formats = [f for f in re.findall(r'"\$CP3[^"]*"', text) if "%" in f]
        if formats:
            # tag + 22 data fields = 23 parts, i.e. 22 commas before the CRC.
            parts = formats[0].split(",")
            assert len(parts) == 23, f"{relative}: {len(parts)} parts before the CRC"
            assert parts[-1].endswith('%u\"') or parts[-1].endswith('%d\"'), f"{relative}: status must be last"
            continue
        # The ESP8266 concatenates its frame; count the pieces it appends.
        body = text.split('String payload = "$CP3," +', 1)[1].split("return payload", 1)[0]
        # every literal run of missing-data markers must be six fields wide
        assert '"-1,-1,-1,-1,-1,-1," +' in body, f"{relative}: missing-data run is not six fields"


def test_esp8266_pod_frame_matches_the_cp3_layout():
    """The ESP8266 builds its frame by concatenation; emulate it and parse the result."""
    text = (REPO / "hardware/esp8266/endo_twin_sensor_pod/endo_twin_sensor_pod.ino").read_text(encoding="utf-8")
    assert '"$CP3," +' in text, "the pod should build a CP3 frame"
    # Field order as written in makePacket(): ms, ir, red, imu x6, temp0, temp1,
    # six explicit not-measured channels (mic x3, ecg, fsr, lux), room/hum/press,
    # buttons, status - then the CRC is appended by the firmware.
    payload = ("$CP3,1000,12000,11000,0.01,0.02,0.98,0.1,0.2,0.3,32.5,nan,"
               "-1,-1,-1,-1,-1,-1,24.3,41.2,1008.4,0,0")
    assert len(payload.split(",")) == 23, "the tag plus 22 data fields"
    frame = payload + "," + f"{xor_crc_ascii(payload):02X}"
    assert len(frame.split(",")) == 24, "CP3 is 24 comma-separated parts"
    sample = PacketParser(require_crc=True).parse(frame)
    assert sample.temp_c == 32.5
    assert sample.lux == -1          # not fitted, reported as absent, not fabricated
    assert sample.ecg_raw == -1
    assert sample.gsr_raw == NOT_MEASURED


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


def test_legacy_field_order_is_documented_for_readers():
    parser_source = (REPO / "src/serial_io/packet_parser.py").read_text(encoding="utf-8")
    assert CP3_FIELDS in parser_source
    assert CP2_FIELDS in parser_source
