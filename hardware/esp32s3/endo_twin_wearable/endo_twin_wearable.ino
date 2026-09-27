/* ENDO-TWIN NEXUS V9.0 — Adafruit Feather ESP32-S3 2MB PSRAM
   Primary analog wearable, CP3 transport, patient-specific PPG calibration.
   VERIFIED BOARD MAP:
     I2C SDA = GPIO8
     I2C SCL = GPIO9
     Analog PPG = GPIO4
     GSR AO = GPIO5
     DS18B20 DATA = GPIO6
     Status LED = LED_BUILTIN (board LED)
   I2C sensors: MPU6050 0x68/0x69, BME280 0x76/0x77, BH1750 0x23/0x5C.
   Commands: PPG_PERSON=<ID>, PPG_NEW_PERSON, PPG_CAL, PPG_PROFILE, SENSORS,
             PING, WHOAMI, CALIBRATE.
   CP3: $CP3,ms,ppg_raw,gsr_raw,ax,ay,az,gx,gy,gz,skinT,roomT,hum,press,lux,status,crc
*/
#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <Preferences.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <BH1750.h>
#include <Adafruit_BME280.h>
#include <math.h>

static constexpr uint8_t I2C_SDA_PIN=8, I2C_SCL_PIN=9;
static constexpr uint8_t ANALOG_PPG_PIN=4, GSR_PIN=5, ONE_WIRE_BUS=6;
static constexpr uint8_t STATUS_LED_PIN=LED_BUILTIN;
static constexpr uint32_t BAUD_RATE=115200, TCP_PORT=7777;
static constexpr uint32_t PPG_PERIOD_MS=50, IMU_PERIOD_MS=20, GSR_PERIOD_MS=50;
static constexpr uint32_t ENV_PERIOD_MS=500, TEMP_PERIOD_MS=1000, TEMP_CONVERSION_MS=200, PACKET_PERIOD_MS=50;

static const char* AP_NAME="ENDO-TWIN-S3";
static const char* AP_PASSWORD="endotwins3";

enum StatusBit : uint16_t {
  ST_PPG_LOW=0, ST_PPG_SAT=1, ST_MPU_ERR=2, ST_TEMP_ERR=3,
  ST_GSR_SAT=4, ST_I2C_ERR=5, ST_LOW_QUALITY=6, ST_BME_ERR=8,
  ST_LIGHT_ERR=9
};

Adafruit_MPU6050 mpu;
BH1750 lightMeter;
Adafruit_BME280 bme;
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature tempSensor(&oneWire);
WiFiServer server(TCP_PORT);
WiFiClient tcpClient;
Preferences prefs;

bool mpuOK=false,bmeOK=false,lightOK=false,tempOK=false,tempValid=false;
bool tempPending=false;
uint16_t statusBase=0;
uint16_t ppgRaw=0,gsrRaw=0;
float ax_g=0,ay_g=0,az_g=1,gx_dps=0,gy_dps=0,gz_dps=0;
float axBias=0,ayBias=0,azBiasError=0,gxBias=0,gyBias=0,gzBias=0;
float skinTemp=NAN,roomTemp=NAN,humidity=NAN,pressure=NAN,luxValue=NAN;
uint32_t lastPPG=0,lastIMU=0,lastGSR=0,lastEnv=0,lastTempRequest=0,lastTempRead=0,lastPacket=0,lastStatus=0,lastSensorRetry=0;
uint32_t tempRequestStarted=0;
bool i2cInitAttempted=false;

String commandBuffer;
String ppgProfileId="default";
float ppgBaseline=0,ppgNoise=0,ppgP2P=0;
bool ppgCalibrated=false;

static uint8_t xorCRC(const char* s){uint8_t c=0;while(*s)c^=(uint8_t)*s++;return c;}
static void setLed(bool on){pinMode(STATUS_LED_PIN,OUTPUT);digitalWrite(STATUS_LED_PIN,on?HIGH:LOW);}

