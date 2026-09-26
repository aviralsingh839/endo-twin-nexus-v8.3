/*
  MINIMAL TEST - ENDO-TWIN S3 - No I2C, only Serial + Pulse GPIO40 + DS18 GPIO6
  Use this to prove dashboard can receive data.
  If this works at 20Hz, then full V8.4 with I2C will work after fixing wiring.
*/

#include <Arduino.h>
#include <OneWire.h>
#include <DallasTemperature.h>

static constexpr uint8_t PULSE_PIN = 40;
static constexpr uint8_t ONE_WIRE_BUS = 6;
static constexpr uint8_t GSR_PIN = 5;

OneWire ow(ONE_WIRE_BUS);
DallasTemperature ds18(&ow);
bool ds18OK=false;
float skinTemp=NAN;
int pulseRaw=0;
int gsrRaw=0;

uint8_t crc8(const char* s){ uint8_t c=0; while(*s) c^=(uint8_t)(*s++); return c; }

void setup(){
  pinMode(PULSE_PIN, INPUT);
  pinMode(GSR_PIN, INPUT);
  analogReadResolution(12);
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n\n=== MINIMAL TEST V8.4 ===");
  Serial.println("No I2C, only Pulse GPIO40 + DS18 GPIO6 + GSR GPIO5");
  Serial.println("Should publish $CP2 at 20Hz immediately");
  ds18.begin();
  ds18OK = ds18.getDeviceCount()>0;
  Serial.printf("DS18B20 devices: %d\n", ds18.getDeviceCount());
  if(ds18OK){
    ds18.setResolution(12);
    ds18.setWaitForConversion(false);
    ds18.requestTemperatures();
  }
}

void loop(){
  static uint32_t tPulse=0, tTemp=0, tPack=0, tGsr=0;
  uint32_t now=millis();
  if(now - tPulse >= 20){ tPulse=now; pulseRaw=analogRead(PULSE_PIN); }
  if(now - tGsr >= 100){ tGsr=now; gsrRaw=analogRead(GSR_PIN); }
  if(now - tTemp >= 1000){
    tTemp=now;
    if(ds18OK){
      float t=ds18.getTempCByIndex(0);
      if(t>-40 && t<85) skinTemp=t;
      ds18.requestTemperatures();
    }
  }
  if(now - tPack >= 50){
    tPack=now;
    char tSkin[16];
    if(isnan(skinTemp)) strcpy(tSkin,"nan"); else snprintf(tSkin,sizeof(tSkin),"%.2f",skinTemp);
    char p[320];
    // status 4096 = analog active
    snprintf(p,sizeof(p),"$CP2,%lu,%d,-1,0.01,0.02,1.00,0.1,0.2,0.3,%s,nan,%d,0,0.00,0.0,-1,-1,150,25.0,50.0,1010.0,0,4096",
      (unsigned long)now, pulseRaw, tSkin, gsrRaw);
    char out[340];
    uint8_t c=crc8(p);
    snprintf(out,sizeof(out),"%s,%02X",p,c);
    Serial.println(out);
  }
}
