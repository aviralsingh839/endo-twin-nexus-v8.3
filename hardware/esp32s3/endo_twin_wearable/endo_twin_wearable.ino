/*
  ENDO-TWIN NEXUS — ESP32-S3 PRIMARY WEARABLE
  ------------------------------------------------
  Active wearable controller for the ESP32-S3-DevKitC-1.
  Arduino Mega 2560 remains the separate bench/lab controller.

  Target: ESP32-S3-DevKitC-1 (Arduino FQBN: esp32:esp32:esp32s3)
  USB Serial: 115200 baud
  Wi-Fi SoftAP: ENDO-TWIN-S3 / endotwins3
  TCP: 7777

  I2C bus:
    SDA GPIO8
    SCL GPIO9
    MAX30102 0x57
    MPU6050  0x68/0x69
    BME280   0x76/0x77
    BH1750   0x23/0x5C

  Skin temperature:
    DS18B20 data -> GPIO4 (OneWire, 4.7k pull-up to 3V3)
    The probe is taped to skin contact, so temp0 is skin temperature, not ambient.
    GPIO4 is the pin the GSR module used to occupy. GSR is no longer fitted and
    the firmware contains no GSR code path.

  Status LED:
    external LED + 220 ohm resistor -> GPIO2
    Single colour, so commands select a pattern: LED,G steady on, LED,Y off,
    LED,R 250 ms blink.

  Canonical CP3 (current hardware):
    $CP3,ms,ir,red,ax,ay,az,gx,gy,gz,temp0,temp1,micRaw,micRms,micPitch,ecg,fsr,lux,roomT,hum,press,buttons,status,crc

  Deprecated CP2 (kept on the host side so old recordings still parse):
    $CP2,ms,ir,red,ax,ay,az,gx,gy,gz,temp0,temp1,gsr,micRaw,micRms,micPitch,ecg,fsr,lux,roomT,hum,press,buttons,status,crc
    The only difference is the `gsr` field after temp1, which this board no
    longer measures. New firmware never emits CP2.

  Extended environmental channels:
    lux   = BH1750 ambient light
    roomT = BME280 temperature (ambient, NOT skin temperature)
    hum   = BME280 relative humidity
    press = BME280 pressure in hPa

  temp1 is intentionally NAN: one DS18B20 probe is fitted, in skin contact.
  mic/ECG/FSR/buttons remain explicit missing-data placeholders on the wearable;
  the host shows them as "not fitted" rather than as physiological zeros.

  TCP and USB carry the same newline-terminated CP3 frame.
  This is an educational/research acquisition device, not a medical device.
*/

#include <Wire.h>
#include <WiFi.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include "MAX30105.h"
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <BH1750.h>
#include <Adafruit_BME280.h>
#include <math.h>

#define I2C_SDA_PIN 8
#define I2C_SCL_PIN 9
#define ONEWIRE_PIN 4
#define STATUS_LED_PIN 2

#define BAUD_RATE 115200
#define TCP_PORT 7777
#define PACKET_PERIOD_MS 50
#define IMU_PERIOD_MS 20
// MAX30105 setup below uses sampleRate=100 with sampleAverage=4, so the FIFO
// produces 100/4 = 25 samples/s. Reading faster than that re-reads the same FIFO
// slot, so 40 ms (25 Hz) is the fastest cadence that returns new samples.
#define PPG_PERIOD_MS 40
#define TEMP_PERIOD_MS 1000
#define ENV_PERIOD_MS 500

static const char* AP_NAME = "ENDO-TWIN-S3";
static const char* AP_PASSWORD = "endotwins3";

enum StatusBit : uint16_t {
  ST_PPG_ABSENT = 0,
  ST_PPG_SAT = 1,
  ST_MPU_ERR = 2,
  ST_TEMP_ERR = 3,
  ST_I2C_ERR = 5,
  ST_LOW_QUALITY = 6,
  ST_BME_ERR = 8,
  // Bit 9 is the Mega lab controller's OLED error. This board has no OLED, so
  // its ambient-light error uses a free bit instead of colliding with that label.
  ST_LIGHT_ERR = 12
};

