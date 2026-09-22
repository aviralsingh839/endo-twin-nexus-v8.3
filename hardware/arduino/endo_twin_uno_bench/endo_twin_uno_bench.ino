/* ENDO-TWIN UNO Bench Firmware. UNO is for desk/prototype validation; ESP32 is the wearable controller. */
#include <Wire.h>
#include "MAX30105.h"
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#define ONE_WIRE_BUS 2
#define GSR_PIN A0
#define BAUD 115200
MAX30105 ppg; Adafruit_MPU6050 mpu; OneWire ow(ONE_WIRE_BUS); DallasTemperature temp(&ow);
bool pk=false,mk=false,tk=false; uint16_t st0=0; uint32_t ir=0,red=0; float ax=0,ay=0,az=1,gx=0,gy=0,gz=0,t0=NAN; int gsr=0; uint32_t lp=0,li=0,lg=0,lt=0,lpack=0;
uint8_t crc8(const char*s){uint8_t c=0;while(*s)c^=(uint8_t)*s++;return c;}
void setup(){Serial.begin(BAUD);Wire.begin();if(ppg.begin(Wire,I2C_SPEED_FAST)){pk=true;ppg.setup(0x24,4,2,100,411,4096);ppg.setPulseAmplitudeRed(0x24);ppg.setPulseAmplitudeIR(0x24);}else st0|=1<<5;if(mpu.begin()){mk=true;mpu.setAccelerometerRange(MPU6050_RANGE_4_G);mpu.setGyroRange(MPU6050_RANGE_500_DEG);}else st0|=1<<2;temp.begin();tk=temp.getDeviceCount()>0;if(!tk)st0|=1<<3;}
void loop(){uint32_t n=millis();if(n-lp>=20){lp=n;if(pk){ir=ppg.getIR();red=ppg.getRed();}}if(n-li>=20){li=n;if(mk){sensors_event_t a,g,t;mpu.getEvent(&a,&g,&t);ax=a.acceleration.x/9.80665f;ay=a.acceleration.y/9.80665f;az=a.acceleration.z/9.80665f;gx=g.gyro.x*57.29578f;gy=g.gyro.y*57.29578f;gz=g.gyro.z*57.29578f;}}if(n-lg>=100){lg=n;gsr=analogRead(GSR_PIN);}if(n-lt>=1000){lt=n;if(tk){temp.requestTemperatures();t0=temp.getTempCByIndex(0);}}if(n-lpack>=50){lpack=n;uint16_t s=st0;if(pk&&ir<5000)s|=1;if(gsr<5||gsr>1018)s|=1<<4;char tb[16],p[220],o[240];if(isnan(t0))strcpy(tb,"nan");else dtostrf(t0,1,2,tb);snprintf(p,sizeof(p),"$CP2,%lu,%lu,%lu,%.4f,%.4f,%.4f,%.3f,%.3f,%.3f,%s,nan,%d,0,0.00,0.0,-1,-1,-1,nan,nan,nan,0,%u",(unsigned long)n,(unsigned long)ir,(unsigned long)red,ax,ay,az,gx,gy,gz,tb,gsr,s);uint8_t c=crc8(p);snprintf(o,sizeof(o),"%s,%02X",p,c);Serial.println(o);}}}
