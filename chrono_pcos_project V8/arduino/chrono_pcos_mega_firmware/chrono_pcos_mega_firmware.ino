/*
  ENDO-TWIN NEXUS / CHRONO-PCOS V8.7 — Arduino Mega 2560 sensor hub
  Optimized for smooth 20 Hz PC packets with non-blocking slow sensors.

  CORE WIRING
    I2C: SDA D20, SCL D21, common GND
    MAX30102: power/logic according to breakout specification + I2C
    MPU6050: power/logic according to breakout specification + I2C
    DS18B20: DATA D2, 4.7k DATA -> VCC pull-up
    GSR: AO A0

  OPTIONAL
    MAX4466 AO A1
    AD8232 OUT A2, LO+ D11, LO- D12
    FSR AO A3
    BH1750/BME280/SSD1306 share I2C
    Buttons D3/D4/D5
    LED G/Y/R D8/D9/D10 via 220 ohm
    Buzzer D6

  MEGA <-> ESP8266
    Mega TX1 D18 -> 5V->3.3V level shift -> ESP RX0 GPIO3
    Mega RX1 D19 <- ESP TX0 GPIO1
    Common GND
    The same $CP2 packet is written to USB Serial and Serial1.

  Protocol:
    $CP2,ms,ir,red,ax,ay,az,gx,gy,gz,temp0,temp1,gsr,micRaw,micRms,micPitch,ecg,fsr,lux,roomT,hum,press,buttons,status,crc
    115200 baud, 20 packets/s, XOR CRC of the payload including '$'.

  Medical safety: educational/research physiological acquisition only.
*/

#include <Wire.h>
#include "MAX30105.h"
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <OneWire.h>
#include <DallasTemperature.h>

#define USE_BH1750 1
#define USE_BME280 1
#define USE_OLED 1
#define MIRROR_TO_SERIAL1 1

#if USE_BH1750
  #include <BH1750.h>
  BH1750 lightMeter;
#endif
#if USE_BME280
  #include <Adafruit_BME280.h>
  Adafruit_BME280 bme;
#endif
#if USE_OLED
  #include <Adafruit_GFX.h>
  #include <Adafruit_SSD1306.h>
  Adafruit_SSD1306 display(128, 64, &Wire, -1);
#endif

#define ONE_WIRE_BUS 2
#define BTN_MODE 3
#define BTN_BASE 4
#define BTN_POST 5
#define BUZZER_PIN 6
#define LED_GREEN 8
#define LED_YELLOW 9
#define LED_RED 10
#define ECG_LO_PLUS 11
#define ECG_LO_MINUS 12
#define GSR_PIN A0
#define MIC_PIN A1
#define ECG_PIN A2
#define FSR_PIN A3

#define BAUD_RATE 115200
#define PPG_PERIOD_MS 20
#define IMU_PERIOD_MS 20
#define ANALOG_PERIOD_MS 20
#define TEMP_REQUEST_PERIOD_MS 1000
#define TEMP_CONVERSION_MS 200
#define ENV_PERIOD_MS 1000
#define MIC_INTERVAL_MS 100
#define MIC_SAMPLE_US 500
#define MIC_N 128
#define OLED_PERIOD_MS 1000
#define PACKET_PERIOD_MS 50

#define ST_PPG_ABSENT   0
#define ST_PPG_SAT      1
#define ST_MPU_ERR      2
#define ST_TEMP_ERR     3
#define ST_GSR_SAT      4
#define ST_I2C_ERR      5
#define ST_LOW_QUALITY  6
#define ST_ECG_LEADS    7
#define ST_BME_ERR      8
#define ST_OLED_ERR     9
#define ST_MIC_LOW      10
#define ST_FSR_ARTIFACT 11

MAX30105 particleSensor;
Adafruit_MPU6050 mpu;
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature tempSensor(&oneWire);

bool ppgOK=false, mpuOK=false, tempOK=false, lightOK=false, bmeOK=false, oledOK=false;
uint16_t statusBase=0;
uint32_t irValue=0, redValue=0;
float ax_g=0, ay_g=0, az_g=1, gx_dps=0, gy_dps=0, gz_dps=0;
float ax_bias=0, ay_bias=0, az_bias=0, gx_bias=0, gy_bias=0, gz_bias=0;
float temp0=NAN, temp1=NAN;
int gsrRaw=0, ecgRaw=0, fsrRaw=0, micRaw=0;
float micRms=0, micPitchHz=0;
float luxValue=-1, roomT=NAN, humidity=NAN, pressure=NAN;
uint8_t buttonMask=0;
char ledState='Y';

