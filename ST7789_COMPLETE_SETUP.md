# ST7789 Display Setup Guide

## Quick Reference
- **Display Model:** ST7789V3
- **Resolution:** 240 x 280 pixels
- **Interface:** SPI (Hardware)
- **Compatibility:** Raspberry Pi 5, Pi 4, Pi Zero W
- **OS Required:** Raspberry Pi OS Bookworm

---

## Hardware Setup

### Pinout Configuration
Connect the ST7789V3 display to your Raspberry Pi using these GPIO pins:

| Display Pin | GPIO Function | Raspberry Pi Pin |
|-------------|----------------|-----------------|
| SCK (Clock) | GPIO 11 | Pin 23 |
| MOSI (Data) | GPIO 10 | Pin 19 |
| CS (Chip Select) | GPIO 8 | Pin 24 |
| DC (Data/Command) | GPIO 24 | Pin 18 |
| RST (Reset) | GPIO 25 | Pin 22 |
| GND (Ground) | Ground | Pins 6, 9, 14, 20, 25, 30 |
| VCC (Power) | 3.3V | Pins 1 or 17 |

### Physical Connection Diagram
```
Raspberry Pi (Top View)
┌─────────────────────────┐
│ 1   2  │  VCC (3.3V)    │
│ 3   4  │                │
│ 5   6  │  GND           │
│ 7   8  │  CS (GPIO 8)   │ ← Connect to ST7789 CS
│ 9  10  │                │
│11  12  │  SCK (GPIO 11) │ ← Connect to ST7789 SCK
│13  14  │  GND           │
│15  16  │                │
│17  18  │  DC (GPIO 24)  │ ← Connect to ST7789 DC
│19  20  │  MOSI (GPIO 10)│ ← Connect to ST7789 MOSI
│21  22  │  RST (GPIO 25) │ ← Connect to ST7789 RST
│23  24  │                │
│25  26  │                │
└─────────────────────────┘
```

---

## System Installation & Setup

### Step 1: System Dependencies
Run the automated setup script or manually install:

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install required packages
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    python3-setuptools \
    python3-pil \
    python3-dev \
    libjpeg-dev \
    zlib1g-dev \
    git \
    i2c-tools \
    spidev
```

### Step 2: Enable Hardware Interfaces
```bash
# Enable I2C
sudo raspi-config nonint do_i2c 0

# Enable SPI
sudo raspi-config nonint do_spi 0
```

### Step 3: Create Python Virtual Environment
```bash
# Navigate to home directory
cd ~

# Create virtual environment
python3 -m venv st7789_env

# Activate it
source st7789_env/bin/activate
```

### Step 4: Install Python Libraries
```bash
# Upgrade pip, setuptools, wheel
pip3 install --upgrade pip setuptools wheel

# Install required libraries
pip3 install --upgrade adafruit-blinka
pip3 install adafruit-circuitpython-st7789
pip3 install psutil requests
pip3 install Pillow  # PIL for image processing
```

### Step 5: Verify Installation
```bash
# Test Blinka
python3 -c "import board; print('✓ Blinka OK')"

# Test ST7789 library
python3 -c "import adafruit_st7789; print('✓ ST7789 library OK')"

