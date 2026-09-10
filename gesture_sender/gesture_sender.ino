// Reads the MPU6886 100 times per second and sends one CSV line per sample over UDP.
// Line format: micros,ax,ay,az,gx,gy,gz
// Set your Wi-Fi credentials in secrets.h and the PC address below.

#include <M5Unified.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include "secrets.h"

float ax, ay, az, gx, gy, gz;
WiFiUDP udp;
IPAddress PC_IP(192, 168, 100, 5);  
const int PC_PORT = 5005;

unsigned long counter;
void setup() {
  auto cfg = M5.config();
  M5.begin(cfg);
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(WiFi.localIP());
  udp.begin(PC_PORT);
  // Time to start the receiver on the PC before the stream begins.
  delay(5000);
  counter = micros();
}
void loop() {
  // Note: micros() overflows after ~71 minutes and the stream stops
  if (micros() >= counter) {
    counter += 10000;
    M5.Imu.getAccel(&ax, &ay, &az);
    M5.Imu.getGyro(&gx, &gy, &gz);
    udp.beginPacket(PC_IP, PC_PORT);
    udp.print(micros());
    udp.print(",");
    udp.print(ax, 4);
    udp.print(",");
    udp.print(ay, 4);
    udp.print(",");
    udp.print(az, 4);
    udp.print(",");
    udp.print(gx, 4);
    udp.print(",");
    udp.print(gy, 4);
    udp.print(",");
    udp.println(gz, 4);
  }
}
