/*
  ENDO-TWIN NEXUS V9.0 — ESP32-S3 PRIMARY ANALOG WEARABLE
  ---------------------------------------------------------
  Primary desktop wearable acquisition node.

  Pin map (keep synchronized with the workstation):
    I2C SDA -> GPIO21
    I2C SCL -> GPIO22
    Analog Pulse Sensor -> GPIO4 (12-bit ADC)
    GSR analog -> GPIO34 (12-bit ADC)
    Status LED -> GPIO2

  Optional I2C sensors:
    MPU6050 @ 0x68/0x69
    BME280  @ 0x76/0x77
    BH1750  @ 0x23/0x5C

  Transport:
    USB Serial 115200
    Wi-Fi SoftAP: ENDO-TWIN-S3 / endotwins3
    TCP port 7777

  CP3 frame:
    $CP3,ms,ppg_raw,gsr_raw,ax,ay,az,gx,gy,gz,roomT,hum,press,lux,status,crc

  Raw values are deliberately preserved on the wire. The desktop workstation
  applies robust automatic calibration before physiological feature extraction.
  This firmware is an educational/research acquisition device, not a medical
  device.
*/

#include <Wire.h>
#include <WiFi.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <BH1750.h>
#include <Adafruit_BME280.h>
#include <math.h>

#define I2C_SDA_PIN 21
#define I2C_SCL_PIN 22
#define ANALOG_PPG_PIN 4
#define GSR_PIN 34
#define STATUS_LED_PIN 2

#define BAUD_RATE 115200
#define TCP_PORT 7777
#define PPG_PERIOD_MS 50
#define IMU_PERIOD_MS 20
#define GSR_PERIOD_MS 50
#define ENV_PERIOD_MS 500
#define PACKET_PERIOD_MS 50

static const char* AP_NAME = "ENDO-TWIN-S3";
static const char* AP_PASSWORD = "endotwins3";

enum StatusBit : uint16_t {
  ST_PPG_LOW = 0,
  ST_PPG_SAT = 1,
  ST_MPU_ERR = 2,
  ST_GSR_SAT = 4,
  ST_I2C_ERR = 5,
  ST_LOW_QUALITY = 6,
  ST_BME_ERR = 8,
  ST_LIGHT_ERR = 9,
};

Adafruit_MPU6050 mpu;
BH1750 lightMeter;
Adafruit_BME280 bme;
WiFiServer server(TCP_PORT);
WiFiClient tcpClient;

bool mpuOK = false;
bool bmeOK = false;
bool lightOK = false;
uint16_t statusBase = 0;

uint16_t ppgRaw = 0;
uint16_t gsrRaw = 0;

float ax_g = 0.0f, ay_g = 0.0f, az_g = 1.0f;
float gx_dps = 0.0f, gy_dps = 0.0f, gz_dps = 0.0f;
float axBias = 0.0f, ayBias = 0.0f, azBiasError = 0.0f;
float gxBias = 0.0f, gyBias = 0.0f, gzBias = 0.0f;

float luxValue = NAN;
float roomTemp = NAN;
float humidity = NAN;
float pressure = NAN;

unsigned long lastPPG = 0;
unsigned long lastIMU = 0;
unsigned long lastGSR = 0;
unsigned long lastEnv = 0;
unsigned long lastPacket = 0;

char cmdBuf[64];
uint8_t cmdIdx = 0;

uint8_t xorCRC(const char* text) {
  uint8_t c = 0;
  while (*text) c ^= (uint8_t)(*text++);
  return c;
}

void setLed(bool on) {
  digitalWrite(STATUS_LED_PIN, on ? HIGH : LOW);
}

uint16_t readADCMedian(uint8_t pin) {
  uint16_t v[5];
  for (int i = 0; i < 5; ++i) v[i] = (uint16_t)analogRead(pin);
  for (int i = 1; i < 5; ++i) {
    uint16_t key = v[i];
    int j = i - 1;
    while (j >= 0 && v[j] > key) {
      v[j + 1] = v[j];
      --j;
    }
    v[j + 1] = key;
  }
  return v[2];
}

