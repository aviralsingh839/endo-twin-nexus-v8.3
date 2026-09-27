/*
  ENDO-TWIN NEXUS — ESP32-S3 Wearable Firmware
  Serial-safe diagnostic build with person-specific PPG calibration.

  IMPORTANT:
  - USB Serial (CDC) is initialized before any sensor/BLE code.
  - Startup progress is printed at every stage.
  - Sensor failures are non-fatal.
  - BLE advertising starts even when optional sensors are absent.
  - USB Serial remains available for PC bring-up and diagnostics.

  Current harness:
    I2C SDA = GPIO8
    I2C SCL = GPIO9
    DS18B20 DATA = GPIO6
    GSR = GPIO34
    Analog PPG = GPIO4
    Status LED = GPIO2
    VCC = 3V3
    GND = GND

  Note:
  GPIO40 -> GPIO4 is NOT assumed by the firmware. The analog PPG output
  must actually reach GPIO4 for ANALOG_PPG to change.
*/

#include <Arduino.h>
#include <Wire.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include "MAX30105.h"
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Adafruit_BME280.h>
#include <BH1750.h>
#include <math.h>
#include <Preferences.h>

static constexpr uint8_t SDA_PIN = 8;
static constexpr uint8_t SCL_PIN = 9;
static constexpr uint8_t ONE_WIRE_BUS = 6;
static constexpr uint8_t GSR_PIN = 34;
static constexpr uint8_t ANALOG_PPG_PIN = 4;
static constexpr uint8_t STATUS_LED_PIN = 2;

static constexpr uint32_t BAUD_RATE = 115200;
static constexpr uint32_t PPG_PERIOD_MS = 20;     // 50 Hz
static constexpr uint32_t IMU_PERIOD_MS = 20;     // 50 Hz
static constexpr uint32_t GSR_PERIOD_MS = 100;    // 10 Hz
static constexpr uint32_t TEMP_PERIOD_MS = 1000;  // 1 Hz
static constexpr uint32_t PACKET_PERIOD_MS = 50;  // 20 Hz
static constexpr uint32_t STATUS_PERIOD_MS = 2000;
static constexpr uint32_t ENV_PERIOD_MS = 1000; // 1 Hz

#define ST_PPG_ABSENT 0
#define ST_PPG_SAT    1
#define ST_MPU_ERR    2
#define ST_TEMP_ERR   3
#define ST_GSR_SAT    4
#define ST_I2C_ERR    5
#define ST_LOW_QUALITY 6
#define ST_BME_ERR    8
#define ST_BH1750_ERR 12

static const char* SERVICE_UUID = "7f300001-6c12-4f70-9e6b-8e9f7b8b1001";
static const char* DATA_UUID    = "7f300002-6c12-4f70-9e6b-8e9f7b8b1001";
static const char* CMD_UUID     = "7f300003-6c12-4f70-9e6b-8e9f7b8b1001";

MAX30105 ppg;
Adafruit_MPU6050 mpu;
OneWire ow(ONE_WIRE_BUS);
DallasTemperature tempSensor(&ow);
Adafruit_BME280 bme;
BH1750 lightMeter;

BLECharacteristic* dataChar = nullptr;
bool bleConnected = false;

bool ppgOK = false;
bool mpuOK = false;
bool tempOK = false;
bool analogPpgOK = false;
bool bmeOK = false;
bool lightOK = false;

uint16_t statusBase = 0;

uint32_t ir = 0;
uint32_t red = 0;
int gsr = 0;

float ax = 0.0f, ay = 0.0f, az = 1.0f;
float gx = 0.0f, gy = 0.0f, gz = 0.0f;
float temp0 = NAN;
float roomT = NAN;
float humidity = NAN;
float pressure = NAN;
float luxValue = -1.0f;

float axb = 0.0f, ayb = 0.0f, azb = 0.0f;
float gxb = 0.0f, gyb = 0.0f, gzb = 0.0f;

uint32_t lastPPG = 0;
uint32_t lastIMU = 0;
uint32_t lastGSR = 0;
uint32_t lastTEMP = 0;
uint32_t lastPACKET = 0;
uint32_t lastStatus = 0;
uint32_t lastENV = 0;

