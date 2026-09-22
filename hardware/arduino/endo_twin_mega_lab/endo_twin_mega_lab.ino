/*
  ENDO-TWIN NEXUS V8.7 — Arduino Mega 2560 BENCH / LAB CONTROLLER
  -----------------------------------------------------------------
  Active bench controller for expanded sensor experiments and diagnostics.
  It is NOT the wearable and does not bridge through another controller.

  I2C SDA D20, SCL D21
  DS18B20 DATA D2 + 4.7k pull-up to sensor supply
  GSR A0
  MAX4466 A1 (optional)
  AD8232 OUT A2, LO+ D11, LO- D12 (optional)
  FSR A3 (optional)
  Buttons D3/D4/D5, LEDs D8/D9/D10, buzzer D6
  USB Serial 115200

  Canonical packet:
  $CP2,ms,ir,red,ax,ay,az,gx,gy,gz,temp0,temp1,gsr,micRaw,micRms,micPitch,ecg,fsr,lux,roomT,hum,press,buttons,status,crc

  Educational/research acquisition only. Not a diagnostic medical device.
*/

#include <Wire.h>
#include "MAX30105.h"
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <BH1750.h>
#include <Adafruit_BME280.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <math.h>

#define BAUD_RATE 115200
#define ONE_WIRE_BUS 2
#define GSR_PIN A0
#define MIC_PIN A1
#define ECG_PIN A2
#define FSR_PIN A3
#define ECG_LO_PLUS 11
#define ECG_LO_MINUS 12
#define BTN_MODE 3
#define BTN_BASE 4
#define BTN_POST 5
#define BUZZER_PIN 6
#define LED_GREEN 8
#define LED_YELLOW 9
#define LED_RED 10
#define PACKET_PERIOD_MS 50
#define IMU_PERIOD_MS 20
#define PPG_PERIOD_MS 20
#define ANALOG_PERIOD_MS 20
#define TEMP_REQUEST_PERIOD_MS 1000
#define TEMP_CONVERSION_MS 200
#define ENV_PERIOD_MS 1000
#define OLED_PERIOD_MS 1000
#define MIC_INTERVAL_MS 100
#define MIC_SAMPLE_US 500
#define MIC_N 128

enum StatusBit {
  ST_PPG_ABSENT=0, ST_PPG_SAT=1, ST_MPU_ERR=2, ST_TEMP_ERR=3,
  ST_GSR_SAT=4, ST_I2C_ERR=5, ST_LOW_QUALITY=6, ST_ECG_LEADS=7,
  ST_BME_ERR=8, ST_OLED_ERR=9, ST_MIC_LOW=10, ST_FSR_ARTIFACT=11
};

MAX30105 particleSensor;
Adafruit_MPU6050 mpu;
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature tempSensor(&oneWire);
BH1750 lightMeter;
Adafruit_BME280 bme;
Adafruit_SSD1306 display(128,64,&Wire,-1);

bool ppgOK=false,mpuOK=false,tempOK=false,lightOK=false,bmeOK=false,oledOK=false;
uint16_t statusBase=0;
uint32_t irValue=0,redValue=0;
float ax_g=0,ay_g=0,az_g=1,gx_dps=0,gy_dps=0,gz_dps=0;
float ax_bias=0,ay_bias=0,az_bias=0,gx_bias=0,gy_bias=0,gz_bias=0;
float temp0=NAN,temp1=NAN,luxValue=NAN,roomT=NAN,humidity=NAN,pressure=NAN,micRms=0,micPitchHz=0;
int gsrRaw=0,micRaw=0,ecgRaw=-1,fsrRaw=-1;
uint8_t buttonMask=0;
unsigned long lastPPG=0,lastIMU=0,lastAnalog=0,lastTempRequest=0,lastTempReady=0,lastEnv=0,lastOLED=0,lastPacket=0,lastMic=0;
bool tempPending=false;
char cmdBuf[48]; uint8_t cmdIdx=0;
int16_t micBuffer[MIC_N]; uint16_t micIndex=0; bool micSampling=false; unsigned long nextMicUs=0;

