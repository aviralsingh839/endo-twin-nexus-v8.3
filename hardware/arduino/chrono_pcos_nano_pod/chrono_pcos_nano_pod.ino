/*
  CHRONO-PCOS Nano Pod Firmware
  V8.8 analog Pulse Sensor option.

  Active PPG hardware:
    Generic analog Pulse Sensor SIG -> PULSE_PIN (A1 default)
    VCC -> sensor-supported supply
    GND -> GND
  MPU6050: I2C SDA=A4, SCL=A5
  DS18B20: D2, 4.7k pull-up
  GSR optional: A0

  $CP2 remains the transport contract:
    ir  = analog pulse ADC waveform
    red = -1 (no optical red channel)
    status bit 12 = analog Pulse Sensor active
    status bit 13 = invalid/clipped pulse sample

  SpO2 is unavailable in analog Pulse Sensor mode.

  Educational physiological monitoring only. Not a diagnostic medical device.
*/

#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <OneWire.h>
#include <DallasTemperature.h>

#define PULSE_PIN A1
#define ONE_WIRE_BUS 2
#define GSR_PIN A0
#define LED_GREEN 8
#define LED_YELLOW 9
#define LED_RED 10
#define BUZZER_PIN 6

#define BAUD_RATE 115200
#define PULSE_PERIOD_MS 20
#define IMU_PERIOD_MS 20
#define GSR_PERIOD_MS 100
#define TEMP_PERIOD_MS 1000
#define PACKET_PERIOD_MS 50

#define ST_PPG_ABSENT 0
#define ST_PPG_SAT 1
#define ST_MPU_ERR 2
#define ST_TEMP_ERR 3
#define ST_GSR_SAT 4
#define ST_I2C_ERR 5
#define ST_LOW_QUALITY 6
#define ST_PPG_ANALOG 12
#define ST_PPG_INVALID 13

Adafruit_MPU6050 mpu;
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature tempSensor(&oneWire);

bool mpuOK=false, tempOK=false;
uint16_t statusBase=(1 << ST_PPG_ANALOG);
int pulseRaw=0, gsrRaw=0;
float ax_g=0, ay_g=0, az_g=1, gx_dps=0, gy_dps=0, gz_dps=0, temp0=NAN;
float ax_bias=0, ay_bias=0, az_bias=0, gx_bias=0, gy_bias=0, gz_bias=0;
unsigned long lastPulse=0,lastIMU=0,lastGSR=0,lastTemp=0,lastPacket=0;
char cmdBuf[40]; uint8_t cmdIdx=0;

uint8_t xorCRC(const char *s){uint8_t c=0;while(*s)c^=(uint8_t)(*s++);return c;}
void setLedState(char s){digitalWrite(LED_GREEN,s=='G');digitalWrite(LED_YELLOW,s=='Y');digitalWrite(LED_RED,s=='R');}
void beepShort(){tone(BUZZER_PIN,2200,120);}

void setupSensors(){
  pinMode(PULSE_PIN,INPUT);
  if(mpu.begin()){mpuOK=true;mpu.setAccelerometerRange(MPU6050_RANGE_4_G);mpu.setGyroRange(MPU6050_RANGE_500_DEG);mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);}
  else statusBase|=(1<<ST_MPU_ERR);
  tempSensor.begin(); tempOK=tempSensor.getDeviceCount()>0; if(!tempOK)statusBase|=(1<<ST_TEMP_ERR);
}

void calibrateIMU(){
  if(!mpuOK)return;
  const int N=160; float sx=0,sy=0,sz=0,sgx=0,sgy=0,sgz=0;
  for(int i=0;i<N;i++){
    sensors_event_t a,g,t; mpu.getEvent(&a,&g,&t);
    sx+=a.acceleration.x/9.80665f; sy+=a.acceleration.y/9.80665f; sz+=a.acceleration.z/9.80665f;
    sgx+=g.gyro.x*57.29578f; sgy+=g.gyro.y*57.29578f; sgz+=g.gyro.z*57.29578f; delay(8);
  }
  ax_bias=sx/N; ay_bias=sy/N; az_bias=sz/N-1.0f; gx_bias=sgx/N; gy_bias=sgy/N; gz_bias=sgz/N;
}
void readPulse(){pulseRaw=analogRead(PULSE_PIN);}
void readIMU(){if(!mpuOK)return;sensors_event_t a,g,t;mpu.getEvent(&a,&g,&t);ax_g=a.acceleration.x/9.80665f-ax_bias;ay_g=a.acceleration.y/9.80665f-ay_bias;az_g=a.acceleration.z/9.80665f-az_bias;gx_dps=g.gyro.x*57.29578f-gx_bias;gy_dps=g.gyro.y*57.29578f-gy_bias;gz_dps=g.gyro.z*57.29578f-gz_bias;}
void readGSR(){gsrRaw=analogRead(GSR_PIN);}
void readTemp(){if(!tempOK)return;tempSensor.requestTemperatures();temp0=tempSensor.getTempCByIndex(0);}