# Test PIL
python3 -c "import PIL; print('✓ PIL OK')"
```

---

## Project Files

### Core Driver Files

#### `st7789_display_driver.py`
**Purpose:** Low-level display driver and hardware interface
**Key Features:**
- ST7789V3 hardware communication via SPI
- GPIO control for reset, data/command, and backlight pins
- RGB image conversion and transmission
- System information retrieval functions
- Font loading and text rendering

**GPIO Pin Configuration:**
- RST_PIN = 27 (Reset)
- DC_PIN = 25 (Data/Command)
- BL_PIN = 17 (Backlight)

**Key Functions:**
- `ST7789Display()` - Main display class
- `get_cpu_usage()` - Get CPU percentage
- `get_memory_usage()` - Get memory percentage
- `get_temperature()` - Get CPU temp
- `get_gpu_temperature()` - Get GPU temp
- `get_disk_usage()` - Get disk stats
- `get_hostname()` - Get system hostname
- `get_uptime()` - Get uptime string
- `get_ip_address()` - Get IP address

#### `st7789_stats_dashboard.py`
**Purpose:** Real-time system statistics display
**Display Format:**
- System hostname and IP address
- CPU usage percentage
- Memory usage percentage
- Disk usage percentage
- CPU & GPU temperatures
- System uptime
- Scrolling updates every 2 seconds

#### `st7789_carousel_dashboard.py`
**Purpose:** Multi-screen carousel dashboard
**Features:**
- Rotates through multiple display screens
- Shows different system metrics on each screen
- Auto-cycling between views

#### `st7789_premium_dashboard.py`
**Purpose:** Advanced statistics dashboard with enhanced UI
**Features:**
- Graphical displays
- Better formatting
- More detailed metrics
- Enhanced visual presentation

#### `st7789_stats_dashboard_enhanced.py`
**Purpose:** Enhanced version of stats dashboard
**Features:**
- Improved layout
- Better color coding
- Additional metrics

#### `st7789_carousel_dashboard_pro.py`
**Purpose:** Professional carousel dashboard
**Features:**
- Multiple view modes
- Professional styling
- Full system monitoring

### Setup Files

#### `setup_display.sh`
**Purpose:** Automated installation and configuration script
**What it does:**
1. Updates system packages
2. Installs Python dependencies
3. Enables I2C and SPI interfaces
4. Creates Python virtual environment
5. Installs required Python libraries
6. Tests display connection
7. Configures autostart via crontab

**Usage:**
```bash
chmod +x setup_display.sh
./setup_display.sh
```

---

## Quick Start Commands

### Activate Virtual Environment
```bash
source ~/st7789_env/bin/activate
```

### Run Display Applications
```bash
# Stats dashboard (shows system info)
python3 ~/st7789_stats_dashboard.py

# Carousel dashboard (rotating views)
python3 ~/st7789_carousel_dashboard.py

# Premium dashboard (enhanced UI)
python3 ~/st7789_premium_dashboard.py

# Carousel pro (professional mode)
python3 ~/st7789_carousel_dashboard_pro.py
```

### Stop Display Application
```bash
pkill -f st7789_stats_dashboard
# or
Ctrl+C
```

### View Logs
```bash
tail -f /tmp/st7789_display.log
```

### Check Autostart Status
```bash
crontab -l
```

### Edit Autostart Settings
```bash
crontab -e
# Look for: @reboot /home/lddevs/st7789_display_launcher.sh
```

---

## Configuration

### SPI Settings (in st7789_display_driver.py)
```python
self.spi.max_speed_hz = 24000000  # SPI clock speed
self.spi.mode = 0                  # SPI mode
self.spi.cshigh = False           # CS signal level
```

### Display Initialization Sequence
```python
# Key initialization commands:
0x01  # SWRESET - Software reset
0x11  # SLPOUT - Sleep out
0x3A  # COLMOD - 16-bit color mode
0x36  # MADCTL - Portrait orientation
0x21  # INVON - Display inversion on
0x13  # NORON - Normal display mode
0x29  # DISPON - Display on
```

### Update Interval
For stats dashboard, modify update frequency:
```python
display = StatsDisplay(update_interval=2)  # 2 seconds between updates
```

---

## Troubleshooting

### Display Not Showing
1. **Check physical connections:**
   - Verify all wires are seated properly
   - Check for correct GPIO pins
   - Verify power supply (3.3V)

2. **Check hardware interfaces:**
   ```bash
   # Verify SPI is enabled
   ls /dev/spidev*

   # Should show: /dev/spidev0.0
   ```

3. **Test display directly:**
   ```bash
   source st7789_env/bin/activate
   python3 st7789_display_driver.py
   ```

### ImportError for Libraries
```bash
# Reactivate virtual environment
source st7789_env/bin/activate

