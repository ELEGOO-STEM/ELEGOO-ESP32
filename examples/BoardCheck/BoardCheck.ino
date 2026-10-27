#include <Arduino.h>
#include <Wire.h>
#include <SPI.h>
#include <WiFi.h>

#if defined(ARDUINO_ELEGOO_ESP32C6)
static constexpr char BOARD_NAME[] = "ELEGOO-ESP32-C6";
static_assert(SDA == 6 && SCL == 7, "Incorrect board I2C pins");
static_assert(TX == 16 && RX == 17, "Incorrect board UART pins");
static_assert(PIN_RGB_LED == 8 && BOOT_BUILTIN == 9, "Incorrect board LED/BOOT pins");
static_assert(SS == 18 && MOSI == 19 && MISO == 20 && SCK == 21, "Incorrect SPI defaults");
#elif defined(ARDUINO_ELEGOO_ESP32S3_BOT_CAM)
static constexpr char BOARD_NAME[] = "ELEGOO ESP32-S3 BOT CAM";
static_assert(SDA == 4 && SCL == 5, "Incorrect camera I2C pins");
static_assert(TX == 40 && RX == 3, "Incorrect P1 UART pins");
static_assert(LED_BUILTIN == 46 && BOOT_BUILTIN == 0, "Incorrect board LED/BOOT pins");
static_assert(SS == 21 && MOSI == 47 && MISO == 48 && SCK == 14, "Incorrect SPI defaults");
#else
#error Select an ELEGOO board before compiling BoardCheck.
#endif

void setup() {
  Serial.begin(115200);
  delay(1500);
  pinMode(BOOT_BUILTIN, INPUT_PULLUP);
#ifndef RGB_BUILTIN
  digitalWrite(LED_BUILTIN, LED_BUILTIN_OFF);
  pinMode(LED_BUILTIN, OUTPUT);
#endif
  Wire.begin();
  Serial.println(BOARD_NAME);
  Serial.printf("Flash detected: %u bytes\n", ESP.getFlashChipSize());
  Serial.printf("PSRAM detected: %u bytes\n", ESP.getPsramSize());
#ifdef RGB_BUILTIN
  Serial.printf("I2C: SDA=%u SCL=%u; RGB=%u; BOOT=%u\n",
                SDA, SCL, PIN_RGB_LED, BOOT_BUILTIN);
  Serial.println("Press BOOT to show red; release to show green.");
#else
  Serial.printf("I2C: SDA=%u SCL=%u; LED=%u (active low); BOOT=%u\n",
                SDA, SCL, LED_BUILTIN, BOOT_BUILTIN);
  Serial.println("Hold BOOT to light the green LED.");
#endif
}

void loop() {
  const bool pressed = digitalRead(BOOT_BUILTIN) == LOW;
#ifdef RGB_BUILTIN
  rgbLedWrite(RGB_BUILTIN, pressed ? 16 : 0, pressed ? 0 : 16, 0);
#else
  digitalWrite(LED_BUILTIN, pressed ? LED_BUILTIN_ON : LED_BUILTIN_OFF);
#endif
  delay(50);
}