// Analog PPG calibration / signal-processing state.
float ppgBaseline = 0.0f;
float ppgFiltered = 0.0f;
float ppgAC = 0.0f;
float ppgNoise = 0.0f;
float ppgCalPeakToPeak = 0.0f;
float ppgWindowMin = 4095.0f;
float ppgWindowMax = 0.0f;
float ppgQuality = 0.0f;
float ppgBPM = 0.0f;
bool ppgCalibrated = false;
bool ppgFingerDetected = false;
bool ppgPeakArmed = false;
uint32_t ppgLastPeakMs = 0;
uint32_t ppgWindowStartMs = 0;
float ppgLastFiltered = 0.0f;

String commandBuffer;

// Personal PPG profile. The wearable stores only calibration parameters,
// not the raw PPG waveform. A new wearer can start a fresh calibration
// with PPG_NEW_PERSON (or PPG_CAL).
Preferences ppgPrefs;
String ppgProfileId = "default";
bool ppgProfileLoaded = false;

static void resetPPGProcessingState() {
  ppgFiltered = 0.0f;
  ppgAC = 0.0f;
  ppgWindowMin = 4095.0f;
  ppgWindowMax = 0.0f;
  ppgQuality = 0.0f;
  ppgBPM = 0.0f;
  ppgPeakArmed = false;
  ppgLastPeakMs = 0;
  ppgWindowStartMs = millis();
  ppgLastFiltered = 0.0f;
}

static int findPPGProfileSlot(const String& id, bool allocateIfMissing) {
  // Four lightweight calibration profiles. Only calibration parameters and
  // the short profile ID are stored; raw PPG samples are never stored here.
  for (int slot = 0; slot < 4; ++slot) {
    const String key = String("id") + slot;
    String stored = ppgPrefs.getString(key.c_str(), "");
    if (stored == id) return slot;
  }

  if (!allocateIfMissing) return -1;

  for (int slot = 0; slot < 4; ++slot) {
    const String key = String("id") + slot;
    if (ppgPrefs.getString(key.c_str(), "").length() == 0) return slot;
  }

  return -1;
}

static bool loadPPGProfile(const String& id) {
  if (!ppgPrefs.begin("endo_ppg", true)) {
    Serial.println("[PPG] Profile storage unavailable; using live calibration.");
    return false;
  }

  const int slot = findPPGProfileSlot(id, false);
  bool exists = false;

  if (slot >= 0) {
    const String okKey = String("ok") + slot;
    exists = ppgPrefs.getBool(okKey.c_str(), false);
    if (exists) {
      const String bKey = String("b") + slot;
      const String nKey = String("n") + slot;
      const String pKey = String("p") + slot;
      ppgBaseline = ppgPrefs.getFloat(bKey.c_str(), 0.0f);
      ppgNoise = ppgPrefs.getFloat(nKey.c_str(), 1.0f);
      ppgCalPeakToPeak = ppgPrefs.getFloat(pKey.c_str(), 0.0f);
      ppgCalibrated = ppgBaseline > 0.0f;
    }
  }

  ppgPrefs.end();

  if (exists && ppgCalibrated) {
    resetPPGProcessingState();
    Serial.print("[PPG] Loaded personal profile: ");
    Serial.print(id);
    Serial.print(" (slot ");
    Serial.print(slot);
    Serial.println(")");
    Serial.print("[PPG] Stored baseline ADC = ");
    Serial.println(ppgBaseline, 2);
    Serial.print("[PPG] Stored noise SD     = ");
    Serial.println(ppgNoise, 2);
    Serial.print("[PPG] Stored Cal P2P      = ");
    Serial.println(ppgCalPeakToPeak, 2);
    return true;
  }

  return false;
}