unsigned long lastPPG=0,lastIMU=0,lastAnalog=0,lastTempRequest=0,lastTempReady=0,lastEnv=0,lastOLED=0,lastPacket=0,lastMicStart=0;
bool tempPending=false;
bool micSampling=false;
uint16_t micIndex=0;
int16_t micBuffer[MIC_N];
unsigned long nextMicSampleUs=0;

char cmdBuf[48];
uint8_t cmdIdx=0;

uint8_t xorCRC(const char *s){ uint8_t c=0; while(*s)c^=(uint8_t)(*s++); return c; }
void setLedState(char s){ ledState=s; digitalWrite(LED_GREEN,s=='G'); digitalWrite(LED_YELLOW,s=='Y'); digitalWrite(LED_RED,s=='R'); }
void beepShort(){ tone(BUZZER_PIN,2200,120); }

void setupPins(){
  pinMode(LED_GREEN,OUTPUT); pinMode(LED_YELLOW,OUTPUT); pinMode(LED_RED,OUTPUT);
  pinMode(BUZZER_PIN,OUTPUT); pinMode(BTN_MODE,INPUT_PULLUP); pinMode(BTN_BASE,INPUT_PULLUP); pinMode(BTN_POST,INPUT_PULLUP);
  pinMode(ECG_LO_PLUS,INPUT); pinMode(ECG_LO_MINUS,INPUT); setLedState('Y');
}
void setupPPG(){
  if(!particleSensor.begin(Wire,I2C_SPEED_FAST)){ ppgOK=false; statusBase|=(1<<ST_I2C_ERR); return; }
  ppgOK=true; particleSensor.setup(0x28,4,2,100,411,4096); particleSensor.setPulseAmplitudeRed(0x28); particleSensor.setPulseAmplitudeIR(0x28); particleSensor.setPulseAmplitudeGreen(0);
}
void setupMPU(){
  if(!mpu.begin()){mpuOK=false;statusBase|=(1<<ST_MPU_ERR);return;}
  mpuOK=true; mpu.setAccelerometerRange(MPU6050_RANGE_4_G); mpu.setGyroRange(MPU6050_RANGE_500_DEG); mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
}
void setupTemp(){
  tempSensor.begin(); tempSensor.setResolution(10); tempSensor.setWaitForConversion(false);
  tempOK=tempSensor.getDeviceCount()>0; if(!tempOK) statusBase|=(1<<ST_TEMP_ERR);
}
void setupLight(){
#if USE_BH1750
  lightOK=lightMeter.begin(BH1750::CONTINUOUS_LOW_RES_MODE); if(!lightOK) statusBase|=(1<<ST_I2C_ERR);
#endif
}
void setupBME(){
#if USE_BME280
  bmeOK=bme.begin(0x76)||bme.begin(0x77); if(!bmeOK) statusBase|=(1<<ST_BME_ERR);
#endif
}
void setupOLED(){
#if USE_OLED
  oledOK=display.begin(SSD1306_SWITCHCAPVCC,0x3C); if(!oledOK){statusBase|=(1<<ST_OLED_ERR);return;}
  display.clearDisplay(); display.setTextColor(SSD1306_WHITE); display.setTextSize(1); display.setCursor(0,0); display.println("ENDO-TWIN MEGA V8.7"); display.println("Research prototype"); display.display();
#endif
}
void calibrateIMU(){
  if(!mpuOK)return;
  const int N=120; float sax=0,say=0,saz=0,sgx=0,sgy=0,sgz=0;
  for(int i=0;i<N;i++){ sensors_event_t a,g,t; mpu.getEvent(&a,&g,&t);
    sax+=a.acceleration.x/9.80665; say+=a.acceleration.y/9.80665; saz+=a.acceleration.z/9.80665;
    sgx+=g.gyro.x*57.29578; sgy+=g.gyro.y*57.29578; sgz+=g.gyro.z*57.29578; delay(5); }
  ax_bias=sax/N; ay_bias=say/N; az_bias=(saz/N)-1.0; gx_bias=sgx/N; gy_bias=sgy/N; gz_bias=sgz/N;
}
void readPPG(){ if(ppgOK){redValue=particleSensor.getRed();irValue=particleSensor.getIR();} }
void readIMU(){ if(!mpuOK)return; sensors_event_t a,g,t; mpu.getEvent(&a,&g,&t);
  ax_g=a.acceleration.x/9.80665-ax_bias; ay_g=a.acceleration.y/9.80665-ay_bias; az_g=a.acceleration.z/9.80665-az_bias;
  gx_dps=g.gyro.x*57.29578-gx_bias; gy_dps=g.gyro.y*57.29578-gy_bias; gz_dps=g.gyro.z*57.29578-gz_bias; }