void setupMPU() {
  if (!mpu.begin(0x68, &Wire)) {
    if (!mpu.begin(0x69, &Wire)) {
      statusBase |= (1 << ST_MPU_ERR);
      return;
    }
  }
  mpuOK = true;
  mpu.setAccelerometerRange(MPU6050_RANGE_4_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
}

void setupEnvironment() {
  lightOK = lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE, 0x23, &Wire);
  if (!lightOK) lightOK = lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE, 0x5C, &Wire);
  if (!lightOK) statusBase |= (1 << ST_LIGHT_ERR);

  bmeOK = bme.begin(0x76, &Wire);
  if (!bmeOK) bmeOK = bme.begin(0x77, &Wire);
  if (!bmeOK) statusBase |= (1 << ST_BME_ERR);
}

void calibrateIMU() {
  if (!mpuOK) return;
  const int N = 120;
  float sax=0, say=0, saz=0, sgx=0, sgy=0, sgz=0;

  for (int i = 0; i < N; ++i) {
    sensors_event_t a, g, t;
    mpu.getEvent(&a, &g, &t);
    sax += a.acceleration.x / 9.80665f;
    say += a.acceleration.y / 9.80665f;
    saz += a.acceleration.z / 9.80665f;
    sgx += g.gyro.x * 57.29578f;
    sgy += g.gyro.y * 57.29578f;
    sgz += g.gyro.z * 57.29578f;
    delay(5);
  }

  axBias = sax / N;
  ayBias = say / N;
  const float zMean = saz / N;
  const float zSign = (zMean >= 0.0f) ? 1.0f : -1.0f;
  azBiasError = zMean - zSign;
  gxBias = sgx / N;
  gyBias = sgy / N;
  gzBias = sgz / N;
}

void readIMU() {
  if (!mpuOK) return;
  sensors_event_t a, g, t;
  mpu.getEvent(&a, &g, &t);
  ax_g = a.acceleration.x / 9.80665f - axBias;
  ay_g = a.acceleration.y / 9.80665f - ayBias;
  az_g = a.acceleration.z / 9.80665f - azBiasError;
  gx_dps = g.gyro.x * 57.29578f - gxBias;
  gy_dps = g.gyro.y * 57.29578f - gyBias;
  gz_dps = g.gyro.z * 57.29578f - gzBias;
}

void readEnvironment() {
  if (lightOK) {
    float v = lightMeter.readLightLevel();
    if (isfinite(v) && v >= 0.0f) luxValue = v;
  }
  if (bmeOK) {
    float t = bme.readTemperature();
    float h = bme.readHumidity();
    float p = bme.readPressure() / 100.0f;
    if (isfinite(t)) roomTemp = t;
    if (isfinite(h)) humidity = h;
    if (isfinite(p)) pressure = p;
  }
}

uint16_t makeStatus() {
  uint16_t st = statusBase;
  if (ppgRaw < 30) st |= (1 << ST_PPG_LOW);
  if (ppgRaw > 4060) st |= (1 << ST_PPG_SAT);
  if (gsrRaw < 5 || gsrRaw > 4090) st |= (1 << ST_GSR_SAT);
  return st;
}

void sendPacket() {
  char ax[16], ay[16], az[16], gx[16], gy[16], gz[16];
  char rt[16], hu[16], pr[16], lx[16];

  dtostrf(ax_g, 1, 4, ax);
  dtostrf(ay_g, 1, 4, ay);
  dtostrf(az_g, 1, 4, az);
  dtostrf(gx_dps, 1, 3, gx);
  dtostrf(gy_dps, 1, 3, gy);
  dtostrf(gz_dps, 1, 3, gz);
  dtostrf(roomTemp, 1, 2, rt);
  dtostrf(humidity, 1, 1, hu);
  dtostrf(pressure, 1, 1, pr);
  dtostrf(luxValue, 1, 1, lx);

  char payload[280];
  const uint16_t status = makeStatus();

  snprintf(payload, sizeof(payload),
    "$CP3,%lu,%u,%u,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%u",
    millis(),
    (unsigned int)ppgRaw,
    (unsigned int)gsrRaw,
    ax, ay, az, gx, gy, gz,
    rt, hu, pr, lx, (unsigned int)status
  );

  char line[320];
  const uint8_t crc = xorCRC(payload);
  snprintf(line, sizeof(line), "%s,%02X\n", payload, crc);

  Serial.print(line);
  if (tcpClient && tcpClient.connected()) tcpClient.print(line);
}

