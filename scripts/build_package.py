#!/usr/bin/env python3
"""Build a self-contained Arduino package index and an immutable board archive.

Python 3.11+, standard library only. Tool binaries stay at Espressif's URLs;
their exact versions, sizes and checksums are pinned in config/upstream.json.
"""
import argparse
import copy
import hashlib
import json
import re
import shutil
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_NAME = "package_elegoo_esp32_index.json"
LEGACY_INDEX_NAME = "package_elegoo_esp32c6_index.json"
BOARDS = {
    "elegoo_esp32c6": {
        "upstream": "esp32c6", "name": "ELEGOO-ESP32-C6", "macro": "ELEGOO_ESP32C6",
        "properties": {"build.flash_mode": "dio", "build.boot": "dio"},
        "menus": {"CDCOnBoot": "cdc", "FlashMode": "dio"},
    },
    "elegoo_esp32s3_bot_cam": {
        "upstream": "esp32s3", "name": "ELEGOO ESP32-S3 BOT CAM", "macro": "ELEGOO_ESP32S3_BOT_CAM",
        "properties": {"build.flash_size": "8MB", "build.boot": "qio",
                       "build.partitions": "default_8MB",
                       "build.psram_type": "opi", "build.defines": "-DBOARD_HAS_PSRAM"},
        "menus": {"CDCOnBoot": "cdc", "FlashMode": "qio", "FlashSize": "8M",
                  "PSRAM": "opi", "PartitionScheme": "default_8MB"},
    },
}
PACKAGER = "elegoo"
PLATFORM_NAME = "ELEGOO"


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def checked_archive(path, metadata):
    return (path.is_file() and path.stat().st_size == int(metadata["size"])
            and "SHA-256:" + sha256(path) == metadata["checksum"])


def obtain_archive(metadata, cache, supplied):
    if supplied:
        if not checked_archive(supplied, metadata):
            raise ValueError(f"Upstream archive checksum/size mismatch: {supplied}")
        return supplied
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / metadata["archiveFileName"]
    if not checked_archive(path, metadata):
        partial = path.with_suffix(path.suffix + ".part")
        print(f"Downloading {metadata['url']}", flush=True)
        request = urllib.request.Request(metadata["url"], headers={"User-Agent": "elegoo-board-packager"})
        with urllib.request.urlopen(request, timeout=60) as source, partial.open("wb") as target:
            shutil.copyfileobj(source, target)
        if not checked_archive(partial, metadata):
            raise ValueError(f"Downloaded archive checksum/size mismatch: {partial}")
        partial.replace(path)
    return path


def board_definitions(upstream):
    # Retain pinned upstream menus/recipes, exposing only ELEGOO variants.
    all_lines = []
    used_menus = set()
    for board_id, config in BOARDS.items():
        source = config["upstream"]
        lines = [line.replace(source + ".", board_id + ".", 1)
                 for line in upstream.splitlines() if line.startswith(source + ".")]
        if not lines:
            raise ValueError(f"Pinned upstream archive has no {source} board")
        replacements = {"name": config["name"], "build.variant": board_id,
                        "build.board": config["macro"], "build.cdc_on_boot": "1",
                        **config["properties"]}
        for key, value in replacements.items():
            prop = f"{board_id}.{key}="
            if not any(line.startswith(prop) for line in lines):
                raise ValueError(f"Missing upstream board property: {source}.{key}")
            lines = [prop + value if line.startswith(prop) else line for line in lines]
        # Arduino selects the first menu option, overriding build.* defaults.
        # Move complete option groups so IDE defaults match the fitted module.
        for menu, preferred in config["menus"].items():
            prefix = f"{board_id}.menu.{menu}."
            if not any(line.startswith(prefix + preferred + "=") for line in lines):
                raise ValueError(f"Missing upstream menu option: {source}.{menu}.{preferred}")
            start = next(i for i, line in enumerate(lines) if line.startswith(prefix))
            options = [line for line in lines if line.startswith(prefix)]
            options.sort(key=lambda line: not line.startswith(prefix + preferred + ".")
                         and not line.startswith(prefix + preferred + "="))
            lines = [line for line in lines if not line.startswith(prefix)]
            lines[start:start] = options
        used_menus.update(line.split(".")[2] for line in lines if line.startswith(f"{board_id}.menu."))
        all_lines.extend([""] + lines)
    menus = [line for line in upstream.splitlines()
             if line.startswith("menu.") and line.split(".", 1)[1].split("=", 1)[0] in used_menus]
    return "# Generated from pinned Espressif ESP32-C6/S3 configurations.\n" + "\n".join(menus + all_lines) + "\n"


