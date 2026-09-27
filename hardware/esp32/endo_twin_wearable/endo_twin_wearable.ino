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

  Person-specific calibration:
    PPG_PERSON=<ID>
    PPG_NEW_PERSON
    PPG_CAL
    $PCAL,<profile>,<baseline>,<noise>,<p2p>,<quality>,<ms>
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
static constexpr uint32_t PPG_PERIOD_MS = 20;
static constexpr uint32_t IMU_PERIOD_MS = 20;
static constexpr uint32_t GSR_PERIOD_MS = 100;
static constexpr uint32_t TEMP_PERIOD_MS = 1000;
static constexpr uint32_t PACKET_PERIOD_MS = 50;
static constexpr uint32_t STATUS_PERIOD_MS = 2000;
static constexpr uint32_t ENV_PERIOD_MS = 1000;

#define ST_PPG_ABSENT 0
#define ST_PPG_SAT 1
#define ST_MPU_ERR 2
#define ST_TEMP_ERR 3
#define ST_GSR_SAT 4
#define ST_I2C_ERR 5
#define ST_LOW_QUALITY 6
#define ST_BME_ERR 8
#define ST_BH1750_ERR 12

static const char* SERVICE_UUID="7f300001-6c12-4f70-9e6b-8e9f7b8b1001";
static const char* DATA_UUID="7f300002-6c12-4f70-9e6b-8e9f7b8b1001";
static const char* CMD_UUID="7f300003-6c12-4f70-9e6b-8e9f7b8b1001";

MAX30105 ppg;
Adafruit_MPU6050 mpu;
OneWire ow(ONE_WIRE_BUS);
DallasTemperature tempSensor(&ow);
Adafruit_BME280 bme;
BH1750 lightMeter;
BLECharacteristic* dataChar=nullptr;
bool bleConnected=false, ppgOK=false, mpuOK=false, tempOK=false, analogPpgOK=false, bmeOK=false, lightOK=false;
uint16_t statusBase=0;
uint32_t ir=0, red=0;
int gsr=0;
float ax=0,ay=0,az=1,gx=0,gy=0,gz=0,temp0=NAN,roomT=NAN,humidity=NAN,pressure=NAN,luxValue=-1;
float axb=0,ayb=0,azb=0,gxb=0,gyb=0,gzb=0;
uint32_t lastPPG=0,lastIMU=0,lastGSR=0,lastTEMP=0,lastPACKET=0,lastStatus=0,lastENV=0;
float ppgBaseline=0,ppgFiltered=0,ppgAC=0,ppgNoise=0,ppgCalPeakToPeak=0,ppgWindowMin=4095,ppgWindowMax=0,ppgQuality=0,ppgBPM=0;
bool ppgCalibrated=false,ppgFingerDetected=false,ppgPeakArmed=false;
uint32_t ppgLastPeakMs=0,ppgWindowStartMs=0;
float ppgLastFiltered=0;
String commandBuffer;
Preferences ppgPrefs;
String ppgProfileId="default";

