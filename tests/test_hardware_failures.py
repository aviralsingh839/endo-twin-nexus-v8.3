"""Test hardware failure handling - V8.3."""
import sys
sys.path.insert(0, '.')
from src.serial_io.packet_parser import PacketParser, PacketParseError
from src.core.quality_control import SensorQualityControl
from src.utils.synthetic import generate_subject_timeline, SyntheticSubjectProfile

def test_packet_parser_corrupted():
    parser = PacketParser(require_crc=True)
    # Valid packet example from nano pod
    # $CP2,ms,ir,red,ax,ay,az,gx,gy,gz,temp0,temp1,gsr,micRaw,micRms,micPitch,ecg,fsr,lux,roomT,hum,press,buttons,status,crc
    # We'll test corrupted CRC
    valid_payload = "$CP2,1234,10000,9000,0.1,0.2,0.9,0.1,0.2,0.3,32.5,nan,450,0,0.0,0.0,-1,-1,-1,nan,nan,nan,0,0"
    # Calculate CRC
    c = 0
    for ch in valid_payload:
        c ^= ord(ch)
    crc = c & 0xFF
    valid_packet = f"{valid_payload},{crc:02X}"
    try:
        sample = parser.parse(valid_packet)
        print(f"Valid packet parsed: ir={sample.ir}")
    except PacketParseError as e:
        print(f"Valid packet failed: {e}")
        assert False

    # Corrupted CRC
    corrupted = f"{valid_payload},00"
    try:
        parser.parse(corrupted)
        assert False, "Should have raised CRC error"
    except PacketParseError:
        print("Corrupted packet correctly rejected")

    # Missing fields
    try:
        parser.parse("$CP2,1234,10000")
        assert False
    except PacketParseError:
        print("Missing fields correctly rejected")

    print("test_packet_parser_corrupted PASSED")

def test_disconnected_sensors():
    qc = SensorQualityControl()
    # Legacy optical disconnect remains supported.
    q_ir = qc.evaluate("ir", 0, source="legacy-optical-ppg")
    assert q_ir.quality == 0.0
    assert q_ir.artifact == True
    print("Disconnected legacy optical PPG detected")

    # V8.8 analog Pulse Sensor uses the 0..1023 Arduino ADC range.
    q_pulse = qc.evaluate("analog_pulse", 0, source="serial-nano-analog-pulse")
    assert q_pulse.quality == 0.0
    assert q_pulse.artifact == True
    q_pulse_live = qc.evaluate("analog_pulse", 512, source="serial-nano-analog-pulse")
    assert q_pulse_live.quality > 0.0
    assert not q_pulse_live.artifact
    print("Analog Pulse Sensor disconnect/live handling detected")

    # Disconnected temp: nan
    q_temp = qc.evaluate("temp_c", None, source="DS18B20")
    assert q_temp.artifact == True
    print("Disconnected temp detected")

    # Flatline
    for _ in range(10):
        qc.evaluate("hr", 70.0, source="test")
    q_flat = qc.evaluate("hr", 70.0, source="test")
    print(f"Flatline: {q_flat.artifact}, {q_flat.artifact_type}")

    print("test_disconnected_sensors PASSED")

def test_noisy_ppg():
    qc = SensorQualityControl()
    # Stable HR then noisy
    for i in range(20):
        qc.evaluate("hr", 70 + (i % 2), source="legacy-optical-ppg")
    q_noisy = qc.evaluate("hr", 150, source="MAX30102")
    print(f"Noisy PPG: quality {q_noisy.quality}, artifact {q_noisy.artifact}")
    assert q_noisy.quality < 1.0
    print("test_noisy_ppg PASSED")

def test_excessive_motion():
    # Motion index high should degrade quality
    from src.signal_processing.imu import IMUProcessor
    imu = IMUProcessor()
    # Simulate high motion
    import time
    for i in range(50):
        imu.add_sample(time.time() + i*0.02, 2.0, 1.5, 0.5, 100, 100, 100)
    features = imu.features()
    print(f"Motion index: {features['motion_index']}, activity {features['activity_level']}")
    assert features["motion_index"] > 0.5
    print("test_excessive_motion PASSED")

def test_sensor_reconnection():
    qc = SensorQualityControl()
    # Disconnect then reconnect
    q1 = qc.evaluate("hr", None, source="test")
    assert q1.artifact == True
    q2 = qc.evaluate("hr", 70, source="test")
    assert q2.artifact == False
    assert q2.quality > 0.5
    print("test_sensor_reconnection PASSED")

def test_missing_data_not_physiological():
    # Sensor failure scenario should have low quality, not be interpreted as physiological abnormality
    profile = SyntheticSubjectProfile(subject_id="FAIL", age_years=22, bmi=23.5)
    vectors = generate_subject_timeline(profile, days=10, samples_per_day=12, scenario="sensor_failure",
                                        scenario_params={"sensor_failure_day": 5}, seed=42)
    # Check quality drops after failure day
    qualities_before = [v.signal_quality for v in vectors[:60]]
    qualities_after = [v.signal_quality for v in vectors[60:]]
    avg_before = sum(qualities_before)/len(qualities_before) if qualities_before else 0
    avg_after = sum(qualities_after)/len(qualities_after) if qualities_after else 0
    print(f"Quality before: {avg_before:.2f}, after: {avg_after:.2f}")
    assert avg_after < avg_before or avg_after < 0.5
    print("test_missing_data_not_physiological PASSED")

if __name__ == "__main__":
    test_packet_parser_corrupted()
    test_disconnected_sensors()
    test_noisy_ppg()
    test_excessive_motion()
    test_sensor_reconnection()
    test_missing_data_not_physiological()
