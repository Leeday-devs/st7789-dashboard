# ST7789 Installation Kit

This folder contains everything you need to quickly reinstall and set up your ST7789 display on a Raspberry Pi.

## Folder Structure

```
ST7789_INSTALLATION_KIT/
├── README.md                      # This file
├── ST7789_COMPLETE_SETUP.md       # Full documentation & reference
├── scripts/
│   └── setup_display.sh           # Automated setup script
├── drivers/
│   └── st7789_display_driver.py   # Low-level hardware driver
└── dashboards/
    ├── st7789_stats_dashboard.py              # Basic stats display
    ├── st7789_carousel_dashboard.py           # Rotating views
    ├── st7789_stats_dashboard_enhanced.py     # Enhanced stats
    ├── st7789_premium_dashboard.py            # Premium UI
    └── st7789_carousel_dashboard_pro.py       # Professional carousel
```

## Quick Reinstallation Guide

### Step 1: Copy Files to Home Directory
```bash
# Copy all files to your home directory
cp -r ST7789_INSTALLATION_KIT/* ~

# Or copy individual components as needed
cp ST7789_INSTALLATION_KIT/scripts/setup_display.sh ~
cp ST7789_INSTALLATION_KIT/drivers/st7789_display_driver.py ~
cp -r ST7789_INSTALLATION_KIT/dashboards/*.py ~
```

### Step 2: Run Setup Script
```bash
# Make script executable
chmod +x ~/setup_display.sh

# Run the automated setup
./setup_display.sh
```

This will:
- Update system packages
- Install dependencies
- Enable I2C/SPI interfaces
- Create Python virtual environment
- Install required libraries
- Test the display

### Step 3: Choose & Run Dashboard
```bash
# Activate virtual environment
source ~/st7789_env/bin/activate

# Pick one and run:
python3 st7789_stats_dashboard.py           # Basic stats
python3 st7789_carousel_dashboard.py        # Carousel view
python3 st7789_premium_dashboard.py         # Enhanced UI
```

## File Descriptions

### ST7789_COMPLETE_SETUP.md
**The ultimate reference guide** - Contains:
- Hardware pinout diagram
- Complete installation steps
- Configuration details
- Troubleshooting tips
- Autostart setup
- Advanced configuration options

**READ THIS FIRST** if you're setting up from scratch.

### setup_display.sh
**Automated installation script** - Handles:
- System updates
- Package installation
- Hardware interface enablement (I2C/SPI)
- Virtual environment creation
- Python dependencies
- Display testing

**Run this** after copying files to automate 80% of setup.

### Drivers

#### st7789_display_driver.py
Low-level hardware interface for the display:
- Direct SPI communication
- GPIO control
- Image conversion & transmission
- System info retrieval functions

**Used by:** All dashboard applications

### Dashboards

Choose based on your needs:

| Dashboard | Best For | Features |
|-----------|----------|----------|
| **stats_dashboard** | Minimal setup | Basic system stats, minimal dependencies |
| **carousel_dashboard** | Multiple views | Rotates between different screens |
| **stats_enhanced** | Better UI | Improved layout and formatting |
| **premium_dashboard** | Full features | Advanced graphics and detailed metrics |
| **carousel_pro** | Professional | Multiple views with pro styling |

## Hardware Requirements

- Raspberry Pi (5, 4, or Zero W)
- ST7789V3 Display (240x280)
- 7 jumper wires (or similar)
- 3.3V power supply from Pi

## GPIO Pinout

```
Display Pin  →  GPIO Pin  →  Raspberry Pi Pin
SCK          →  GPIO 11   →  Pin 23
MOSI         →  GPIO 10   →  Pin 19
CS           →  GPIO 8    →  Pin 24
DC           →  GPIO 24   →  Pin 18
RST          →  GPIO 25   →  Pin 22
GND          →  Ground    →  Pins 6, 9, 14, 20, 25, 30
VCC          →  3.3V      →  Pins 1 or 17
```

See **ST7789_COMPLETE_SETUP.md** for detailed wiring diagram.

## Essential Commands

```bash
# Setup & Installation
./setup_display.sh                    # Run automated setup
source st7789_env/bin/activate       # Activate environment
deactivate                            # Deactivate environment

# Running Applications
python3 st7789_stats_dashboard.py    # Run stats display
pkill -f st7789                      # Stop display

# Diagnostics
crontab -l                           # Check autostart
i2cdetect -y 1                       # Check I2C devices
ls /dev/spidev*                      # Check SPI devices
tail -f /tmp/st7789_display.log      # View logs

# System
sudo reboot                          # Reboot system
raspi-config                         # Configure Raspberry Pi
```

## Troubleshooting Checklist

- [ ] Display physically connected correctly (check wiring diagram)
- [ ] Power supply is 3.3V
- [ ] SPI interface is enabled: `ls /dev/spidev*` should show `/dev/spidev0.0`
- [ ] I2C interface is enabled: `i2cdetect -y 1` should work
- [ ] Python virtual environment activated: `which python3` should show venv path
- [ ] All packages installed: `pip3 list | grep adafruit`
- [ ] Test driver runs: `python3 st7789_display_driver.py`

For detailed troubleshooting, see **ST7789_COMPLETE_SETUP.md**

## Quick Test

After running setup_display.sh:

```bash
# Activate environment
source st7789_env/bin/activate

# Run display driver test
python3 st7789_display_driver.py

# Or try a dashboard
python3 st7789_stats_dashboard.py
```

If you see the display working, installation is successful!

## File Manifest

This kit includes everything from:
- **Original Location:** `/home/lddevs/`
- **All Driver Files:** st7789_display_driver.py
- **All Dashboard Apps:** 5 different dashboard options
- **Setup Automation:** setup_display.sh script
- **Complete Documentation:** ST7789_COMPLETE_SETUP.md

## When You Need Each File

| Situation | What to Use |
|-----------|------------|
| First-time setup | **setup_display.sh** (automated) + **ST7789_COMPLETE_SETUP.md** (reference) |
| Hardware issues | **ST7789_COMPLETE_SETUP.md** (Troubleshooting section) |
| Want to run display | Copy **drivers/** and **dashboards/** to home directory |
| Need reference | **ST7789_COMPLETE_SETUP.md** (full documentation) |
| Configuration changes | Edit dashboard .py files directly |
| Autostart setup | Follow **ST7789_COMPLETE_SETUP.md** (Autostart Setup section) |

## Virtual Environment Note

The setup script creates `st7789_env` folder. If you need to delete and recreate:

```bash
# Remove old environment
rm -rf ~/st7789_env

# Run setup again
./setup_display.sh
```

## Next Steps

1. **Read:** ST7789_COMPLETE_SETUP.md (5-10 minutes)
2. **Copy:** Files to home directory
3. **Run:** setup_display.sh (10-15 minutes)
4. **Connect:** Display hardware (verify wiring)
5. **Test:** Run a dashboard application
6. **Configure:** Autostart if desired

## Support

If something goes wrong:
1. Check troubleshooting in **ST7789_COMPLETE_SETUP.md**
2. Verify hardware connections match pinout diagram
3. Test SPI/I2C: `ls /dev/spidev*` and `i2cdetect -y 1`
4. Re-run setup script if needed

---

**Created:** October 27, 2025
**Kit Version:** 1.0
**Compatible with:** Raspberry Pi OS Bookworm
