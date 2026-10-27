# elegoo-esp32c6-board

为自制 `elegoo-esp32c6-board` 提供 Arduino IDE 开发板管理器安装包。
硬件依据为 [ESP32C6 原理图](doc/ESP32C6.pdf)，日期 2026-10-16。

## 公开安装链接

仓库：[ELEGOO-STEM/ELEGOO-ESP32-C6](https://github.com/ELEGOO-STEM/ELEGOO-ESP32-C6)。
`v1.0.0` Release 发布成功后，在 Arduino IDE → 文件 → 首选项 → 附加开发板管理器网址中添加：

```text
https://github.com/ELEGOO-STEM/ELEGOO-ESP32-C6/releases/latest/download/package_elegoo_esp32c6_index.json
```

在开发板管理器搜索并安装 `elegoo-esp32c6-board`，随后在“工具 → 开发板”选择同名开发板。
Flash 当前按已确认的暂定方案使用 **4MB**；实际容量确定后可在工具菜单调整。

## 在本机立即安装

已生成的文件在 `dist/`。在项目目录运行以下命令，并在安装期间保持窗口打开：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/serve_local.ps1
```

把下面的网址加入 Arduino IDE → 文件 → 首选项 → 附加开发板管理器网址：

```text
http://127.0.0.1:8123/package_elegoo_esp32c6_index.json
```

打开“开发板管理器”，搜索 `elegoo-esp32c6-board` 并安装。随后选择：

```text
工具 → 开发板 → elegoo-esp32c6-board → elegoo-esp32c6-board
```

`127.0.0.1` 只对运行这个服务的电脑有效。公开分享请使用下文的 GitHub 发布流程。
首次打包会下载上游核心；安装时还需要访问 Espressif 在 GitHub 托管的工具链文件。
安装完成后可停止本地服务，编译和通过 USB 上传不需要本地服务继续运行。

## 发布一个可以分享的永久链接

仓库包含 `.github/workflows/release.yml`。将本项目提交到自己的**公开 GitHub 仓库**，然后推送版本标签：

```powershell
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions 会下载并校验固定版本的上游核心，生成 ZIP 和 JSON，在隔离环境实际安装并编译示例，成功后创建 Release。工作流需要仓库允许 Actions 使用 `contents: write` 权限。

发布成功后，用户在 Arduino IDE 首选项填入以下格式的地址。**将 `OWNER/REPO` 换成自己的 GitHub 用户名和仓库名；这段模板本身不是已上线链接。**

```text
https://github.com/OWNER/REPO/releases/latest/download/package_elegoo_esp32c6_index.json
```

索引使用稳定的 `latest` 下载地址，ZIP 使用带版本的不可变下载地址；更新时用户无需更换首选项链接。后续发布更高版本的 `vX.Y.Z` 标签即可。脚本默认版本来自 `package.json`；发布工作流使用标签版本。

如需手动打包并上传到 Release：

```powershell
python scripts/build_package.py --repository ELEGOO-STEM/ELEGOO-ESP32-C6 --version 1.0.0
```

上传 `dist/elegoo-esp32c6-board-1.0.0.zip`、`dist/package_elegoo_esp32c6_index.json` 和 `dist/SHA256SUMS` 到 `v1.0.0` Release。也可以使用自己的静态文件服务器：

```powershell
python scripts/build_package.py --base-url https://your-domain.example/arduino --version 1.0.0
```

将 ZIP 与 JSON 放在 `--base-url` 对应目录。最终首选项地址也会写入 `dist/install-url.txt`。
手动更新时传入 `--previous-index 旧索引文件`，可以保留旧版本入口；GitHub 工作流会自动保留。
发布前务必确认索引和其中 ZIP 的下载地址都能公开访问。

## 默认硬件配置

| 项目 | 设置 | 依据 |
| --- | --- | --- |
| 芯片 | ESP32-C6，160MHz | 原理图及官方 C6 配置 |
| 核心 | Arduino-ESP32 3.3.12 | `config/upstream.json` 固定版本 |
| Flash | 默认 4MB，DIO，80MHz | 容量未在原理图标明，暂用保守默认值 |
| USB | 原生 USB Serial/JTAG，默认开启 USB CDC | D−=GPIO12，D+=GPIO13 |
| `Serial` | USB CDC 串口 | 不使用板外 UART 转换芯片 |
| `TX` / `RX` | GPIO16 / GPIO17 | ESP32-C6 UART0，排针标为 U0TXD/U0RXD |
| `SDA` / `SCL` | GPIO6 / GPIO7 | 原理图 I²C 接口 |
| `PIN_RGB_LED` | GPIO8 | 原理图 RGB DIN |
| `LED_BUILTIN` / `RGB_BUILTIN` | 核心提供的 RGB 虚拟引脚 | 标准 Blink / `rgbLedWrite()` 可用 |
| `BOOT_BUILTIN` | GPIO9，按下为 LOW | 原理图 BOOT 按钮 |
| `SS` / `MOSI` / `MISO` / `SCK` | GPIO18 / 19 / 20 / 21 | 软件默认映射，均引至排针 |
| `A0`–`A6` | GPIO0–GPIO6 | ESP32-C6 ADC 映射 |

**Flash 容量需要按实际装配模组确认。** 若不是 4MB，请在“工具 → Flash Size”选择实际容量，并在“Partition Scheme”选择能容纳于该容量的分区表。例如 8MB 可选择 `8M with spiffs`；2MB 可选择 `Zigbee 2MB with spiffs`（这只选择分区，不会自动启用 Zigbee）。不要将 4MB 默认分区表用于 2MB Flash。

`Wire1` 的低功耗 I²C 引脚也固定为 GPIO6/7；不要让 `Wire` 和 `Wire1` 同时占用这两根引脚。
GPIO8 连接可寻址 RGB 灯，直接操作物理 GPIO8 不等同于普通单色 LED。
未分配自有 USB VID/PID，设备列表可能显示通用 ESP32 设备，请在 IDE 中手动选择本开发板。

## 首次烧录与检查

1. 使用可传输数据的 USB 线连接开发板并选择相应串口。
2. 如未出现串口或无法上传，按住 BOOT，按下并松开 RST，再松开 BOOT；重新选择出现的端口。
3. 打开“文件 → 示例 → ElegooBoard → BoardCheck”，编译并上传。
4. 如首次上传后未运行，按一下 RST。以 115200 打开串口监视器。
5. 示例打印实际检测到的 Flash 容量和默认引脚；RGB 灯通常显示绿色，按住 BOOT 显示红色。RGB 器件具体型号未在原理图中注明，灯协议按常见 WS2812 兼容器件配置，仍需实板确认。

`Serial0` 可用于 UART0；若关闭 USB CDC On Boot，`Serial` 的行为会随核心配置改为 UART。C6 的原生 USB 提供 CDC/JTAG，不支持 S2/S3 的 USB DFU 功能。

## 文件与验证

- `variants/elegoo_esp32c6/pins_arduino.h`：本板引脚。
- `config/upstream.json`：Espressif 官方索引的固定快照，含核心和所需工具的 URL、版本、大小与校验值。
- `scripts/build_package.py`：保留上游核心、库、上传配方与许可证，只替换开发板配置及 variant。
- `scripts/verify_package.py`：校验安装包、依赖完整性和默认菜单；`--compile` 会在 `tmp/verification/` 隔离安装并编译。
- `examples/BoardCheck/BoardCheck.ino`：USB 串口、RGB、BOOT 与引脚验证示例。

脚本仅依赖 Python 3.11+ 标准库；编译验证另需 `arduino-cli`：

```powershell
python scripts/verify_package.py
python scripts/verify_package.py --compile
```

2026-10-27 已在 Windows / Arduino CLI 1.5.0 验证：隔离的开发板包安装、默认 USB CDC/DIO/4MB 菜单、引脚静态断言、BoardCheck 示例编译、示例菜单发现，以及本地 HTTP 索引/ZIP 下载和 SHA-256 一致性。编译结果为程序 382306 字节、全局变量 22020 字节。测试复用了电脑上已安装且版本一致的编译工具，C6 3.3.12 SDK 独立安装。尚未连接实板烧录；Linux/macOS 发布流程需在实际 GitHub Actions 运行中验证。

安装包的 packager 为 `elegoo`，architecture 为 `esp32`，FQBN 为：

```text
elegoo:esp32:elegoo_esp32c6
```

工具依赖元数据包含在同一个索引中；用户不必额外添加 Espressif 索引或预装官方 ESP32 开发板包。仅安装 C6 所需的 RISC-V 工具、C6 SDK、上传与调试工具。

上游核心许可证及文件内版权声明原样保留在生成的 ZIP 中。自定义 variant 以 LGPL-2.1-or-later 提供。

参考：[Arduino 索引规范](https://docs.arduino.cc/arduino-cli/package_index_json-specification/)、[Espressif 官方索引](https://espressif.github.io/arduino-esp32/package_esp32_index.json)、[USB CDC 说明](https://docs.espressif.com/projects/arduino-esp32/en/latest/tutorials/cdc_dfu_flash.html)。