static void savePPGProfile(const String& id) {
  if (!ppgCalibrated) return;

  if (!ppgPrefs.begin("endo_ppg", false)) {
    Serial.println("[PPG] ERROR: could not open profile storage.");
    return;
  }

  const int slot = findPPGProfileSlot(id, true);
  if (slot < 0) {
    ppgPrefs.end();
    Serial.println("[PPG] ERROR: all 4 personal profile slots are full.");
    Serial.println("[PPG] Reuse an existing ID or clear NVS before adding another.");
    return;
  }

  const String idKey = String("id") + slot;
  const String okKey = String("ok") + slot;
  const String bKey = String("b") + slot;
  const String nKey = String("n") + slot;
  const String pKey = String("p") + slot;

  ppgPrefs.putString(idKey.c_str(), id);
  ppgPrefs.putBool(okKey.c_str(), true);
  ppgPrefs.putFloat(bKey.c_str(), ppgBaseline);
  ppgPrefs.putFloat(nKey.c_str(), ppgNoise);
  ppgPrefs.putFloat(pKey.c_str(), ppgCalPeakToPeak);
  ppgPrefs.end();

  Serial.print("[PPG] Personal calibration saved for profile: ");
  Serial.print(id);
  Serial.print(" (slot ");
  Serial.print(slot);
  Serial.println(")");
}

static void flushSerial() {
  Serial.flush();
  delay(10);
}

static void printStage(const char* stage) {
  Serial.print("[ENDO-TWIN] ");
  Serial.println(stage);
  flushSerial();
}

static uint8_t crc8(const char* text) {
  uint8_t c = 0;
  while (*text) {
    c ^= static_cast<uint8_t>(*text++);
  }
  return c;
}

static void setLed(bool on) {
  pinMode(STATUS_LED_PIN, OUTPUT);
  digitalWrite(STATUS_LED_PIN, on ? HIGH : LOW);
}

static void scanI2C() {
  Serial.println("[I2C] Scanning SDA=GPIO8 SCL=GPIO9...");
  uint8_t found = 0;

  for (uint8_t address = 1; address < 127; ++address) {
    Wire.beginTransmission(address);
    const uint8_t error = Wire.endTransmission();

    if (error == 0) {
      Serial.print("[I2C] FOUND 0x");
      if (address < 16) Serial.print('0');
      Serial.println(address, HEX);
      found++;
    }
  }

  Serial.print("[I2C] Devices found: ");
  Serial.println(found);
}

static bool setupAnalogPPG() {
  pinMode(ANALOG_PPG_PIN, INPUT);
  analogSetPinAttenuation(ANALOG_PPG_PIN, ADC_11db);

  const int sample = analogRead(ANALOG_PPG_PIN);
  analogPpgOK = (sample >= 0 && sample <= 4095);

  Serial.print("[SENSOR] Analog PPG GPIO");
  Serial.print(ANALOG_PPG_PIN);
  Serial.print(" initial=");
  Serial.println(sample);

  return analogPpgOK;
}

