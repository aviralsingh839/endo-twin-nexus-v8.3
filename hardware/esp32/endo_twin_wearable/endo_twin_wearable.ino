/*
  ENDO-TWIN ESP32-S3 Wearable Firmware V8.4 - Shoulder + Forearm Mount
  ====================================================================

  HARDWARE MAP (user final wiring):
  - ESP32-S3 DevKit
  - I2C Bus shared: SDA=GPIO8, SCL=GPIO9, VCC=3V3, GND=GND
    * MPU6050 / MPU2060 (GY-521) - shoulder mount - accel + gyro
      ADDR 0x68 (AD0 low) / 0x69 if AD0 high
    * BME280 - shoulder mount - room temp + humidity + pressure
      ADDR 0x76 (default) / 0x77 alternate
    * BH1750 - shoulder mount - ambient light lux
      ADDR 0x23 (default) / 0x5C alternate
  - Analog Pulse Sensor (generic 3-pin module):
    * S (signal) -> GPIO40 (ADC1_CH0 on S3)
    * VCC -> 3V3 (check module rating, most are 3.3-5V)
    * GND -> GND
    * Mount: inner forearm, light pressure, avoid tendon
  - DS18B20 digital temp:
    * DATA -> GPIO6 with 4.7k pull-up to 3V3
    * VCC -> 3V3
    * GND -> GND
    * Mount: inner forearm near pulse sensor, skin contact with tape
  - Optional GSR (if present):
    * -> GPIO5 (ADC)
  - Status LED -> GPIO2

  MOUNTING LOGIC:
  - Shoulder: environmental + motion context stable, less motion artifact for BME280/BH1750,
    good for activity/posture via MPU6050.
  - Inner forearm: vascular + thermal window for pulse + skin temp.

  PACKET FORMAT ($CP2) - kept compatible with desktop parser:
  $CP2,ms,ir,red,ax,ay,az,gx,gy,gz,temp0,temp1,gsr,micRaw,micRms,micPitch,ecg,fsr,lux,roomT,hum,press,buttons,status,crc
  - ms: millis()
  - ir: analog pulse raw 0..4095 (mapped to legacy IR slot)
  - red: -1 (no optical red channel in analog mode)
  - ax,ay,az: g units, gx,gy,gz: deg/s, bias-corrected
  - temp0: DS18B20 skin temp C (forearm) or nan
  - temp1: nan (reserved for second DS18B20)
  - gsr: raw ADC or -1
  - mic/ecg/fsr: -1 / 0 placeholder (not used in this build)
  - lux: BH1750 lux
  - roomT: BME280 temperature C
  - hum: BME280 humidity %
  - press: BME280 pressure hPa
  - buttons: 0
  - status: bitmask (see below)
  - crc: XOR of all chars before last comma

  STATUS BITS:
  0  PPG absent (pulseRaw < threshold)
  1  PPG saturated
  2  MPU6050/2060 error
  3  DS18B20 error
  4  GSR saturated
  5  I2C error (bus)
  6  Low signal quality (generic)
  7  ECG leads off (unused)
  8  BME280 error
  9  OLED error (unused)
  10 MIC low (unused)
  11 FSR artifact (unused)
  12 ANALOG_PULSE active (always 1 in this build)
  13 ANALOG_PULSE invalid (out of ADC range)
  14 BH1750 error
  15 Reserved

  NOTES:
  - Educational research prototype, NOT a medical device.
  - No SpO2 from analog pulse sensor - do NOT fabricate.
  - All I2C devices share bus; handle init failures gracefully.
  - BLE + Serial dual output for desktop dashboard.
*/

#include <Arduino.h>
#include <Wire.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <BH1750.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// -------------------- Pin map (user specified) --------------------
static constexpr uint8_t SDA_PIN = 8;
static constexpr uint8_t SCL_PIN = 9;
static constexpr uint8_t PULSE_PIN = 40;      // analog pulse S -> 40
static constexpr uint8_t ONE_WIRE_BUS = 6;    // DS18B20 DATA -> 6
static constexpr uint8_t GSR_PIN = 5;         // optional GSR
static constexpr uint8_t STATUS_LED = 2;

