from pathlib import Path
import urllib.request
import json
import shutil
import subprocess

DOWNLOADS = Path("Downloads")
RELEASES = Path("Releases")

def download(url):
	with urllib.request.urlopen(url) as resp:
		return resp.read()

# super crappy msi format parser just to find required .cab files
def get_msi_cabs(msi):
	index = 0
	while True:
		index = msi.find(b".cab", index+4)
		if index < 0:
			return
		yield msi[index-32:index+4].decode("ascii")

def get_sub_dirs(path):
	return [x for x in path.iterdir() if x.is_dir()]

MANIFEST_URL = "https://aka.ms/vs/17/release/channel"
print("Checking Visual Studio Manifest...")
chman = json.loads(download(MANIFEST_URL))
vsman_url = chman["channelItems"][0]["payloads"][0]["url"]
license = chman["channelItems"][1]["localizedResources"][0]["license"]
vsman = json.loads(download(vsman_url))
packages = vsman["packages"]

version = ""
payloads = []
for i in range(len(packages)-1, -1, -1):
	if packages[i]["id"].startswith("Win11SDK_10.0."):	
		version = packages[i]["version"]
		payloads = packages[i]["payloads"]
		break

def download_payload(filename):
	for p in payloads:
		if p["fileName"] == "Installers\\" + filename:
			data = download(p["url"])
			with open(DOWNLOADS / filename, "wb") as file:
				file.write(data)
			return data			

yes = input(f"Do you accept Microsoft Visual Studio license: {license} [Y/N] ? ")
if yes.upper() not in ["", "YES", "Y"]:
	exit(0)

MSI_FILENAME = "Windows SDK Signing Tools-x86_en-us.msi"
print(f"Downloading {MSI_FILENAME}...")
DOWNLOADS.mkdir(exist_ok=True)
msi = download_payload(MSI_FILENAME)			
cabs = get_msi_cabs(msi)
for cab in cabs:
	download_payload(cab)

print(f"Unpacking {MSI_FILENAME}...")
ARCHIVES = DOWNLOADS / "Archives"
shutil.rmtree(ARCHIVES, ignore_errors=True)
subprocess.run(["msiexec.exe", "/a", DOWNLOADS / MSI_FILENAME, "/quiet", "/qn", f"TARGETDIR={ARCHIVES.resolve()}"])

print(f"Creating Zip in {RELEASES.resolve()}...")
SDK = get_sub_dirs(ARCHIVES / "Windows Kits/10/bin")[0]
ARCHS = get_sub_dirs(SDK)
for arch in ARCHS:
	shutil.make_archive(RELEASES / f"SignTool-{version}-{arch.name}", "zip", arch)

print("Done!")