static void calibrateAnalogPPG(const String& profileId = "default") {
  if (!analogPpgOK) {
    Serial.println("[PPG] Calibration skipped: GPIO4 ADC unavailable");
    return;
  }

  Serial.println();
  Serial.println("[PPG] ANALOG PPG CALIBRATION");
  Serial.println("[PPG] Place one finger gently on the optical sensor.");
  Serial.println("[PPG] Keep the finger still for 5 seconds...");

  const uint32_t start = millis();
  uint32_t count = 0;
  double sum = 0.0;
  double sumSq = 0.0;
  float minValue = 4095.0f;
  float maxValue = 0.0f;

  while (millis() - start < 5000) {
    const int raw = analogRead(ANALOG_PPG_PIN);
    sum += raw;
    sumSq += static_cast<double>(raw) * raw;

    if (raw < minValue) minValue = raw;
    if (raw > maxValue) maxValue = raw;

    count++;
    delay(PPG_PERIOD_MS);
  }

  if (count == 0) {
    Serial.println("[PPG] Calibration FAILED: no samples");
    return;
  }

  const float mean = static_cast<float>(sum / count);
  const float variance = fmaxf(0.0f, static_cast<float>((sumSq / count) - (mean * mean)));
  const float stddev = sqrtf(variance);
  const float peakToPeak = maxValue - minValue;

  ppgBaseline = mean;
  ppgNoise = stddev;
  ppgCalPeakToPeak = peakToPeak;
  ppgFiltered = 0.0f;
  ppgAC = 0.0f;
  ppgWindowMin = mean;
  ppgWindowMax = mean;
  ppgWindowStartMs = millis();
  ppgCalibrated = true;
  ppgProfileId = profileId;
  resetPPGProcessingState();

  Serial.print("[PPG] Personal profile = ");
  Serial.println(profileId);
  Serial.print("[PPG] Baseline ADC = ");
  Serial.println(ppgBaseline, 2);
  Serial.print("[PPG] Noise SD     = ");
  Serial.println(ppgNoise, 2);
  Serial.print("[PPG] Cal P2P      = ");
  Serial.println(ppgCalPeakToPeak, 2);

  if (ppgCalPeakToPeak < 8.0f) {
    Serial.println("[PPG] WARNING: almost no optical waveform detected.");
    Serial.println("[PPG] Check finger contact, sensor LED, VCC, GND and GPIO4.");
  } else {
    Serial.println("[PPG] Calibration accepted.");
  }

  savePPGProfile(profileId);

  // Machine-readable event consumed by the project backend/UI.
  const calQuality = fminf(100.0f, (ppgCalPeakToPeak / fmaxf(1.0f, ppgNoise)) * 20.0f);
  Serial.print("$PCAL,");
  Serial.print(profileId);
  Serial.print(",");
  Serial.print(ppgBaseline, 3);
  Serial.print(",");
  Serial.print(ppgNoise, 3);
  Serial.print(",");
  Serial.print(ppgCalPeakToPeak, 3);
  Serial.print(",");
  Serial.print(calQuality, 1);
  Serial.print(",");
  Serial.println(static_cast<unsigned long>(millis()));
}

static void updateAnalogPPG() {
  const float raw = static_cast<float>(analogRead(ANALOG_PPG_PIN));
  ir = static_cast<uint32_t>(raw);
  red = 0;

  if (ppgBaseline <= 0.0f) ppgBaseline = raw;
  ppgBaseline += 0.01f * (raw - ppgBaseline);

  ppgAC = raw - ppgBaseline;
  ppgFiltered += 0.20f * (ppgAC - ppgFiltered);

  if (raw < ppgWindowMin) ppgWindowMin = raw;
  if (raw > ppgWindowMax) ppgWindowMax = raw;

  const float dynamicThreshold = max(8.0f, ppgNoise * 3.0f);
  ppgFingerDetected = fabsf(ppgFiltered) > dynamicThreshold;

  const uint32_t now = millis();
  const bool risingThenFalling =
    (ppgLastFiltered > 0.0f) &&
    (ppgFiltered < ppgLastFiltered) &&
    (ppgLastFiltered > max(8.0f, ppgNoise * 3.0f));

  if (risingThenFalling && (now - ppgLastPeakMs >= 300)) {
    if (ppgLastPeakMs != 0) {
      const uint32_t ibi = now - ppgLastPeakMs;
      if (ibi >= 300 && ibi <= 2000) {
        const float instantBPM = 60000.0f / ibi;
        if (ppgBPM <= 0.0f) ppgBPM = instantBPM;
        else ppgBPM = 0.75f * ppgBPM + 0.25f * instantBPM;
      }
    }
    ppgLastPeakMs = now;
    ppgPeakArmed = true;
  }

  ppgLastFiltered = ppgFiltered;

  if (now - ppgWindowStartMs >= 1000) {
    const float p2p = ppgWindowMax - ppgWindowMin;
    const float referenceNoise = max(1.0f, ppgNoise);
    const float snrLike = p2p / referenceNoise;

    float q = 0.0f;
    if (p2p >= 8.0f) q += 20.0f;
    if (p2p >= 20.0f) q += 20.0f;
    if (p2p >= 50.0f) q += 20.0f;
    if (snrLike >= 3.0f) q += 20.0f;
    if (ppgBPM >= 40.0f && ppgBPM <= 180.0f) q += 20.0f;

    ppgQuality = min(100.0f, q);
    ppgWindowMin = raw;
    ppgWindowMax = raw;
    ppgWindowStartMs = now;

    if (ppgLastPeakMs == 0 || now - ppgLastPeakMs > 5000) {
      ppgBPM = 0.0f;
    }
  }
}