# Reinstall packages
pip3 install --upgrade adafruit-blinka adafruit-circuitpython-st7789
```

### GPIO Access Denied
```bash
# Run with sudo
sudo -u $(whoami) bash -c 'source st7789_env/bin/activate && python3 st7789_stats_dashboard.py'
```

### Display Shows Garbage/Corrupted
1. Power cycle the display
2. Run `st7789_display_driver.py` to reset
3. Check SPI clock speed in driver

### High CPU Usage
- Check update interval (increase it to reduce frequency)
- Verify backlight pin configuration
- Check for infinite loops in display code

---

## Autostart Setup

### Create Launcher Script
Create file: `/home/lddevs/st7789_display_launcher.sh`

```bash
#!/bin/bash
# ST7789 Display Launcher
cd /home/lddevs
source st7789_env/bin/activate
python3 st7789_stats_dashboard.py >> /tmp/st7789_display.log 2>&1
```

### Enable Autostart
```bash
# Make launcher executable
chmod +x ~/st7789_display_launcher.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "@reboot $HOME/st7789_display_launcher.sh") | crontab -

# Verify
crontab -l
```

### Disable Autostart
```bash
# Edit crontab
crontab -e

# Remove the @reboot line for st7789_display_launcher
```

---

## System Information Functions

All available in `st7789_display_driver.py`:

- **CPU Usage:** `get_cpu_usage()` - Returns percentage (0-100)
- **Memory Usage:** `get_memory_usage()` - Returns percentage (0-100)
- **CPU Temperature:** `get_temperature()` - Returns °C
- **GPU Temperature:** `get_gpu_temperature()` - Returns °C
- **Disk Usage:** `get_disk_usage()` - Returns dict with percent, used, total
- **Hostname:** `get_hostname()` - Returns system hostname
- **Uptime:** `get_uptime()` - Returns formatted string (e.g., "2h 30m")
- **IP Address:** `get_ip_address()` - Returns IPv4 address

---

## Advanced Configuration

### Change Display Orientation
In `st7789_display_driver.py`, modify MADCTL register:
```python
# Current: Portrait (0x00)
# Landscape: 0xA0
# Portrait inverted: 0xC0
# Landscape inverted: 0x60
```

### Adjust Backlight
```python
# Backlight control uses GPIO 17
# Set low: GPIO.output(17, GPIO.LOW)   # Off
# Set high: GPIO.output(17, GPIO.HIGH) # On
```

### Change Font Sizes
In `_load_fonts()` method, adjust point sizes:
```python
ImageFont.truetype("path/to/font.ttf", 28)  # Size in points
```

### Modify Color Scheme
In dashboard files, update color tuples:
```python
self.BLACK = (0, 0, 0)
self.WHITE = (255, 255, 255)
self.GREEN = (0, 255, 0)
self.RED = (255, 0, 0)
self.YELLOW = (255, 255, 0)
```

---

## Reinstallation Quick Checklist

- [ ] Hardware connections verified
- [ ] System updated (`apt-get update && apt-get upgrade`)
- [ ] I2C/SPI interfaces enabled
- [ ] Virtual environment created
- [ ] Python packages installed
- [ ] Test script runs successfully
- [ ] Main dashboard application running
- [ ] Autostart configured (optional)
- [ ] Logs accessible and monitoring

---

## Common Commands Reference

```bash
# Activate environment
source ~/st7789_env/bin/activate

# Deactivate environment
deactivate

# Check SPI
ls /dev/spidev*

# Check I2C
i2cdetect -y 1

# Monitor system
top  # or htop if installed

# View display logs
tail -f /tmp/st7789_display.log

# Stop all display processes
pkill -f st7789

# Reboot system
sudo reboot

# Check cron jobs
crontab -l

# GPIO info
gpioinfo
```

---

## Version Information
- **Python Version:** 3.11+
- **Blinka Version:** Latest
- **ST7789 Library:** adafruit-circuitpython-st7789
- **PIL/Pillow:** Latest
- **Tested On:** Raspberry Pi 5, OS: Bookworm

---

## Support & Resources
- Adafruit ST7789 Library: https://github.com/adafruit/Adafruit_CircuitPython_ST7789
- Blinka Documentation: https://learn.adafruit.com/circuitpython-on-raspberrypi-linux
- Raspberry Pi GPIO: https://pinout.xyz/

---

**Last Updated:** October 27, 2025
**Status:** Complete Setup Guide