static bool probeI2C(uint8_t address){
  Wire.beginTransmission(address);
  return Wire.endTransmission()==0;
}

static void scanKnownI2C(){
  Serial.println("[I2C] Known-device scan:");
  const uint8_t addresses[]={0x23,0x5C,0x68,0x69,0x76,0x77,0x36,0x0B,0x57};
  const char* names[]={"BH1750","BH1750","MPU6050","MPU6050","BME280","BME280","MAX17048","LC709203","MAX30102"};
  for(size_t i=0;i<sizeof(addresses);++i){
    if(probeI2C(addresses[i])){
      Serial.print("[I2C] FOUND ");Serial.print(names[i]);Serial.print(" 0x");
      if(addresses[i]<16)Serial.print('0');
      Serial.println(addresses[i],HEX);
    }
  }
}

static uint16_t readADCMedian(uint8_t pin){
  uint16_t v[5];
  for(int i=0;i<5;i++){v[i]=(uint16_t)analogRead(pin);delayMicroseconds(80);}
  for(int i=1;i<5;i++){uint16_t k=v[i];int j=i-1;while(j>=0&&v[j]>k){v[j+1]=v[j];--j;}v[j+1]=k;}
  return v[2];
}

static int profileSlot(const String& id,bool allocate){
  for(int s=0;s<4;s++){String k="id"+String(s);if(prefs.getString(k.c_str(),"")==id)return s;}
  if(!allocate)return -1;
  for(int s=0;s<4;s++){String k="id"+String(s);if(prefs.getString(k.c_str(),"").length()==0)return s;}
  return -1;
}
static bool loadPPGProfile(const String& id){
  if(!prefs.begin("endo_ppg",true))return false;
  int s=profileSlot(id,false);bool ok=false;
  if(s>=0){ok=prefs.getBool((String("ok")+s).c_str(),false);
    if(ok){ppgBaseline=prefs.getFloat((String("b")+s).c_str(),0);
      ppgNoise=prefs.getFloat((String("n")+s).c_str(),1);
      ppgP2P=prefs.getFloat((String("p")+s).c_str(),0);
      ppgCalibrated=ppgBaseline>0;
    }}
  prefs.end();return ok&&ppgCalibrated;
}
static void savePPGProfile(const String& id){
  if(!ppgCalibrated)return;
  if(!prefs.begin("endo_ppg",false))return;
  int s=profileSlot(id,true);
  if(s<0){prefs.end();Serial.println("[PPG] ERROR: profile slots full");return;}
  prefs.putString((String("id")+s).c_str(),id);
  prefs.putBool((String("ok")+s).c_str(),true);
  prefs.putFloat((String("b")+s).c_str(),ppgBaseline);
  prefs.putFloat((String("n")+s).c_str(),ppgNoise);
  prefs.putFloat((String("p")+s).c_str(),ppgP2P);
  prefs.end();
}
static void calibratePPG(const String& id){
  Serial.println("[PPG] PERSONAL CALIBRATION — place finger gently and stay still for 5 s");
  uint32_t start=millis(),count=0;double sum=0,sumSq=0;float mn=4095,mx=0;
  while(millis()-start<5000){
    int raw=analogRead(ANALOG_PPG_PIN);
    sum+=raw;sumSq+=(double)raw*raw;if(raw<mn)mn=raw;if(raw>mx)mx=raw;
    count++;delay(10);
  }
  if(!count){Serial.println("[PPG] FAILED: no ADC samples");return;}
  ppgBaseline=(float)(sum/count);
  float var=fmaxf(0.0f,(float)((sumSq/count)-(ppgBaseline*ppgBaseline)));
  ppgNoise=sqrtf(var);ppgP2P=mx-mn;ppgCalibrated=ppgBaseline>0;ppgProfileId=id;savePPGProfile(id);
  float q=fminf(100.0f,(ppgP2P/fmaxf(1.0f,ppgNoise))*20.0f);
  Serial.print("[PPG] profile=");Serial.println(id);
  Serial.print("[PPG] baseline=");Serial.println(ppgBaseline,2);
  Serial.print("[PPG] noise=");Serial.println(ppgNoise,2);
  Serial.print("[PPG] p2p=");Serial.println(ppgP2P,2);
  Serial.print("[PPG] quality=");Serial.println(q,1);
  if(ppgP2P<8)Serial.println("[PPG] WARNING: very small waveform; check sensor power/wiring/contact.");
  char pcal[180];
  snprintf(pcal,sizeof(pcal),"$PCAL,%s,%.3f,%.3f,%.3f,%.1f,%lu",
           id.c_str(),ppgBaseline,ppgNoise,ppgP2P,q,(unsigned long)millis());
  Serial.println(pcal);
  if(tcpClient&&tcpClient.connected())tcpClient.println(pcal);
}
static void setupMPU(){
  mpuOK=mpu.begin(0x68,&Wire);
  if(!mpuOK)mpuOK=mpu.begin(0x69,&Wire);
  if(mpuOK){
    statusBase&=~(1u<<ST_MPU_ERR);
    mpu.setAccelerometerRange(MPU6050_RANGE_4_G);
    mpu.setGyroRange(MPU6050_RANGE_500_DEG);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  }else statusBase|=(1u<<ST_MPU_ERR);
}
static void setupEnv(){
  lightOK=lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE,0x23,&Wire);
  if(!lightOK)lightOK=lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE,0x5C,&Wire);
  if(lightOK)statusBase&=~(1u<<ST_LIGHT_ERR);else statusBase|=(1u<<ST_LIGHT_ERR);
  bmeOK=bme.begin(0x76,&Wire);
  if(!bmeOK)bmeOK=bme.begin(0x77,&Wire);
  if(bmeOK)statusBase&=~(1u<<ST_BME_ERR);else statusBase|=(1u<<ST_BME_ERR);
}
static void setupTemperature(){
  tempSensor.begin();
  tempSensor.setResolution(10);
  tempSensor.setWaitForConversion(false);
  tempOK=false;
  tempValid=false;
  const uint8_t count=tempSensor.getDeviceCount();
  Serial.print("[TEMP] devices on GPIO6: ");Serial.println(count);
  if(count>0){
    DeviceAddress addr;
    if(tempSensor.getAddress(addr,0)){
      Serial.print("[TEMP] DS18B20 ROM=");
      for(uint8_t i=0;i<8;i++){if(addr[i]<16)Serial.print('0');Serial.print(addr[i],HEX);}
      Serial.println();
      tempOK=true;
      statusBase&=~(1u<<ST_TEMP_ERR);
      tempSensor.requestTemperatures();
      tempPending=true;
      tempRequestStarted=millis();
      lastTempRequest=millis();
    }else{
      Serial.println("[TEMP] device count >0 but ROM address could not be read");
      statusBase|=(1u<<ST_TEMP_ERR);
    }
  }else{
    statusBase|=(1u<<ST_TEMP_ERR);
    Serial.println("[TEMP] DS18B20 not found on GPIO6; check DATA + 4.7k pull-up to 3V3");
  }
}
static void calibrateIMU(){
  if(!mpuOK)return;
  const int N=80;float sx=0,sy=0,sz=0,sgx=0,sgy=0,sgz=0;
  for(int i=0;i<N;i++){
    sensors_event_t a,g,t;mpu.getEvent(&a,&g,&t);
    sx+=a.acceleration.x/9.80665f;sy+=a.acceleration.y/9.80665f;sz+=a.acceleration.z/9.80665f;
    sgx+=g.gyro.x*57.29578f;sgy+=g.gyro.y*57.29578f;sgz+=g.gyro.z*57.29578f;delay(5);
  }
  axBias=sx/N;ayBias=sy/N;float zm=sz/N;azBiasError=zm-((zm>=0)?1.0f:-1.0f);
  gxBias=sgx/N;gyBias=sgy/N;gzBias=sgz/N;
}
static uint16_t makeStatus(){
  uint16_t st=statusBase;
  if(ppgRaw<30)st|=(1u<<ST_PPG_LOW);if(ppgRaw>4060)st|=(1u<<ST_PPG_SAT);
  if(gsrRaw<5||gsrRaw>4090)st|=(1u<<ST_GSR_SAT);
  if(ppgCalibrated && ppgP2P>0 && ppgRaw>ppgBaseline+fmaxf(8.0f,3.0f*ppgP2P))st|=(1u<<ST_LOW_QUALITY);
  if(!tempValid)st|=(1u<<ST_TEMP_ERR);
  return st;
}
static void sendPacket(){
  char ax[16],ay[16],az[16],gx[16],gy[16],gz[16],st[16],rt[16],hu[16],pr[16],lx[16];
  dtostrf(ax_g,1,4,ax);dtostrf(ay_g,1,4,ay);dtostrf(az_g,1,4,az);
  dtostrf(gx_dps,1,3,gx);dtostrf(gy_dps,1,3,gy);dtostrf(gz_dps,1,3,gz);
  dtostrf(skinTemp,1,2,st);dtostrf(roomTemp,1,2,rt);dtostrf(humidity,1,1,hu);dtostrf(pressure,1,1,pr);dtostrf(luxValue,1,1,lx);
  char payload[320];uint16_t status=makeStatus();
  // CP3 is always 17 comma-separated fields including CRC:
  // $CP3 + 15 data fields + crc.
  snprintf(payload,sizeof(payload),"$CP3,%lu,%u,%u,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%u",
    millis(),(unsigned)ppgRaw,(unsigned)gsrRaw,ax,ay,az,gx,gy,gz,st,rt,hu,pr,lx,(unsigned)status);
  char line[360];uint8_t crc=xorCRC(payload);
  snprintf(line,sizeof(line),"%s,%02X\n",payload,crc);
  Serial.print(line);if(tcpClient&&tcpClient.connected())tcpClient.print(line);
}
static void sendAck(const char* s){Serial.println(s);if(tcpClient&&tcpClient.connected())tcpClient.println(s);}
static void printSensorSummary(){
  Serial.print("[SENSORS] I2C pins SDA=");Serial.print(I2C_SDA_PIN);Serial.print(" SCL=");Serial.println(I2C_SCL_PIN);
  Serial.print("[SENSORS] PPG GPIO");Serial.print(ANALOG_PPG_PIN);Serial.print(" raw=");Serial.println(ppgRaw);
  Serial.print("[SENSORS] GSR GPIO");Serial.print(GSR_PIN);Serial.print(" raw=");Serial.println(gsrRaw);
  Serial.print("[SENSORS] DS18B20 GPIO");Serial.print(ONE_WIRE_BUS);Serial.print(" = ");Serial.println(tempOK?"OK":"ERR");
  Serial.print("[SENSORS] MPU6050=");Serial.print(mpuOK?"OK":"ERR");
  Serial.print(" BH1750=");Serial.print(lightOK?"OK":"ERR");
  Serial.print(" BME280=");Serial.println(bmeOK?"OK":"ERR");
}
static void handleCommand(String c){
  c.trim();if(!c.length())return;
  if(c=="PING")sendAck("$ACK,PONG,00");
  else if(c=="WHOAMI")sendAck("$ACK,WHOAMI,ENDO-TWIN-FEATHER-S3-ANALOG");
  else if(c=="SENSORS"){scanKnownI2C();printSensorSummary();}
  else if(c=="CALIBRATE"){calibrateIMU();sendAck("$ACK,CALIBRATE,IMU-RESET");}
  else if(c=="PPG_PROFILE"){Serial.print("[PPG] Active profile: ");Serial.println(ppgProfileId);Serial.print("[PPG] Calibrated: ");Serial.println(ppgCalibrated?"YES":"NO");}
  else if(c=="PPG_CAL"||c=="PPG_NEW_PERSON")calibratePPG(ppgProfileId);
  else if(c.startsWith("PPG_PERSON=")){
    String id=c.substring(11);id.trim();if(id.length()>24)id=id.substring(0,24);
    if(id.length()){ppgProfileId=id;ppgCalibrated=loadPPGProfile(id);Serial.print("[PPG] Active profile: ");Serial.println(id);Serial.println(ppgCalibrated?"[PPG] Saved calibration loaded":"[PPG] No saved calibration; send PPG_NEW_PERSON");}
  }else if(c=="LED,G")setLed(true);
  else if(c=="LED,Y"||c=="LED,R")setLed(false);
}
static void readCommands(Stream& s){while(s.available()){char c=(char)s.read();if(c=='\n'||c=='\r'){if(commandBuffer.length()){handleCommand(commandBuffer);commandBuffer="";}}else if(commandBuffer.length()<80)commandBuffer+=c;}}
static void setupWiFi(){WiFi.mode(WIFI_AP);WiFi.softAP(AP_NAME,AP_PASSWORD);delay(100);Serial.print("[WIFI] AP IP=");Serial.println(WiFi.softAPIP());server.begin();server.setNoDelay(true);}

