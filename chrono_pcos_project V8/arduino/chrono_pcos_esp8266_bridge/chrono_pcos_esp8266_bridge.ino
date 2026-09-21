/*
  ENDO-TWIN NEXUS V8.7 — ESP8266 transparent Wi-Fi bridge.

  Mega side:
    D18/TX1 -> ESP8266 RX0 GPIO3 through a 5V->3.3V level shifter/divider
    D19/RX1 <- ESP8266 TX0 GPIO1
    GND     -> GND
  Do not connect Mega 5V directly to ESP8266 VCC or RX0.

  UART0 (Serial) is the bridge data channel. UART1 (Serial1) is TX-only debug.
  TCP port 7777. Raw $CP2 packets are forwarded unchanged; commands are sent
  back to the Mega. The bridge adds no sensor data and makes no clinical claims.
*/

#include <ESP8266WiFi.h>

#define WIFI_SSID     "CHRONO_PCOS_WIFI"
#define WIFI_PASSWORD "changeme1234"
#define TCP_PORT      7777
#define SERIAL_BAUD  115200

WiFiServer server(TCP_PORT);
WiFiClient client;

static void pumpSerialToTcp(){
  uint8_t buf[256];
  size_t n = Serial.available();
  if(!n || !client || !client.connected()) return;
  n = Serial.readBytes(buf, min(n,(size_t)sizeof(buf)));
  if(n) client.write(buf,n);
}

static void pumpTcpToSerial(){
  if(!client || !client.connected()) return;
  uint8_t buf[128]; size_t n=0;
  while(client.available() && n<sizeof(buf)) buf[n++]=(uint8_t)client.read();
  if(n) Serial.write(buf,n);
}

void setup(){
  Serial.begin(SERIAL_BAUD);
  Serial1.begin(115200);
  Serial.setTimeout(20);

  Serial1.println("ENDO-TWIN ESP8266 BRIDGE V8.7");
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID,WIFI_PASSWORD);
  unsigned long t0=millis();
  while(WiFi.status()!=WL_CONNECTED && millis()-t0<15000){ delay(100); }

  if(WiFi.status()==WL_CONNECTED){
    Serial1.print("STA IP: "); Serial1.println(WiFi.localIP());
  }else{
    WiFi.mode(WIFI_AP);
    WiFi.softAP("CHRONO-PCOS-BRIDGE","chronopcos",6,0,1);
    Serial1.print("AP IP: "); Serial1.println(WiFi.softAPIP());
  }
  server.begin();
  Serial1.print("TCP: "); Serial1.println(TCP_PORT);
}

void loop(){
  if(!client || !client.connected()){
    WiFiClient candidate=server.available();
    if(candidate){ client=candidate; client.setNoDelay(true); Serial1.println("CLIENT CONNECTED"); }
  }
  pumpTcpToSerial();
  pumpSerialToTcp();
  yield();
}
