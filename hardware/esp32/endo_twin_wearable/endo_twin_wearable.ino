/*
  ENDO-TWIN ESP32 Wearable Firmware
  Primary wearable controller.

  PPG HARDWARE MIGRATION (V8.8):
    Legacy: MAX3010x optical PPG (IR + red over I2C)
    New: generic analog Pulse Sensor module shown in project BOM/screenshot.

  The new module provides a single analog pulse waveform. It does NOT provide
  IR/red optical channels, so SpO2 and legacy optical-specific features are marked
  unavailable rather than fabricated.

  Wiring for ESP32-S3 / ESP32-class board:
    Pulse Sensor SIG -> PULSE_PIN
    Pulse Sensor VCC -> 3V3 (use the sensor/module voltage rating)
    Pulse Sensor GND -> GND
    MPU6050 -> same I2C bus
    DS18B20 -> ONE_WIRE_BUS with required pull-up
    GSR -> GSR_PIN (optional)

  BLE packets keep the existing $CP2 transport for compatibility. The legacy
  ir field carries the analog pulse sample and red is set to -1. The desktop
  parser/data model now interprets this as analog PPG when source metadata says
  ANALOG_PULSE.

  Safety: educational physiological monitoring only. Not a diagnostic medical
  device. Do not claim SpO2 or diagnostic accuracy from this sensor.
*/

#include <Arduino.h>
#include <Wire.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// ESP32-safe default pins. Change PULSE_PIN to the ADC-capable GPIO actually
// wired on your board. GPIO34 works on classic ESP32 but is input-only.
// ESP32-S3 boards have different ADC-capable pin maps, so configure locally.
static constexpr uint8_t SDA_PIN=21, SCL_PIN=22, PULSE_PIN=4, ONE_WIRE_BUS=18, GSR_PIN=5, STATUS_LED=2;
static constexpr uint32_t BAUD_RATE=115200;
static constexpr uint32_t PULSE_PERIOD_MS=20;   // 50 Hz packet-facing sample
static constexpr uint32_t IMU_PERIOD_MS=20;     // 50 Hz
static constexpr uint32_t GSR_PERIOD_MS=100;    // 10 Hz
static constexpr uint32_t TEMP_PERIOD_MS=1000;  // 1 Hz
static constexpr uint32_t PACKET_PERIOD_MS=50;  // 20 Hz

#define ST_PPG_ABSENT 0
#define ST_PPG_SAT 1
#define ST_MPU_ERR 2
#define ST_TEMP_ERR 3
#define ST_GSR_SAT 4
#define ST_I2C_ERR 5
#define ST_PPG_ANALOG 12
#define ST_PPG_INVALID 13

static const char* SERVICE_UUID="7f300001-6c12-4f70-9e6b-8e9f7b8b1001";
static const char* DATA_UUID="7f300002-6c12-4f70-9e6b-8e9f7b8b1001";
static const char* CMD_UUID="7f300003-6c12-4f70-9e6b-8e9f7b8b1001";

Adafruit_MPU6050 mpu;
OneWire ow(ONE_WIRE_BUS);
DallasTemperature temp(&ow);

BLECharacteristic* dataChar=nullptr;
bool bleConnected=false;
bool mpuOK=false,tempOK=false;

uint16_t statusBase=0;
int pulseRaw=0;
int gsr=0;
float ax=0,ay=0,az=1,gx=0,gy=0,gz=0,temp0=NAN;
float axb=0,ayb=0,azb=0,gxb=0,gyb=0,gzb=0;

uint32_t lp=0,li=0,lg=0,lt=0,lpack=0;

uint8_t crc8(const char* s){
  uint8_t c=0;
  while(*s)c^=(uint8_t)(*s++);
  return c;
}

void setupSensors(){
  // Analog pulse sensor: no I2C initialization required.
  pinMode(PULSE_PIN, INPUT);
  analogReadResolution(12);
  #if defined(ADC_11db)
    analogSetPinAttenuation(PULSE_PIN, ADC_11db);
  #endif
  statusBase |= (1<<ST_PPG_ANALOG);

  if(mpu.begin()){
    mpuOK=true;
    mpu.setAccelerometerRange(MPU6050_RANGE_4_G);
    mpu.setGyroRange(MPU6050_RANGE_500_DEG);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  }else{
    statusBase|=(1<<ST_MPU_ERR);
  }

  temp.begin();
  tempOK=temp.getDeviceCount()>0;
  if(!tempOK) statusBase|=(1<<ST_TEMP_ERR);
}

void calibrateIMU(){
  if(!mpuOK)return;
  const int N=160;
  float sx=0,sy=0,sz=0,sgx=0,sgy=0,sgz=0;
  for(int i=0;i<N;i++){
    sensors_event_t a,g,t;
    mpu.getEvent(&a,&g,&t);
    sx+=a.acceleration.x/9.80665f;
    sy+=a.acceleration.y/9.80665f;
    sz+=a.acceleration.z/9.80665f;
    sgx+=g.gyro.x*57.29578f;
    sgy+=g.gyro.y*57.29578f;
    sgz+=g.gyro.z*57.29578f;
    delay(8);
  }
  axb=sx/N; ayb=sy/N; azb=sz/N-1.0f;
  gxb=sgx/N; gyb=sgy/N; gzb=sgz/N;
}

