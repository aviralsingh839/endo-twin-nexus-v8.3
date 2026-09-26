/*
  MINIMAL TEST V8.4.1 - ESP32-S3 Pulse Debug
  Scans multiple ADC pins to find pulse sensor, since GPIO40 may be PSRAM on some boards.
  Also shows DS18B20 on GPIO6.

  Wiring for test:
  Pulse S -> try GPIO40, then GPIO4, GPIO5, GPIO6 (but 6 is DS18), GPIO1,2,3,8,9,10
  DS18 DATA -> GPIO6 + 4.7k to 3V3
  GSR -> GPIO5

  This sketch publishes $CP2 at 20Hz with pulseRaw from best pin.
*/

#include <Arduino.h>
#include <OneWire.h>
#include <DallasTemperature.h>

static constexpr uint8_t PULSE_PIN_PRIMARY = 40;
static constexpr uint8_t PULSE_PINS_ALT[] = {44,4, 5, 1, 2, 3, 10, 8, 9, 6};
static constexpr uint8_t ONE_WIRE_BUS = 6;
static constexpr uint8_t GSR_PIN = 5;

OneWire ow(ONE_WIRE_BUS);
DallasTemperature ds18(&ow);
bool ds18OK=false;
float skinTemp=NAN;
int pulseRaw=0;
int gsrRaw=0;
uint8_t activePulsePin = PULSE_PIN_PRIMARY;

uint8_t crc8(const char* s){ uint8_t c=0; while(*s) c^=(uint8_t)(*s++); return c; }

void setup(){
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n\n=== MINIMAL TEST V8.4.1 - PULSE DEBUG ===");
  Serial.println("Scanning ADC pins for pulse sensor (S should be 3V3 powered, GND, Signal to GPIO)");
  Serial.println("Primary: GPIO40, Alt: 4,5,1,2,3,10,8,9");

  // Setup all candidate pins
  pinMode(PULSE_PIN_PRIMARY, INPUT);
  for(uint8_t p: PULSE_PINS_ALT) pinMode(p, INPUT);
  pinMode(GSR_PIN, INPUT);
  analogReadResolution(12);
  #if defined(ADC_11db)
    analogSetPinAttenuation(PULSE_PIN_PRIMARY, ADC_11db);
    for(uint8_t p: PULSE_PINS_ALT) analogSetPinAttenuation(p, ADC_11db);
  #endif

  // Quick ADC scan
  Serial.println("ADC scan (10 readings each):");
  for(int i=0;i<10;i++){
    Serial.printf("  GPIO40=%4d", analogRead(40));
    Serial.printf("  GPIO4=%4d", analogRead(4));
    Serial.printf("  GPIO5=%4d", analogRead(5));
    Serial.printf("  GPIO1=%4d", analogRead(1));
    Serial.printf("  GPIO2=%4d", analogRead(2));
    Serial.printf("  GPIO3=%4d\n", analogRead(3));
    delay(100);
  }

  // Auto-select pin with most variation (likely pulse) - includes 44 which you joined to 40
  int bestVar=0;
  uint8_t bestPin=PULSE_PIN_PRIMARY;
  for(uint8_t pin: {40,44,4,5,1,2,3,10}){
    int minV=4095, maxV=0;
    for(int k=0;k<50;k++){
      int v=analogRead(pin);
      if(v<minV) minV=v;
      if(v>maxV) maxV=v;
      delay(5);
    }
    int var = maxV-minV;
    Serial.printf("  Pin %d variation %d (min %d max %d)\n", pin, var, minV, maxV);
    if(var>bestVar){
      bestVar=var;
      bestPin=pin;
    }
  }
  activePulsePin=bestPin;
  Serial.printf("Selected pulse pin: GPIO%d with variation %d\n", activePulsePin, bestVar);
  if(bestVar<5){
    Serial.println("WARNING: All pins flat! Check pulse sensor VCC=3V3 GND, S to GPIO, and sensor powered.");
    Serial.println("Try: 1) Pulse sensor VCC to 3V3 (not 5V) 2) S to GPIO4 (often more stable than 40 on Feather) 3) Cover sensor, press finger");
  }

  ds18.begin();
  ds18OK = ds18.getDeviceCount()>0;
  Serial.printf("DS18B20 devices on GPIO6: %d\n", ds18.getDeviceCount());
  if(ds18OK){
    ds18.setResolution(12);
    ds18.setWaitForConversion(false);
    ds18.requestTemperatures();
  }
  Serial.println("Publishing $CP2 at 20Hz with active pulse pin...");
}

void loop(){
  static uint32_t tPulse=0, tTemp=0, tPack=0, tGsr=0;
  static float baseline=250;
  static float filt=250;
  uint32_t now=millis();
  if(now - tPulse >= 20){ 
    tPulse=now; 
    int raw=analogRead(activePulsePin);
    float filt = raw*0.3f + 250*0.7f; // quick low-pass
    if(raw>0 && raw<500){
      baseline = baseline*0.997f + filt*0.003f;
      float diff = filt - baseline;
      int amplified = (int)(1850 + diff*3.0f);
      if(amplified<0) amplified=0;
      if(amplified>4095) amplified=4095;
      pulseRaw=amplified;
    } else {
      pulseRaw=raw;
      baseline = baseline*0.997f + raw*0.005f;
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
