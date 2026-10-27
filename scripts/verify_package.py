#!/usr/bin/env python3
"""Validate release artifacts; optionally install and compile in isolated CLI data."""
import argparse
import functools
import hashlib
import http.server
import json
import shutil
import subprocess
import threading
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_NAME = "package_elegoo_esp32_index.json"
LEGACY_INDEX_NAME = "package_elegoo_esp32c6_index.json"
BOARDS = {
    "elegoo_esp32c6": {
        "name": "ELEGOO-ESP32-C6", "mcu": "esp32c6", "macro": "ELEGOO_ESP32C6",
        "options": {"CDCOnBoot": "cdc", "FlashMode": "dio", "FlashSize": "4M"},
        "examples": ["BoardCheck"],
    },
    "elegoo_esp32s3_bot_cam": {
        "name": "ELEGOO ESP32-S3 BOT CAM", "mcu": "esp32s3", "macro": "ELEGOO_ESP32S3_BOT_CAM",
        "options": {"CDCOnBoot": "cdc", "USBMode": "hwcdc", "UploadMode": "default",
                    "FlashMode": "qio", "FlashSize": "8M", "PSRAM": "opi", "PartitionScheme": "default_8MB"},
        "examples": ["BoardCheck", "CameraCheck"],
    },
}


def properties(text):
    return dict(line.split("=", 1) for line in text.splitlines()
                if "=" in line and not line.lstrip().startswith("#"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compile", action="store_true")
    parser.add_argument("--dist", type=Path, default=ROOT / "dist")
    parser.add_argument("--work-dir", type=Path, default=ROOT / "tmp/verification")
    args = parser.parse_args()
    index = json.loads((args.dist / INDEX_NAME).read_text(encoding="utf-8"))
    require((args.dist / LEGACY_INDEX_NAME).read_bytes() == (args.dist / INDEX_NAME).read_bytes(),
            "Legacy installation index must match the current index")
    package, = index["packages"]
    platform = package["platforms"][0]
    require(platform["name"] == "ELEGOO", "Incorrect Boards Manager platform name")
    require(platform["boards"] == [{"name": config["name"]} for config in BOARDS.values()],
            "Incorrect Boards Manager board list")
    archive_path = args.dist / platform["archiveFileName"]
    with archive_path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    require(platform["checksum"] == "SHA-256:" + digest, "Archive SHA-256 mismatch")
    require(int(platform["size"]) == archive_path.stat().st_size, "Archive size mismatch")
    available = {(tool["name"], tool["version"]) for tool in package["tools"]}
    for dep in platform["toolsDependencies"]:
        require(dep["packager"] == package["name"], "Dependency is not self-contained")
        require((dep["name"], dep["version"]) in available, "Missing tool definition")
    required_tools = {"esp-rv32", "esp32c6-libs", "esp-x32", "xtensa-esp-elf-gdb", "esp32s3-libs", "dfu-util"}
    require(required_tools <= {dep["name"] for dep in platform["toolsDependencies"]},
            "Missing C6/S3 tool dependency")
    with zipfile.ZipFile(archive_path) as archive:
        require(archive.testzip() is None, "Corrupt ZIP entry")
        root = archive.namelist()[0].split("/")[0]
        board_text = archive.read(f"{root}/boards.txt").decode()
        board = properties(board_text)
        require([key for key in board if key.endswith(".name")] == [f"{board_id}.name" for board_id in BOARDS],
                "Package must expose exactly the supported ELEGOO boards")
        for board_id, config in BOARDS.items():
            for key, value in {"name": config["name"], "build.mcu": config["mcu"], "build.variant": board_id,
                               "build.cdc_on_boot": "1", "build.board": config["macro"]}.items():
                require(board[f"{board_id}.{key}"] == value, f"Incorrect property {board_id}.{key}")
            for menu, first in config["options"].items():
                choices = [key for key in board if key.startswith(f"{board_id}.menu.{menu}.")]
                require(choices[0] == f"{board_id}.menu.{menu}.{first}", f"Incorrect default {board_id}.{menu}")
            require(archive.read(f"{root}/variants/{board_id}/pins_arduino.h") ==
                    (ROOT / f"variants/{board_id}/pins_arduino.h").read_bytes(), "Variant differs from source")
            for example in config["examples"]:
                require(archive.read(f"{root}/libraries/ElegooBoard/examples/{example}/{example}.ino") ==
                        (ROOT / f"examples/{example}/{example}.ino").read_bytes(), "Example differs from source")
        for key, value in {"build.flash_size": "8MB", "build.psram_type": "opi", "build.boot": "qio",
                           "build.defines": "-DBOARD_HAS_PSRAM", "build.partitions": "default_8MB",
                           "menu.PartitionScheme.default_8MB.upload.maximum_size": "3342336"}.items():
            require(board[f"elegoo_esp32s3_bot_cam.{key}"] == value, f"Incorrect N8R8 property {key}")
        platform_properties = properties(archive.read(f"{root}/platform.txt").decode())
        require(platform_properties["name"] == "ELEGOO", "Incorrect board menu group")
        require(platform_properties["version"] == platform["version"],
                "Platform version mismatch")
        require(any(name.split("/")[-1].startswith("LICENSE") for name in archive.namelist()),
                "Upstream license is missing")
    print("PASS: ZIP, SHA-256, size, board defaults, variant, license and tool dependencies", flush=True)
    if not args.compile:
        return
    require(shutil.which("arduino-cli") is not None, "arduino-cli is required for --compile")
    work = args.work_dir.resolve()
    work.mkdir(parents=True, exist_ok=True)

    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *_):
            pass

    handler = functools.partial(Handler, directory=str(args.dist.resolve()))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    base = f"http://127.0.0.1:{server.server_port}"
    # Serve a test-only index so CI can install artifacts before a release exists.
    # Only the platform URL changes; its bytes and checksum remain the release's.
    local_index = json.loads(json.dumps(index))
    local_index["packages"][0]["platforms"][0]["url"] = f"{base}/{platform['archiveFileName']}"
    test_name = "package_elegoo_verify_index.json"
    test_path = args.dist / test_name
    test_path.write_text(json.dumps(local_index), encoding="utf-8")
    cli_config = work / "arduino-cli.yaml"
    cli_config.write_text(json.dumps({
        "directories": {"data": str(work / "data"), "downloads": str(work / "downloads"), "user": str(work / "sketchbook")},
        "board_manager": {"additional_urls": [f"{base}/{test_name}"]},
    }, indent=2), encoding="utf-8")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    commands = [
        ["core", "update-index"],
        ["core", "install", f"elegoo:esp32@{platform['version']}"],
    ]
    board_logs = {}
    for board_id, config in BOARDS.items():
        fqbn = f"elegoo:esp32:{board_id}"
        commands.append(["board", "details", "--fqbn", fqbn, "--format", "json"])
        board_logs[board_id] = work / f"{len(commands)}-board.log"
        for example in config["examples"]:
            commands.append(["compile", "--fqbn", fqbn, "--warnings", "default",
                             "--build-path", str(work / f"build-{board_id}-{example}"), str(ROOT / f"examples/{example}")])
    try:
        for number, command in enumerate(commands, 1):
            print("arduino-cli " + " ".join(command), flush=True)
            result = subprocess.run(["arduino-cli", "--config-file", str(cli_config), *command],
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                    encoding="utf-8", errors="replace", timeout=1800)
            (work / f"{number}-{command[0]}.log").write_text(result.stdout, encoding="utf-8")
            if command[0] == "board" and result.returncode == 0:
                print(f"Board metadata saved to {work / f'{number}-board.log'}", flush=True)
            else:
                print(result.stdout, flush=True)
            require(result.returncode == 0, f"Arduino CLI failed (log: {work / f'{number}-{command[0]}.log'})")
            if command[:2] == ["core", "install"]:
                installed = work / "data/packages/elegoo/hardware/esp32" / platform["version"]
                files = ["boards.txt", "platform.txt"]
                files += [f"variants/{board_id}/pins_arduino.h" for board_id in BOARDS]
                files += [f"libraries/ElegooBoard/examples/{example}/{example}.ino"
                          for example in {item for config in BOARDS.values() for item in config["examples"]}]
                with zipfile.ZipFile(archive_path) as archive:
                    for relative in files:
                        require((installed / relative).read_bytes() == archive.read(f"{root}/{relative}"),
                                f"Installed file differs from release archive: {relative}")
        for board_id, path in board_logs.items():
            config = BOARDS[board_id]
            details = json.loads(path.read_text(encoding="utf-8"))
            require(details["name"] == config["name"], "Installed board has an incorrect menu entry")
            require(details["platform"]["name"] == "ELEGOO", "Installed board has an incorrect menu group")
            options = {option["option"]: next(value["value"] for value in option["values"] if value.get("selected"))
                       for option in details["config_options"]}
            for option, expected in config["options"].items():
                require(options[option] == expected, f"Unexpected default {board_id}.{option}")
        print("PASS: isolated Boards Manager installation, C6/S3 IDE defaults and all board examples", flush=True)
    finally:
        server.shutdown()
        server.server_close()
        test_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
