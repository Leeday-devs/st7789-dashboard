#!/bin/bash

###############################################################################
# ST7789V3 Display Setup Script
# Automates installation and configuration for Raspberry Pi OS Bookworm
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VENV_NAME="st7789_env"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_PATH="${SCRIPT_DIR}/${VENV_NAME}"

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_header "ST7789V3 Display Setup for Raspberry Pi OS Bookworm"

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    print_warning "This script is optimized for Raspberry Pi"
fi

# Step 1: Update system
print_header "Step 1: Updating system"
echo "Running apt update and upgrade (this may take a few minutes)..."
sudo apt-get update
sudo apt-get -y upgrade
print_success "System updated"

# Step 2: Install system dependencies
print_header "Step 2: Installing system dependencies"
echo "Installing required packages..."
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    python3-setuptools \
    python3-pil \
    python3-dev \
    libjpeg-dev \
    zlib1g-dev \
    git \
    i2c-tools

print_success "System dependencies installed"

# Step 3: Enable I2C and SPI interfaces
print_header "Step 3: Enabling hardware interfaces"
echo "Enabling I2C interface..."
sudo raspi-config nonint do_i2c 0
print_success "I2C enabled"

echo "Enabling SPI interface..."
sudo raspi-config nonint do_spi 0
print_success "SPI enabled"

# Step 4: Create virtual environment
print_header "Step 4: Creating Python virtual environment"

if [ -d "$VENV_PATH" ]; then
    print_warning "Virtual environment already exists at $VENV_PATH"
    read -p "Do you want to recreate it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$VENV_PATH"
    else
        print_success "Using existing virtual environment"
        SKIP_VENV=1
    fi
fi

if [ "$SKIP_VENV" != "1" ]; then
    python3 -m venv "$VENV_PATH" --system-site-packages
    print_success "Virtual environment created at $VENV_PATH"
fi

# Step 5: Activate and install Python packages
print_header "Step 5: Installing Python packages"

# Create a temporary activation script
TEMP_SCRIPT=$(mktemp)
cat > "$TEMP_SCRIPT" << 'EOF'
#!/bin/bash
source "$1/bin/activate"

echo "Upgrading pip, setuptools, and wheel..."
pip3 install --upgrade pip setuptools wheel

echo "Installing Adafruit Blinka..."
pip3 install --upgrade adafruit-blinka

echo "Installing ST7789 library..."
pip3 install adafruit-circuitpython-st7789

echo "Installing additional libraries..."
pip3 install psutil requests

echo "Verifying installations..."
python3 -c "import board; print('✓ Blinka working')"
python3 -c "import adafruit_st7789; print('✓ ST7789 library working')"
python3 -c "import PIL; print('✓ PIL working')"

echo "Done!"
EOF

chmod +x "$TEMP_SCRIPT"
bash "$TEMP_SCRIPT" "$VENV_PATH"
rm "$TEMP_SCRIPT"

print_success "Python packages installed"

# Step 6: Verify display connection
print_header "Step 6: Verifying display connection"

cat > /tmp/test_i2c.sh << 'EOF'
#!/bin/bash
source "$1/bin/activate"
echo "Checking I2C devices..."
i2cdetect -y 1
EOF

chmod +x /tmp/test_i2c.sh
echo ""
echo "Checking I2C/SPI connections..."
i2cdetect -y 1 2>/dev/null || print_warning "Could not detect I2C devices (this is OK for SPI displays)"

print_warning "Please verify your display is properly connected:"
print_warning "  SCK  -> GPIO 11 (pin 23)"
print_warning "  MOSI -> GPIO 10 (pin 19)"
print_warning "  CS   -> GPIO  8 (pin 24)"
print_warning "  DC   -> GPIO 24 (pin 18)"
print_warning "  RST  -> GPIO 25 (pin 22)"
print_warning "  GND  -> GND (pin 6, 9, 14, 20, 25, 30)"
print_warning "  VCC  -> 3.3V (pin 1 or 17)"

# Step 7: Test the display
print_header "Step 7: Testing display driver"

read -p "Is your display connected? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd "$SCRIPT_DIR"
    source "$VENV_PATH/bin/activate"

    echo "Running display test..."
    python3 st7789_driver.py

    if [ $? -eq 0 ]; then
        print_success "Display driver test passed!"
    else
        print_error "Display driver test failed"
        print_error "Check your wiring and connections"
        exit 1
    fi
else
    print_warning "Skipping display test"
    print_warning "Please connect your display and run: source $VENV_PATH/bin/activate && python3 st7789_driver.py"
fi

# Step 8: Setup autostart
print_header "Step 8: Setting up autostart"

# Make the launcher script executable
chmod +x "$SCRIPT_DIR/st7789_display_launcher.sh"

# Create cron job
echo "Setting up cron job for autostart..."

CRON_JOB="@reboot $SCRIPT_DIR/st7789_display_launcher.sh"

# Remove existing job if present
crontab -l 2>/dev/null | grep -v "st7789_display_launcher" | crontab - 2>/dev/null || true

# Add new job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

print_success "Autostart configured"
echo "Display will start automatically on boot"

# Final summary
print_header "Setup Complete!"

echo ""
echo -e "${GREEN}Your ST7789V3 display is ready!${NC}"
echo ""
echo "Quick start:"
echo "  1. Source the virtual environment:"
echo "     ${YELLOW}source $VENV_PATH/bin/activate${NC}"
echo ""
echo "  2. Run the stats display:"
echo "     ${YELLOW}python3 $SCRIPT_DIR/st7789_stats.py${NC}"
echo ""
echo "  3. View autostart status:"
echo "     ${YELLOW}crontab -l${NC}"
echo ""
echo "  4. View logs:"
echo "     ${YELLOW}tail -f /tmp/st7789_display.log${NC}"
echo ""
echo "To manually stop the display:"
echo "  ${YELLOW}pkill -f st7789_stats.py${NC}"
echo ""
echo "To disable autostart:"
echo "  ${YELLOW}crontab -e${NC} (remove the st7789 line)"
echo ""

print_success "Setup script completed!"
