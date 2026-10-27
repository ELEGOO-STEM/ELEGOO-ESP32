// Based on Espressif Arduino-ESP32's esp32c6 variant (LGPL-2.1-or-later).
// Board wiring: doc/ESP32C6.pdf, schematic dated 2026-10-16.
#ifndef Pins_Arduino_h
#define Pins_Arduino_h

#include <stdint.h>
#include "soc/soc_caps.h"

#define PIN_RGB_LED 8
// The virtual pin lets Arduino's standard Blink control the addressable RGB LED.
static const uint8_t LED_BUILTIN = SOC_GPIO_PIN_COUNT + PIN_RGB_LED;
#define BUILTIN_LED LED_BUILTIN
#define LED_BUILTIN LED_BUILTIN
#define RGB_BUILTIN LED_BUILTIN
#define RGB_BRIGHTNESS 64
static const uint8_t BOOT_BUILTIN = 9;

static const uint8_t TX = 16;
static const uint8_t RX = 17;
static const uint8_t SDA = 6;
static const uint8_t SCL = 7;

// Software defaults on exposed GPIOs; no fixed SPI peripheral is on this board.
static const uint8_t SS = 18;
static const uint8_t MOSI = 19;
static const uint8_t MISO = 20;
static const uint8_t SCK = 21;

static const uint8_t A0 = 0;
static const uint8_t A1 = 1;
static const uint8_t A2 = 2;
static const uint8_t A3 = 3;
static const uint8_t A4 = 4;
static const uint8_t A5 = 5;
static const uint8_t A6 = 6;

// Fixed low-power I2C pins, as in the upstream ESP32-C6 variant.
// Wire and Wire1 share these physical pins; do not use both at the same time.
#define WIRE1_PIN_DEFINED
static const uint8_t SDA1 = 6;
static const uint8_t SCL1 = 7;

#endif
