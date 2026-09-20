/*
  CHRONO-PCOS Nano Pod Firmware
  -----------------------------
  Board: Arduino Nano (ATmega328P). The same sketch also runs on an UNO.

  This is the wearable pod: the small board that stays on the body and keeps
  collecting the three continuous signals the project depends on.

    MAX30102 PPG (IR + red)   I2C  SDA=A4  SCL=A5   (pins 27/28 on a Nano)
    MPU6050 IMU               I2C  same bus, address 0x68
    DS18B20 skin temperature  D2   OneWire, 4.7k pull-up to 5V
    GSR module (optional)     A0

  Serial output, 115200 baud, 20 Hz:

    $CP2,ms,ir,red,ax,ay,az,gx,gy,gz,temp0,temp1,gsr,micRaw,micRms,micPitch,ecg,fsr,lux,roomT,hum,press,buttons,status,crc

  Channels the pod does not have are sent as fixed placeholders (-1 for the
  analog channels, nan for the environment channels), so the Python dashboard
  reads a pod exactly like it reads the Mega bench rig.

  Two ways to connect the pod (no firmware change needed, the Nano has one
  UART and the USB chip sits on the same two pins):

    1. Pod -> PC:        plug the Nano USB cable straight into the laptop and
                         start the dashboard with --port <nano port>.
    2. Pod -> Mega -> PC: Nano pin D1 (TX) to Mega pin D19 (RX1), common GND,
                         power the Nano from a USB phone charger. Flash the
                         Mega with RELAY_POD_SERIAL1 set to 1 and the Mega
                         forwards every pod line to its own USB port. The
                         dashboard then connects to the Mega only.

  Commands accepted on the same serial line (sent by the dashboard):
    LED,G / LED,Y / LED,R   status LEDs on D8 / D9 / D10 through 220 ohm
    BEEP                    120 ms tone on D6
    PING                    answers $ACK,PONG,00

  Arduino libraries needed (Library Manager):
    SparkFun MAX3010x Pulse and Proximity Sensor Library
    Adafruit MPU6050
    Adafruit Unified Sensor
    OneWire
    DallasTemperature

  Safety: educational physiological monitoring only. Not a diagnostic medical
  device. Keep the pod on a battery or the laptop's own USB when it is on a
  person, and never power a body-worn circuit from mains.
*/

#include <Wire.h>
#include "MAX30105.h"
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <OneWire.h>
#include <DallasTemperature.h>

#define ONE_WIRE_BUS 2
#define GSR_PIN A0
#define LED_GREEN 8
#define LED_YELLOW 9
#define LED_RED 10
#define BUZZER_PIN 6

#define BAUD_RATE 115200
#define PPG_PERIOD_MS 20      // 50 Hz sampling of the pulse waveform
#define IMU_PERIOD_MS 20      // 50 Hz motion sampling
#define GSR_PERIOD_MS 100     // 10 Hz
#define TEMP_PERIOD_MS 1000   // 1 Hz
#define PACKET_PERIOD_MS 50   // 20 Hz packets to the dashboard

// Status bits, same numbering as the Mega firmware and packet_parser.py
#define ST_PPG_ABSENT   0
#define ST_PPG_SAT      1
#define ST_MPU_ERR      2
#define ST_TEMP_ERR     3
#define ST_GSR_SAT      4
#define ST_I2C_ERR      5
#define ST_LOW_QUALITY  6

MAX30105 particleSensor;
Adafruit_MPU6050 mpu;
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature tempSensor(&oneWire);

bool ppgOK = false;
bool mpuOK = false;
bool tempOK = false;

uint32_t irValue = 0;
uint32_t redValue = 0;
float ax_g = 0, ay_g = 0, az_g = 1;
float gx_dps = 0, gy_dps = 0, gz_dps = 0;
float ax_bias = 0, ay_bias = 0, az_bias = 0;
float gx_bias = 0, gy_bias = 0, gz_bias = 0;
float temp0 = NAN;
int gsrRaw = 0;
uint16_t statusBase = 0;
char ledState = 'Y';

unsigned long lastPPG = 0;
unsigned long lastIMU = 0;
unsigned long lastGSR = 0;
unsigned long lastTemp = 0;
unsigned long lastPacket = 0;

char cmdBuf[40];
uint8_t cmdIdx = 0;

uint8_t xorCRC(const char *s) {
  uint8_t c = 0;
  while (*s) c ^= (uint8_t)(*s++);
  return c;
}

void setLedState(char s) {
  ledState = s;
  digitalWrite(LED_GREEN, s == 'G');
  digitalWrite(LED_YELLOW, s == 'Y');
  digitalWrite(LED_RED, s == 'R');
}

void beepShort() { tone(BUZZER_PIN, 2200, 120); }

void setupPPG() {
  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) {
    ppgOK = false;
    statusBase |= (1 << ST_I2C_ERR);
    return;
  }
  ppgOK = true;
  // Conservative finger/wrist PPG setup: 4x averaging, red + IR, 100 Hz
  // internal sampling, 411 us pulse width, 18 bit ADC.
  particleSensor.setup(0x24, 4, 2, 100, 411, 4096);
  particleSensor.setPulseAmplitudeRed(0x24);
  particleSensor.setPulseAmplitudeIR(0x24);
  particleSensor.setPulseAmplitudeGreen(0);
}

