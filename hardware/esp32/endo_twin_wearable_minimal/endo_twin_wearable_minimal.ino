/*
  MINIMAL TEST V8.4.5 - ESP32-S3 Pulse Debug - WEARABLE STABLE
  PSRAM-safe: Feather S3 2MB PSRAM uses GPIO40/44 for Octal PSRAM.
  Using GPIO40 as INPUT crashes PSRAM and causes connect/disconnect while wearing.
  FIX: Use GPIO4 (joined to 40 with wire) as safe pin.

  Wiring:
  Pulse S -> 40 physically, joined to 4 with wire (read GPIO4)
  DS18 DATA -> GPIO6 + 4.7k to 3V3
  GSR -> GPIO5

  Publishes $CP2 at 20Hz
*/

#include <Arduino.h>
#include <OneWire.h>
#include <DallasTemperature.h>

static constexpr uint8_t PULSE_PIN_SAFE = 4;
static constexpr uint8_t ONE_WIRE_BUS = 6;
static constexpr uint8_t GSR_PIN = 5;

OneWire ow(ONE_WIRE_BUS);
DallasTemperature ds18(&ow);
bool ds18OK=false;
float skinTemp=NAN;
int pulseRaw=0;
int gsrRaw=0;
uint8_t activePulsePin = PULSE_PIN_SAFE;

uint8_t crc8(const char* s){ uint8_t c=0; while(*s) c^=(uint8_t)(*s++); return c; }

void setup(){
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n\n=== MINIMAL TEST V8.4.5 - PULSE DEBUG - WEARABLE STABLE ===");
  bool hasPSRAM = (ESP.getPsramSize() > 0);
  Serial.printf("PSRAM %d bytes %s\n", ESP.getPsramSize(), hasPSRAM?"PSRAM-safe mode, using GPIO4 only":"no PSRAM");
  Serial.println("Wiring: Pulse S=40 joined to 4 with wire, reading GPIO4 (PSRAM-safe)");
  
  pinMode(PULSE_PIN_SAFE, INPUT);
  pinMode(5, INPUT);
  pinMode(1, INPUT);
  pinMode(2, INPUT);
  pinMode(3, INPUT);
  pinMode(10, INPUT);
  analogReadResolution(12);
  #if defined(ADC_11db)
    analogSetPinAttenuation(4, ADC_11db);
    analogSetPinAttenuation(5, ADC_11db);
    analogSetPinAttenuation(1, ADC_11db);
    analogSetPinAttenuation(2, ADC_11db);
  #endif

  Serial.println("ADC scan PSRAM-safe (GPIO4,5,1,2,3,10):");
  for(int i=0;i<10;i++){
    Serial.printf("  GPIO4=%4d GPIO5=%4d GPIO1=%4d GPIO2=%4d GPIO3=%4d\n",
      analogRead(4), analogRead(5), analogRead(1), analogRead(2), analogRead(3));
    delay(100);
  }

  int bestVar=0;
  uint8_t bestPin=PULSE_PIN_SAFE;
  uint8_t candidates[] = {4,1,2,3,5,10};
  for(uint8_t pin: candidates){
    int minV=4095, maxV=0;
    for(int k=0;k<50;k++){
      int v=analogRead(pin);
      if(v<minV) minV=v;
      if(v>maxV) maxV=v;
      delay(5);
    }
    int var = maxV-minV;
    Serial.printf("  Pin %d var %d (min %d max %d)\n", pin, var, minV, maxV);
    if(var>bestVar){ bestVar=var; bestPin=pin; }
  }
  activePulsePin=bestPin;
  Serial.printf("Selected pulse pin: GPIO%d var %d - STABLE\n", activePulsePin, bestVar);
  if(bestVar<5) Serial.println("WARNING: All pins flat! Check VCC=3V3 GND S, press finger firmly");

  ds18.begin();
  ds18OK = ds18.getDeviceCount()>0;
  Serial.printf("DS18B20 devices on GPIO6: %d\n", ds18.getDeviceCount());
  if(ds18OK){
    ds18.setResolution(12);
    ds18.setWaitForConversion(false);
    ds18.requestTemperatures();
  }
  Serial.println("Publishing $CP2 at 20Hz - WEARABLE STABLE, no GPIO40 touch");
}

void loop(){
  static uint32_t tPulse=0, tTemp=0, tPack=0, tGsr=0;
  static float baseline=250;
  uint32_t now=millis();
  if(now - tPulse >= 20){ 
    tPulse=now; 
    int raw=analogRead(activePulsePin);
    // Low-pass + gain x3 for calm HR
    static float filt=250;
    filt = filt*0.7f + raw*0.3f;
    if(raw>0 && raw<500){
      baseline = baseline*0.997f + filt*0.003f;
      float diff = filt - baseline;
      int amplified = (int)(1850 + diff*3.0f);
      if(amplified<0) amplified=0;
      if(amplified>4095) amplified=4095;
      pulseRaw=amplified;
    } else {
      pulseRaw=(int)filt;
      baseline = baseline*0.997f + filt*0.003f;
    } 
  }
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
    snprintf(p,sizeof(p),"$CP2,%lu,%d,-1,0.01,0.02,1.00,0.1,0.2,0.3,%s,nan,%d,0,0.00,0.0,-1,-1,150,25.0,50.0,1010.0,0,4096",
      (unsigned long)now, pulseRaw, tSkin, gsrRaw);
    char out[340];
    uint8_t c=crc8(p);
    snprintf(out,sizeof(out),"%s,%02X",p,c);
    Serial.println(out);
  }
}
