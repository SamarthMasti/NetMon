# Cisco WLAN Poller GUI

Enterprise-grade GUI tool for polling Cisco WLCs and Access Points using SSH automation.

## Features

- WLC Only Polling
- AP Only Polling
- WLC & AP Combined Mode
- Multi-threaded AP SSH execution
- Flash Vulnerability Checker
- Regex-based Log Parser
- Excel Export (AP + Vulnerable Reports)
- Clean PySide6 GUI

## Technologies Used

- Python 3.12
- PySide6
- Netmiko
- ThreadPoolExecutor
- OpenPyXL

## How to Run

```bash
pip install -r requirements.txt
python WlanPollerGUI.py

## Commands to build the executable

```bash
Windows : python -m PyInstaller --noconfirm --windowed --onefile --icon=assets/ciscologo.ico --add-data "assets;assets" WlanPollerGUI.py
Macos : python -m PyInstaller \
--onedir \
--windowed \
--icon=assets/ciscologo.icns \
WlanPollerGUI.py