static void resetPPGProcessingState(){ppgFiltered=0;ppgAC=0;ppgWindowMin=4095;ppgWindowMax=0;ppgQuality=0;ppgBPM=0;ppgPeakArmed=false;ppgLastPeakMs=0;ppgWindowStartMs=millis();ppgLastFiltered=0;}
static int findPPGProfileSlot(const String& id,bool allocate){for(int slot=0;slot<4;slot++){String k=String("id")+slot;if(ppgPrefs.getString(k.c_str(),"")==id)return slot;}if(!allocate)return -1;for(int slot=0;slot<4;slot++){String k=String("id")+slot;if(ppgPrefs.getString(k.c_str(),"").length()==0)return slot;}return -1;}
static bool loadPPGProfile(const String& id){if(!ppgPrefs.begin("endo_ppg",true))return false;int slot=findPPGProfileSlot(id,false);bool exists=false;if(slot>=0){String ok=String("ok")+slot;exists=ppgPrefs.getBool(ok.c_str(),false);if(exists){ppgBaseline=ppgPrefs.getFloat((String("b")+slot).c_str(),0);ppgNoise=ppgPrefs.getFloat((String("n")+slot).c_str(),1);ppgCalPeakToPeak=ppgPrefs.getFloat((String("p")+slot).c_str(),0);ppgCalibrated=ppgBaseline>0;}}ppgPrefs.end();if(exists&&ppgCalibrated){resetPPGProcessingState();Serial.print("[PPG] Loaded personal profile: ");Serial.println(id);return true;}return false;}
static void savePPGProfile(const String& id){if(!ppgCalibrated)return;if(!ppgPrefs.begin("endo_ppg",false)){Serial.println("[PPG] ERROR: profile storage unavailable");return;}int slot=findPPGProfileSlot(id,true);if(slot<0){ppgPrefs.end();Serial.println("[PPG] ERROR: all 4 personal profile slots are full");return;}ppgPrefs.putString((String("id")+slot).c_str(),id);ppgPrefs.putBool((String("ok")+slot).c_str(),true);ppgPrefs.putFloat((String("b")+slot).c_str(),ppgBaseline);ppgPrefs.putFloat((String("n")+slot).c_str(),ppgNoise);ppgPrefs.putFloat((String("p")+slot).c_str(),ppgCalPeakToPeak);ppgPrefs.end();Serial.print("[PPG] Personal calibration saved for profile: ");Serial.println(id);}
static uint8_t crc8(const char* text){uint8_t c=0;while(*text)c^=(uint8_t)*text++;return c;}
static void scanI2C(){Serial.println("[I2C] Scanning SDA=GPIO8 SCL=GPIO9...");for(uint8_t a=1;a<127;a++){Wire.beginTransmission(a);if(Wire.endTransmission()==0){Serial.print("[I2C] FOUND 0x");if(a<16)Serial.print('0');Serial.println(a,HEX);}}}
static bool setupAnalogPPG(){pinMode(ANALOG_PPG_PIN,INPUT);analogSetPinAttenuation(ANALOG_PPG_PIN,ADC_11db);int sample=analogRead(ANALOG_PPG_PIN);analogPpgOK=sample>=0&&sample<=4095;Serial.print("[SENSOR] Analog PPG GPIO");Serial.print(ANALOG_PPG_PIN);Serial.print(" initial=");Serial.println(sample);return analogPpgOK;}
static void calibrateAnalogPPG(const String& profileId="default"){
 if(!analogPpgOK){Serial.println("[PPG] Calibration skipped: GPIO4 ADC unavailable");return;}
 Serial.println("[PPG] ANALOG PPG CALIBRATION");Serial.println("[PPG] Place one finger gently on the optical sensor.");Serial.println("[PPG] Keep the finger still for 5 seconds...");
 uint32_t start=millis(),count=0;double sum=0,sumSq=0;float minValue=4095,maxValue=0;
 while(millis()-start<5000){int raw=analogRead(ANALOG_PPG_PIN);sum+=raw;sumSq+=(double)raw*raw;if(raw<minValue)minValue=raw;if(raw>maxValue)maxValue=raw;count++;delay(PPG_PERIOD_MS);}
 if(!count){Serial.println("[PPG] Calibration FAILED: no samples");return;}
 float mean=(float)(sum/count);float variance=fmaxf(0.0f,(float)((sumSq/count)-(mean*mean)));float stddev=sqrtf(variance);float peakToPeak=maxValue-minValue;
 ppgBaseline=mean;ppgNoise=stddev;ppgCalPeakToPeak=peakToPeak;ppgCalibrated=true;ppgProfileId=profileId;resetPPGProcessingState();
 Serial.print("[PPG] Personal profile = ");Serial.println(profileId);Serial.print("[PPG] Baseline ADC = ");Serial.println(ppgBaseline,2);Serial.print("[PPG] Noise SD = ");Serial.println(ppgNoise,2);Serial.print("[PPG] Cal P2P = ");Serial.println(ppgCalPeakToPeak,2);
 if(ppgCalPeakToPeak<8)Serial.println("[PPG] WARNING: almost no optical waveform detected. Check finger contact, sensor LED, VCC, GND and GPIO4.");else Serial.println("[PPG] Calibration accepted.");
 savePPGProfile(profileId);
 float calQuality=fminf(100.0f,(ppgCalPeakToPeak/fmaxf(1.0f,ppgNoise))*20.0f);
 Serial.print("$PCAL,");Serial.print(profileId);Serial.print(",");Serial.print(ppgBaseline,3);Serial.print(",");Serial.print(ppgNoise,3);Serial.print(",");Serial.print(ppgCalPeakToPeak,3);Serial.print(",");Serial.print(calQuality,1);Serial.print(",");Serial.println((unsigned long)millis());
}
static void updateAnalogPPG(){float raw=(float)analogRead(ANALOG_PPG_PIN);ir=(uint32_t)raw;red=0;if(ppgBaseline<=0)ppgBaseline=raw;ppgBaseline+=0.01f*(raw-ppgBaseline);ppgAC=raw-ppgBaseline;ppgFiltered+=0.20f*(ppgAC-ppgFiltered);if(raw<ppgWindowMin)ppgWindowMin=raw;if(raw>ppgWindowMax)ppgWindowMax=raw;float dynamicThreshold=fmaxf(8.0f,ppgNoise*3.0f);ppgFingerDetected=fabsf(ppgFiltered)>dynamicThreshold;uint32_t now=millis();bool peak=(ppgLastFiltered>0)&&(ppgFiltered<ppgLastFiltered)&&(ppgLastFiltered>fmaxf(8.0f,ppgNoise*3.0f));if(peak&&(now-ppgLastPeakMs>=300)){if(ppgLastPeakMs){uint32_t ibi=now-ppgLastPeakMs;if(ibi>=300&&ibi<=2000){float bpm=60000.0f/ibi;if(ppgBPM<=0)ppgBPM=bpm;else ppgBPM=0.75f*ppgBPM+0.25f*bpm;}}ppgLastPeakMs=now;ppgPeakArmed=true;}ppgLastFiltered=ppgFiltered;if(now-ppgWindowStartMs>=1000){float p2p=ppgWindowMax-ppgWindowMin;float referenceNoise=fmaxf(1.0f,ppgNoise);float snrLike=p2p/referenceNoise;float q=0;if(p2p>=8)q+=20;if(p2p>=20)q+=20;if(p2p>=50)q+=20;if(snrLike>=3)q+=20;if(ppgBPM>=40&&ppgBPM<=180)q+=20;ppgQuality=fminf(100.0f,q);ppgWindowMin=raw;ppgWindowMax=raw;ppgWindowStartMs=now;if(ppgLastPeakMs==0||now-ppgLastPeakMs>5000)ppgBPM=0;}}
static void setupSensors(){
 if(ppg.begin(Wire,I2C_SPEED_FAST)){ppgOK=true;ppg.setup(0x24,4,2,100,411,4096);ppg.setPulseAmplitudeRed(0x24);ppg.setPulseAmplitudeIR(0x24);ppg.setPulseAmplitudeGreen(0);Serial.println("[SENSOR] MAX3010x: OK");}else{statusBase|=(1u<<ST_I2C_ERR);Serial.println("[SENSOR] MAX3010x: NOT FOUND");}
 setupAnalogPPG();
 if(mpu.begin()){mpuOK=true;mpu.setAccelerometerRange(MPU6050_RANGE_4_G);mpu.setGyroRange(MPU6050_RANGE_500_DEG);mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);Serial.println("[SENSOR] MPU6050: OK");}else{statusBase|=(1u<<ST_MPU_ERR);Serial.println("[SENSOR] MPU6050: NOT FOUND");}
 tempSensor.begin();if(tempSensor.getDeviceCount()>0){tempOK=true;Serial.println("[SENSOR] DS18B20: OK");}else{statusBase|=(1u<<ST_TEMP_ERR);Serial.println("[SENSOR] DS18B20: NOT FOUND");}
 lightOK=lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE,0x23,&Wire);if(!lightOK)lightOK=lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE,0x5C,&Wire);if(!lightOK)statusBase|=(1u<<ST_BH1750_ERR);
 bmeOK=bme.begin(0x76,&Wire);if(!bmeOK)bmeOK=bme.begin(0x77,&Wire);if(!bmeOK)statusBase|=(1u<<ST_BME_ERR);
}
static void calibrateIMU(){if(!mpuOK)return;const int N=160;float sx=0,sy=0,sz=0,sgx=0,sgy=0,sgz=0;for(int i=0;i<N;i++){sensors_event_t a,g,t;mpu.getEvent(&a,&g,&t);sx+=a.acceleration.x/9.80665f;sy+=a.acceleration.y/9.80665f;sz+=a.acceleration.z/9.80665f;sgx+=g.gyro.x*57.29578f;sgy+=g.gyro.y*57.29578f;sgz+=g.gyro.z*57.29578f;delay(8);}axb=sx/N;ayb=sy/N;azb=(sz/N)-1;gxb=sgx/N;gyb=sgy/N;gzb=sgz/N;}
static uint16_t getStatus(){uint16_t s=statusBase;if(ppgOK&&ir<5)s|=(1u<<ST_PPG_ABSENT);if(analogPpgOK&&ppgCalibrated&&ppgQuality<20)s|=(1u<<ST_LOW_QUALITY);if(ppgOK&&(ir>250000UL||red>250000UL))s|=(1u<<ST_PPG_SAT);if(tempOK&&!(temp0>-20&&temp0<80))s|=(1u<<ST_TEMP_ERR);if(gsr<5||gsr>4090)s|=(1u<<ST_GSR_SAT);return s;}
static String makePacket(){char ft0[16],ft1[16],frt[16],fhum[16],fpress[16],flux[16];if(isnan(temp0))snprintf(ft0,sizeof(ft0),"nan");else snprintf(ft0,sizeof(ft0),"%.2f",temp0);snprintf(ft1,sizeof(ft1),"nan");if(isnan(roomT))snprintf(frt,sizeof(frt),"nan");else snprintf(frt,sizeof(frt),"%.2f",roomT);if(isnan(humidity))snprintf(fhum,sizeof(fhum),"nan");else snprintf(fhum,sizeof(fhum),"%.1f",humidity);if(isnan(pressure))snprintf(fpress,sizeof(fpress),"nan");else snprintf(fpress,sizeof(fpress),"%.1f",pressure);snprintf(flux,sizeof(flux),"%.1f",luxValue);char payload[360];uint16_t s=getStatus();snprintf(payload,sizeof(payload),"$CP2,%lu,%lu,%lu,%.4f,%.4f,%.4f,%.3f,%.3f,%.3f,%s,%s,%d,0,0.00,0.0,-1,-1,%s,%s,%s,%s,0,%u",(unsigned long)millis(),(unsigned long)ir,(unsigned long)red,ax,ay,az,gx,gy,gz,ft0,ft1,gsr,flux,frt,fhum,fpress,s);uint8_t c=crc8(payload);char out[390];snprintf(out,sizeof(out),"%s,%02X",payload,c);return String(out);}
static void publishPacket(){String packet=makePacket();Serial.println(packet);if(bleConnected&&dataChar){dataChar->setValue(packet.c_str());dataChar->notify();}}
static void handleCommand(String c){c.trim();if(!c.length())return;if(c=="PING")Serial.println("$ACK,PONG,00");else if(c=="WHOAMI")Serial.println("ENDO-TWIN-ESP32-S3-WEARABLE");else if(c=="STATUS"){Serial.print("STATUS=");Serial.println(getStatus());}else if(c=="PPG_CAL"||c=="PPG_NEW_PERSON"){calibrateAnalogPPG(ppgProfileId);}else if(c.startsWith("PPG_PERSON=")){String id=c.substring(10);id.trim();if(id.length()){if(id.length()>12)id=id.substring(0,12);ppgProfileId=id;ppgCalibrated=false;if(!loadPPGProfile(id))Serial.println("[PPG] No saved calibration; send PPG_NEW_PERSON.");}}else if(c=="PPG_PROFILE"){Serial.print("[PPG] Active profile: ");Serial.println(ppgProfileId);Serial.print("[PPG] Calibrated: ");Serial.println(ppgCalibrated?"YES":"NO");}else Serial.println("$ACK,UNKNOWN_CMD,00");}
class ServerCB:public BLEServerCallbacks{void onConnect(BLEServer*)override{bleConnected=true;Serial.println("[BLE] Client connected");}void onDisconnect(BLEServer*)override{bleConnected=false;BLEDevice::startAdvertising();}};
class CmdCB:public BLECharacteristicCallbacks{void onWrite(BLECharacteristic* ch)override{String v=ch->getValue();if(v.length())handleCommand(v);}};
static void setupBLE(){BLEDevice::init("ENDO-TWIN-ESP32-S3");BLEServer* server=BLEDevice::createServer();server->setCallbacks(new ServerCB());BLEService* service=server->createService(SERVICE_UUID);dataChar=service->createCharacteristic(DATA_UUID,BLECharacteristic::PROPERTY_NOTIFY);dataChar->addDescriptor(new BLE2902());BLECharacteristic* cmd=service->createCharacteristic(CMD_UUID,BLECharacteristic::PROPERTY_WRITE|BLECharacteristic::PROPERTY_WRITE_NR);cmd->setCallbacks(new CmdCB());service->start();BLEAdvertising* adv=BLEDevice::getAdvertising();adv->addServiceUUID(SERVICE_UUID);adv->setScanResponse(true);adv->setMinPreferred(0x06);adv->setMinPreferred(0x12);BLEDevice::startAdvertising();}
void setup(){Serial.begin(BAUD_RATE);delay(1200);pinMode(STATUS_LED_PIN,OUTPUT);digitalWrite(STATUS_LED_PIN,LOW);Wire.begin(SDA_PIN,SCL_PIN);Wire.setClock(400000);scanI2C();analogReadResolution(12);analogSetPinAttenuation(GSR_PIN,ADC_11db);analogSetPinAttenuation(ANALOG_PPG_PIN,ADC_11db);setupSensors();calibrateIMU();if(analogPpgOK&&!ppgOK){if(!loadPPGProfile(ppgProfileId))calibrateAnalogPPG(ppgProfileId);}setupBLE();digitalWrite(STATUS_LED_PIN,HIGH);Serial.println("[READY] ENDO-TWIN-WEARABLE READY");Serial.println("[READY] Personal calibration: PPG_PERSON=<ID> then PPG_NEW_PERSON");}
void loop(){uint32_t now=millis();if(now-lastPPG>=PPG_PERIOD_MS){lastPPG=now;if(ppgOK){ir=ppg.getIR();red=ppg.getRed();}else if(analogPpgOK)updateAnalogPPG();else{ir=0;red=0;}}if(now-lastIMU>=IMU_PERIOD_MS){lastIMU=now;if(mpuOK){sensors_event_t a,g,t;mpu.getEvent(&a,&g,&t);ax=a.acceleration.x/9.80665f-axb;ay=a.acceleration.y/9.80665f-ayb;az=a.acceleration.z/9.80665f-azb;gx=g.gyro.x*57.29578f-gxb;gy=g.gyro.y*57.29578f-gyb;gz=g.gyro.z*57.29578f-gzb;}}if(now-lastGSR>=GSR_PERIOD_MS){lastGSR=now;gsr=analogRead(GSR_PIN);}if(now-lastENV>=ENV_PERIOD_MS){lastENV=now;if(lightOK)luxValue=lightMeter.readLightLevel();if(bmeOK){roomT=bme.readTemperature();humidity=bme.readHumidity();pressure=bme.readPressure()/100.0f;}}if(now-lastTEMP>=TEMP_PERIOD_MS){lastTEMP=now;if(tempOK){tempSensor.requestTemperatures();temp0=tempSensor.getTempCByIndex(0);}}if(now-lastPACKET>=PACKET_PERIOD_MS){lastPACKET=now;publishPacket();}if(now-lastStatus>=STATUS_PERIOD_MS){lastStatus=now;Serial.print("[STATUS] PPG=");Serial.print(ppgOK?"MAX3010x":(analogPpgOK?"ANALOG":"NONE"));Serial.print(" MPU=");Serial.print(mpuOK?"OK":"ERR");Serial.print(" TEMP=");Serial.print(tempOK?"OK":"ERR");Serial.print(" BME=");Serial.print(bmeOK?"OK":"ERR");Serial.print(" BH1750=");Serial.print(lightOK?"OK":"ERR");Serial.print(" GSR=");Serial.print(gsr);Serial.print(" PROFILE=");Serial.print(ppgProfileId);Serial.print(" RAW=");Serial.print(ir);Serial.print(" BASE=");Serial.print(ppgBaseline,1);Serial.print(" Q=");Serial.print(ppgQuality,0);Serial.print("% BPM=");Serial.print(ppgBPM,1);Serial.print(" STATUS=");Serial.println(getStatus());}}while(Serial.available()){char c=(char)Serial.read();if(c=='\n'||c=='\r'){if(commandBuffer.length())handleCommand(commandBuffer);commandBuffer="";}else if(commandBuffer.length()<64)commandBuffer+=c;}delay(1);}
