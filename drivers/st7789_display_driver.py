#!/usr/bin/env python3
"""
ST7789V3 Display Driver
Pi 5 Compatible with Hardware SPI CS
"""

import RPi.GPIO as GPIO
import spidev
from PIL import Image, ImageDraw, ImageFont
import time

class ST7789Display:
    """ST7789V3 Display Controller"""

    # GPIO pins (hardware SPI handles CS on GPIO 8)
    RST_PIN = 27   # Reset
    DC_PIN = 25    # Data/Command
    BL_PIN = 17    # Backlight

    # Display dimensions
    WIDTH = 240
    HEIGHT = 280

    def __init__(self):
        """Initialize ST7789V3 display"""
        self.width = self.WIDTH
        self.height = self.HEIGHT

        # Initialize GPIO
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
        except RuntimeError:
            GPIO.cleanup()
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)

        # Setup GPIO pins
        GPIO.setup(self.RST_PIN, GPIO.OUT)
        GPIO.setup(self.DC_PIN, GPIO.OUT)
        GPIO.setup(self.BL_PIN, GPIO.OUT)

        # Initial states
        GPIO.output(self.RST_PIN, GPIO.HIGH)
        GPIO.output(self.DC_PIN, GPIO.LOW)
        GPIO.output(self.BL_PIN, GPIO.HIGH)  # Backlight ON

        # Initialize SPI (hardware handles CS on GPIO 8)
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)  # Bus 0, Device 0
        self.spi.max_speed_hz = 24000000
        self.spi.mode = 0
        self.spi.cshigh = False

        # Reset and initialize display
        self._reset()
        self._init_display()

        # Create image buffer
        self.image = Image.new("RGB", (self.width, self.height), color=(0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)

        # Load fonts
        self._load_fonts()

        # Color definitions
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)
        self.YELLOW = (255, 255, 0)
        self.CYAN = (0, 255, 255)
        self.BLUE = (0, 0, 255)
        self.MAGENTA = (255, 0, 255)

        print("ST7789V3 Display initialized successfully")

    def _reset(self):
        """Reset the display"""
        GPIO.output(self.RST_PIN, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(self.RST_PIN, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(self.RST_PIN, GPIO.HIGH)
        time.sleep(0.1)

    def _write_command(self, cmd):
        """Write command byte"""
        GPIO.output(self.DC_PIN, GPIO.LOW)
        self.spi.writebytes([cmd])

    def _write_data(self, data):
        """Write data bytes"""
        GPIO.output(self.DC_PIN, GPIO.HIGH)
        self.spi.writebytes(data if isinstance(data, list) else [data])

    def _write_command_data(self, cmd, data):
        """Write command followed by data"""
        self._write_command(cmd)
        if data:
            self._write_data(data)

    def _init_display(self):
        """Initialize display with ST7789V3 commands"""
        init_sequence = [
            (0x01, None, 100),     # SWRESET
            (0x11, None, 50),      # SLPOUT
            (0x3A, [0x05], 0),     # COLMOD - 16-bit
            (0x36, [0x00], 0),     # MADCTL - Portrait mode
            (0x21, None, 0),       # INVON
            (0x13, None, 0),       # NORON
            (0x29, None, 10),      # DISPON
        ]

        for cmd, data, delay in init_sequence:
            if data:
                self._write_command_data(cmd, data)
            else:
                self._write_command(cmd)
            if delay > 0:
                time.sleep(delay / 1000.0)

    def _load_fonts(self):
        """Load fonts"""
        try:
            self.font_xlarge = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28
            )
            self.font_large = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18
            )
            self.font_medium = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12
            )
            self.font_small = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10
            )
        except (OSError, IOError):
            print("Warning: TrueType fonts not found, using default")
            self.font_xlarge = ImageFont.load_default()
            self.font_large = ImageFont.load_default()
            self.font_medium = ImageFont.load_default()
            self.font_small = ImageFont.load_default()

    def clear(self, color=None):
        """Clear display"""
        if color is None:
            color = self.BLACK
        self.image.paste(color, (0, 0, self.width, self.height))

    def draw_text(self, x, y, text, font=None, color=None, anchor="lt"):
        """Draw text"""
        if font is None:
            font = self.font_medium
        if color is None:
            color = self.WHITE
        self.draw.text((x, y), text, font=font, fill=color, anchor=anchor)

    def draw_line(self, x1, y1, x2, y2, color=None, width=1):
        """Draw line"""
        if color is None:
            color = self.WHITE
        self.draw.line([(x1, y1), (x2, y2)], fill=color, width=width)

    def draw_rectangle(self, x1, y1, x2, y2, color=None, outline=None, fill=None):
        """Draw rectangle"""
        if color is None:
            color = self.WHITE
        self.draw.rectangle(
            [(x1, y1), (x2, y2)], outline=outline or color, fill=fill
        )

    def update(self):
        """Send image to display"""
        try:
            # Convert RGB to RGB565
            img_565 = self._convert_to_rgb565(self.image)

            # Send to display
            self._send_image_data(img_565)
        except Exception as e:
            print(f"Error updating display: {e}")

    def _convert_to_rgb565(self, image):
        """Convert RGB888 to RGB565"""
        rgb_data = image.tobytes()
        rgb565_data = []

        for i in range(0, len(rgb_data), 3):
            r = rgb_data[i] >> 3
            g = rgb_data[i + 1] >> 2
            b = rgb_data[i + 2] >> 3

            pixel = (r << 11) | (g << 5) | b
            rgb565_data.append(pixel >> 8)
            rgb565_data.append(pixel & 0xFF)

        return bytes(rgb565_data)

    def _send_image_data(self, image_data):
        """Send image data to display"""
        # Column address (0 to 239)
        self._write_command_data(0x2A, [0x00, 0x00, 0x00, 0xEF])

        # Row address (0 to 279)
        self._write_command_data(0x2B, [0x00, 0x00, 0x01, 0x17])

        # Memory write
        self._write_command(0x2C)

        # Send data
        GPIO.output(self.DC_PIN, GPIO.HIGH)
        chunk_size = 4096
        for i in range(0, len(image_data), chunk_size):
            chunk = image_data[i : i + chunk_size]
            self.spi.writebytes(list(chunk))

    def cleanup(self):
        """Cleanup"""
        GPIO.output(self.BL_PIN, GPIO.LOW)
        GPIO.cleanup()


