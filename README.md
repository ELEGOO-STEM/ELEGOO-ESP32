# ELEGOO ESP32-C6

English | [简体中文](README_zh-CN.md)

The ELEGOO ESP32-C6 is an ESP32-C6 development board programmable with the Arduino IDE. It features a USB Type-C connector, an RGB LED, BOOT and RST buttons, and GPIO, I²C, SPI, and UART interfaces for electronics education, sensor applications, and IoT projects.

## Board Overview

| Feature | Description |
| --- | --- |
| Board name | `elegoo-esp32c6-board` |
| Processor | ESP32-C6, 160MHz RISC-V processor |
| Default Flash configuration | 4MB |
| USB interface | USB Type-C for uploading sketches and serial communication |
| Onboard LED | Programmable RGB LED |
| Buttons | BOOT and RST |

## Arduino IDE Installation

1. Open the Arduino IDE and go to **File → Preferences**. Add the following URL to **Additional Boards Manager URLs**:

   ```text
   https://github.com/ELEGOO-STEM/ELEGOO-ESP32-C6/releases/latest/download/package_elegoo_esp32c6_index.json
   ```

2. Open **Boards Manager**, search for `elegoo-esp32c6-board`, and click **Install**.
3. Select **elegoo-esp32c6-board** under **Tools → Board → elegoo-esp32c6-board**.

## Upload Your First Sketch

1. Connect the board to your computer using a USB Type-C data cable.
2. Select the board's serial port under **Tools → Port**.
3. Open **File → Examples → ElegooBoard → BoardCheck** and click **Upload**.
4. Open the Serial Monitor and set the baud rate to **115200** to view board information. The example turns the RGB LED green; holding BOOT turns it red.

If the serial port does not appear or uploading fails, hold **BOOT**, press and release **RST**, then release **BOOT**. Select the port again and retry uploading. If the sketch does not run after the first upload, press **RST** once.

## Pin Reference

| Function | Pins |
| --- | --- |
| RGB LED | GPIO8; control with `RGB_BUILTIN` |
| BOOT button | GPIO9; active low |
| I²C | SDA: GPIO6; SCL: GPIO7 |
| UART0 | TX: GPIO16; RX: GPIO17 |
| Default SPI pins | SS: GPIO18; MOSI: GPIO19; MISO: GPIO20; SCK: GPIO21 |

USB serial is enabled by default and available through `Serial`. Calling `Wire.begin()` uses the I²C pins listed above. The default Flash configuration is 4MB. If your hardware has a different capacity, select the correct **Tools → Flash Size** setting and a matching partition scheme.

## Resources

- [Board schematic](doc/ESP32C6.pdf)
- [Project repository](https://github.com/ELEGOO-STEM/ELEGOO-ESP32-C6)