static void setupSensors() {
  printStage("Sensor initialization: MAX3010x");
  if (ppg.begin(Wire, I2C_SPEED_FAST)) {
    ppgOK = true;
    ppg.setup(0x24, 4, 2, 100, 411, 4096);
    ppg.setPulseAmplitudeRed(0x24);
    ppg.setPulseAmplitudeIR(0x24);
    ppg.setPulseAmplitudeGreen(0);
    Serial.println("[SENSOR] MAX3010x: OK");
  } else {
    statusBase |= (1u << ST_I2C_ERR);
    Serial.println("[SENSOR] MAX3010x: NOT FOUND (non-fatal)");
  }

  printStage("Sensor initialization: analog PPG");
  setupAnalogPPG();

  printStage("Sensor initialization: MPU6050");
  if (mpu.begin()) {
    mpuOK = true;
    mpu.setAccelerometerRange(MPU6050_RANGE_4_G);
    mpu.setGyroRange(MPU6050_RANGE_500_DEG);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
    Serial.println("[SENSOR] MPU6050: OK");
  } else {
    statusBase |= (1u << ST_MPU_ERR);
    Serial.println("[SENSOR] MPU6050: NOT FOUND (non-fatal)");
  }

  printStage("Sensor initialization: DS18B20");
  tempSensor.begin();
  const uint8_t deviceCount = tempSensor.getDeviceCount();

  if (deviceCount > 0) {
    tempOK = true;
    Serial.print("[SENSOR] DS18B20: OK devices=");
    Serial.println(deviceCount);
  } else {
    statusBase |= (1u << ST_TEMP_ERR);
    Serial.println("[SENSOR] DS18B20: NOT FOUND (non-fatal)");
  }

  printStage("Sensor initialization: BH1750");
  lightOK = lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE, 0x23, &Wire);
  if (lightOK) {
    Serial.println("[SENSOR] BH1750 @ 0x23: OK");
  } else {
    // Some BH1750 boards use the alternate address 0x5C.
    lightOK = lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE, 0x5C, &Wire);
    if (lightOK) {
      Serial.println("[SENSOR] BH1750 @ 0x5C: OK");
    } else {
      statusBase |= (1u << ST_BH1750_ERR);
      Serial.println("[SENSOR] BH1750: NOT FOUND (non-fatal)");
    }
  }

  printStage("Sensor initialization: BME280");
  bmeOK = bme.begin(0x76, &Wire);
  if (!bmeOK) {
    bmeOK = bme.begin(0x77, &Wire);
  }

  if (bmeOK) {
    Serial.println("[SENSOR] BME280: OK");
  } else {
    statusBase |= (1u << ST_BME_ERR);
    Serial.println("[SENSOR] BME280: NOT FOUND (non-fatal)");
  }

  printStage("Sensor initialization complete");
}

static void calibrateIMU() {
  if (!mpuOK) {
    Serial.println("[IMU] Calibration skipped: MPU6050 unavailable");
    return;
  }

  Serial.println("[IMU] Keep wearable still: calibrating for ~1.3 s");

  const int N = 160;
  float sx = 0.0f, sy = 0.0f, sz = 0.0f;
  float sgx = 0.0f, sgy = 0.0f, sgz = 0.0f;

  for (int i = 0; i < N; ++i) {
    sensors_event_t a, g, t;
    mpu.getEvent(&a, &g, &t);

    sx += a.acceleration.x / 9.80665f;
    sy += a.acceleration.y / 9.80665f;
    sz += a.acceleration.z / 9.80665f;

    sgx += g.gyro.x * 57.29578f;
    sgy += g.gyro.y * 57.29578f;
    sgz += g.gyro.z * 57.29578f;

    delay(8);
  }

  axb = sx / N;
  ayb = sy / N;
  azb = (sz / N) - 1.0f;
  gxb = sgx / N;
  gyb = sgy / N;
  gzb = sgz / N;

  Serial.println("[IMU] Calibration complete");
}