MAX30105 particleSensor;
Adafruit_MPU6050 mpu;
BH1750 lightMeter;
Adafruit_BME280 bme;
OneWire oneWire(ONEWIRE_PIN);
DallasTemperature skinSensor(&oneWire);
WiFiServer server(TCP_PORT);
WiFiClient tcpClient;

bool ppgOK=false, mpuOK=false, lightOK=false, bmeOK=false, tempOK=false;

uint16_t statusBase=0;

uint32_t irValue=0, redValue=0;
float ax_g=0, ay_g=0, az_g=1;
float gx_dps=0, gy_dps=0, gz_dps=0;
float ax_bias=0, ay_bias=0, az_bias=0;
float gx_bias=0, gy_bias=0, gz_bias=0;

// Skin temperature from the DS18B20 in contact with skin. NAN until the first
// conversion completes, and again if the probe is disconnected mid-session.
float skinTempC=NAN;
bool tempPrimed=false;

float luxValue=NAN, roomT=NAN, humidity=NAN, pressure=NAN;

unsigned long lastPPG=0, lastIMU=0, lastTemp=0, lastEnv=0, lastPacket=0;
char cmdBuf[48];
uint8_t cmdIdx=0;

// The board has a single status LED, so LED commands select a *pattern*, not a
// colour: LED,G = steady on, LED,Y = off, LED,R = 250 ms blink (error attention).
uint8_t ledMode = 0;          // 0 off, 1 steady, 2 blink
bool ledOn = false;
unsigned long lastBlink = 0;

uint8_t xorCRC(const char* text) {
  uint8_t c=0;
  while (*text) c ^= (uint8_t)(*text++);
  return c;
}

void setLed(bool on) {
  ledOn = on;
  digitalWrite(STATUS_LED_PIN, on ? HIGH : LOW);
}

void serviceLed(unsigned long now) {
  if (ledMode != 2 || now - lastBlink < 250UL) return;
  lastBlink = now;
  setLed(!ledOn);
}

void setupPPG() {
  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) {
    statusBase |= (1 << ST_I2C_ERR);
    return;
  }
  ppgOK=true;
  particleSensor.setup(0x24, 4, 2, 100, 411, 4096);
  particleSensor.setPulseAmplitudeRed(0x24);
  particleSensor.setPulseAmplitudeIR(0x24);
  particleSensor.setPulseAmplitudeGreen(0);
}

void setupMPU() {
  if (!mpu.begin(0x68, &Wire)) {
    if (!mpu.begin(0x69, &Wire)) {
      statusBase |= (1 << ST_MPU_ERR);
      return;
    }
  }
  mpuOK=true;
  mpu.setAccelerometerRange(MPU6050_RANGE_4_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
}

void setupEnvironment() {
  lightOK = lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE, 0x23, &Wire);
  if (!lightOK) {
    lightOK = lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE, 0x5C, &Wire);
  }
  if (!lightOK) statusBase |= (1 << ST_LIGHT_ERR);

  bmeOK = bme.begin(0x76, &Wire);
  if (!bmeOK) bmeOK = bme.begin(0x77, &Wire);
  if (!bmeOK) statusBase |= (1 << ST_BME_ERR);
}

void setupSkinTemp() {
  skinSensor.begin();
  if (skinSensor.getDeviceCount() == 0) {
    statusBase |= (1 << ST_TEMP_ERR);
    return;
  }
  tempOK=true;
  skinSensor.setResolution(12);
  // 12-bit conversion needs ~750 ms, which must not block the 50 ms packet loop,
  // so the sensor converts in the background and is read on the next cycle.
  skinSensor.setWaitForConversion(false);
}

