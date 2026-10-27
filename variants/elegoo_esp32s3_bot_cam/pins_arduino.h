// Board wiring: doc/esp32S3_Camera_PCB_V2.2.pdf.
// Fitted module: ESP32-S3-WROOM-1-N8R8 (8MB Flash, 8MB OPI PSRAM).
#ifndef Pins_Arduino_h
#define Pins_Arduino_h

#include <stdint.h>

#define USB_VID 0x303a
#define USB_PID 0x1001

// LED2 is a conventional green LED tied to 3V3; LOW turns it on.
static const uint8_t LED_BUILTIN = 46;
#define LED_BUILTIN LED_BUILTIN
#define BUILTIN_LED LED_BUILTIN
#define LED_BUILTIN_ON LOW
#define LED_BUILTIN_OFF HIGH
static const uint8_t BOOT_BUILTIN = 0;

// P1 serial connector, remapped by Serial1.begin(baud, SERIAL_8N1, RX, TX).
// Native USB Serial is independent; UART0 module pads are GPIO43/44.
static const uint8_t TX = 40;
static const uint8_t RX = 3;
// Shared with the camera SCCB bus; coordinate access with the camera driver.
static const uint8_t SDA = 4;
static const uint8_t SCL = 5;

// Software SPI defaults on unused module pads; there is no SPI header.
static const uint8_t SS = 21;
static const uint8_t MOSI = 47;
static const uint8_t MISO = 48;
static const uint8_t SCK = 14;

static const uint8_t A0 = 1;
static const uint8_t A1 = 2;
static const uint8_t A2 = 3;

// J1 24-pin DVP camera connector. RESET is pulled high; PWDN is pulled low.
#define CAM_PIN_PWDN -1
#define CAM_PIN_RESET -1
#define CAM_PIN_XCLK 15
#define CAM_PIN_SIOD 4
#define CAM_PIN_SIOC 5
#define CAM_PIN_D0 11  // Y2
#define CAM_PIN_D1 9   // Y3
#define CAM_PIN_D2 8   // Y4
#define CAM_PIN_D3 10  // Y5
#define CAM_PIN_D4 12  // Y6
#define CAM_PIN_D5 18  // Y7
#define CAM_PIN_D6 17  // Y8
#define CAM_PIN_D7 16  // Y9
#define CAM_PIN_VSYNC 6
#define CAM_PIN_HREF 7
#define CAM_PIN_PCLK 13

#endif
