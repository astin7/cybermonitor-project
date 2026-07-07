# CyberMonitor

A high-performance system telemetry and security utility built with **Python** and **Eel**. This tool provides real-time hardware diagnostics while maintaining enterprise-level software protection 

## Installation
1. **Download the latest release: Download CyberMonitor**
2. **Local Development Setup:**

   **If you are cloning this repository to build from source, you must configure your local environments variables:**
   * Rename `secrets_config.example.py` to `secrets_config.py`
   * Open `secrets_config.py` and replace the placeholder strings with your own custom crytopgraphic salts
   * *Note: The application will not compile or run without a local `secrets_config.py` file.*

## Engineering Highlights
* **Minimal Overhead Engine**: Leverages `psutil` and `LibreHardwareMonitorLib` to deliver granular hardware telemetry with **<1% CPU utilization** 
* **Hybrid GUI Architecture**: Utilizes a decoupled architecture where a **Python backend** manages low-level hardware access, communicating via WebSockets to a **HTML5/CSS3/JS frontend**
* **Advanced Licensing System**: Implements a custom authentication layer using **SHA-256 cryptographic signatures** tied to unique **Motherboard UUIDs (HWID)** 
* **Registry-Based Persistence**: Uses the **Windows Registry (`winreg`)** for secure license tracking, avoiding easily manipulated flat-file storage

## Technical Stack
* **Core Logic**: Python 3.10+
* **Security**: `hashlib` (SHA-256), `wmi` (Hardware Identification) 
* **Telemetry**: `psutil`, `pythonnet` (CLR bridge for .NET Hardware Libraries)
* **Interface**: Eel (Chromium-based UI), CSS Grid, SVG Rings 

## Security Implementation
The application performs a **Mathematical Validation Check** on startup. Rather than checking a database, it verifies the license key against a **salted SHA-256 hash** of the user's Motherboard UUID
* **Permanent Keys**: Verified using a specific `PERM_SALT` 
* **Trial Keys**: Decoupled using a `TRIAL_SALT` with an integrated countdown timer stored in an encrypted registry state

## Dashboard Capabilities
* **CPU**: Name detection, usage %, temperature, and real-time MHz tracking via WMI MaxClockSpeed 
* **GPU**: NVIDIA/AMD detection with core load and thermal metrics
* **Threads**: Sorted list of the top 5 resource-intensive system processes 

---
*Developed by Astin Huynh (astin7)