static constexpr uint32_t BAUD_RATE = 115200;
static constexpr uint32_t PULSE_PERIOD_MS = 20;   // 50 Hz read
static constexpr uint32_t IMU_PERIOD_MS = 20;     // 50 Hz
static constexpr uint32_t GSR_PERIOD_MS = 100;    // 10 Hz
static constexpr uint32_t TEMP_PERIOD_MS = 1000;  // 1 Hz DS18B20
static constexpr uint32_t ENV_PERIOD_MS = 1000;   // 1 Hz BME280+BH1750
static constexpr uint32_t PACKET_PERIOD_MS = 50;  // 20 Hz output (smooth dashboard)

// Status bits
#define ST_PPG_ABSENT 0
#define ST_PPG_SAT 1
#define ST_MPU_ERR 2
#define ST_TEMP_ERR 3
#define ST_GSR_SAT 4
#define ST_I2C_ERR 5
#define ST_LOW_Q 6
#define ST_BME_ERR 8
#define ST_PPG_ANALOG 12
#define ST_PPG_INVALID 13
#define ST_BH1750_ERR 14

// BLE UUIDs
static const char* SERVICE_UUID = "7f300001-6c12-4f70-9e6b-8e9f7b8b1001";
static const char* DATA_UUID    = "7f300002-6c12-4f70-9e6b-8e9f7b8b1001";
static const char* CMD_UUID     = "7f300003-6c12-4f70-9e6b-8e9f7b8b1001";

// Sensors
Adafruit_MPU6050 mpu;
Adafruit_BME280 bme;
BH1750 bh1750;
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature ds18(&oneWire);

BLECharacteristic* dataChar = nullptr;
bool bleConnected = false;
bool mpuOK = false, bmeOK = false, bh1750OK = false, ds18OK = false;
uint16_t statusBase = 0;

// Live data
int pulseRaw = 0;
int gsrRaw = 0;
float ax=0, ay=0, az=1, gx=0, gy=0, gz=0;
float axb=0, ayb=0, azb=0, gxb=0, gyb=0, gzb=0;
float skinTempC = NAN;      // DS18B20 forearm
float bmeTempC = NAN;       // BME280 room temp (shoulder)
float bmeHum = NAN;         // %
float bmePress = NAN;       // hPa
float lux = NAN;            // BH1750
uint8_t activePulsePin = 40; // will auto-select if 40 is flat

uint32_t tPulse=0, tImu=0, tGsr=0, tTemp=0, tEnv=0, tPack=0;

// CRC8 XOR
uint8_t crc8(const char* s){
  uint8_t c=0;
  while(*s) c ^= (uint8_t)(*s++);
  return c;
}

String buildPacket(); // forward decl for early test publish

// -------------------- Sensor Setup --------------------
void setupI2C(){
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(100000); // start safe 100k, then try 400k after scan
  Wire.setTimeOut(20); // 20ms timeout to avoid hang
  delay(50);
  Serial.println("[I2C] scanning SDA=8 SCL=9 @100k for 0x68/0x69/0x76/0x77/0x23/0x5C...");
  int found=0;
  uint8_t addrs[] = {0x68,0x69,0x76,0x77,0x23,0x5C};
  for(uint8_t a: addrs){
    Wire.beginTransmission(a);
    uint8_t err = Wire.endTransmission();
    if(err==0){
      Serial.printf("  I2C 0x%02X found\n",a);
      found++;
    }
  }
  if(found==0){
    Serial.println("[I2C] WARNING: no expected devices found! Check SDA=8 SCL=9 wiring, 3V3, GND");
    Serial.println("[I2C] Continuing anyway - pulse+DS18 will still publish at 20Hz");
    // Don't set I2C error as fatal, allow pulse to work
  } else {
    Serial.printf("[I2C] %d expected device(s) found, switching to 400kHz\n",found);
    Wire.setClock(400000);
  }
  // Quick publish test to prove serial works before sensor init
  Serial.println("[I2C] I2C scan done, testing serial...");
  Serial.println("$CP2,0,1850,-1,0.01,0.02,1.00,0.1,0.2,0.3,32.50,nan,450,0,0.00,0.0,-1,-1,100,25,50,1010,0,4096,6A");
  Serial.println("$CP2,20,1860,-1,0.01,0.02,1.00,0.1,0.2,0.3,32.51,nan,451,0,0.00,0.0,-1,-1,101,25.1,50.1,1010.1,0,4096,6B");
  Serial.println("$CP2,40,1870,-1,0.01,0.02,1.00,0.1,0.2,0.3,32.52,nan,452,0,0.00,0.0,-1,-1,102,25.2,50.2,1010.2,0,4096,6C");
}