uint8_t xorCRC(const char*s){uint8_t c=0;while(*s)c^=(uint8_t)(*s++);return c;}
void setLed(char s){digitalWrite(LED_GREEN,s=='G');digitalWrite(LED_YELLOW,s=='Y');digitalWrite(LED_RED,s=='R');}
void beep(){tone(BUZZER_PIN,2200,120);}
void setupSensors(){
  if(!particleSensor.begin(Wire,I2C_SPEED_FAST)){statusBase|=(1<<ST_I2C_ERR);} else {ppgOK=true;particleSensor.setup(0x28,4,2,100,411,4096);}
  if(!mpu.begin()){statusBase|=(1<<ST_MPU_ERR);} else {mpuOK=true;mpu.setAccelerometerRange(MPU6050_RANGE_4_G);mpu.setGyroRange(MPU6050_RANGE_500_DEG);mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);}
  tempSensor.begin();tempSensor.setResolution(10);tempSensor.setWaitForConversion(false);tempOK=tempSensor.getDeviceCount()>0;if(!tempOK)statusBase|=(1<<ST_TEMP_ERR);
  lightOK=lightMeter.begin(BH1750::CONTINUOUS_LOW_RES_MODE);if(!lightOK)statusBase|=(1<<ST_I2C_ERR);
  bmeOK=bme.begin(0x76)||bme.begin(0x77);if(!bmeOK)statusBase|=(1<<ST_BME_ERR);
  oledOK=display.begin(SSD1306_SWITCHCAPVCC,0x3C);if(!oledOK)statusBase|=(1<<ST_OLED_ERR);
}
void calibrate(){
  if(!mpuOK)return;const int N=100;float sax=0,say=0,saz=0,sgx=0,sgy=0,sgz=0;
  for(int i=0;i<N;i++){sensors_event_t a,g,t;mpu.getEvent(&a,&g,&t);sax+=a.acceleration.x/9.80665f;say+=a.acceleration.y/9.80665f;saz+=a.acceleration.z/9.80665f;sgx+=g.gyro.x*57.29578f;sgy+=g.gyro.y*57.29578f;sgz+=g.gyro.z*57.29578f;delay(5);}
  ax_bias=sax/N;ay_bias=say/N;az_bias=saz/N-1.0f;gx_bias=sgx/N;gy_bias=sgy/N;gz_bias=sgz/N;
}
void readPPG(){if(ppgOK){irValue=particleSensor.getIR();redValue=particleSensor.getRed();}}
void readIMU(){if(!mpuOK)return;sensors_event_t a,g,t;mpu.getEvent(&a,&g,&t);ax_g=a.acceleration.x/9.80665f-ax_bias;ay_g=a.acceleration.y/9.80665f-ay_bias;az_g=a.acceleration.z/9.80665f-az_bias;gx_dps=g.gyro.x*57.29578f-gx_bias;gy_dps=g.gyro.y*57.29578f-gy_bias;gz_dps=g.gyro.z*57.29578f-gz_bias;}
void readAnalog(){gsrRaw=analogRead(GSR_PIN);ecgRaw=analogRead(ECG_PIN);fsrRaw=analogRead(FSR_PIN);buttonMask=0;if(digitalRead(BTN_MODE)==LOW)buttonMask|=1;if(digitalRead(BTN_BASE)==LOW)buttonMask|=2;if(digitalRead(BTN_POST)==LOW)buttonMask|=4;}
void tempTick(unsigned long now){if(!tempOK)return;if(!tempPending&&now-lastTempRequest>=TEMP_REQUEST_PERIOD_MS){tempSensor.requestTemperatures();tempPending=true;lastTempRequest=now;lastTempReady=now+TEMP_CONVERSION_MS;}if(tempPending&&now>=lastTempReady){temp0=tempSensor.getTempCByIndex(0);temp1=tempSensor.getDeviceCount()>1?tempSensor.getTempCByIndex(1):NAN;tempPending=false;}}
void envTick(){if(lightOK)luxValue=lightMeter.readLightLevel();if(bmeOK){roomT=bme.readTemperature();humidity=bme.readHumidity();pressure=bme.readPressure()/100.0F;}}
void micTick(){if(!micSampling){micSampling=true;micIndex=0;nextMicUs=micros();}if(!micSampling)return;unsigned long u=micros();if((long)(u-nextMicUs)<0)return;micBuffer[micIndex++]=(int16_t)analogRead(MIC_PIN);nextMicUs+=MIC_SAMPLE_US;if(micIndex>=MIC_N){long sum=0;for(int i=0;i<MIC_N;i++)sum+=micBuffer[i];float mean=sum/(float)MIC_N,ss=0;int crossings=0,lastSign=0;for(int i=0;i<MIC_N;i++){float d=micBuffer[i]-mean;ss+=d*d;int sign=d>=0?1:-1;if(i&&sign!=lastSign)crossings++;lastSign=sign;}micRaw=micBuffer[MIC_N-1];micRms=sqrt(ss/MIC_N);micPitchHz=(crossings/2.0f)*(2000000.0f/MIC_N);if(micPitchHz<60||micPitchHz>400)micPitchHz=0;micSampling=false;}}
uint16_t status(){uint16_t s=statusBase;if(ppgOK){if(irValue<5000)s|=(1<<ST_PPG_ABSENT);if(irValue>250000UL||redValue>250000UL)s|=(1<<ST_PPG_SAT);}if(tempOK&&!(temp0>-20&&temp0<80))s|=(1<<ST_TEMP_ERR);if(gsrRaw<5||gsrRaw>1018)s|=(1<<ST_GSR_SAT);if(digitalRead(ECG_LO_PLUS)||digitalRead(ECG_LO_MINUS))s|=(1<<ST_ECG_LEADS);if(micRms<2)s|=(1<<ST_MIC_LOW);if(fsrRaw<20||fsrRaw>1000)s|=(1<<ST_FSR_ARTIFACT);return s;}
void sendPacket(){char ax[12],ay[12],az[12],gx[12],gy[12],gz[12],t0[12],t1[12],lx[12],rt[12],hu[12],pr[12],mr[12],mp[12];dtostrf(ax_g,1,4,ax);dtostrf(ay_g,1,4,ay);dtostrf(az_g,1,4,az);dtostrf(gx_dps,1,3,gx);dtostrf(gy_dps,1,3,gy);dtostrf(gz_dps,1,3,gz);dtostrf(temp0,1,2,t0);dtostrf(temp1,1,2,t1);dtostrf(luxValue,1,1,lx);dtostrf(roomT,1,2,rt);dtostrf(humidity,1,1,hu);dtostrf(pressure,1,1,pr);dtostrf(micRms,1,2,mr);dtostrf(micPitchHz,1,1,mp);char p[280];uint16_t s=status();snprintf(p,sizeof(p),"$CP2,%lu,%lu,%lu,%s,%s,%s,%s,%s,%s,%s,%s,%d,%d,%s,%s,%d,%d,%s,%s,%s,%s,%u,%u",millis(),(unsigned long)irValue,(unsigned long)redValue,ax,ay,az,gx,gy,gz,t0,t1,gsrRaw,micRaw,mr,mp,ecgRaw,fsrRaw,lx,rt,hu,pr,buttonMask,s);uint8_t crc=xorCRC(p);Serial.print(p);Serial.print(',');if(crc<16)Serial.print('0');Serial.println(crc,HEX);}
void handleCommand(const char*c){if(!strcmp(c,"PING"))Serial.println("$ACK,PONG,00");else if(!strcmp(c,"WHOAMI"))Serial.println("$ACK,WHOAMI,ENDO-TWIN-MEGA-LAB");else if(!strcmp(c,"LED,G"))setLed('G');else if(!strcmp(c,"LED,Y"))setLed('Y');else if(!strcmp(c,"LED,R"))setLed('R');else if(!strcmp(c,"BEEP"))beep();}
void commands(){while(Serial.available()){char c=(char)Serial.read();if(c=='\n'||c=='\r'){if(cmdIdx){cmdBuf[cmdIdx]=0;handleCommand(cmdBuf);cmdIdx=0;}}else if(cmdIdx<sizeof(cmdBuf)-1)cmdBuf[cmdIdx++]=c;}}
void setup(){pinMode(LED_GREEN,OUTPUT);pinMode(LED_YELLOW,OUTPUT);pinMode(LED_RED,OUTPUT);pinMode(BUZZER_PIN,OUTPUT);pinMode(BTN_MODE,INPUT_PULLUP);pinMode(BTN_BASE,INPUT_PULLUP);pinMode(BTN_POST,INPUT_PULLUP);pinMode(ECG_LO_PLUS,INPUT);pinMode(ECG_LO_MINUS,INPUT);setLed('Y');Serial.begin(BAUD_RATE);Wire.begin();Wire.setClock(400000L);delay(250);setupSensors();calibrate();envTick();setLed('G');beep();}
void loop(){unsigned long now=millis();if(now-lastPPG>=PPG_PERIOD_MS){lastPPG=now;readPPG();}if(now-lastIMU>=IMU_PERIOD_MS){lastIMU=now;readIMU();}if(now-lastAnalog>=ANALOG_PERIOD_MS){lastAnalog=now;readAnalog();}tempTick(now);if(now-lastEnv>=ENV_PERIOD_MS){lastEnv=now;envTick();}micTick();if(now-lastOLED>=OLED_PERIOD_MS){lastOLED=now;
#if 1
if(oledOK){display.clearDisplay();display.setTextSize(1);display.setTextColor(SSD1306_WHITE);display.setCursor(0,0);display.println("ENDO-TWIN MEGA LAB");display.print("IR:");display.println(irValue);display.print("T:");display.println(temp0);display.print("GSR:");display.println(gsrRaw);display.println("Research prototype");display.display();}
#endif
}if(now-lastPacket>=PACKET_PERIOD_MS){lastPacket=now;sendPacket();}commands();}