void calibrateIMU() {
  if (!mpuOK) return;

  const int N=120;
  float sax=0, say=0, saz=0, sgx=0, sgy=0, sgz=0;

  for (int i=0; i<N; i++) {
    sensors_event_t a,g,t;
    mpu.getEvent(&a,&g,&t);
    sax += a.acceleration.x/9.80665f;
    say += a.acceleration.y/9.80665f;
    saz += a.acceleration.z/9.80665f;
    sgx += g.gyro.x*57.29578f;
    sgy += g.gyro.y*57.29578f;
    sgz += g.gyro.z*57.29578f;
    delay(5);
  }

  // Assumes the board is flat and still during boot; az bias removes the 1 g of
  // gravity so a resting wearable reads ~0 g on every axis.
  ax_bias=sax/N;
  ay_bias=say/N;
  az_bias=(saz/N)-1.0f;
  gx_bias=sgx/N;
  gy_bias=sgy/N;
  gz_bias=sgz/N;
}

void readPPG() {
  if (!ppgOK) return;
  irValue=particleSensor.getIR();
  redValue=particleSensor.getRed();
}

void readIMU() {
  if (!mpuOK) return;
  sensors_event_t a,g,t;
  mpu.getEvent(&a,&g,&t);
  ax_g=a.acceleration.x/9.80665f-ax_bias;
  ay_g=a.acceleration.y/9.80665f-ay_bias;
  az_g=a.acceleration.z/9.80665f-az_bias;
  gx_dps=g.gyro.x*57.29578f-gx_bias;
  gy_dps=g.gyro.y*57.29578f-gy_bias;
  gz_dps=g.gyro.z*57.29578f-gz_bias;
}

void readSkinTemp() {
  if (!tempOK) return;
  if (!tempPrimed) {
    // First cycle has no completed conversion yet - start one, do not report 85C.
    tempPrimed=true;
    skinSensor.requestTemperatures();
    return;
  }
  float v=skinSensor.getTempCByIndex(0);
  if (v <= DEVICE_DISCONNECTED_C) {
    // Probe fell off or the bus broke: report missing data, never a fake value.
    skinTempC=NAN;
    statusBase |= (1 << ST_TEMP_ERR);
    return;
  }
  skinTempC=v;
  statusBase &= ~(1 << ST_TEMP_ERR);
  skinSensor.requestTemperatures();
}

void readEnvironment() {
  if (lightOK) {
    float v=lightMeter.readLightLevel();
    if (isfinite(v) && v >= 0) luxValue=v;
  }

  if (bmeOK) {
    float t=bme.readTemperature();
    float h=bme.readHumidity();
    float p=bme.readPressure()/100.0f;

    if (isfinite(t)) roomT=t;
    if (isfinite(h)) humidity=h;
    if (isfinite(p)) pressure=p;
  }
}

uint16_t makeStatus() {
  uint16_t st=statusBase;

  if (ppgOK) {
    if (irValue < 5000) st |= (1 << ST_PPG_ABSENT);
    if (irValue > 250000UL || redValue > 250000UL) st |= (1 << ST_PPG_SAT);
  }

  return st;
}

void sendPacket() {
  char ax[16],ay[16],az[16],gx[16],gy[16],gz[16];
  char t0[16],t1[16],lx[16],rt[16],hu[16],pr[16];

  dtostrf(ax_g,1,4,ax);
  dtostrf(ay_g,1,4,ay);
  dtostrf(az_g,1,4,az);
  dtostrf(gx_dps,1,3,gx);
  dtostrf(gy_dps,1,3,gy);
  dtostrf(gz_dps,1,3,gz);
  dtostrf(skinTempC,1,2,t0);
  dtostrf(NAN,1,2,t1);          // temp1: no second probe is fitted
  dtostrf(luxValue,1,1,lx);
  dtostrf(roomT,1,2,rt);
  dtostrf(humidity,1,1,hu);
  dtostrf(pressure,1,1,pr);

  char payload[300];
  uint16_t status=makeStatus();

  // CP3 = CP2 without the retired `gsr` field. Microphone, ECG and FSR are not
  // fitted on the wearable, so they carry the not-measured marker (-1) rather
  // than 0, which would look like a genuine zero reading once plotted.
  snprintf(payload,sizeof(payload),
    "$CP3,%lu,%lu,%lu,%s,%s,%s,%s,%s,%s,%s,%s,-1,-1,-1,-1,-1,%s,%s,%s,%s,0,%u",
    millis(),
    (unsigned long)irValue,
    (unsigned long)redValue,
    ax,ay,az,gx,gy,gz,
    t0,t1,
    lx,rt,hu,pr,status
  );

  uint8_t crc=xorCRC(payload);
  char line[320];
  snprintf(line,sizeof(line),"%s,%02X\n",payload,crc);

  Serial.print(line);
  if (tcpClient && tcpClient.connected()) tcpClient.print(line);
}