void setup(){
  Serial.begin(BAUD_RATE);delay(1200);setLed(false);
  Serial.println("\n==============================================");
  Serial.println("ENDO-TWIN NEXUS V9.0 READY");
  Serial.println("ADAFRUIT FEATHER ESP32-S3 2MB PSRAM");
  Serial.println("USB SERIAL 115200 • CP3 • personal PPG calibration");
  Serial.println("==============================================");

#if defined(PIN_I2C_POWER)
  pinMode(PIN_I2C_POWER,OUTPUT);
  digitalWrite(PIN_I2C_POWER,HIGH);
  delay(25);
  Serial.print("[I2C] POWER PIN GPIO");Serial.print(PIN_I2C_POWER);Serial.println(" HIGH");
#endif

  Wire.begin(I2C_SDA_PIN,I2C_SCL_PIN);
  Wire.setClock(100000L);
  Wire.setTimeOut(25);
  Serial.print("[I2C] SDA=GPIO");Serial.print(I2C_SDA_PIN);Serial.print(" SCL=GPIO");Serial.println(I2C_SCL_PIN);

  analogReadResolution(12);
  analogSetPinAttenuation(ANALOG_PPG_PIN,ADC_11db);
  analogSetPinAttenuation(GSR_PIN,ADC_11db);
  pinMode(ANALOG_PPG_PIN,INPUT);
  pinMode(GSR_PIN,INPUT);

  if(!prefs.begin("endo_ppg",true)){Serial.println("[PPG] Preferences unavailable");}
  else{prefs.end();loadPPGProfile(ppgProfileId);}

  tempSensor.begin();
  setupWiFi();
  setLed(true);
  Serial.println("[READY] Streaming $CP3 every 50 ms");
  Serial.println("[READY] PPG_PERSON=<ID> then PPG_NEW_PERSON");
  Serial.println("[READY] I2C/temperature probing deferred until stream is live");
}

