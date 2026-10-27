# ELEGOO-ESP32

[English](README.md) | 简体中文

ELEGOO ESP32 系列开发板的 Arduino IDE 支持包。当前支持：**ELEGOO-ESP32-C6**。

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

## Arduino IDE 安装

1. 打开 Arduino IDE，进入 **文件 → 首选项**，在 **附加开发板管理器网址** 中添加以下链接：

   ```text
   https://github.com/ELEGOO-STEM/ELEGOO-ESP32/releases/latest/download/package_elegoo_esp32_index.json
   ```

2. 打开 **开发板管理器**，搜索 `ELEGOO`，安装 **ELEGOO** 开发板包。
3. 安装完成后，选择 **工具 → 开发板 → ELEGOO → ELEGOO-ESP32-C6**。

## 上传第一个程序

1. 使用支持数据传输的 USB Type-C 线连接开发板与电脑。
2. 在 **工具 → 端口** 中选择开发板对应的串口。
3. 打开 **文件 → 示例 → ElegooBoard → BoardCheck**，点击 **上传**。
4. 打开串口监视器，将波特率设为 **115200**，查看开发板信息。示例运行时，RGB LED 显示绿色，按住 BOOT 后显示红色。

若无法识别串口或上传失败，请按住 **BOOT**，按下并松开 **RST**，再松开 **BOOT**，随后重新选择端口并上传。首次上传后如程序未运行，按一下 **RST**。

## 常用引脚

| 功能 | 引脚 |
| --- | --- |
| RGB LED | GPIO8，使用 `RGB_BUILTIN` 控制 |
| BOOT 按键 | GPIO9，按下为低电平 |
| I²C | SDA：GPIO6；SCL：GPIO7 |
| UART0 | TX：GPIO16；RX：GPIO17 |
| SPI 默认引脚 | SS：GPIO18；MOSI：GPIO19；MISO：GPIO20；SCK：GPIO21 |

USB 串口默认开启，可直接使用 `Serial`；调用 `Wire.begin()` 即使用上表中的 I²C 引脚。Flash 默认配置为 4MB，如所用硬件容量不同，请在 **工具 → Flash Size** 中选择对应容量，并匹配分区方案。

## 硬件资料

- [ELEGOO-ESP32-C6 原理图](doc/ESP32C6.pdf)
- [项目主页](https://github.com/ELEGOO-STEM/ELEGOO-ESP32)