# System info functions
def get_cpu_usage():
    """Get CPU usage percentage"""
    try:
        with open('/proc/stat', 'r') as f:
            tokens = f.readline().split()
        user = float(tokens[1])
        nice = float(tokens[2])
        system = float(tokens[3])
        idle = float(tokens[4])
        iowait = float(tokens[5])
        total = user + nice + system + idle + iowait
        busy = user + nice + system
        return round((busy / total) * 100, 1)
    except Exception as e:
        print(f"Error getting CPU: {e}")
        return 0.0


def get_memory_usage():
    """Get memory usage percentage"""
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
        meminfo = {}
        for line in lines:
            key, value = line.split(':')
            meminfo[key.strip()] = int(value.split()[0])
        total = meminfo['MemTotal']
        free = meminfo['MemFree']
        used = total - free
        return round((used / total) * 100, 1)
    except Exception as e:
        print(f"Error getting memory: {e}")
        return 0.0


def get_temperature():
    """Get CPU temperature"""
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp = int(f.read()) / 1000
        return round(temp, 1)
    except Exception as e:
        return 0.0


def get_gpu_temperature():
    """Get GPU temperature"""
    try:
        import subprocess
        result = subprocess.check_output(['/opt/vc/bin/vcgencmd', 'measure_temp']).decode()
        temp = float(result.split('=')[1].split("'")[0])
        return round(temp, 1)
    except Exception:
        return 0.0


def get_disk_usage():
    """Get disk usage"""
    try:
        import shutil
        stat = shutil.disk_usage('/')
        total_gb = stat.total / (1024 ** 3)
        used_gb = stat.used / (1024 ** 3)
        percent = round((stat.used / stat.total) * 100, 1)
        return {'percent': percent, 'used': round(used_gb, 1), 'total': round(total_gb, 1)}
    except Exception as e:
        return {'percent': 0, 'used': 0, 'total': 0}


def get_hostname():
    """Get hostname"""
    try:
        with open('/etc/hostname', 'r') as f:
            return f.read().strip()
    except:
        return "RPi5"


def get_uptime():
    """Get uptime string"""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = int(float(f.read().split()[0]))
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60

        if days > 0:
            return f"{days}d {hours}h"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    except:
        return "N/A"


def get_ip_address():
    """Get IP address"""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "N/A"


if __name__ == "__main__":
    try:
        display = ST7789Display()
        display.clear()
        display.draw_text(120, 140, "Display\nWorking!", color=display.GREEN, anchor="mm")
        display.update()
        print("Display test successful!")
        import time
        time.sleep(3)
        display.cleanup()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
