/*
 * ENDO-TWIN NEXUS — ESP8266 Sensor Pod
 * ------------------------------------
 * Direct Wi-Fi sensor pod for the current research prototype.
 *
 * Sensors:
 *   MAX30102 / MAX30105-compatible PPG  -> I2C
 *   MPU6050                             -> I2C
 *   BME280 (optional)                   -> I2C
 *   DS18B20                             -> D5
 *   GSR                                 -> A0
 *
 * Network:
 *   Wi-Fi AP: ENDO-TWIN-POD
 *   AP IP:    192.168.4.1
 *   TCP:      7777
 *
 * Data:
 *   newline-delimited $CP2 packet
 *   XOR CRC over the payload before the final comma
 *   20 Hz packet cadence
 *
 * Missing channels are explicit placeholders. No synthetic physiology is
 * generated. This firmware is for a research/engineering prototype only.
 */

#include <Arduino.h>
#include <Wire.h>
#include <ESP8266WiFi.h>
#include <Adafruit_BME280.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <MAX30105.h>
#include <MPU6050.h>

static const char* AP_SSID = "ENDO-TWIN-POD";
static const char* AP_PASSWORD = "endotwin123";   // change before any non-lab use
static const uint16_t TCP_PORT = 7777;

static const uint8_t DS18B20_PIN = D5;
static const uint8_t GSR_PIN = A0;

WiFiServer server(TCP_PORT);
WiFiClient tcpClient;
MAX30105 ppg;
MPU6050 imu;
Adafruit_BME280 bme;
OneWire oneWire(DS18B20_PIN);
DallasTemperature tempSensor(&oneWire);

bool ppgOk = false;
bool imuOk = false;
bool bmeOk = false;
bool tempOk = false;
uint32_t seqMs = 0;
uint32_t packetCount = 0;

uint8_t xorCrc(const String& payload) {
  uint8_t crc = 0;
  for (size_t i = 0; i < payload.length(); ++i) crc ^= (uint8_t)payload[i];
  return crc;
}

String hex2(uint8_t value) {
  char buf[3];
  snprintf(buf, sizeof(buf), "%02X", value);
  return String(buf);
}

void sendLine(const String& line) {
  Serial.println(line);
  if (tcpClient && tcpClient.connected()) tcpClient.println(line);
}

String makePacket() {
  uint32_t ms = millis();

  long ir = 0;
  long red = 0;
  float ax = NAN, ay = NAN, az = NAN;
  float gx = NAN, gy = NAN, gz = NAN;
  float skinTemp = NAN;
  int gsr = 0;
  float roomTemp = NAN, humidity = NAN, pressure = NAN;

  uint16_t status = 0;

  if (ppgOk) {
    ir = (long)ppg.getIR();
    red = (long)ppg.getRed();

    // MAX30102/05 compatibility: zero/very-low IR is treated as no-finger.
    if (ir < 5000) status |= (1u << 0);
  } else {
    status |= (1u << 5);
    status |= (1u << 1);
  }

  if (imuOk) {
    int16_t iax, iay, iaz, igx, igy, igz;
    imu.getMotion6(&iax, &iay, &iaz, &igx, &igy, &igz);
    ax = iax / 16384.0f;
    ay = iay / 16384.0f;
    az = iaz / 16384.0f;
    gx = igx / 131.0f;
    gy = igy / 131.0f;
    gz = igz / 131.0f;
  } else {
    status |= (1u << 2);
    status |= (1u << 5);
  }

  if (tempOk) {
    tempSensor.requestTemperatures();
    skinTemp = tempSensor.getTempCByIndex(0);
    if (skinTemp == DEVICE_DISCONNECTED_C) {
      skinTemp = NAN;
      status |= (1u << 3);
    }
  } else {
    status |= (1u << 3);
  }

  if (bmeOk) {
    roomTemp = bme.readTemperature();
    humidity = bme.readHumidity();
    pressure = bme.readPressure() / 100.0f;
  } else {
    status |= (1u << 8);
  }

  gsr = analogRead(GSR_PIN);

  // $CP2,ms,ir,red,ax,ay,az,gx,gy,gz,temp0,temp1,gsr,
  //      micRaw,micRms,micPitch,ecg,fsr,lux,roomT,hum,press,buttons,status,crc
  String payload = "$CP2," +
    String(ms) + "," +
    String(ir) + "," + String(red) + "," +
    String(ax, 4) + "," + String(ay, 4) + "," + String(az, 4) + "," +
    String(gx, 3) + "," + String(gy, 3) + "," + String(gz, 3) + "," +
    String(skinTemp, 2) + "," + String(NAN, 2) + "," +
    String(gsr) + "," +
    "-1,-1,-1,-1,-1,-1," +
    String(roomTemp, 2) + "," +
    String(humidity, 2) + "," +
    String(pressure, 2) + "," +
    "0," + String(status);

  return payload + "," + hex2(xorCrc(payload));
}

void handleCommand() {
  if (!tcpClient || !tcpClient.connected()) return;
  if (!tcpClient.available()) return;

  String command = tcpClient.readStringUntil('\n');
  command.trim();

  if (command == "PING") {
    tcpClient.println("$ACK,PONG,00");
  } else if (command == "WHOAMI") {
    tcpClient.println("ENDO-TWIN-ESP8266-SENSOR-POD");
  }
}

void setupPPG() {
  ppgOk = ppg.begin(Wire, I2C_SPEED_FAST);
  if (ppgOk) {
    ppg.setup(
      60,       // LED brightness
      4,        // sample average
      2,        // RED + IR
      100,      // sample rate
      411,      // pulse width
      4096      // ADC range
    );
    ppg.setPulseAmplitudeGreen(0);
  }
}

void setup() {
  Serial.begin(115200);
  delay(100);

  Wire.begin(D2, D1); // SDA, SCL for NodeMCU ESP8266
  Wire.setClock(400000);

  pinMode(GSR_PIN, INPUT);

  setupPPG();

  imu.initialize();
  imuOk = imu.testConnection();

  tempSensor.begin();
  tempOk = tempSensor.getDeviceCount() > 0;

  bmeOk = bme.begin(0x76, &Wire);
  if (!bmeOk) bmeOk = bme.begin(0x77, &Wire);

  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASSWORD);

  server.begin();
  server.setNoDelay(true);

  Serial.println();
  Serial.println("ENDO-TWIN ESP8266 SENSOR POD");
  Serial.print("AP: ");
  Serial.println(AP_SSID);
  Serial.print("IP: ");
  Serial.println(WiFi.softAPIP());
  Serial.println("TCP: 7777");
  Serial.println("WHOAMI: ENDO-TWIN-ESP8266-SENSOR-POD");
}

void loop() {
  if (!tcpClient || !tcpClient.connected()) {
    WiFiClient candidate = server.available();
    if (candidate) {
      tcpClient.stop();
      tcpClient = candidate;
      tcpClient.setNoDelay(true);
      tcpClient.println("ENDO-TWIN-ESP8266-SENSOR-POD");
    }
  }

  handleCommand();

  const uint32_t now = millis();
  if (now - seqMs >= 50) {
    seqMs = now;
    sendLine(makePacket());
    packetCount++;
  }

  yield();
}