void readPulse(){
  pulseRaw=analogRead(PULSE_PIN);
}

void readIMU(){
  if(!mpuOK)return;
  sensors_event_t a,g,t;
  mpu.getEvent(&a,&g,&t);
  ax=a.acceleration.x/9.80665f-axb;
  ay=a.acceleration.y/9.80665f-ayb;
  az=a.acceleration.z/9.80665f-azb;
  gx=g.gyro.x*57.29578f-gxb;
  gy=g.gyro.y*57.29578f-gyb;
  gz=g.gyro.z*57.29578f-gzb;
}

void readGSR(){ gsr=analogRead(GSR_PIN); }

void readTemp(){
  if(!tempOK)return;
  temp.requestTemperatures();
  temp0=temp.getTempCByIndex(0);
}

uint16_t status(){
  uint16_t s=statusBase;
  if(pulseRaw<=0 || pulseRaw>=4095)s|=(1<<ST_PPG_INVALID);
  if(pulseRaw<20)s|=(1<<ST_PPG_ABSENT);
  if(pulseRaw>4075)s|=(1<<ST_PPG_SAT);
  if(tempOK && !(temp0>-20&&temp0<80))s|=(1<<ST_TEMP_ERR);
  if(gsr<5 || gsr>4090)s|=(1<<ST_GSR_SAT);
  return s;
}

String packet(){
  char t[16];
  if(isnan(temp0)) strcpy(t,"nan"); else snprintf(t,sizeof(t),"%.2f",temp0);

  // $CP2 compatibility mapping:
  //   ir = analog pulse waveform sample (0..4095)
  //   red = -1 because no optical red channel exists
  //   analog source is explicitly documented by status/provenance.
  char p[260];
  uint16_t s=status();
  snprintf(
    p,sizeof(p),
    "$CP2,%lu,%d,-1,%.4f,%.4f,%.4f,%.3f,%.3f,%.3f,%s,nan,%d,0,0.00,0.0,-1,-1,-1,nan,nan,nan,0,%u",
    (unsigned long)millis(), pulseRaw, ax,ay,az,gx,gy,gz,t,gsr,s
  );
  char out[280];
  uint8_t c=crc8(p);
  snprintf(out,sizeof(out),"%s,%02X",p,c);
  return String(out);
}

void publish(){
  String x=packet();
  Serial.println(x);
  if(bleConnected && dataChar){
    dataChar->setValue(x.c_str());
    dataChar->notify();
  }
}

void command(String c){
  c.trim();
  if(c=="PING"){
    Serial.println("$ACK,PONG,00");
  }else if(c=="WHOAMI"){
    Serial.println("ENDO-TWIN-ESP32-WEARABLE-ANALOG-PULSE");
  }
}

class ServerCB:public BLEServerCallbacks{
  void onConnect(BLEServer*)override{bleConnected=true;}
  void onDisconnect(BLEServer*)override{bleConnected=false;BLEDevice::startAdvertising();}
};

class CmdCB:public BLECharacteristicCallbacks{
  void onWrite(BLECharacteristic* ch)override{
    std::string v=ch->getValue();
    if(!v.empty())command(String(v.c_str()));
  }
};

void setupBLE(){
  BLEDevice::init("ENDO-TWIN-PULSE");
  BLEServer* s=BLEDevice::createServer();
  s->setCallbacks(new ServerCB());
  BLEService* svc=s->createService(SERVICE_UUID);

  dataChar=svc->createCharacteristic(DATA_UUID,BLECharacteristic::PROPERTY_NOTIFY);
  dataChar->addDescriptor(new BLE2902());

  BLECharacteristic* cmd=svc->createCharacteristic(
    CMD_UUID,
    BLECharacteristic::PROPERTY_WRITE|BLECharacteristic::PROPERTY_WRITE_NR
  );
  cmd->setCallbacks(new CmdCB());

  svc->start();
  BLEAdvertising* a=BLEDevice::getAdvertising();
  a->addServiceUUID(SERVICE_UUID);
  a->setScanResponse(true);
  a->setMinPreferred(0x06);
  a->setMinPreferred(0x12);
  BLEDevice::startAdvertising();
}

void setup(){
  pinMode(STATUS_LED,OUTPUT);
  Serial.begin(BAUD_RATE);
  Wire.begin(SDA_PIN,SCL_PIN);
  #if defined(ADC_11db)
    analogSetPinAttenuation(GSR_PIN, ADC_11db);
  #endif
  delay(300);
  setupSensors();
  calibrateIMU();
  setupBLE();
}

void loop(){
  uint32_t n=millis();
  if(n-lp>=PULSE_PERIOD_MS){lp=n;readPulse();}
  if(n-li>=IMU_PERIOD_MS){li=n;readIMU();}
  if(n-lg>=GSR_PERIOD_MS){lg=n;readGSR();}
  if(n-lt>=TEMP_PERIOD_MS){lt=n;readTemp();}
  if(n-lpack>=PACKET_PERIOD_MS){lpack=n;publish();}

  static String b;
  while(Serial.available()){
    char c=(char)Serial.read();
    if(c=='\n'||c=='\r'){
      if(b.length())command(b);
      b="";
    }else if(b.length()<48)b+=c;
  }
}
