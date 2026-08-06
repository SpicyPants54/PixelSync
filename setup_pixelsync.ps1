# PixelSync Foundation Setup Script
# Creates initial project structure

Write-Host "Creating PixelSync project structure..."

$folders = @(
    "app",
    "app/core",
    "app/adb",
    "app/database",
    "app/importer",
    "app/exporter",
    "app/media",
    "app/ui",
    "app/service",
    "app/utils",
    "tests",
    "docs",
    "installer",
    "assets",
    "scripts",
    ".github",
    ".github/workflows"
)

foreach ($folder in $folders) {
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
}

Write-Host "Creating files..."

@"
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

## License

MIT
"@ | Out-File README.md -Encoding utf8


@"
MIT License

Copyright (c) 2026 PixelSync

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
"@ | Out-File LICENSE -Encoding utf8


@"
pyside6
watchdog
sqlalchemy
pydantic
loguru
pillow
piexif
adbutils
pytest
pyinstaller
"@ | Out-File requirements.txt -Encoding utf8


@"
[project]
name = "pixelsync"
version = "0.1.0"
description = "Automatic iPhone to Pixel photo synchronization"
requires-python = ">=3.12"

dependencies = [
    "pyside6",
    "watchdog",
    "sqlalchemy",
    "pydantic",
    "loguru",
    "pillow",
    "piexif",
    "adbutils"
]

[tool.pytest.ini_options]
testpaths = [
    "tests"
]
"@ | Out-File pyproject.toml -Encoding utf8


@"
# Python
__pycache__/
*.pyc
*.pyo

# Virtual environments
.venv/
venv/

# Build
build/
dist/

# IDE
.vscode/
.idea/

# Logs
logs/

# Database
*.db

# OS
Thumbs.db
.DS_Store
"@ | Out-File .gitignore -Encoding utf8


Write-Host ""
Write-Host "PixelSync foundation created successfully!"
Write-Host "Next steps:"
Write-Host "  git add ."
Write-Host "  git commit -m 'Initial PixelSync project structure'"
Write-Host "  git push origin main"