void setupMPU() {
  if (!mpu.begin()) {
    mpuOK = false;
    statusBase |= (1 << ST_MPU_ERR);
    return;
  }
  mpuOK = true;
  mpu.setAccelerometerRange(MPU6050_RANGE_4_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
}

void setupTemp() {
  tempSensor.begin();
  tempOK = tempSensor.getDeviceCount() > 0;
  if (!tempOK) statusBase |= (1 << ST_TEMP_ERR);
}

// Rest the board flat and still for the first ~1.3 s: the mean reading becomes
// the zero offset, so the motion index is dynamic movement only.
void calibrateIMU() {
  if (!mpuOK) return;
  const int N = 160;
  float sax = 0, say = 0, saz = 0, sgx = 0, sgy = 0, sgz = 0;
  for (int i = 0; i < N; i++) {
    sensors_event_t a, g, t;
    mpu.getEvent(&a, &g, &t);
    sax += a.acceleration.x / 9.80665; say += a.acceleration.y / 9.80665; saz += a.acceleration.z / 9.80665;
    sgx += g.gyro.x * 57.29578; sgy += g.gyro.y * 57.29578; sgz += g.gyro.z * 57.29578;
    delay(8);
  }
  ax_bias = sax / N; ay_bias = say / N; az_bias = (saz / N) - 1.0;
  gx_bias = sgx / N; gy_bias = sgy / N; gz_bias = sgz / N;
}

void readPPG() {
  if (ppgOK) {
    redValue = particleSensor.getRed();
    irValue = particleSensor.getIR();
  }
}

void readIMU() {
  if (!mpuOK) return;
  sensors_event_t a, g, t;
  mpu.getEvent(&a, &g, &t);
  ax_g = a.acceleration.x / 9.80665 - ax_bias;
  ay_g = a.acceleration.y / 9.80665 - ay_bias;
  az_g = a.acceleration.z / 9.80665 - az_bias;
  gx_dps = g.gyro.x * 57.29578 - gx_bias;
  gy_dps = g.gyro.y * 57.29578 - gy_bias;
  gz_dps = g.gyro.z * 57.29578 - gz_bias;
}

void readGSR() { gsrRaw = analogRead(GSR_PIN); }

void readTemp() {
  if (!tempOK) return;
  tempSensor.requestTemperatures();
  temp0 = tempSensor.getTempCByIndex(0);
}

uint16_t makeStatus() {
  uint16_t st = statusBase;
  if (ppgOK) {
    if (irValue < 5000) st |= (1 << ST_PPG_ABSENT);
    if (irValue > 250000UL || redValue > 250000UL) st |= (1 << ST_PPG_SAT);
  }
  if (tempOK && !(temp0 > -20 && temp0 < 80)) st |= (1 << ST_TEMP_ERR);
  if (gsrRaw < 5 || gsrRaw > 1018) st |= (1 << ST_GSR_SAT);
  return st;
}

void sendPacket() {
  char fax[12], fay[12], faz[12], fgx[12], fgy[12], fgz[12], ft0[12];
  dtostrf(ax_g, 1, 4, fax); dtostrf(ay_g, 1, 4, fay); dtostrf(az_g, 1, 4, faz);
  dtostrf(gx_dps, 1, 3, fgx); dtostrf(gy_dps, 1, 3, fgy); dtostrf(gz_dps, 1, 3, fgz);
  dtostrf(temp0, 1, 2, ft0);
  char payload[220];
  uint16_t st = makeStatus();
  // Pod channels that do not exist on this board: mic* = 0, ecg/fsr = -1,
  // lux = -1, roomT/hum/press = nan, buttons = 0.
  snprintf(payload, sizeof(payload),
           "$CP2,%lu,%lu,%lu,%s,%s,%s,%s,%s,%s,%s,nan,%d,0,0.00,0.0,-1,-1,-1,nan,nan,nan,0,%u",
           millis(), (unsigned long)irValue, (unsigned long)redValue,
           fax, fay, faz, fgx, fgy, fgz, ft0, gsrRaw, st);
  uint8_t crc = xorCRC(payload);
  Serial.print(payload);
  Serial.print(',');
  if (crc < 16) Serial.print('0');
  Serial.println(crc, HEX);
}

void handleCommand(const char *cmd) {
  if (strncmp(cmd, "LED,G", 5) == 0) setLedState('G');
  else if (strncmp(cmd, "LED,Y", 5) == 0) setLedState('Y');
  else if (strncmp(cmd, "LED,R", 5) == 0) setLedState('R');
  else if (strncmp(cmd, "BEEP", 4) == 0) beepShort();
  else if (strncmp(cmd, "PING", 4) == 0) Serial.println("$ACK,PONG,00");
}

void readSerialCommands() {
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (cmdIdx > 0) { cmdBuf[cmdIdx] = 0; handleCommand(cmdBuf); cmdIdx = 0; }
    } else if (cmdIdx < sizeof(cmdBuf) - 1) cmdBuf[cmdIdx++] = c;
  }
}

void setup() {
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_YELLOW, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  setLedState('Y');

  Serial.begin(BAUD_RATE);
  Wire.begin();
  delay(250);

  setupPPG();
  setupMPU();
  setupTemp();
  calibrateIMU();
  readTemp();
  readGSR();

  setLedState('G');
  beepShort();
}

void loop() {
  unsigned long now = millis();
  if (now - lastPPG >= PPG_PERIOD_MS) { lastPPG = now; readPPG(); }
  if (now - lastIMU >= IMU_PERIOD_MS) { lastIMU = now; readIMU(); }
  if (now - lastGSR >= GSR_PERIOD_MS) { lastGSR = now; readGSR(); }
  if (now - lastTemp >= TEMP_PERIOD_MS) { lastTemp = now; readTemp(); }
  if (now - lastPacket >= PACKET_PERIOD_MS) { lastPacket = now; sendPacket(); }
  readSerialCommands();
}
