# SignTool.exe
Windows SDK Signing Tools for Desktop Apps: Extract from Windows 11 SDK.

## Download
Download from [Releases](../../releases) or build latest version:
```
python signtool.py
```

## How to use
```
signtool.exe sign /f Cert.pfx /p <password> /fd SHA256 /td SHA256 /tr http://timestamp.com App.exe
```
