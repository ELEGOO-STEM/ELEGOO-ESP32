# ELEGOO-ESP32

English | [简体中文](README_zh-CN.md)

Arduino IDE support for ELEGOO ESP32 development boards. Supported boards: **ELEGOO-ESP32-C6** and **ELEGOO ESP32-S3 BOT CAM**.

## ELEGOO-ESP32-C6

The ELEGOO-ESP32-C6 features a USB Type-C connector, an RGB LED, BOOT and RST buttons, and GPIO, I²C, SPI, and UART interfaces for electronics education, sensor applications, and IoT projects.

| Feature | Description |
| --- | --- |
| Board name | `ELEGOO-ESP32-C6` |
| Processor | ESP32-C6, 160MHz RISC-V processor |
| Default Flash configuration | 4MB |
| USB interface | USB Type-C for uploading sketches and serial communication |
| Onboard LED | Programmable RGB LED |
| Buttons | BOOT and RST |

## ELEGOO ESP32-S3 BOT CAM

Camera board based on the **ESP32-S3-WROOM-1-N8R8** module, with native USB Type-C, a 24-pin DVP camera connector, a P1 serial connector, a green status LED, and BOOT/RST buttons.

| Feature | Description |
| --- | --- |
| Board name | `ELEGOO ESP32-S3 BOT CAM` |
| Processor | ESP32-S3, dual-core Xtensa LX7, 240MHz |
| Flash | 8MB; QIO 80MHz by default |
| PSRAM | 8MB; OPI PSRAM enabled by default |
| Partition scheme | Default 8MB with SPIFFS (3MB application) |
| USB defaults | Hardware CDC and JTAG; USB CDC On Boot enabled |
| Onboard LEDs | Green status LED on GPIO46 (active low); red power LED |

The memory configuration follows the confirmed module part number; see the [Espressif module datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf).

## Arduino IDE Installation

1. Open the Arduino IDE and go to **File → Preferences**. Add the following URL to **Additional Boards Manager URLs**:

   ```text
   https://github.com/ELEGOO-STEM/ELEGOO-ESP32/releases/latest/download/package_elegoo_esp32_index.json
   ```

2. Open **Boards Manager**, search for `ELEGOO`, and install the **ELEGOO** package.
3. Under **Tools → Board → ELEGOO**, select **ELEGOO-ESP32-C6** or **ELEGOO ESP32-S3 BOT CAM**.

## Upload Your First Sketch

1. Connect the board to your computer using a USB Type-C data cable.
2. Select the board's serial port under **Tools → Port**.
3. Open **File → Examples → ElegooBoard → BoardCheck** and click **Upload**.
4. Open the Serial Monitor at **115200** to view board information, detected Flash, and PSRAM. On C6, the RGB LED is green and turns red while BOOT is held. On BOT CAM, holding BOOT lights the green LED.

For BOT CAM, open **File → Examples → ElegooBoard → CameraCheck** to check camera initialization and capture. Use a compatible JPEG DVP sensor (for example, OV2640). The example prints frame dimensions and JPEG byte counts; it does not stream video. Keep **Flash Size: 8MB**, **PSRAM: OPI PSRAM**, and **Partition Scheme: Default 8MB with spiffs** selected.

If the serial port does not appear or uploading fails, hold **BOOT**, press and release **RST**, then release **BOOT**. Select the port again and retry uploading. If the sketch does not run after the first upload, press **RST** once.

## ELEGOO-ESP32-C6 Pin Reference

| Function | Pins |
| --- | --- |
| RGB LED | GPIO8; control with `RGB_BUILTIN` |
| BOOT button | GPIO9; active low |
| I²C | SDA: GPIO6; SCL: GPIO7 |
| UART0 | TX: GPIO16; RX: GPIO17 |
| Default SPI pins | SS: GPIO18; MOSI: GPIO19; MISO: GPIO20; SCK: GPIO21 |

USB serial is enabled by default and available through `Serial`. Calling `Wire.begin()` uses the I²C pins listed above. The default Flash configuration is 4MB. If your hardware has a different capacity, select the correct **Tools → Flash Size** setting and a matching partition scheme.

## ELEGOO ESP32-S3 BOT CAM Pin Reference

| Function | Pins |
| --- | --- |
| Green status LED | GPIO46; `LED_BUILTIN`; LOW = on, HIGH = off; no RGB LED |
| BOOT button | GPIO0; active low |
| Camera SCCB / default I²C | SDA: GPIO4; SCL: GPIO5 |
| P1 serial connector | Pin 1: RX GPIO3; pin 2: TX GPIO40; pin 3: GND; pin 4: EXT_5V |
| Camera XCLK / PCLK | GPIO15 / GPIO13 |
| Camera VSYNC / HREF | GPIO6 / GPIO7 |
| Camera D0–D7 (J1 Y2–Y9) | GPIO11, GPIO9, GPIO8, GPIO10, GPIO12, GPIO18, GPIO17, GPIO16 |
| Camera RESET / PWDN | Pulled high / low in hardware; `CAM_PIN_RESET` / `CAM_PIN_PWDN` = -1 |
| Software SPI defaults | SS: GPIO21; MOSI: GPIO47; MISO: GPIO48; SCK: GPIO14 |

Use `Serial` for native USB and `Serial1.begin(115200, SERIAL_8N1, RX, TX)` for P1. UART0 module pads are GPIO43/44. SPI defaults are unused module pads, not a dedicated header. GPIO35–37 are reserved for the module's OPI PSRAM.

Camera pin macros (`CAM_PIN_*`) are provided by the board variant. `Wire.begin()` uses the same GPIO4/5 bus as the camera; coordinate access with the camera driver. `CameraCheck` lets `esp_camera_init()` initialize this bus.

## Resources

- [ELEGOO-ESP32-C6 schematic](doc/ESP32C6.pdf)
- [ELEGOO ESP32-S3 BOT CAM V2.2 schematic](doc/esp32S3_Camera_PCB_V2.2.pdf)
- [Project repository](https://github.com/ELEGOO-STEM/ELEGOO-ESP32)
