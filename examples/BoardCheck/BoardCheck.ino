#include <Arduino.h>
#include <Wire.h>
#include <SPI.h>
#include <WiFi.h>

static_assert(SDA == 6 && SCL == 7, "Incorrect board I2C pins");
static_assert(TX == 16 && RX == 17, "Incorrect board UART pins");
static_assert(PIN_RGB_LED == 8 && BOOT_BUILTIN == 9, "Incorrect board LED/BOOT pins");
static_assert(SS == 18 && MOSI == 19 && MISO == 20 && SCK == 21, "Incorrect SPI defaults");

void setup() {
  Serial.begin(115200);
  delay(1500);
  pinMode(BOOT_BUILTIN, INPUT_PULLUP);
  Wire.begin();
  Serial.println("elegoo-esp32c6-board");
  Serial.printf("Flash detected: %u bytes\n", ESP.getFlashChipSize());
  Serial.printf("I2C: SDA=%u SCL=%u; RGB=%u; BOOT=%u\n",
                SDA, SCL, PIN_RGB_LED, BOOT_BUILTIN);
  Serial.println("Press BOOT to show red; release to show green.");
}

void loop() {
  const bool pressed = digitalRead(BOOT_BUILTIN) == LOW;
  rgbLedWrite(RGB_BUILTIN, pressed ? 16 : 0, pressed ? 0 : 16, 0);
  delay(50);
}