void setupMPU(){
  // Try 0x68 then 0x69 with small delay, don't block forever
  for(int attempt=0; attempt<2; attempt++){
    uint8_t addr = (attempt==0)?0x68:0x69;
    if(mpu.begin(addr, &Wire, 0)){
      mpuOK = true;
      mpu.setAccelerometerRange(MPU6050_RANGE_4_G);
      mpu.setGyroRange(MPU6050_RANGE_500_DEG);
      mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
      Serial.printf("[MPU] OK at 0x%02X (MPU6050/2060 compatible)\n",addr);
      return;
    }
    delay(50);
  }
  statusBase |= (1<<ST_MPU_ERR);
  Serial.println("[MPU] not found at 0x68/0x69 - check wiring SDA=8 SCL=9, VCC=3V3, AD0=GND for 0x68");
}

void setupBME280(){
  // Try 0x76 then 0x77, with timeout
  for(int attempt=0; attempt<2; attempt++){
    uint8_t addr = (attempt==0)?0x76:0x77;
    if(bme.begin(addr, &Wire)){
      bmeOK = true;
      Serial.printf("[BME280] OK at 0x%02X\n",addr);
      return;
    }
    delay(30);
  }
  statusBase |= (1<<ST_BME_ERR);
  Serial.println("[BME280] not found at 0x76/0x77 - check wiring, 3V3");
}

void setupBH1750(){
  if(bh1750.begin(BH1750::CONTINUOUS_HIGH_RES_MODE, 0x23, &Wire)){
    bh1750OK = true;
    Serial.println("[BH1750] OK at 0x23");
    return;
  }
  delay(30);
  if(bh1750.begin(BH1750::CONTINUOUS_HIGH_RES_MODE, 0x5C, &Wire)){
    bh1750OK = true;
    Serial.println("[BH1750] OK at 0x5C");
    return;
  }
  statusBase |= (1<<ST_BH1750_ERR);
  Serial.println("[BH1750] not found at 0x23/0x5C - check wiring, lens not covered");
}

void setupPulse(){
  pinMode(PULSE_PIN, INPUT);
  // Also setup alt pins for auto-detect
  pinMode(4, INPUT);
  pinMode(5, INPUT);
  pinMode(1, INPUT);
  pinMode(2, INPUT);
  analogReadResolution(12);
  #if defined(ADC_11db)
    analogSetPinAttenuation(PULSE_PIN, ADC_11db);
    analogSetPinAttenuation(4, ADC_11db);
    analogSetPinAttenuation(5, ADC_11db);
    analogSetPinAttenuation(1, ADC_11db);
    analogSetPinAttenuation(2, ADC_11db);
  #endif
  statusBase |= (1<<ST_PPG_ANALOG); // mark analog pulse active

  // Auto-detect best pulse pin (since GPIO40 is PSRAM on some S3 Feather boards and reads 0)
  delay(100);
  int bestVar=0;
  uint8_t bestPin=PULSE_PIN;
  uint8_t candidates[] = {40,4,1,2,3,10};
  Serial.println("[PULSE] scanning ADC pins for variation...");
  for(uint8_t pin: candidates){
    int minV=4095, maxV=0;
    for(int k=0;k<40;k++){
      int v=analogRead(pin);
      if(v<minV) minV=v;
      if(v>maxV) maxV=v;
      delay(5);
    }
    int var = maxV-minV;
    Serial.printf("  GPIO%d var %d (min %d max %d)\n", pin, var, minV, maxV);
    if(var>bestVar){
      bestVar=var;
      bestPin=pin;
    }
  }
  activePulsePin=bestPin;
  Serial.printf("[PULSE] selected GPIO%d var %d\n", activePulsePin, bestVar);
  if(bestVar<5){
    Serial.println("[PULSE] WARNING: all pins flat, check VCC=3V3 GND S wiring, sensor needs light pressure");
  }
}

