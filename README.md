# PixelSync

Automatically sync iPhone photos and videos to a Google Pixel device for Google Photos backup.

## Vision

PixelSync creates a reliable pipeline:

iPhone → Windows → Pixel → Google Photos

## Planned Features

- USB iPhone import workflow
- Pixel USB detection
- Automatic photo transfer
- Duplicate detection
- Live Photo support
- Video support
- Background service
- System tray application
- Windows installer

## Status

🚧 Early Development

## Local iPhone import

PixelSync can read the iPhone camera roll locally over USB or Wi-Fi. It does
not require iCloud storage and never deletes media from the iPhone.

On Windows, install the optional libimobiledevice tools from PowerShell:

```powershell
.\scripts\setup_iphone_tools.ps1
```

The setup script downloads a pinned Windows release, verifies its SHA-256
checksum, and extracts it under `tools/libimobiledevice`. The tools are
provided by the independent libimobiledevice project under LGPL-2.1-or-later;
they are not committed to this repository.

For Wi-Fi discovery, first connect the iPhone over USB, trust the computer,
then enable **Show this iPhone when on Wi-Fi** in Apple Devices and apply the
change. USB is preferred whenever both transports are available.

Background importing is opt-in. After the tools and Wi-Fi connection are
verified, set `iphone_import.enabled` to `true` in `config/settings.json`.
Imported media is copied atomically into the existing watched import folder,
where it follows the same persistent queue, duplicate detection, transfer
history, and Pixel transfer path as other media.

## License

MIT
