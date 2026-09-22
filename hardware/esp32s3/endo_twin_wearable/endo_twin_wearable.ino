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

  Analog:
    GSR module analog output -> GPIO4 / ADC1
    GSR uses finger electrodes connected to the sensor module, not directly to GPIO4.

  Status LED:
    external LED + 220 ohm resistor -> GPIO2

  Canonical CP2:
    $CP2,ms,ir,red,ax,ay,az,gx,gy,gz,temp0,temp1,gsr,micRaw,micRms,micPitch,ecg,fsr,lux,roomT,hum,press,buttons,status,crc

  Extended environmental channels:
    lux   = BH1750 ambient light
    roomT = BME280 temperature
    hum   = BME280 relative humidity
    press = BME280 pressure in hPa

  temp0/temp1 are intentionally NAN because the wearable no longer uses DS18B20.
  mic/ECG/FSR/buttons remain explicit missing-data placeholders on the wearable.

  TCP and USB carry the same newline-terminated CP2 frame.
  This is an educational/research acquisition device, not a medical device.
*/

#include <Wire.h>
#include <WiFi.h>
#include "MAX30105.h"
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <BH1750.h>
#include <Adafruit_BME280.h>
#include <math.h>

#define I2C_SDA_PIN 8
#define I2C_SCL_PIN 9
#define GSR_PIN 4
#define STATUS_LED_PIN 2

#define BAUD_RATE 115200
#define TCP_PORT 7777
#define PACKET_PERIOD_MS 50
#define IMU_PERIOD_MS 20
#define PPG_PERIOD_MS 20
#define GSR_PERIOD_MS 50
#define ENV_PERIOD_MS 500

static const char* AP_NAME = "ENDO-TWIN-S3";
static const char* AP_PASSWORD = "endotwins3";

enum StatusBit : uint16_t {
  ST_PPG_ABSENT = 0,
  ST_PPG_SAT = 1,
  ST_MPU_ERR = 2,
  ST_TEMP_ERR = 3,
  ST_GSR_SAT = 4,
  ST_I2C_ERR = 5,
  ST_LOW_QUALITY = 6,
  ST_BME_ERR = 8,
  ST_LIGHT_ERR = 9
};

MAX30105 particleSensor;
Adafruit_MPU6050 mpu;
BH1750 lightMeter;
Adafruit_BME280 bme;
WiFiServer server(TCP_PORT);
WiFiClient tcpClient;

bool ppgOK=false, mpuOK=false, lightOK=false, bmeOK=false;
uint16_t statusBase=0;

uint32_t irValue=0, redValue=0;
float ax_g=0, ay_g=0, az_g=1;
float gx_dps=0, gy_dps=0, gz_dps=0;
float ax_bias=0, ay_bias=0, az_bias=0;
float gx_bias=0, gy_bias=0, gz_bias=0;

int gsrRaw=0;
float luxValue=NAN, roomT=NAN, humidity=NAN, pressure=NAN;

unsigned long lastPPG=0, lastIMU=0, lastGSR=0, lastEnv=0, lastPacket=0;
char cmdBuf[48];
uint8_t cmdIdx=0;

uint8_t xorCRC(const char* text) {
  uint8_t c=0;
  while (*text) c ^= (uint8_t)(*text++);
  return c;
}

void setLed(bool on) {
  digitalWrite(STATUS_LED_PIN, on ? HIGH : LOW);
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

  if (gsrRaw < 5 || gsrRaw > 4090) st |= (1 << ST_GSR_SAT);

  return st;
}

void sendPacket() {
  char ax[16],ay[16],az[16],gx[16],gy[16],gz[16];
  char lx[16],rt[16],hu[16],pr[16];

  dtostrf(ax_g,1,4,ax);
  dtostrf(ay_g,1,4,ay);
  dtostrf(az_g,1,4,az);
  dtostrf(gx_dps,1,3,gx);
  dtostrf(gy_dps,1,3,gy);
  dtostrf(gz_dps,1,3,gz);
  dtostrf(luxValue,1,1,lx);
  dtostrf(roomT,1,2,rt);
  dtostrf(humidity,1,1,hu);
  dtostrf(pressure,1,1,pr);

  char payload[300];
  uint16_t status=makeStatus();

  snprintf(payload,sizeof(payload),
    "$CP2,%lu,%lu,%lu,%s,%s,%s,%s,%s,%s,nan,nan,%d,0,0.00,0.0,-1,-1,%s,%s,%s,%s,0,%u",
    millis(),
    (unsigned long)irValue,
    (unsigned long)redValue,
    ax,ay,az,gx,gy,gz,
    gsrRaw,lx,rt,hu,pr,status
  );

  uint8_t crc=xorCRC(payload);
  char line[320];
  snprintf(line,sizeof(line),"%s,%02X
",payload,crc);

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
    sendAck("$ACK,WHOAMI,ENDO-TWIN-ESP32S3");
  } else if (!strcmp(cmd,"LED,G")) {
    setLed(true);
  } else if (!strcmp(cmd,"LED,Y")) {
    setLed(false);
  } else if (!strcmp(cmd,"LED,R")) {
    setLed(true);
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
  calibrateIMU();
  readEnvironment();

  setupWiFi();
  setLed(true);
}

void loop() {
  unsigned long now=millis();

  WiFiClient incoming=server.available();
  if (incoming) {
    if (tcpClient && tcpClient.connected()) tcpClient.stop();
    tcpClient=incoming;
    tcpClient.setNoDelay(true);
    tcpClient.println("$ACK,CONNECTED,ENDO-TWIN-ESP32S3");
  }

  if (now-lastPPG >= PPG_PERIOD_MS) {
    lastPPG=now;
    readPPG();
  }

  if (now-lastIMU >= IMU_PERIOD_MS) {
    lastIMU=now;
    readIMU();
  }

  if (now-lastGSR >= GSR_PERIOD_MS) {
    lastGSR=now;
    gsrRaw=analogRead(GSR_PIN);
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

  if (tcpClient && !tcpClient.connected()) tcpClient.stop();
}