static uint16_t getStatus() {
  uint16_t s = statusBase;

  const uint32_t ppgValue = ir;
  if (ppgOK && ppgValue < 5) {
    s |= (1u << ST_PPG_ABSENT);
  }

  if (analogPpgOK && ppgCalibrated && ppgQuality < 20.0f) {
    s |= (1u << ST_LOW_QUALITY);
  }

  if (ppgOK && (ir > 250000UL || red > 250000UL)) {
    s |= (1u << ST_PPG_SAT);
  }

  if (tempOK && !(temp0 > -20.0f && temp0 < 80.0f)) {
    s |= (1u << ST_TEMP_ERR);
  }

  if (gsr < 5 || gsr > 4090) {
    s |= (1u << ST_GSR_SAT);
  }

  return s;
}

static String makePacket() {
  char ft0[16], ft1[16], frt[16], fhum[16], fpress[16], flux[16];

  if (isnan(temp0)) snprintf(ft0, sizeof(ft0), "nan");
  else snprintf(ft0, sizeof(ft0), "%.2f", temp0);

  // ESP32-S3 wearable currently has one DS18B20.
  snprintf(ft1, sizeof(ft1), "nan");

  if (isnan(roomT)) snprintf(frt, sizeof(frt), "nan");
  else snprintf(frt, sizeof(frt), "%.2f", roomT);

  if (isnan(humidity)) snprintf(fhum, sizeof(fhum), "nan");
  else snprintf(fhum, sizeof(fhum), "%.1f", humidity);

  if (isnan(pressure)) snprintf(fpress, sizeof(fpress), "nan");
  else snprintf(fpress, sizeof(fpress), "%.1f", pressure);

  snprintf(flux, sizeof(flux), "%.1f", luxValue);

  // Keep CP2 compatible with the project's extended Mega firmware.
  // Unsupported wearable channels are explicit placeholders.
  char payload[360];
  const uint16_t s = getStatus();

  snprintf(
    payload,
    sizeof(payload),
    "$CP2,%lu,%lu,%lu,%.4f,%.4f,%.4f,%.3f,%.3f,%.3f,%s,%s,%d,0,0.00,0.0,-1,-1,%s,%s,%s,%s,0,%u",
    static_cast<unsigned long>(millis()),
    static_cast<unsigned long>(ir),
    static_cast<unsigned long>(red),
    ax, ay, az,
    gx, gy, gz,
    ft0, ft1,
    gsr,
    flux, frt, fhum, fpress,
    s
  );

  const uint8_t c = crc8(payload);

  char out[390];
  snprintf(out, sizeof(out), "%s,%02X", payload, c);
  return String(out);
}

static void publishPacket() {
  const String packet = makePacket();

  Serial.println(packet);

  if (bleConnected && dataChar != nullptr) {
    dataChar->setValue(packet.c_str());
    dataChar->notify();
  }
}

static void handleCommand(String c) {
  c.trim();

  if (c.length() == 0) {
    return;
  }

  Serial.print("[CMD] ");
  Serial.println(c);

  if (c == "PING") {
    Serial.println("$ACK,PONG,00");
  } else if (c == "WHOAMI") {
    Serial.println("ENDO-TWIN-ESP32-S3-WEARABLE");
  } else if (c == "STATUS") {
    Serial.print("STATUS=");
    Serial.println(getStatus());
  } else if (c == "PPG_CAL" || c == "PPG_NEW_PERSON") {
    Serial.print("[PPG] Starting new-person calibration for profile: ");
    Serial.println(ppgProfileId);
    calibrateAnalogPPG(ppgProfileId);
  } else if (c.startsWith("PPG_PERSON=")) {
    String id = c.substring(10);
    id.trim();
    if (id.length() == 0) {
      Serial.println("[PPG] Profile ID cannot be empty.");
    } else {
      // Keep the key short/safe for ESP32 Preferences.
      if (id.length() > 12) id = id.substring(0, 12);
      ppgProfileId = id;
      ppgCalibrated = false;
      Serial.print("[PPG] Active person profile = ");
      Serial.println(ppgProfileId);
      if (!loadPPGProfile(ppgProfileId)) {
        Serial.println("[PPG] No saved calibration for this person.");
        Serial.println("[PPG] Send PPG_NEW_PERSON to calibrate this wearer.");
      }
    }
  } else if (c == "PPG_PROFILE") {
    Serial.print("[PPG] Active profile: ");
    Serial.println(ppgProfileId);
    Serial.print("[PPG] Calibrated: ");
    Serial.println(ppgCalibrated ? "YES" : "NO");
  } else {
    Serial.println("$ACK,UNKNOWN_CMD,00");
  }
}

