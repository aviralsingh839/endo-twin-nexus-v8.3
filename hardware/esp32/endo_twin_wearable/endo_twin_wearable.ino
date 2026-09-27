/*
  ENDO-TWIN NEXUS — ESP32-S3 Wearable Firmware
  Serial-safe diagnostic build.

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
#include <math.h>

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

#define ST_PPG_ABSENT 0
#define ST_PPG_SAT    1
#define ST_MPU_ERR    2
#define ST_TEMP_ERR   3
#define ST_GSR_SAT    4
#define ST_I2C_ERR    5

static const char* SERVICE_UUID = "7f300001-6c12-4f70-9e6b-8e9f7b8b1001";
static const char* DATA_UUID    = "7f300002-6c12-4f70-9e6b-8e9f7b8b1001";
static const char* CMD_UUID     = "7f300003-6c12-4f70-9e6b-8e9f7b8b1001";

MAX30105 ppg;
Adafruit_MPU6050 mpu;
OneWire ow(ONE_WIRE_BUS);
DallasTemperature tempSensor(&ow);

BLECharacteristic* dataChar = nullptr;
bool bleConnected = false;

bool ppgOK = false;
bool mpuOK = false;
bool tempOK = false;
bool analogPpgOK = false;

uint16_t statusBase = 0;

uint32_t ir = 0;
uint32_t red = 0;
int gsr = 0;

float ax = 0.0f, ay = 0.0f, az = 1.0f;
float gx = 0.0f, gy = 0.0f, gz = 0.0f;
float temp0 = NAN;

float axb = 0.0f, ayb = 0.0f, azb = 0.0f;
float gxb = 0.0f, gyb = 0.0f, gzb = 0.0f;

uint32_t lastPPG = 0;
uint32_t lastIMU = 0;
uint32_t lastGSR = 0;
uint32_t lastTEMP = 0;
uint32_t lastPACKET = 0;
uint32_t lastStatus = 0;

String commandBuffer;

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
  digitalWrite(STATUS_LED_PIN, on ? HIGH : LOW);
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

  const uint32_t ppgValue = ppgOK ? ir : ir;
  if ((ppgOK || analogPpgOK) && ppgValue < 5) {
    s |= (1u << ST_PPG_ABSENT);
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
  char t[20];

  if (isnan(temp0)) {
    snprintf(t, sizeof(t), "nan");
  } else {
    snprintf(t, sizeof(t), "%.2f", temp0);
  }

  char payload[260];
  const uint16_t s = getStatus();

  snprintf(
    payload,
    sizeof(payload),
    "$CP2,%lu,%lu,%lu,%.4f,%.4f,%.4f,%.3f,%.3f,%.3f,%s,nan,%d,0,0.00,0.0,-1,-1,-1,nan,nan,nan,0,%u",
    static_cast<unsigned long>(millis()),
    static_cast<unsigned long>(ir),
    static_cast<unsigned long>(red),
    ax, ay, az,
    gx, gy, gz,
    t,
    gsr,
    s
  );

  const uint8_t c = crc8(payload);

  char out[290];
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
  // FIRST: initialize USB CDC serial before touching sensors/BLE.
  Serial.begin(BAUD_RATE);

  // Give native USB CDC time to enumerate on the host.
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

  printStage("Starting ADC");
  analogReadResolution(12);
  analogSetPinAttenuation(GSR_PIN, ADC_11db);
  pinMode(GSR_PIN, INPUT);
  pinMode(ANALOG_PPG_PIN, INPUT);
  analogSetPinAttenuation(ANALOG_PPG_PIN, ADC_11db);

  setupSensors();

  // Do not block startup because of IMU calibration.
  calibrateIMU();

  setupBLE();

  setLed(true);

  Serial.println();
  Serial.println("[READY] ENDO-TWIN-WEARABLE READY");
  Serial.println("[READY] USB Serial + BLE active");
  Serial.println("[READY] Streaming $CP2 packets every 50 ms");
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
      ir = static_cast<uint32_t>(analogRead(ANALOG_PPG_PIN));
      red = 0;
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
    Serial.print(" GSR=");
    Serial.print(gsr);
    Serial.print(" BLE=");
    Serial.print(bleConnected ? "CONNECTED" : "ADVERTISING");
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