void sendAck(const char* line) {
  Serial.println(line);
  if (tcpClient && tcpClient.connected()) tcpClient.println(line);
}

void handleCommand(const char* cmd) {
  if (!strcmp(cmd,"PING")) {
    sendAck("$ACK,PONG,00");
  } else if (!strcmp(cmd,"WHOAMI")) {
    sendAck("$ACK,WHOAMI,ENDO-TWIN-ESP32S3-CP3");
  } else if (!strcmp(cmd,"LED,G")) {
    ledMode=1;
    setLed(true);
  } else if (!strcmp(cmd,"LED,Y")) {
    ledMode=0;
    setLed(false);
  } else if (!strcmp(cmd,"LED,R")) {
    ledMode=2;
    lastBlink=0;
  }
}

void readUsbCommands() {
  while (Serial.available()) {
    char c=(char)Serial.read();
    if (c=='\n' || c=='\r') {
      if (cmdIdx) {
        cmdBuf[cmdIdx]=0;
        handleCommand(cmdBuf);
        cmdIdx=0;
      }
    } else if (cmdIdx < sizeof(cmdBuf)-1) {
      cmdBuf[cmdIdx++]=c;
    }
  }
}

void handleTcpCommands() {
  if (!tcpClient || !tcpClient.connected()) return;

  static char tcpBuf[48];
  static uint8_t tcpIdx=0;

  while (tcpClient.available()) {
    char c=(char)tcpClient.read();
    if (c=='\n' || c=='\r') {
      if (tcpIdx) {
        tcpBuf[tcpIdx]=0;
        handleCommand(tcpBuf);
        tcpIdx=0;
      }
    } else if (tcpIdx < sizeof(tcpBuf)-1) {
      tcpBuf[tcpIdx++]=c;
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
  Serial.printf("TCP server listening on %d\n",TCP_PORT);
}

void setup() {
  pinMode(STATUS_LED_PIN,OUTPUT);
  setLed(false);

  Serial.begin(BAUD_RATE);
  Wire.begin(I2C_SDA_PIN,I2C_SCL_PIN);
  Wire.setClock(400000L);
  analogReadResolution(12);

  delay(300);

  setupPPG();
  setupMPU();
  setupEnvironment();
  setupSkinTemp();
  calibrateIMU();
  readEnvironment();
  readSkinTemp();               // starts the first conversion

  setupWiFi();
  ledMode=1;
  setLed(true);
}

void loop() {
  unsigned long now=millis();

  WiFiClient incoming=server.available();
  if (incoming) {
    if (tcpClient && tcpClient.connected()) tcpClient.stop();
    tcpClient=incoming;
    tcpClient.setNoDelay(true);
    tcpClient.println("$ACK,CONNECTED,ENDO-TWIN-ESP32S3-CP3");
  }

  if (now-lastPPG >= PPG_PERIOD_MS) {
    lastPPG=now;
    readPPG();
  }

  if (now-lastIMU >= IMU_PERIOD_MS) {
    lastIMU=now;
    readIMU();
  }

  if (now-lastTemp >= TEMP_PERIOD_MS) {
    lastTemp=now;
    readSkinTemp();
  }

  if (now-lastEnv >= ENV_PERIOD_MS) {
    lastEnv=now;
    readEnvironment();
  }

  if (now-lastPacket >= PACKET_PERIOD_MS) {
    lastPacket=now;
    sendPacket();
  }

  readUsbCommands();
  handleTcpCommands();
  serviceLed(now);

  if (tcpClient && !tcpClient.connected()) tcpClient.stop();
}