class ServerCB : public BLEServerCallbacks {
  void onConnect(BLEServer*) override {
    bleConnected = true;
    Serial.println("[BLE] Client connected");
  }

  void onDisconnect(BLEServer*) override {
    bleConnected = false;
    Serial.println("[BLE] Client disconnected");
    BLEDevice::startAdvertising();
    Serial.println("[BLE] Advertising restarted");
  }
};

class CmdCB : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic* ch) override {
    String value = ch->getValue();
    if (value.length() > 0) {
      handleCommand(value);
    }
  }
};

static void setupBLE() {
  printStage("Starting BLE");

  BLEDevice::init("ENDO-TWIN-ESP32-S3");

  BLEServer* server = BLEDevice::createServer();
  server->setCallbacks(new ServerCB());

  BLEService* service = server->createService(SERVICE_UUID);

  dataChar = service->createCharacteristic(
    DATA_UUID,
    BLECharacteristic::PROPERTY_NOTIFY
  );
  dataChar->addDescriptor(new BLE2902());

  BLECharacteristic* cmd = service->createCharacteristic(
    CMD_UUID,
    BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_WRITE_NR
  );
  cmd->setCallbacks(new CmdCB());

  service->start();

  BLEAdvertising* advertising = BLEDevice::getAdvertising();
  advertising->addServiceUUID(SERVICE_UUID);
  advertising->setScanResponse(true);
  advertising->setMinPreferred(0x06);
  advertising->setMinPreferred(0x12);

  BLEDevice::startAdvertising();

  Serial.println("[BLE] Advertising as ENDO-TWIN-ESP32-S3");
}

static void printBanner() {
  Serial.println();
  Serial.println("==============================================");
  Serial.println(" ENDO-TWIN NEXUS — ESP32-S3 WEARABLE");
  Serial.println(" Diagnostic + Sensor + BLE Firmware");
  Serial.println("==============================================");
  Serial.println("USB SERIAL : 115200");
  Serial.println("I2C        : SDA=GPIO8 SCL=GPIO9");
  Serial.println("TEMP       : GPIO6");
  Serial.println("GSR        : GPIO34");
  Serial.println("ANALOG PPG : GPIO4");
  Serial.println("LED        : GPIO2");
  Serial.println("==============================================");
}

void setup() {
  Serial.begin(BAUD_RATE);
  delay(1200);

  setLed(false);
  printBanner();

  printStage("USB serial ready");
  Serial.println("[BOOT] If you can read this, ESP32-S3 USB serial is working.");
  Serial.println("[BOOT] Serial Monitor must be set to 115200 baud.");
  flushSerial();

  printStage("Starting I2C");
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(400000);
  scanI2C();

  printStage("Starting ADC");
  analogReadResolution(12);
  analogSetPinAttenuation(GSR_PIN, ADC_11db);
  pinMode(GSR_PIN, INPUT);
  pinMode(ANALOG_PPG_PIN, INPUT);
  analogSetPinAttenuation(ANALOG_PPG_PIN, ADC_11db);

  setupSensors();
  calibrateIMU();

  if (analogPpgOK && !ppgOK) {
    if (!loadPPGProfile(ppgProfileId)) {
      Serial.println("[PPG] No saved personal profile found.");
      calibrateAnalogPPG(ppgProfileId);
    } else {
      Serial.println("[PPG] Using saved personal calibration.");
      Serial.println("[PPG] For another wearer: send PPG_PERSON=<ID>, then PPG_NEW_PERSON.");
    }
  }

  setupBLE();

  setLed(true);

  Serial.println();
  Serial.println("[READY] ENDO-TWIN-WEARABLE READY");
  Serial.println("[READY] USB Serial + BLE active");
  Serial.println("[READY] Streaming $CP2 packets every 50 ms");
  Serial.println("[READY] PPG diagnostics are printed every 2 seconds.");
  Serial.println("[READY] Personal calibration: PPG_PERSON=<ID> then PPG_NEW_PERSON");
  Serial.println("[READY] Reuse current profile: PPG_CAL");
  Serial.println();

  flushSerial();
}

