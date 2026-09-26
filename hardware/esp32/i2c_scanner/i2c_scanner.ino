/*
 I2C Scanner for ENDO-TWIN V8.4
 SDA=8 SCL=9
 Scans all addresses and reports MPU6050/2060 (0x68/69), BME280 (0x76/77), BH1750 (0x23/5C)
*/
#include <Wire.h>
static constexpr uint8_t SDA_PIN=8;
static constexpr uint8_t SCL_PIN=9;

void setup(){
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n=== ENDO-TWIN I2C SCANNER SDA=8 SCL=9 ===");
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(100000);
  Wire.setTimeOut(50);
  delay(200);
  Serial.println("Scanning 0x03-0x77...");
}

void loop(){
  int found=0;
  for(uint8_t addr=0x03; addr<=0x77; addr++){
    Wire.beginTransmission(addr);
    uint8_t err = Wire.endTransmission();
    if(err==0){
      Serial.printf("  FOUND 0x%02X - ", addr);
      if(addr==0x68 || addr==0x69) Serial.println("MPU6050/2060");
      else if(addr==0x76 || addr==0x77) Serial.println("BME280");
      else if(addr==0x23 || addr==0x5C) Serial.println("BH1750");
      else Serial.println("unknown");
      found++;
    }
    delay(5);
  }
  if(found==0){
    Serial.println("NO I2C DEVICES FOUND!");
    Serial.println("Check:");
    Serial.println(" 1) SDA=8 SCL=9 wired to ALL modules");
    Serial.println(" 2) VCC=3V3 GND common");
    Serial.println(" 3) Modules have pull-up resistors (or add 4.7k SDA->3V3 SCL->3V3)");
    Serial.println(" 4) Try one module at a time");
  } else {
    Serial.printf("%d device(s) found. Expected: MPU 0x68/69, BME 0x76/77, BH 0x23/5C\n", found);
  }
  Serial.println("--- rescan in 3 sec ---\n");
  delay(3000);
}
