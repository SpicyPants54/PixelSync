# PixelSync Architecture

## Overview

PixelSync is a Windows application designed to automatically transfer iPhone media to a connected Google Pixel device over USB.

The Pixel device acts as the upload bridge to Google Photos.

The application pipeline is:

iPhone Import Folder
        |
        v
Folder Watcher
        |
        v
Import Queue
        |
        v
Media Processor
        |
        v
Duplicate Detection
        |
        v
Transfer Engine
        |
        v
Pixel Device
        |
        v
Google Photos


---

# Core Components

## Core

Location:

app/core/

Responsibilities:

- Application startup
- Configuration
- Logging
- Database initialization
- Service coordination


---

# ADB Layer

Location:

app/adb/

Responsibilities:

- Detect Pixel devices
- Maintain USB communication
- Transfer files
- Trigger Android media scans


Components:

## adb_manager.py

Responsible for:

- Checking ADB availability
- Detecting connected devices
- Reading device information


## transfer.py

Responsible for:

- Sending media files
- Retry handling
- Transfer validation
- Media scanner triggering



---

# Import Pipeline

Location:

app/importer/


The importer handles incoming media.


## folder_watcher.py

Monitors:

Windows import directory


Detects:

- Photos
- Videos
- Live Photo components


---


## queue.py

Provides:

- FIFO processing
- Thread-safe queue handling


---


## processor.py

Controls:

- Hash generation
- Duplicate checking
- Bundle detection
- Transfer requests



---

# Duplicate Prevention

PixelSync uses SHA-256 hashes.

Flow:

New File

↓

Calculate Hash

↓

Check Database

↓

Already Exists?

YES:
Skip

NO:
Transfer



---

# Database

Current database:

SQLite


Purpose:

Store:

- filename
- hash
- size
- status
- timestamp


Future:

Migration support will be added.


---

# Configuration

Future configuration system:

settings.json


Will control:

- Import folder
- Pixel destination
- Retry count
- Logging level
- Startup behavior


---

# Logging

PixelSync uses structured logging.

Goals:

- Easy troubleshooting
- User support
- Debugging


Future:

- Rotating logs
- Export diagnostics


---

# Future Components


## System Tray UI

Provides:

- Status
- Queue information
- Manual sync
- Settings


## Windows Service

Provides:

- Automatic startup
- Background operation
- No console window


## Installer

Provides:

- One-click installation
- Configuration setup
- Updates


## iPhone Connector

Future:

Direct iPhone USB import.


---

# Design Principles

## Reliability First

A failed transfer should recover automatically.


## No Data Loss

Files are never deleted until confirmed transferred.


## Simple User Experience

The user should not need technical knowledge.


## Modular Architecture

Each component should have one responsibility.