void setupDS18(){
  ds18.begin();
  ds18OK = ds18.getDeviceCount() > 0;
  if(!ds18OK){
    statusBase |= (1<<ST_TEMP_ERR);
    Serial.println("[DS18B20] not found on GPIO6");
  } else {
    ds18.setResolution(12);
    ds18.setWaitForConversion(false);
    ds18.requestTemperatures();
    Serial.printf("[DS18B20] %d device(s) found\n", ds18.getDeviceCount());
  }
}

void setupGSR(){
  pinMode(GSR_PIN, INPUT);
  #if defined(ADC_11db)
    analogSetPinAttenuation(GSR_PIN, ADC_11db);
  #endif
}

void setupSensors(){
  setupI2C();
  setupPulse();
  setupGSR();
  setupMPU();
  setupBME280();
  setupBH1750();
  setupDS18();
}

// -------------------- Calibration --------------------
void calibrateIMU(){
  if(!mpuOK) return;
  const int N=200;
  float sx=0,sy=0,sz=0,sgx=0,sgy=0,sgz=0;
  int cnt=0;
  for(int i=0;i<N;i++){
    sensors_event_t a,g,t;
    if(!mpu.getEvent(&a,&g,&t)) continue;
    sx += a.acceleration.x/9.80665f;
    sy += a.acceleration.y/9.80665f;
    sz += a.acceleration.z/9.80665f;
    sgx += g.gyro.x*57.29578f;
    sgy += g.gyro.y*57.29578f;
    sgz += g.gyro.z*57.29578f;
    cnt++;
    delay(10);
  }
  if(cnt>0){
    axb = sx/cnt; ayb = sy/cnt; azb = sz/cnt - 1.0f;
    gxb = sgx/cnt; gyb = sgy/cnt; gzb = sgz/cnt;
    Serial.printf("[MPU] bias ax %.3f ay %.3f az %.3f gx %.2f gy %.2f gz %.2f\n", axb,ayb,azb,gxb,gyb,gzb);
  }
}

// -------------------- Readers --------------------
void readPulse(){
  pulseRaw = analogRead(activePulsePin);
}

void readIMU(){
  if(!mpuOK) return;
  sensors_event_t a,g,t;
  if(!mpu.getEvent(&a,&g,&t)) return;
  // Low-pass complementary: raw bias-corrected
  float nax = a.acceleration.x/9.80665f - axb;
  float nay = a.acceleration.y/9.80665f - ayb;
  float naz = a.acceleration.z/9.80665f - azb;
  float ngx = g.gyro.x*57.29578f - gxb;
  float ngy = g.gyro.y*57.29578f - gyb;
  float ngz = g.gyro.z*57.29578f - gzb;
  // V8.4.1: more responsive for activity detection (0.7), still smooth for display
  const float alpha = 0.70f;
  ax = ax* (1-alpha) + nax*alpha;
  ay = ay* (1-alpha) + nay*alpha;
  az = az* (1-alpha) + naz*alpha;
  gx = gx* (1-alpha) + ngx*alpha;
  gy = gy* (1-alpha) + ngy*alpha;
  gz = gz* (1-alpha) + ngz*alpha;
}

void readGSR(){
  gsrRaw = analogRead(GSR_PIN);
}

void readDS18(){
  if(!ds18OK) return;
  // Non-blocking: request already sent, now read
  float t = ds18.getTempCByIndex(0);
  if(t > -40 && t < 85) skinTempC = t;
  ds18.requestTemperatures(); // start next conversion
}

void readENV(){
  if(bmeOK){
    float t = bme.readTemperature();
    float h = bme.readHumidity();
    float p = bme.readPressure() / 100.0f; // hPa
    if(!isnan(t) && t>-40 && t<85) bmeTempC = t;
    if(!isnan(h) && h>=0 && h<=100) bmeHum = h;
    if(!isnan(p) && p>300 && p<1100) bmePress = p;
  }
  if(bh1750OK){
    float l = bh1750.readLightLevel();
    if(l>=0 && l< 100000) lux = l;
  }
}

