/* LEGACY HARDWARE — historical ESP32 wearable snapshot. Not part of the active architecture. */

/*
  ENDO-TWIN NEXUS V8.7 — ESP32 PRIMARY WEARABLE
  ------------------------------------------------
  Active wearable controller for the ENDO-TWIN platform.
  CHRONO-PCOS is a disease-specific research extension; this firmware is
  platform-wide and emits the canonical CP2 physiological packet.

  Board: ESP32
  USB Serial: 115200 baud

  Core sensors:
    MAX30102 PPG       I2C SDA GPIO21, SCL GPIO22
    MPU6050 IMU        I2C SDA GPIO21, SCL GPIO22
    DS18B20 temperature DATA GPIO18, 4.7k pull-up to 3.3V
    GSR/EDA            ADC GPIO34
    Status LED         GPIO2

  BLE:
    Device: ENDO-TWIN-ESP32
    Service: 7f300001-6c12-4f70-9e6b-8e9f7b8b1001
    Notify:  7f300002-6c12-4f70-9e6b-8e9f7b8b1001
    Command: 7f300003-6c12-4f70-9e6b-8e9f7b8b1001

  Commands:
    PING
    WHOAMI
    LED,G / LED,Y / LED,R

  CP2:
    $CP2,ms,ir,red,ax,ay,az,gx,gy,gz,temp0,temp1,gsr,micRaw,micRms,micPitch,ecg,fsr,lux,roomT,hum,press,buttons,status,crc

  CRC is XOR of every character in the payload before the final comma,
  including the '$' prefix. BLE notifications are chunked and end at '\n';
  Android/Desktop reconstructs the same CP2 frame before parsing.

  Safety: educational/research acquisition only. Not a diagnostic medical device.
*/

#include <Wire.h>
#include "MAX30105.h"
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <math.h>

#define SDA_PIN 21
#define SCL_PIN 22
#define DS18B20_PIN 18
#define GSR_PIN 34
#define STATUS_LED_PIN 2
#define BAUD_RATE 115200

#define PACKET_PERIOD_MS 50
#define IMU_PERIOD_MS 20
#define PPG_PERIOD_MS 20
#define GSR_PERIOD_MS 100
#define TEMP_REQUEST_PERIOD_MS 1000
#define TEMP_CONVERSION_MS 200

#define ST_PPG_ABSENT   0
#define ST_PPG_SAT      1
#define ST_MPU_ERR      2
#define ST_TEMP_ERR     3
#define ST_GSR_SAT      4
#define ST_I2C_ERR      5
#define ST_LOW_QUALITY  6

static const char* BLE_DEVICE_NAME = "ENDO-TWIN-ESP32";
static const char* BLE_SERVICE_UUID = "7f300001-6c12-4f70-9e6b-8e9f7b8b1001";
static const char* BLE_NOTIFY_UUID  = "7f300002-6c12-4f70-9e6b-8e9f7b8b1001";
static const char* BLE_COMMAND_UUID = "7f300003-6c12-4f70-9e6b-8e9f7b8b1001";

MAX30105 particleSensor;
Adafruit_MPU6050 mpu;
OneWire oneWire(DS18B20_PIN);
DallasTemperature tempSensor(&oneWire);

bool ppgOK=false, mpuOK=false, tempOK=false;
uint16_t statusBase=0;
uint32_t irValue=0, redValue=0;
float ax_g=0, ay_g=0, az_g=1, gx_dps=0, gy_dps=0, gz_dps=0;
float ax_bias=0, ay_bias=0, az_bias=0, gx_bias=0, gy_bias=0, gz_bias=0;
float temp0=NAN, temp1=NAN;
int gsrRaw=0;
unsigned long lastPPG=0,lastIMU=0,lastGSR=0,lastTempRequest=0,lastTempReady=0,lastPacket=0;
bool tempPending=false;

BLECharacteristic* notifyCharacteristic=nullptr;
bool bleConnected=false;
char cmdBuf[48];
uint8_t cmdIdx=0;

uint8_t xorCRC(const char* text){
  uint8_t c=0;
  while(*text) c ^= (uint8_t)(*text++);
  return c;
}

void setLed(bool on){ digitalWrite(STATUS_LED_PIN,on ? HIGH : LOW); }

class ServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer*) override { bleConnected=true; setLed(true); }
  void onDisconnect(BLEServer*) override {
    bleConnected=false;
    setLed(false);
    BLEDevice::startAdvertising();
  }
};

