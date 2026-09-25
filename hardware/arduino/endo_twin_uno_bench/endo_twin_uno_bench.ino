/* ENDO-TWIN UNO Bench Firmware - V8.8 analog Pulse Sensor
   Analog Pulse Sensor SIG -> PULSE_PIN (A1 default)
   MPU6050 -> SDA=A4/SCL=A5
   DS18B20 -> D2, GSR -> A0
   $CP2: ir=analog pulse ADC, red=-1, status bit 12=analog pulse.
   SpO2 is unavailable in analog pulse mode.
   Educational research prototype; not a diagnostic medical device.
*/
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#define PULSE_PIN A1
#define ONE_WIRE_BUS 2
#define GSR_PIN A0
#define BAUD 115200
#define ST_PPG_ABSENT 0
#define ST_PPG_SAT 1
#define ST_MPU_ERR 2
#define ST_TEMP_ERR 3
#define ST_GSR_SAT 4
#define ST_I2C_ERR 5
#define ST_PPG_ANALOG 12
#define ST_PPG_INVALID 13
Adafruit_MPU6050 mpu; OneWire ow(ONE_WIRE_BUS); DallasTemperature temp(&ow);
bool mk=false,tk=false; uint16_t st0=(1<<ST_PPG_ANALOG); int pulse=0,gsr=0; float ax=0,ay=0,az=1,gx=0,gy=0,gz=0,t0=NAN;
uint32_t lp=0,li=0,lg=0,lt=0,lpack=0;
uint8_t crc8(const char*s){uint8_t c=0;while(*s)c^=(uint8_t)*s++;return c;}
void setup(){Serial.begin(BAUD);Wire.begin();pinMode(PULSE_PIN,INPUT);if(mpu.begin()){mk=true;mpu.setAccelerometerRange(MPU6050_RANGE_4_G);mpu.setGyroRange(MPU6050_RANGE_500_DEG);mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);}else st0|=1<<ST_MPU_ERR;temp.begin();tk=temp.getDeviceCount()>0;if(!tk)st0|=1<<ST_TEMP_ERR;}
void loop(){uint32_t n=millis();if(n-lp>=20){lp=n;pulse=analogRead(PULSE_PIN);}if(n-li>=20){li=n;if(mk){sensors_event_t a,g,t;mpu.getEvent(&a,&g,&t);ax=a.acceleration.x/9.80665f;ay=a.acceleration.y/9.80665f;az=a.acceleration.z/9.80665f;gx=g.gyro.x*57.29578f;gy=g.gyro.y*57.29578f;gz=g.gyro.z*57.29578f;}}if(n-lg>=100){lg=n;gsr=analogRead(GSR_PIN);}if(n-lt>=1000){lt=n;if(tk){temp.requestTemperatures();t0=temp.getTempCByIndex(0);}}if(n-lpack>=50){lpack=n;uint16_t st=st0;if(pulse<20)st|=1<<ST_PPG_ABSENT;if(pulse>=1018)st|=1<<ST_PPG_SAT;if(pulse<=0||pulse>=1023)st|=1<<ST_PPG_INVALID;if(gsr<5||gsr>1018)st|=1<<ST_GSR_SAT;char tb[16],p[240],o[260];if(isnan(t0))strcpy(tb,"nan");else dtostrf(t0,1,2,tb);snprintf(p,sizeof(p),"$CP2,%lu,%d,-1,%.4f,%.4f,%.4f,%.3f,%.3f,%.3f,%s,nan,%d,0,0.00,0.0,-1,-1,-1,nan,nan,nan,0,%u",(unsigned long)n,pulse,ax,ay,az,gx,gy,gz,tb,gsr,st);uint8_t c=crc8(p);snprintf(o,sizeof(o),"%s,%02X",p,c);Serial.println(o);}}}