def write_member(archive, name, data, executable=False):
    info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
    info.create_system = 3
    info.external_attr = (0o100755 if executable else 0o100644) << 16
    archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def build_archive(upstream, output, version):
    top = f"ELEGOO-ESP32-{version}"
    with zipfile.ZipFile(upstream) as source, zipfile.ZipFile(output, "w") as target:
        roots = {item.filename.split("/", 1)[0] for item in source.infolist()}
        if len(roots) != 1:
            raise ValueError("Upstream archive must have exactly one root directory")
        for item in sorted(source.infolist(), key=lambda value: value.filename):
            parts = item.filename.split("/", 1)
            if len(parts) != 2 or item.is_dir():
                continue
            relative = parts[1]
            if ".." in Path(relative).parts or relative.startswith("/"):
                raise ValueError(f"Unsafe archive entry: {relative}")
            if relative.startswith("variants/"):
                continue
            data = source.read(item)
            if relative == "boards.txt":
                data = board_definitions(data.decode("utf-8")).encode("utf-8")
            elif relative == "platform.txt":
                text = data.decode("utf-8")
                text = re.sub(r"^name=.*$", "name=" + PLATFORM_NAME, text, count=1, flags=re.M)
                text = re.sub(r"^version=.*$", "version=" + version, text, count=1, flags=re.M)
                data = text.encode("utf-8")
            write_member(target, f"{top}/{relative}", data, bool((item.external_attr >> 16) & 0o111))
        for board_id in BOARDS:
            write_member(target, f"{top}/variants/{board_id}/pins_arduino.h",
                         (ROOT / f"variants/{board_id}/pins_arduino.h").read_bytes())
        for path in sorted((ROOT / "examples").rglob("*.ino")):
            write_member(target, f"{top}/libraries/ElegooBoard/examples/{path.relative_to(ROOT / 'examples').as_posix()}",
                         path.read_bytes())
        write_member(target, f"{top}/libraries/ElegooBoard/library.properties",
                     f"name=ElegooBoard\nversion={version}\nauthor=Board contributors\nmaintainer=Board contributors\n"
                     "sentence=Board verification examples for ELEGOO ESP32 boards.\n"
                     "paragraph=Check USB serial, LEDs, BOOT, I2C and the BOT CAM camera.\n"
                     "category=Other\narchitectures=esp32\n")
        write_member(target, f"{top}/ELEGOO_BOARD_NOTICE.txt",
                     "Boards: ELEGOO-ESP32-C6; ELEGOO ESP32-S3 BOT CAM\n"
                     "Based on Espressif Arduino-ESP32; upstream licenses retained.\n"
                     "Board-specific changes: pin variants, board defaults and C6/S3 package metadata.\n"
                     "C6: RGB=GPIO8; BOOT=GPIO9; SDA=GPIO6; SCL=GPIO7; Flash=4MB.\n"
                     "BOT CAM: LED=GPIO46 (active low); BOOT=GPIO0; SDA=GPIO4; SCL=GPIO5.\n"
                     "BOT CAM module: ESP32-S3-WROOM-1-N8R8; Flash=8MB QIO; PSRAM=8MB OPI.\n"
                     "Native USB CDC enabled on both boards.\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    destination = parser.add_mutually_exclusive_group(required=True)
    destination.add_argument("--repository", help="Public GitHub OWNER/REPO")
    destination.add_argument("--base-url", help="HTTP(S) directory hosting the ZIP and index")
    parser.add_argument("--version", default=json.loads((ROOT / "package.json").read_text())["version"])
    parser.add_argument("--upstream-archive", type=Path)
    parser.add_argument("--cache-dir", type=Path, default=ROOT / ".cache")
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    parser.add_argument("--previous-index", type=Path, help="Keep previously published releases in the new index")
    args = parser.parse_args()
    if not re.fullmatch(r"\d+\.\d+\.\d+", args.version):
        parser.error("Use a release version such as 1.0.0")
    if args.repository:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repository):
            parser.error("--repository must be OWNER/REPO")
        website = f"https://github.com/{args.repository}"
        base = f"{website}/releases/download/v{args.version}"
        index_url = f"{website}/releases/latest/download/{INDEX_NAME}"
    else:
        base = args.base_url.rstrip("/")
        parsed = urllib.parse.urlparse(base)
        if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.query or parsed.fragment:
            parser.error("--base-url must be an HTTP(S) directory URL without query or fragment")
        website = base
        index_url = f"{base}/{INDEX_NAME}"
    locked = json.loads((ROOT / "config/upstream.json").read_text(encoding="utf-8"))
    upstream = obtain_archive(locked["platform"], args.cache_dir, args.upstream_archive)
    args.output.mkdir(parents=True, exist_ok=True)
    archive_name = f"ELEGOO-ESP32-{args.version}.zip"
    archive_path = args.output / archive_name
    build_archive(upstream, archive_path, args.version)
    dependencies = [dict(dep, packager=PACKAGER) for dep in locked["platform"]["toolsDependencies"]]
    platform = {
        "name": PLATFORM_NAME, "architecture": "esp32", "version": args.version,
        "category": "Contributed", "url": f"{base}/{archive_name}",
        "archiveFileName": archive_name, "checksum": "SHA-256:" + sha256(archive_path),
        "size": str(archive_path.stat().st_size), "boards": [{"name": item["name"]} for item in BOARDS.values()],
        "toolsDependencies": dependencies, "help": {"online": website},
    }
    package = {
        "name": PACKAGER, "maintainer": PLATFORM_NAME,
        "websiteURL": website, "email": "", "help": {"online": website},
        "platforms": [platform], "tools": copy.deepcopy(locked["tools"]),
    }
    if args.previous_index:
        previous = json.loads(args.previous_index.read_text(encoding="utf-8"))
        old = next(item for item in previous["packages"] if item["name"] == PACKAGER)
        package["platforms"] += [item for item in old["platforms"] if item["version"] != args.version]
        known = {(item["name"], item["version"]) for item in package["tools"]}
        package["tools"] += [item for item in old["tools"] if (item["name"], item["version"]) not in known]
    index_text = json.dumps({"packages": [package]}, ensure_ascii=False, indent=2) + "\n"
    for index_name in (INDEX_NAME, LEGACY_INDEX_NAME):
        (args.output / index_name).write_text(index_text, encoding="utf-8")
    (args.output / "SHA256SUMS").write_text(f"{sha256(archive_path)}  {archive_name}\n", encoding="utf-8")
    (args.output / "install-url.txt").write_text(index_url + "\n", encoding="utf-8")
    print(f"Board archive: {archive_path}")
    print(f"Boards Manager URL (available after hosting): {index_url}")


if __name__ == "__main__":
    main()