uint16_t makeStatus(){
  uint16_t st=statusBase;
  if(pulseRaw<20)st|=(1<<ST_PPG_ABSENT);
  if(pulseRaw>1000){} // no optical saturation assumption
  if(pulseRaw>=1020)st|=(1<<ST_PPG_SAT);
  if(pulseRaw<=0 || pulseRaw>=1023)st|=(1<<ST_PPG_INVALID);
  if(tempOK && !(temp0>-20&&temp0<80))st|=(1<<ST_TEMP_ERR);
  if(gsrRaw<5||gsrRaw>1018)st|=(1<<ST_GSR_SAT);
  return st;
}

void sendPacket(){
  char fax[12],fay[12],faz[12],fgx[12],fgy[12],fgz[12],ft0[12],payload[240],out[260];
  dtostrf(ax_g,1,4,fax);dtostrf(ay_g,1,4,fay);dtostrf(az_g,1,4,faz);dtostrf(gx_dps,1,3,fgx);dtostrf(gy_dps,1,3,fgy);dtostrf(gz_dps,1,3,fgz);
  if(isnan(temp0))strcpy(ft0,"nan");else dtostrf(temp0,1,2,ft0);
  uint16_t st=makeStatus();
  snprintf(payload,sizeof(payload),"$CP2,%lu,%d,-1,%s,%s,%s,%s,%s,%s,%s,nan,%d,0,0.00,0.0,-1,-1,-1,nan,nan,nan,0,%u",(unsigned long)millis(),pulseRaw,fax,fay,faz,fgx,fgy,fgz,ft0,gsrRaw,st);
  uint8_t crc=xorCRC(payload);snprintf(out,sizeof(out),"%s,%02X",payload,crc);Serial.println(out);
}

void handleCommand(const char* cmd){if(strncmp(cmd,"LED,G",5)==0)setLedState('G');else if(strncmp(cmd,"LED,Y",5)==0)setLedState('Y');else if(strncmp(cmd,"LED,R",5)==0)setLedState('R');else if(strncmp(cmd,"BEEP",4)==0)beepShort();else if(strncmp(cmd,"PING",4)==0)Serial.println("$ACK,PONG,00");else if(strncmp(cmd,"WHOAMI",6)==0)Serial.println("ENDO-TWIN-NANO-ANALOG-PULSE");}
void readSerialCommands(){while(Serial.available()){char c=(char)Serial.read();if(c=='\n'||c=='\r'){if(cmdIdx){cmdBuf[cmdIdx]=0;handleCommand(cmdBuf);cmdIdx=0;}}else if(cmdIdx<sizeof(cmdBuf)-1)cmdBuf[cmdIdx++]=c;}}

void setup(){pinMode(LED_GREEN,OUTPUT);pinMode(LED_YELLOW,OUTPUT);pinMode(LED_RED,OUTPUT);pinMode(BUZZER_PIN,OUTPUT);setLedState('Y');Serial.begin(BAUD_RATE);Wire.begin();delay(250);setupSensors();calibrateIMU();readTemp();readGSR();setLedState('G');beepShort();}
void loop(){unsigned long now=millis();if(now-lastPulse>=PULSE_PERIOD_MS){lastPulse=now;readPulse();}if(now-lastIMU>=IMU_PERIOD_MS){lastIMU=now;readIMU();}if(now-lastGSR>=GSR_PERIOD_MS){lastGSR=now;readGSR();}if(now-lastTemp>=TEMP_PERIOD_MS){lastTemp=now;readTemp();}if(now-lastPacket>=PACKET_PERIOD_MS){lastPacket=now;sendPacket();}readSerialCommands();}