uint16_t currentStatus(){
  uint16_t s = statusBase;
  if(pulseRaw<=5 || pulseRaw>=4090) s |= (1<<ST_PPG_INVALID);
  if(pulseRaw<20) s |= (1<<ST_PPG_ABSENT);
  if(pulseRaw>4075) s |= (1<<ST_PPG_SAT);
  if(!mpuOK) s |= (1<<ST_MPU_ERR);
  if(!ds18OK || !(skinTempC>-20 && skinTempC<80)) s |= (1<<ST_TEMP_ERR);
  if(gsrRaw<5 || gsrRaw>4090) s |= (1<<ST_GSR_SAT);
  if(!bmeOK) s |= (1<<ST_BME_ERR);
  if(!bh1750OK) s |= (1<<ST_BH1750_ERR);
  // Low quality if multiple sensors missing
  int missing = (!mpuOK) + (!bmeOK) + (!bh1750OK) + (!ds18OK);
  if(missing>=2) s |= (1<<ST_LOW_Q);
  return s;
}

String buildPacket(){
  char tSkin[16], tLux[16], tRoom[16], tHum[16], tPress[16];
  if(isnan(skinTempC)) strcpy(tSkin,"nan"); else snprintf(tSkin,sizeof(tSkin),"%.2f",skinTempC);
  if(isnan(lux)) strcpy(tLux,"nan"); else snprintf(tLux,sizeof(tLux),"%.1f",lux);
  if(isnan(bmeTempC)) strcpy(tRoom,"nan"); else snprintf(tRoom,sizeof(tRoom),"%.2f",bmeTempC);
  if(isnan(bmeHum)) strcpy(tHum,"nan"); else snprintf(tHum,sizeof(tHum),"%.1f",bmeHum);
  if(isnan(bmePress)) strcpy(tPress,"nan"); else snprintf(tPress,sizeof(tPress),"%.2f",bmePress);

  // $CP2 compatibility:
  // ir = pulseRaw, red=-1, temp0=skinTemp, temp1=nan, gsr=gsrRaw, lux, roomT, hum, press
  char p[320];
  uint16_t st = currentStatus();
  snprintf(
    p,sizeof(p),
    "$CP2,%lu,%d,-1,%.4f,%.4f,%.4f,%.3f,%.3f,%.3f,%s,nan,%d,0,0.00,0.0,-1,-1,%s,%s,%s,%s,0,%u",
    (unsigned long)millis(),
    pulseRaw,
    ax,ay,az,gx,gy,gz,
    tSkin,
    gsrRaw,
    tLux,
    tRoom,
    tHum,
    tPress,
    st
  );
  char out[340];
  uint8_t c = crc8(p);
  snprintf(out,sizeof(out),"%s,%02X",p,c);
  return String(out);
}

void publishPacket(){
  String pkt = buildPacket();
  Serial.println(pkt);
  if(bleConnected && dataChar){
    dataChar->setValue(pkt.c_str());
    dataChar->notify();
  }
  // Blink status LED on publish for visual feedback
  static bool ledState=false;
  ledState=!ledState;
  digitalWrite(STATUS_LED, ledState);
}

void handleCommand(String c){
  c.trim();
  c.toUpperCase();
  if(c=="PING"){
    Serial.println("$ACK,PONG,00");
  } else if(c=="WHOAMI"){
    Serial.println("ENDO-TWIN-ESP32-S3-SHOULDER-FOREARM-V8.4");
  } else if(c=="STATUS"){
    Serial.printf("$STAT,MPU:%d BME:%d BH:%d DS18:%d PULSE:%d GSR:%d ST:0x%04X\n",
      mpuOK,bmeOK,bh1750OK,ds18OK,pulseRaw,gsrRaw,currentStatus());
  } else if(c=="CALIB"){
    calibrateIMU();
    Serial.println("$ACK,CALIB,DONE");
  } else if(c=="I2CSCAN"){
    Serial.println("I2C scan (expected 0x68/0x69/0x76/0x77/0x23/0x5C):");
    uint8_t addrs[] = {0x68,0x69,0x76,0x77,0x23,0x5C};
    for(uint8_t a: addrs){
      Wire.beginTransmission(a);
      uint8_t err = Wire.endTransmission();
      Serial.printf("  0x%02X %s\n",a, err==0?"found":"not found");
    }
  }
}

class ServerCB: public BLEServerCallbacks{
  void onConnect(BLEServer* s) override { bleConnected=true; Serial.println("[BLE] connected"); }
  void onDisconnect(BLEServer* s) override { bleConnected=false; BLEDevice::startAdvertising(); Serial.println("[BLE] disconnected"); }
};