void readAnalogSensors(){ gsrRaw=analogRead(GSR_PIN); ecgRaw=analogRead(ECG_PIN); fsrRaw=analogRead(FSR_PIN); buttonMask=0;
  if(digitalRead(BTN_MODE)==LOW)buttonMask|=1; if(digitalRead(BTN_BASE)==LOW)buttonMask|=2; if(digitalRead(BTN_POST)==LOW)buttonMask|=4; }

void temperatureTick(unsigned long now){
  if(!tempOK)return;
  if(!tempPending && now-lastTempRequest>=TEMP_REQUEST_PERIOD_MS){ tempSensor.requestTemperatures(); tempPending=true; lastTempRequest=now; lastTempReady=now+TEMP_CONVERSION_MS; }
  if(tempPending && now>=lastTempReady){ temp0=tempSensor.getTempCByIndex(0); temp1=tempSensor.getDeviceCount()>1?tempSensor.getTempCByIndex(1):NAN; tempPending=false; }
}
void startMicWindow(unsigned long now){ if(micSampling)return; if(now-lastMicStart<MIC_INTERVAL_MS)return;
  micSampling=true; micIndex=0; lastMicStart=now; nextMicSampleUs=micros(); }
void micTick(){
  if(!micSampling)return; unsigned long us=micros(); if((long)(us-nextMicSampleUs)<0)return;
  int v=analogRead(MIC_PIN); micRaw=v; micBuffer[micIndex++]=(int16_t)v; nextMicSampleUs+=MIC_SAMPLE_US;
  if(micIndex>=MIC_N){ long sum=0; for(uint16_t i=0;i<MIC_N;i++)sum+=micBuffer[i]; float mean=sum/(float)MIC_N, ss=0; int crossings=0,lastSign=0;
    for(uint16_t i=0;i<MIC_N;i++){float d=micBuffer[i]-mean; ss+=d*d; int sign=d>=0?1:-1; if(i>0&&sign!=lastSign)crossings++; lastSign=sign;}
    micRms=sqrt(ss/MIC_N); const float fs=1000000.0f/MIC_SAMPLE_US; micPitchHz=(crossings/2.0f)*(fs/MIC_N); if(micPitchHz<60||micPitchHz>400)micPitchHz=0; micSampling=false; }
}
uint16_t makeStatus(){ uint16_t st=statusBase;
  if(ppgOK){if(irValue<5000)st|=(1<<ST_PPG_ABSENT); if(irValue>250000UL||redValue>250000UL)st|=(1<<ST_PPG_SAT);}
  if(tempOK&&!(temp0>-20&&temp0<80))st|=(1<<ST_TEMP_ERR); if(gsrRaw<5||gsrRaw>1018)st|=(1<<ST_GSR_SAT);
  if(digitalRead(ECG_LO_PLUS)==HIGH||digitalRead(ECG_LO_MINUS)==HIGH)st|=(1<<ST_ECG_LEADS);
  if(micRms<2)st|=(1<<ST_MIC_LOW); if(fsrRaw<20||fsrRaw>1000)st|=(1<<ST_FSR_ARTIFACT); return st; }