void loop() {
  const uint32_t now = millis();

  if (now - lastPPG >= PPG_PERIOD_MS) {
    lastPPG = now;

    if (ppgOK) {
      ir = ppg.getIR();
      red = ppg.getRed();
    } else if (analogPpgOK) {
      updateAnalogPPG();
    } else {
      ir = 0;
      red = 0;
    }
  }

  if (now - lastIMU >= IMU_PERIOD_MS) {
    lastIMU = now;

    if (mpuOK) {
      sensors_event_t a, g, t;
      mpu.getEvent(&a, &g, &t);

      ax = a.acceleration.x / 9.80665f - axb;
      ay = a.acceleration.y / 9.80665f - ayb;
      az = a.acceleration.z / 9.80665f - azb;

      gx = g.gyro.x * 57.29578f - gxb;
      gy = g.gyro.y * 57.29578f - gyb;
      gz = g.gyro.z * 57.29578f - gzb;
    }
  }

  if (now - lastGSR >= GSR_PERIOD_MS) {
    lastGSR = now;
    gsr = analogRead(GSR_PIN);
  }

  if (now - lastENV >= ENV_PERIOD_MS) {
    lastENV = now;

    if (lightOK) {
      luxValue = lightMeter.readLightLevel();
    }

    if (bmeOK) {
      roomT = bme.readTemperature();
      humidity = bme.readHumidity();
      pressure = bme.readPressure() / 100.0f;
    }
  }

  if (now - lastTEMP >= TEMP_PERIOD_MS) {
    lastTEMP = now;

    if (tempOK) {
      tempSensor.requestTemperatures();
      temp0 = tempSensor.getTempCByIndex(0);
    }
  }

  if (now - lastPACKET >= PACKET_PERIOD_MS) {
    lastPACKET = now;
    publishPacket();
  }

  if (now - lastStatus >= STATUS_PERIOD_MS) {
    lastStatus = now;

    Serial.print("[STATUS] PPG=");
    Serial.print(ppgOK ? "MAX3010x" : (analogPpgOK ? "ANALOG" : "NONE"));
    Serial.print(" MPU=");
    Serial.print(mpuOK ? "OK" : "ERR");
    Serial.print(" TEMP=");
    Serial.print(tempOK ? "OK" : "ERR");
    Serial.print(" BME=");
    Serial.print(bmeOK ? "OK" : "ERR");
    Serial.print(" BH1750=");
    Serial.print(lightOK ? "OK" : "ERR");
    Serial.print(" ENV[T=");
    Serial.print(roomT, 1);
    Serial.print("C H=");
    Serial.print(humidity, 1);
    Serial.print("% P=");
    Serial.print(pressure, 1);
    Serial.print("hPa L=");
    Serial.print(luxValue, 1);
    Serial.print("lx] GSR=");
    Serial.print(gsr);
    Serial.print(" BLE=");
    Serial.print(bleConnected ? "CONNECTED" : "ADVERTISING");
    Serial.print(" PPG_PROFILE=");
    Serial.print(ppgProfileId);
    Serial.print(" PPG_RAW=");
    Serial.print(ir);
    Serial.print(" PPG_BASE=");
    Serial.print(ppgBaseline, 1);
    Serial.print(" PPG_Q=");
    Serial.print(ppgQuality, 0);
    Serial.print("% PPG_BPM=");
    Serial.print(ppgBPM, 1);
    Serial.print(" STATUS=");
    Serial.println(getStatus());
  }

  while (Serial.available() > 0) {
    const char c = static_cast<char>(Serial.read());

    if (c == '\n' || c == '\r') {
      if (commandBuffer.length() > 0) {
        handleCommand(commandBuffer);
      }
      commandBuffer = "";
    } else if (commandBuffer.length() < 64) {
      commandBuffer += c;
    }
  }

  delay(1);
}