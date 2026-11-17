from pathlib import Path
import urllib.request
import json
import re
import shutil
import subprocess
import sys

DOWNLOADS = Path("Downloads")
RELEASES = Path("Releases")
MANIFEST_URL = "https://aka.ms/vs/stable/channel"
MSI_FILENAME = "Windows SDK Signing Tools-x86_en-us.msi"


def download(url: str) -> bytes:
    with urllib.request.urlopen(url) as resp:
        return resp.read()


def get_msi_cabs(msi: bytes) -> set[str]:
    return {m.decode("ascii") for m in re.findall(rb"[0-9a-fA-F]{32}\.cab", msi)}


def get_sub_dirs(path: Path) -> list[Path]:
    return [x for x in path.iterdir() if x.is_dir()]


print("Checking Visual Studio Manifest...")
chman = json.loads(download(MANIFEST_URL))

vsman_url = next(
    p["url"]
    for item in chman["channelItems"]
    for p in item.get("payloads", [])
    if p.get("fileName", "").endswith(".vsman")
)
license_url = next(
    res["license"]
    for item in chman["channelItems"]
    for res in item.get("localizedResources", [])
    if "license" in res
)

yes = input(f"Do you accept Microsoft Visual Studio license: {license_url} [Y/n] ? ")
if yes.strip().upper() not in ("", "YES", "Y"):
    sys.exit(0)

print("Downloading package manifest (this may take a minute)...")
vsman = json.loads(download(vsman_url))

target_payload = f"Installers\\{MSI_FILENAME}"
matching_pkgs = [
    p
    for p in vsman["packages"]
    if any(pl.get("fileName") == target_payload for pl in p.get("payloads", []))
]
if not matching_pkgs:
    raise RuntimeError(f"No package containing {MSI_FILENAME} found in manifest.")

sdk_pkg = max(matching_pkgs, key=lambda p: tuple(map(int, p["version"].split("."))))
version = sdk_pkg["version"]
payloads = sdk_pkg["payloads"]
print(f"Found {sdk_pkg['id']} (version {version})")


def download_payload(filename: str) -> bytes:
    target = f"Installers\\{filename}"
    for p in payloads:
        if p.get("fileName") == target:
            data = download(p["url"])
            (DOWNLOADS / filename).write_bytes(data)
            return data
    raise FileNotFoundError(f"Payload not found in manifest: {target}")


print(f"Downloading {MSI_FILENAME}...")
DOWNLOADS.mkdir(exist_ok=True)
msi = download_payload(MSI_FILENAME)

for cab in get_msi_cabs(msi):
    print(f"Downloading {cab}...")
    download_payload(cab)

print(f"Unpacking {MSI_FILENAME}...")
ARCHIVES = DOWNLOADS / "Archives"
shutil.rmtree(ARCHIVES, ignore_errors=True)
subprocess.run(
    [
        "msiexec.exe",
        "/a",
        str(DOWNLOADS / MSI_FILENAME),
        "/quiet",
        "/qn",
        f"TARGETDIR={ARCHIVES.resolve()}",
    ],
    check=True,
)

RELEASES.mkdir(exist_ok=True)
print(f"Creating Zip in {RELEASES.resolve()}...")
sdk_dir = get_sub_dirs(ARCHIVES / "Windows Kits/10/bin")[0]
for arch in get_sub_dirs(sdk_dir):
    shutil.make_archive(str(RELEASES / f"SignTool-{version}-{arch.name}"), "zip", arch)

print("Done!")
