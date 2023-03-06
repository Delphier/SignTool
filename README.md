# SignTool.exe
Windows SDK Signing Tools for Desktop Apps - Extract from Windows 11 SDK 10.0.22621.755

Download from [Releases](../../releases).

## How to use
```
signtool.exe sign /f Cert.pfx /p <password> /fd SHA256 /td SHA256 /tr http://timestamp.url.com App.exe
```