void writePacketTo(Stream &out,const char *payload,uint8_t crc){ out.print(payload); out.print(','); if(crc<16)out.print('0'); out.println(crc,HEX); }
void sendPacket(){
  char fax[12],fay[12],faz[12],fgx[12],fgy[12],fgz[12],ft0[12],ft1[12],flux[12],frt[12],fhum[12],fpress[12],fmr[12],fmp[12];
  dtostrf(ax_g,1,4,fax);dtostrf(ay_g,1,4,fay);dtostrf(az_g,1,4,faz);dtostrf(gx_dps,1,3,fgx);dtostrf(gy_dps,1,3,fgy);dtostrf(gz_dps,1,3,fgz);
  dtostrf(temp0,1,2,ft0);dtostrf(temp1,1,2,ft1);dtostrf(luxValue,1,1,flux);dtostrf(roomT,1,2,frt);dtostrf(humidity,1,1,fhum);dtostrf(pressure,1,1,fpress);dtostrf(micRms,1,2,fmr);dtostrf(micPitchHz,1,1,fmp);
  char payload[260]; uint16_t st=makeStatus();
  snprintf(payload,sizeof(payload),"$CP2,%lu,%lu,%lu,%s,%s,%s,%s,%s,%s,%s,%s,%d,%d,%s,%s,%d,%d,%s,%s,%s,%s,%u,%u",
    millis(),(unsigned long)irValue,(unsigned long)redValue,fax,fay,faz,fgx,fgy,fgz,ft0,ft1,gsrRaw,micRaw,fmr,fmp,ecgRaw,fsrRaw,flux,frt,fhum,fpress,buttonMask,st);
  uint8_t crc=xorCRC(payload); writePacketTo(Serial,payload,crc);
#if MIRROR_TO_SERIAL1
  writePacketTo(Serial1,payload,crc);
#endif
}
void updateOLED(){
#if USE_OLED
  if(!oledOK)return; display.clearDisplay(); display.setTextSize(1); display.setCursor(0,0); display.println("ENDO-TWIN MEGA V8.7");
  display.print("IR:");display.print(irValue);display.print(" ECG:");display.println(ecgRaw); display.print("T0:");display.print(temp0,1);
  display.print(" GSR:");display.println(gsrRaw); display.print("FSR:");display.print(fsrRaw); display.print(" Mic:");display.println(micPitchHz,0); display.println("Research only"); display.display();
#endif
}
void handleCommand(const char *cmd){
  if(strncmp(cmd,"LED,G",5)==0)setLedState('G'); else if(strncmp(cmd,"LED,Y",5)==0)setLedState('Y'); else if(strncmp(cmd,"LED,R",5)==0)setLedState('R'); else if(strncmp(cmd,"BEEP",4)==0)beepShort();
  else if(strncmp(cmd,"PING",4)==0){Serial.println("$ACK,PONG,00");
#if MIRROR_TO_SERIAL1
    Serial1.println("$ACK,PONG,00");
#endif
  }
}
void readCommandsFrom(Stream &in){ while(in.available()){ char c=(char)in.read();
  if(c=='\n'||c=='\r'){if(cmdIdx>0){cmdBuf[cmdIdx]=0;handleCommand(cmdBuf);cmdIdx=0;}}
  else if(cmdIdx<sizeof(cmdBuf)-1)cmdBuf[cmdIdx++]=c; } }
void readSerialCommands(){ readCommandsFrom(Serial);
#if MIRROR_TO_SERIAL1
  readCommandsFrom(Serial1);
#endif
}
void setup(){
  setupPins(); Serial.begin(BAUD_RATE); Serial1.begin(BAUD_RATE); Wire.begin(); Wire.setClock(400000L); delay(250);
  setupOLED(); setupPPG(); setupMPU(); setupTemp(); setupLight(); setupBME(); calibrateIMU();
  tempSensor.requestTemperatures(); tempPending=true; lastTempRequest=millis(); lastTempReady=millis()+TEMP_CONVERSION_MS;
  readEnvironment(); setLedState('G'); beepShort();
}
void loop(){
  unsigned long now=millis();
  if(now-lastPPG>=PPG_PERIOD_MS){lastPPG=now;readPPG();} if(now-lastIMU>=IMU_PERIOD_MS){lastIMU=now;readIMU();}
  if(now-lastAnalog>=ANALOG_PERIOD_MS){lastAnalog=now;readAnalogSensors();} temperatureTick(now);
  if(now-lastEnv>=ENV_PERIOD_MS){lastEnv=now;readEnvironment();} startMicWindow(now); micTick();
  if(now-lastOLED>=OLED_PERIOD_MS){lastOLED=now;updateOLED();} if(now-lastPacket>=PACKET_PERIOD_MS){lastPacket=now;sendPacket();}
  readSerialCommands();
}
