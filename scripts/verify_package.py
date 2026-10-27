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
INDEX_NAME = "package_elegoo_esp32c6_index.json"


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
    package, = index["packages"]
    platform = package["platforms"][0]
    require(platform["name"] == "ELEGOO", "Incorrect Boards Manager platform name")
    archive_path = args.dist / platform["archiveFileName"]
    with archive_path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    require(platform["checksum"] == "SHA-256:" + digest, "Archive SHA-256 mismatch")
    require(int(platform["size"]) == archive_path.stat().st_size, "Archive size mismatch")
    available = {(tool["name"], tool["version"]) for tool in package["tools"]}
    for dep in platform["toolsDependencies"]:
        require(dep["packager"] == package["name"], "Dependency is not self-contained")
        require((dep["name"], dep["version"]) in available, "Missing tool definition")
    with zipfile.ZipFile(archive_path) as archive:
        require(archive.testzip() is None, "Corrupt ZIP entry")
        root = archive.namelist()[0].split("/")[0]
        board_text = archive.read(f"{root}/boards.txt").decode()
        board = properties(board_text)
        require([key for key in board if key.endswith(".name")] == ["elegoo_esp32c6.name"],
                "Package must expose exactly one board")
        require(board["elegoo_esp32c6.name"] == "ELEGOO-ESP32-C6", "Incorrect board menu entry")
        for key, value in {"build.mcu": "esp32c6", "build.variant": "elegoo_esp32c6",
                           "build.cdc_on_boot": "1", "build.board": "ELEGOO_ESP32C6"}.items():
            require(board["elegoo_esp32c6." + key] == value, f"Incorrect property {key}")
        for menu, first in (("CDCOnBoot", "cdc"), ("FlashMode", "dio")):
            choices = [key for key in board if key.startswith(f"elegoo_esp32c6.menu.{menu}.")]
            require(choices[0] == f"elegoo_esp32c6.menu.{menu}.{first}", "Incorrect default menu option")
        platform_properties = properties(archive.read(f"{root}/platform.txt").decode())
        require(platform_properties["name"] == "ELEGOO", "Incorrect board menu group")
        require(platform_properties["version"] == platform["version"],
                "Platform version mismatch")
        require(archive.read(f"{root}/variants/elegoo_esp32c6/pins_arduino.h") ==
                (ROOT / "variants/elegoo_esp32c6/pins_arduino.h").read_bytes(), "Variant differs from source")
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
    config = work / "arduino-cli.yaml"
    config.write_text(json.dumps({
        "directories": {"data": str(work / "data"), "downloads": str(work / "downloads"), "user": str(work / "sketchbook")},
        "board_manager": {"additional_urls": [f"{base}/{test_name}"]},
    }, indent=2), encoding="utf-8")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    commands = [
        ["core", "update-index"],
        ["core", "install", f"elegoo:esp32@{platform['version']}"],
        ["board", "details", "--fqbn", "elegoo:esp32:elegoo_esp32c6", "--format", "json"],
        ["compile", "--fqbn", "elegoo:esp32:elegoo_esp32c6", "--warnings", "default",
         "--build-path", str(work / "build"), str(ROOT / "examples/BoardCheck")],
    ]
    try:
        for number, command in enumerate(commands, 1):
            print("arduino-cli " + " ".join(command), flush=True)
            result = subprocess.run(["arduino-cli", "--config-file", str(config), *command],
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                    encoding="utf-8", errors="replace", timeout=1800)
            (work / f"{number}-{command[0]}.log").write_text(result.stdout, encoding="utf-8")
            if command[0] == "board" and result.returncode == 0:
                print(f"Board metadata saved to {work / f'{number}-board.log'}", flush=True)
            else:
                print(result.stdout, flush=True)
            require(result.returncode == 0, f"Arduino CLI failed (log: {work / f'{number}-{command[0]}.log'})")
        details = json.loads((work / "3-board.log").read_text(encoding="utf-8"))
        require(details["name"] == "ELEGOO-ESP32-C6", "Installed board has an incorrect menu entry")
        require(details["platform"]["name"] == "ELEGOO", "Installed board has an incorrect menu group")
        options = {option["option"]: next(value["value"] for value in option["values"] if value.get("selected"))
                   for option in details["config_options"]}
        require(options["CDCOnBoot"] == "cdc", "IDE default did not enable USB CDC")
        require(options["FlashSize"] == "4M", "Unexpected default Flash size")
        require(options["FlashMode"] == "dio", "Unexpected default Flash mode")
        print("PASS: isolated Boards Manager installation, IDE defaults and BoardCheck compilation", flush=True)
    finally:
        server.shutdown()
        server.server_close()
        test_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
