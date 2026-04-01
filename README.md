# Cane Toad Smart Trap - Mobile App

A Python/Flet mobile app to control the Raspberry Pi-based cane toad trap from your phone.

## Features
- ✅ Real-time connection status
- ✅ Toad counter display  
- ✅ Remote gate controls
- ✅ Euthanasia cycle trigger
- ✅ WiFi-based (local network only)

## Setup

### For Desktop Testing
```bash
pip install flet requests
python main.py
```

### For Android APK Using Replit

1. Go to https://replit.com (create free account)
2. Click "Create Repl"
3. Select "Python" template
4. Upload these files:
   - `main.py`
   - `requirements.txt`
   - `replit.nix` (optional)
5. In Replit terminal, run:
   ```bash
   pip install -r requirements.txt
   python main.py
   ```
6. To build APK, Replit will show build options

### Configuration
Edit the IP address in the Connect dialog:
- Default: `192.168.1.100:5000`
- Change to your Raspberry Pi's actual local IP

## Requirements
- Python 3.8+
- Flet (Flutter for Python)
- Local WiFi connection to Raspberry Pi
- Android phone with Android 5.0+

## Created for
Raspberry Pi-based Cane Toad Smart Trap system