void bleNotifyLine(const char* line){
  if(!bleConnected || !notifyCharacteristic) return;
  const size_t maxChunk=180;
  const size_t len=strlen(line);
  for(size_t i=0;i<len;i+=maxChunk){
    size_t n=min(maxChunk,len-i);
    notifyCharacteristic->setValue((uint8_t*)(line+i), n);
    notifyCharacteristic->notify();
    delay(2);
  }
}

void setupBLE(){
  BLEDevice::init(BLE_DEVICE_NAME);
  BLEServer* server=BLEDevice::createServer();
  server->setCallbacks(new ServerCallbacks());
  BLEService* service=server->createService(BLE_SERVICE_UUID);
  notifyCharacteristic=service->createCharacteristic(BLE_NOTIFY_UUID, BLECharacteristic::PROPERTY_NOTIFY);
  notifyCharacteristic->addDescriptor(new BLE2902());
  BLECharacteristic* command=service->createCharacteristic(BLE_COMMAND_UUID, BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_WRITE_NR);
  class CmdCallbacks : public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic* c) override {
      std::string value=c->getValue();
      String cmd="";
      for(char ch:value.c_str()) cmd += ch;
      cmd.trim();
      if(cmd=="PING") Serial.println("$ACK,PONG,00");
      else if(cmd=="WHOAMI") Serial.println("$ACK,WHOAMI,ENDO-TWIN-ESP32");
      else if(cmd=="LED,G"){ setLed(true); Serial.println("$ACK,LED,G"); }
      else if(cmd=="LED,Y"){ setLed(false); Serial.println("$ACK,LED,Y"); }
    }
  };
  command->setCallbacks(new CmdCallbacks());
  service->start();
  BLEAdvertising* advertising=BLEDevice::getAdvertising();
  advertising->addServiceUUID(BLE_SERVICE_UUID);
  advertising->setScanResponse(true);
  advertising->setMinPreferred(0x06);
  advertising->setMinPreferred(0x12);
  BLEDevice::startAdvertising();
}