class CmdCB: public BLECharacteristicCallbacks{
  void onWrite(BLECharacteristic* ch) override{
    // Compatible with both old (std::string) and new (Arduino String) BLE API
    auto v = ch->getValue();
    if(v.length() > 0){
      // v.c_str() works for both String and std::string
      String cmd = String(v.c_str());
      handleCommand(cmd);
    }
  }
};

void setupBLE(){
  BLEDevice::init("ENDO-TWIN-S3");
  BLEServer* server = BLEDevice::createServer();
  server->setCallbacks(new ServerCB());
  BLEService* svc = server->createService(SERVICE_UUID);
  dataChar = svc->createCharacteristic(DATA_UUID, BLECharacteristic::PROPERTY_NOTIFY);
  dataChar->addDescriptor(new BLE2902());
  BLECharacteristic* cmdChar = svc->createCharacteristic(CMD_UUID, BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_WRITE_NR);
  cmdChar->setCallbacks(new CmdCB());
  svc->start();
  BLEAdvertising* adv = BLEDevice::getAdvertising();
  adv->addServiceUUID(SERVICE_UUID);
  adv->setScanResponse(true);
  adv->setMinPreferred(0x06);
  adv->setMinPreferred(0x12);
  BLEDevice::startAdvertising();
  Serial.println("[BLE] advertising as ENDO-TWIN-S3");
}

void setup(){
  pinMode(STATUS_LED, OUTPUT);
  digitalWrite(STATUS_LED, LOW);
  Serial.begin(BAUD_RATE);
  delay(800);
  Serial.println("\n\n=== ENDO-TWIN S3 Wearable V8.4 ===");
  Serial.println("Wiring: SDA=8 SCL=9 Pulse=40 DS18=6 GSR=5 LED=2");
  Serial.println("Mount: Shoulder (MPU/BME/BH) + Forearm (Pulse/DS18)");
  Serial.println("[SYS] Serial OK @115200, testing packet...");
  // Immediate test packets to prove dashboard can see data even before I2C
  for(int i=0;i<5;i++){
    Serial.printf("$CP2,%lu,1850,-1,0.01,0.02,1.00,0.1,0.2,0.3,32.50,nan,450,0,0.00,0.0,-1,-1,100,25,50,1010,0,4096,%02X\n",
      (unsigned long)millis(), crc8("$CP2,0,1850,-1,0.01,0.02,1.00,0.1,0.2,0.3,32.50,nan,450,0,0.00,0.0,-1,-1,100,25,50,1010,0,4096"));
    delay(100);
  }
  setupSensors();
  Serial.println("[SYS] Sensors init done, calibrating IMU (if MPU OK)...");
  if(mpuOK){
    calibrateIMU();
  } else {
    Serial.println("[SYS] MPU not OK, skipping calibration");
  }
  setupBLE();
  // Prime env read
  readENV();
  readDS18();
  Serial.println("[SYS] ready - 20Hz packet @ 115200 baud - Connect dashboard to /dev/ttyACM0");
  Serial.println("[SYS] If dashboard shows 0Hz, check: 1) USB CDC On Boot Enabled 2) Cable data 3) sudo chmod 666 /dev/ttyACM0");
}

void loop(){
  uint32_t now = millis();
  if(now - tPulse >= PULSE_PERIOD_MS){ tPulse=now; readPulse(); }
  if(now - tImu >= IMU_PERIOD_MS){ tImu=now; readIMU(); }
  if(now - tGsr >= GSR_PERIOD_MS){ tGsr=now; readGSR(); }
  if(now - tTemp >= TEMP_PERIOD_MS){ tTemp=now; readDS18(); }
  if(now - tEnv >= ENV_PERIOD_MS){ tEnv=now; readENV(); }
  if(now - tPack >= PACKET_PERIOD_MS){ tPack=now; publishPacket(); }

  static String buf;
  while(Serial.available()){
    char ch = (char)Serial.read();
    if(ch=='\n' || ch=='\r'){
      if(buf.length()>0) handleCommand(buf);
      buf="";
    } else if(buf.length()<64){
      buf+=ch;
    }
  }
}