void loop(){
  uint32_t now=millis();

  if(!i2cInitAttempted && now>=1500){
    i2cInitAttempted=true;
    Serial.println("[SENSORS] Initializing optional + temperature sensors...");
    scanKnownI2C();
    setupMPU();
    setupEnv();
    setupTemperature();
    calibrateIMU();
    printSensorSummary();
  }
  if(i2cInitAttempted && now-lastSensorRetry>=5000){
    lastSensorRetry=now;
    if(!mpuOK || !bmeOK || !lightOK){
      Serial.println("[SENSORS] Retrying missing I2C devices...");
      setupMPU();
      setupEnv();
    }
    if(!tempOK) setupTemperature();
  }

  WiFiClient in=server.available();
  if(in){
    if(tcpClient&&tcpClient.connected())tcpClient.stop();
    tcpClient=in;tcpClient.setNoDelay(true);
    tcpClient.println("$ACK,CONNECTED,ENDO-TWIN-FEATHER-S3-ANALOG");
  }

  if(now-lastPPG>=PPG_PERIOD_MS){lastPPG=now;ppgRaw=readADCMedian(ANALOG_PPG_PIN);}
  if(now-lastGSR>=GSR_PERIOD_MS){lastGSR=now;gsrRaw=readADCMedian(GSR_PIN);}

  if(now-lastIMU>=IMU_PERIOD_MS){
    lastIMU=now;
    if(mpuOK){
      sensors_event_t a,g,t;mpu.getEvent(&a,&g,&t);
      ax_g=a.acceleration.x/9.80665f-axBias;ay_g=a.acceleration.y/9.80665f-ayBias;
      az_g=a.acceleration.z/9.80665f-azBiasError;
      gx_dps=g.gyro.x*57.29578f-gxBias;gy_dps=g.gyro.y*57.29578f-gyBias;gz_dps=g.gyro.z*57.29578f-gzBias;
    }
  }

  if(now-lastEnv>=ENV_PERIOD_MS){
    lastEnv=now;
    if(lightOK){float v=lightMeter.readLightLevel();if(isfinite(v))luxValue=v;}
    if(bmeOK){
      float t=bme.readTemperature(),h=bme.readHumidity(),p=bme.readPressure()/100.0f;
      if(isfinite(t))roomTemp=t;if(isfinite(h))humidity=h;if(isfinite(p))pressure=p;
    }
  }

  if(!tempOK && now-lastTempRequest>=5000){
    lastTempRequest=now;
    setupTemperature();
  }
  if(!tempPending && tempOK && now-lastTempRequest>=TEMP_PERIOD_MS){
    tempSensor.requestTemperatures();
    tempPending=true;
    tempRequestStarted=now;
    lastTempRequest=now;
  }
  if(tempPending && now-tempRequestStarted>=TEMP_CONVERSION_MS){
    const float t=tempSensor.getTempCByIndex(0);
    tempPending=false;
    if(t!=DEVICE_DISCONNECTED_C && isfinite(t) && t>-55.0f && t<125.0f){
      skinTemp=t;
      tempValid=true;
      tempOK=true;
      statusBase&=~(1u<<ST_TEMP_ERR);
    }else{
      tempValid=false;
      statusBase|=(1u<<ST_TEMP_ERR);
      Serial.print("[TEMP] invalid DS18B20 reading: ");
      Serial.println(t);
    }
  }

  if(now-lastPacket>=PACKET_PERIOD_MS){lastPacket=now;sendPacket();}

  if(now-lastStatus>=2000){
    lastStatus=now;
    Serial.print("[STATUS] PPG_RAW=");Serial.print(ppgRaw);
    Serial.print(" GSR=");Serial.print(gsrRaw);
    Serial.print(" MPU=");Serial.print(mpuOK?"OK":"ERR");
    Serial.print(" DS18B20=");Serial.print(tempValid?"OK":"ERR");
    Serial.print(" BME=");Serial.print(bmeOK?"OK":"ERR");
    Serial.print(" BH1750=");Serial.print(lightOK?"OK":"ERR");
    Serial.print(" skinT=");Serial.print(skinTemp,2);
    Serial.print(" roomT=");Serial.print(roomTemp,2);
    Serial.print(" lux=");Serial.print(luxValue,1);
    Serial.print(" PROFILE=");Serial.print(ppgProfileId);
    Serial.print(" STATUS=");Serial.println(makeStatus());
  }

  readCommands(Serial);
  if(tcpClient&&tcpClient.connected())readCommands(tcpClient);
  else if(tcpClient)tcpClient.stop();
  delay(1);
}