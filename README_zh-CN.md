# ELEGOO-ESP32

[English](README.md) | 简体中文

ELEGOO ESP32 系列开发板的 Arduino IDE 支持包。当前支持：**ELEGOO-ESP32-C6** 和 **ELEGOO ESP32-S3 BOT CAM**。

## ELEGOO-ESP32-C6

ELEGOO-ESP32-C6 板载 USB Type-C 接口、RGB LED、BOOT 和 RST 按键，提供 GPIO、I²C、SPI 和 UART 接口，适用于电子教学、传感器应用和物联网项目。

| 项目 | 说明 |
| --- | --- |
| 开发板名称 | `ELEGOO-ESP32-C6` |
| 主控芯片 | ESP32-C6，160MHz RISC-V 处理器 |
| Flash 默认配置 | 4MB |
| USB 接口 | USB Type-C，支持程序上传和串口通信 |
| 板载指示灯 | 可编程 RGB LED |
| 板载按键 | BOOT、RST |

## ELEGOO ESP32-S3 BOT CAM

基于 **ESP32-S3-WROOM-1-N8R8** 模组的摄像头开发板，板载原生 USB Type-C、24 针 DVP 摄像头接口、P1 串口接口、绿色状态 LED，以及 BOOT、RST 按键。

| 项目 | 说明 |
| --- | --- |
| 开发板名称 | `ELEGOO ESP32-S3 BOT CAM` |
| 主控芯片 | ESP32-S3，双核 Xtensa LX7，240MHz |
| Flash | 8MB，默认 QIO 80MHz |
| PSRAM | 8MB，默认启用 OPI PSRAM |
| 分区方案 | Default 8MB with spiffs（3MB 应用程序） |
| USB 默认配置 | Hardware CDC and JTAG，USB CDC On Boot 已开启 |
| 板载指示灯 | GPIO46 绿色状态 LED（低电平点亮）、红色电源 LED |

存储配置按已确认的实物模组型号设置，容量及接口类型见 [Espressif 模组数据手册](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf)。

## Arduino IDE 安装

1. 打开 Arduino IDE，进入 **文件 → 首选项**，在 **附加开发板管理器网址** 中添加以下链接：

   ```text
   https://github.com/ELEGOO-STEM/ELEGOO-ESP32/releases/latest/download/package_elegoo_esp32_index.json
   ```

2. 打开 **开发板管理器**，搜索 `ELEGOO`，安装 **ELEGOO** 开发板包。
3. 安装完成后，在 **工具 → 开发板 → ELEGOO** 中选择 **ELEGOO-ESP32-C6** 或 **ELEGOO ESP32-S3 BOT CAM**。

## 上传第一个程序

1. 使用支持数据传输的 USB Type-C 线连接开发板与电脑。
2. 在 **工具 → 端口** 中选择开发板对应的串口。
3. 打开 **文件 → 示例 → ElegooBoard → BoardCheck**，点击 **上传**。
4. 打开串口监视器，将波特率设为 **115200**，查看开发板信息、检测到的 Flash 和 PSRAM 容量。C6 的 RGB LED 默认显示绿色，按住 BOOT 后显示红色；BOT CAM 按住 BOOT 后点亮绿色 LED。

BOT CAM 可打开 **文件 → 示例 → ElegooBoard → CameraCheck** 检查摄像头初始化和采集。需连接兼容的 JPEG DVP 摄像头（例如 OV2640）；示例输出图像尺寸及 JPEG 字节数，不提供视频流。请保持 **Flash Size：8MB**、**PSRAM：OPI PSRAM**、**Partition Scheme：Default 8MB with spiffs**。

若无法识别串口或上传失败，请按住 **BOOT**，按下并松开 **RST**，再松开 **BOOT**，随后重新选择端口并上传。首次上传后如程序未运行，按一下 **RST**。

## ELEGOO-ESP32-C6 常用引脚

| 功能 | 引脚 |
| --- | --- |
| RGB LED | GPIO8，使用 `RGB_BUILTIN` 控制 |
| BOOT 按键 | GPIO9，按下为低电平 |
| I²C | SDA：GPIO6；SCL：GPIO7 |
| UART0 | TX：GPIO16；RX：GPIO17 |
| SPI 默认引脚 | SS：GPIO18；MOSI：GPIO19；MISO：GPIO20；SCK：GPIO21 |

USB 串口默认开启，可直接使用 `Serial`；调用 `Wire.begin()` 即使用上表中的 I²C 引脚。Flash 默认配置为 4MB，如所用硬件容量不同，请在 **工具 → Flash Size** 中选择对应容量，并匹配分区方案。

## ELEGOO ESP32-S3 BOT CAM 常用引脚

| 功能 | 引脚 |
| --- | --- |
| 绿色状态 LED | GPIO46，使用 `LED_BUILTIN`；LOW 点亮、HIGH 熄灭；非 RGB LED |
| BOOT 按键 | GPIO0，按下为低电平 |
| 摄像头 SCCB / 默认 I²C | SDA：GPIO4；SCL：GPIO5 |
| P1 串口接口 | 1 脚：RX GPIO3；2 脚：TX GPIO40；3 脚：GND；4 脚：EXT_5V |
| 摄像头 XCLK / PCLK | GPIO15 / GPIO13 |
| 摄像头 VSYNC / HREF | GPIO6 / GPIO7 |
| 摄像头 D0–D7（J1 Y2–Y9） | GPIO11、GPIO9、GPIO8、GPIO10、GPIO12、GPIO18、GPIO17、GPIO16 |
| 摄像头 RESET / PWDN | 硬件上拉 / 下拉；`CAM_PIN_RESET` / `CAM_PIN_PWDN` 均为 -1 |
| 软件 SPI 默认引脚 | SS：GPIO21；MOSI：GPIO47；MISO：GPIO48；SCK：GPIO14 |

原生 USB 使用 `Serial`；P1 串口使用 `Serial1.begin(115200, SERIAL_8N1, RX, TX)`。模组 UART0 焊盘为 GPIO43/44。SPI 默认引脚是未占用的模组焊盘，板上没有专用 SPI 接口。GPIO35–37 由模组 OPI PSRAM 占用。

板型提供 `CAM_PIN_*` 摄像头引脚宏。`Wire.begin()` 与摄像头共用 GPIO4/5 总线，使用时需协调摄像头驱动对总线的访问；`CameraCheck` 直接由 `esp_camera_init()` 初始化该总线。

## 硬件资料

- [ELEGOO-ESP32-C6 原理图](doc/ESP32C6.pdf)
- [ELEGOO ESP32-S3 BOT CAM V2.2 原理图](doc/esp32S3_Camera_PCB_V2.2.pdf)
- [项目主页](https://github.com/ELEGOO-STEM/ELEGOO-ESP32)