void setupPPG(){
  if(!particleSensor.begin(Wire,I2C_SPEED_FAST)){ ppgOK=false; statusBase|=(1<<ST_I2C_ERR); return; }
  ppgOK=true;
  particleSensor.setup(0x24,4,2,100,411,4096);
  particleSensor.setPulseAmplitudeRed(0x24);
  particleSensor.setPulseAmplitudeIR(0x24);
  particleSensor.setPulseAmplitudeGreen(0);
}
void setupMPU(){
  if(!mpu.begin()){ mpuOK=false; statusBase|=(1<<ST_MPU_ERR); return; }
  mpuOK=true;
  mpu.setAccelerometerRange(MPU6050_RANGE_4_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
}
void setupTemp(){
  tempSensor.begin();
  tempSensor.setResolution(10);
  tempSensor.setWaitForConversion(false);
  tempOK=tempSensor.getDeviceCount()>0;
  if(!tempOK) statusBase|=(1<<ST_TEMP_ERR);
}
void calibrateIMU(){
  if(!mpuOK) return;
  const int N=120; float sax=0,say=0,saz=0,sgx=0,sgy=0,sgz=0;
  for(int i=0;i<N;i++){
    sensors_event_t a,g,t; mpu.getEvent(&a,&g,&t);
    sax += a.acceleration.x/9.80665f; say += a.acceleration.y/9.80665f; saz += a.acceleration.z/9.80665f;
    sgx += g.gyro.x*57.29578f; sgy += g.gyro.y*57.29578f; sgz += g.gyro.z*57.29578f;
    delay(5);
  }
  ax_bias=sax/N; ay_bias=say/N; az_bias=(saz/N)-1.0f;
  gx_bias=sgx/N; gy_bias=sgy/N; gz_bias=sgz/N;
}
void readPPG(){ if(ppgOK){ redValue=particleSensor.getRed(); irValue=particleSensor.getIR(); } }
void readIMU(){
  if(!mpuOK) return;
  sensors_event_t a,g,t; mpu.getEvent(&a,&g,&t);
  ax_g=a.acceleration.x/9.80665f-ax_bias; ay_g=a.acceleration.y/9.80665f-ay_bias; az_g=a.acceleration.z/9.80665f-az_bias;
  gx_dps=g.gyro.x*57.29578f-gx_bias; gy_dps=g.gyro.y*57.29578f-gy_bias; gz_dps=g.gyro.z*57.29578f-gz_bias;
}
void temperatureTick(unsigned long now){
  if(!tempOK) return;
  if(!tempPending && now-lastTempRequest>=TEMP_REQUEST_PERIOD_MS){
    tempSensor.requestTemperatures();
    tempPending=true;
    lastTempRequest=now;
    lastTempReady=now+TEMP_CONVERSION_MS;
  }
  if(tempPending && now>=lastTempReady){
    temp0=tempSensor.getTempCByIndex(0);
    temp1=tempSensor.getDeviceCount()>1?tempSensor.getTempCByIndex(1):NAN;
    tempPending=false;
  }
}
uint16_t makeStatus(){
  uint16_t st=statusBase;
  if(ppgOK){
    if(irValue<5000) st|=(1<<ST_PPG_ABSENT);
    if(irValue>250000UL || redValue>250000UL) st|=(1<<ST_PPG_SAT);
  }
  if(tempOK && !(temp0>-20 && temp0<80)) st|=(1<<ST_TEMP_ERR);
  if(gsrRaw<5 || gsrRaw>1018) st|=(1<<ST_GSR_SAT);
  return st;
}
void sendPacket(){
  char ax[16],ay[16],az[16],gx[16],gy[16],gz[16],t0[16],t1[16];
  dtostrf(ax_g,1,4,ax); dtostrf(ay_g,1,4,ay); dtostrf(az_g,1,4,az);
  dtostrf(gx_dps,1,3,gx); dtostrf(gy_dps,1,3,gy); dtostrf(gz_dps,1,3,gz);
  dtostrf(temp0,1,2,t0); dtostrf(temp1,1,2,t1);
  char payload[240];
  uint16_t status=makeStatus();
  snprintf(payload,sizeof(payload),
    "$CP2,%lu,%lu,%lu,%s,%s,%s,%s,%s,%s,%s,%s,%d,0,0.00,0.0,-1,-1,-1,nan,nan,nan,0,%u",
    millis(),(unsigned long)irValue,(unsigned long)redValue,
    ax,ay,az,gx,gy,gz,t0,t1,gsrRaw,status);
  uint8_t crc=xorCRC(payload);
  char line[260];
  snprintf(line,sizeof(line),"%s,%02X\n",payload,crc);
  Serial.print(line);
  bleNotifyLine(line);
}
void handleUsbCommand(const char* cmd){
  if(!strcmp(cmd,"PING")) Serial.println("$ACK,PONG,00");
  else if(!strcmp(cmd,"WHOAMI")) Serial.println("$ACK,WHOAMI,ENDO-TWIN-ESP32");
  else if(!strcmp(cmd,"LED,G")) setLed(true);
  else if(!strcmp(cmd,"LED,Y")) setLed(false);
  else if(!strcmp(cmd,"LED,R")) setLed(true);
}
void readUsbCommands(){
  while(Serial.available()){
    char c=(char)Serial.read();
    if(c=='\n'||c=='\r'){
      if(cmdIdx){ cmdBuf[cmdIdx]=0; handleUsbCommand(cmdBuf); cmdIdx=0; }
    } else if(cmdIdx<sizeof(cmdBuf)-1) cmdBuf[cmdIdx++]=c;
  }
}
void setup(){
  pinMode(STATUS_LED_PIN,OUTPUT); setLed(false);
  Serial.begin(BAUD_RATE);
  Wire.begin(SDA_PIN,SCL_PIN); Wire.setClock(400000L); delay(200);
  setupPPG(); setupMPU(); setupTemp(); calibrateIMU();
  tempSensor.requestTemperatures(); tempPending=true; lastTempRequest=millis(); lastTempReady=millis()+TEMP_CONVERSION_MS;
  setupBLE();
  setLed(true);
}
void loop(){
  unsigned long now=millis();
  if(now-lastPPG>=PPG_PERIOD_MS){ lastPPG=now; readPPG(); }
  if(now-lastIMU>=IMU_PERIOD_MS){ lastIMU=now; readIMU(); }
  if(now-lastGSR>=GSR_PERIOD_MS){ lastGSR=now; gsrRaw=analogRead(GSR_PIN); }
  temperatureTick(now);
  if(now-lastPacket>=PACKET_PERIOD_MS){ lastPacket=now; sendPacket(); }
  readUsbCommands();
}