void sendAck(const char* line) {
  Serial.println(line);
  if (tcpClient && tcpClient.connected()) tcpClient.println(line);
}

void handleCommand(const char* cmd) {
  if (!strcmp(cmd, "PING")) {
    sendAck("$ACK,PONG,00");
  } else if (!strcmp(cmd, "WHOAMI")) {
    sendAck("$ACK,WHOAMI,ENDO-TWIN-ESP32S3-ANALOG");
  } else if (!strcmp(cmd, "CALIBRATE")) {
    calibrateIMU();
    sendAck("$ACK,CALIBRATE,IMU-RESET");
  } else if (!strcmp(cmd, "LED,G")) {
    setLed(true);
  } else if (!strcmp(cmd, "LED,Y")) {
    setLed(false);
  } else if (!strcmp(cmd, "LED,R")) {
    setLed(true);
  }
}

void readCommands(Stream& stream) {
  while (stream.available()) {
    char c = (char)stream.read();
    if (c == '\n' || c == '\r') {
      if (cmdIdx) {
        cmdBuf[cmdIdx] = 0;
        handleCommand(cmdBuf);
        cmdIdx = 0;
      }
    } else if (cmdIdx < sizeof(cmdBuf) - 1) {
      cmdBuf[cmdIdx++] = c;
    }
  }
}

void setupWiFi() {
  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_NAME, AP_PASSWORD);
  delay(100);
  Serial.print("ESP32-S3 AP IP: ");
  Serial.println(WiFi.softAPIP());
  server.begin();
  server.setNoDelay(true);
  Serial.printf("TCP server listening on %d\n", TCP_PORT);
}

void setup() {
  pinMode(STATUS_LED_PIN, OUTPUT);
  setLed(false);

  Serial.begin(BAUD_RATE);
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  Wire.setClock(400000L);

  analogReadResolution(12);
  analogSetPinAttenuation(ANALOG_PPG_PIN, ADC_11db);
  analogSetPinAttenuation(GSR_PIN, ADC_11db);
  pinMode(ANALOG_PPG_PIN, INPUT);
  pinMode(GSR_PIN, INPUT);

  delay(300);
  setupMPU();
  setupEnvironment();
  calibrateIMU();
  readEnvironment();

  setupWiFi();
  setLed(true);
}

void loop() {
  const unsigned long now = millis();

  WiFiClient incoming = server.available();
  if (incoming) {
    if (tcpClient && tcpClient.connected()) tcpClient.stop();
    tcpClient = incoming;
    tcpClient.setNoDelay(true);
    tcpClient.println("$ACK,CONNECTED,ENDO-TWIN-ESP32S3-ANALOG");
  }

  if (now - lastPPG >= PPG_PERIOD_MS) {
    lastPPG = now;
    ppgRaw = readADCMedian(ANALOG_PPG_PIN);
  }

  if (now - lastGSR >= GSR_PERIOD_MS) {
    lastGSR = now;
    gsrRaw = readADCMedian(GSR_PIN);
  }

  if (now - lastIMU >= IMU_PERIOD_MS) {
    lastIMU = now;
    readIMU();
  }

  if (now - lastEnv >= ENV_PERIOD_MS) {
    lastEnv = now;
    readEnvironment();
  }

  if (now - lastPacket >= PACKET_PERIOD_MS) {
    lastPacket = now;
    sendPacket();
  }

  readCommands(Serial);

  if (tcpClient && tcpClient.connected()) {
    readCommands(tcpClient);
  } else if (tcpClient) {
    tcpClient.stop();
  }
}
