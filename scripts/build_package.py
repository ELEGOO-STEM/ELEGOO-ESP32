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
INDEX_NAME = "package_elegoo_esp32c6_index.json"
BOARD_ID = "elegoo_esp32c6"
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
    # Keep upstream C6 menus/recipes, and only expose this board in the IDE.
    lines = [line for line in upstream.splitlines() if line.startswith("esp32c6.")]
    if not lines:
        raise ValueError("Pinned upstream archive has no esp32c6 board")
    lines = [line.replace("esp32c6.", BOARD_ID + ".", 1) for line in lines]
    replacements = {
        "name": "ELEGOO-ESP32-C6",
        "build.variant": BOARD_ID,
        "build.board": "ELEGOO_ESP32C6",
        "build.cdc_on_boot": "1",
        "build.flash_mode": "dio",
        "build.boot": "dio",
    }
    for key, value in replacements.items():
        prop = f"{BOARD_ID}.{key}="
        if not any(line.startswith(prop) for line in lines):
            raise ValueError(f"Missing upstream board property: {key}")
        lines = [prop + value if line.startswith(prop) else line for line in lines]
    # Arduino selects the first menu option, overriding build.* defaults.
    # Therefore move the entire enabled-CDC and DIO option groups first.
    for menu, preferred in (("CDCOnBoot", "cdc"), ("FlashMode", "dio")):
        prefix = f"{BOARD_ID}.menu.{menu}."
        start = next(i for i, line in enumerate(lines) if line.startswith(prefix))
        options = [line for line in lines if line.startswith(prefix)]
        options.sort(key=lambda line: not line.startswith(prefix + preferred + ".")
                     and not line.startswith(prefix + preferred + "="))
        lines = [line for line in lines if not line.startswith(prefix)]
        lines[start:start] = options
    used_menus = {line.split(".")[2] for line in lines if line.startswith(f"{BOARD_ID}.menu.")}
    menus = [line for line in upstream.splitlines()
             if line.startswith("menu.") and line.split(".", 1)[1].split("=", 1)[0] in used_menus]
    return "# Generated from pinned Espressif ESP32-C6 configuration.\n" + "\n".join(menus + [""] + lines) + "\n"


def write_member(archive, name, data, executable=False):
    info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
    info.create_system = 3
    info.external_attr = (0o100755 if executable else 0o100644) << 16
    archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def build_archive(upstream, output, version):
    top = f"ELEGOO-ESP32-C6-{version}"
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
        write_member(target, f"{top}/variants/{BOARD_ID}/pins_arduino.h",
                     (ROOT / f"variants/{BOARD_ID}/pins_arduino.h").read_bytes())
        for path in sorted((ROOT / "examples").rglob("*.ino")):
            write_member(target, f"{top}/libraries/ElegooBoard/examples/{path.relative_to(ROOT / 'examples').as_posix()}",
                         path.read_bytes())
        write_member(target, f"{top}/libraries/ElegooBoard/library.properties",
                     f"name=ElegooBoard\nversion={version}\nauthor=Board contributors\nmaintainer=Board contributors\n"
                     "sentence=Board verification example for ELEGOO-ESP32-C6.\n"
                     "paragraph=Check USB serial, RGB LED, BOOT and I2C pin defaults.\n"
                     "category=Other\narchitectures=esp32\n")
        write_member(target, f"{top}/ELEGOO_BOARD_NOTICE.txt",
                     "Board: ELEGOO-ESP32-C6\n"
                     "Based on Espressif Arduino-ESP32; upstream licenses retained.\n"
                     "Board-specific changes: pin variant, board defaults, C6-only package metadata.\n"
                     "RGB=GPIO8; BOOT=GPIO9; SDA=GPIO6; SCL=GPIO7; native USB CDC enabled.\n"
                     "Flash defaults to 4MB; verify the fitted module before uploading.\n")


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
    archive_name = f"ELEGOO-ESP32-C6-{args.version}.zip"
    archive_path = args.output / archive_name
    build_archive(upstream, archive_path, args.version)
    dependencies = [dict(dep, packager=PACKAGER) for dep in locked["platform"]["toolsDependencies"]]
    platform = {
        "name": PLATFORM_NAME, "architecture": "esp32", "version": args.version,
        "category": "Contributed", "url": f"{base}/{archive_name}",
        "archiveFileName": archive_name, "checksum": "SHA-256:" + sha256(archive_path),
        "size": str(archive_path.stat().st_size), "boards": [{"name": "ELEGOO-ESP32-C6"}],
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
    (args.output / INDEX_NAME).write_text(json.dumps({"packages": [package]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output / "SHA256SUMS").write_text(f"{sha256(archive_path)}  {archive_name}\n", encoding="utf-8")
    (args.output / "install-url.txt").write_text(index_url + "\n", encoding="utf-8")
    print(f"Board archive: {archive_path}")
    print(f"Boards Manager URL (available after hosting): {index_url}")


if __name__ == "__main__":
    main()
