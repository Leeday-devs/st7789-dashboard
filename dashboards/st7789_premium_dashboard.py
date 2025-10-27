#!/usr/bin/env python3
"""
ST7789V3 Premium Pro Dashboard
Top-of-the-range visual design with multiple graph types, gradients, and animations
"""

import time
import signal
import os
import math
import psutil
from collections import deque
from st7789_display_driver import (
    ST7789Display,
    get_cpu_usage,
    get_memory_usage,
    get_temperature,
    get_gpu_temperature,
    get_disk_usage,
    get_hostname,
    get_uptime,
    get_ip_address
)


def get_load_average():
    """Get system load average"""
    try:
        load = os.getloadavg()
        return round(load[0], 2)
    except:
        return 0


def get_network_connections():
    """Get number of active network connections"""
    try:
        connections = psutil.net_connections()
        established = len([c for c in connections if c.status == 'ESTABLISHED'])
        listening = len([c for c in connections if c.status == 'LISTEN'])
        return {'established': established, 'listening': listening, 'total': len(connections)}
    except:
        return {'established': 0, 'listening': 0, 'total': 0}


def get_nas_storage():
    """Get NAS storage info from /mnt/nas"""
    try:
        stat = os.statvfs('/mnt/nas')
        total = (stat.f_blocks * stat.f_frsize) / (1024 ** 3)  # GB
        free = (stat.f_bavail * stat.f_frsize) / (1024 ** 3)   # GB
        used = total - free
        percent = round((used / total) * 100, 1) if total > 0 else 0
        return {'total': round(total, 1), 'used': round(used, 1), 'free': round(free, 1), 'percent': percent}
    except:
        return {'total': 0, 'used': 0, 'free': 0, 'percent': 0}


def interpolate(p0, p1, t):
    """Linear interpolation"""
    return p0 + (p1 - p0) * t


def bezier_point(p0, p1, p2, p3, t):
    """Cubic bezier interpolation"""
    mt = 1 - t
    return (mt**3 * p0 + 3 * mt**2 * t * p1 +
            3 * mt * t**2 * p2 + t**3 * p3)


class PremiumDashboard:
    """Premium dashboard with advanced visualizations"""

    def __init__(self, update_interval=1, page_duration=5):
        """Initialize premium dashboard"""
        self.display = ST7789Display()
        self.update_interval = update_interval
        self.page_duration = page_duration
        self.running = True
        self.animation_counter = 0

        # History buffers
        self.history = {
            'cpu': deque(maxlen=20),
            'memory': deque(maxlen=20),
            'cpu_temp': deque(maxlen=20),
            'gpu_temp': deque(maxlen=20),
            'disk': deque(maxlen=20),
            'load': deque(maxlen=20),
            'network': deque(maxlen=20),
        }

        # Stats
        self.stats = {
            'cpu': 0, 'memory': 0, 'cpu_temp': 0, 'gpu_temp': 0,
            'disk': 0, 'uptime': '0m', 'ip': 'N/A', 'hostname': 'RPi5',
            'load': 0, 'network': 0,
            'connections': {'established': 0, 'listening': 0, 'total': 0},
            'nas': {'total': 0, 'used': 0, 'free': 0, 'percent': 0}
        }

        # Pages with graph types
        self.pages = [
            ('CPU', 'cpu', self.display.RED, 100, '📊', 'smooth_area'),
            ('RAM', 'memory', self.display.CYAN, 100, '💾', 'filled_area'),
            ('CPU TEMP', 'cpu_temp', self.display.YELLOW, 100, '🌡', 'gauge'),
            ('GPU TEMP', 'gpu_temp', self.display.MAGENTA, 100, '🌡', 'gauge'),
            ('DISK', 'disk', self.display.GREEN, 100, '💿', 'filled_area'),
            ('LOAD AVG', 'load', self.display.WHITE, 10, '📈', 'bars'),
            ('NETWORK', 'network', self.display.BLUE, 1000000, '🌐', 'smooth_area'),
            ('CONNECTIONS', 'connections', self.display.MAGENTA, 100, '🔗', 'info'),
            ('NAS STORAGE', 'nas', self.display.CYAN, 100, '💿', 'info'),
        ]

        self.current_page = 0
        self.page_start_time = time.time()

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, sig, frame):
        """Handle shutdown signals"""
        print("\nShutting down...")
        self.running = False

    def update_stats(self):
        """Update all statistics"""
        try:
            self.stats['cpu'] = get_cpu_usage()
            self.stats['memory'] = get_memory_usage()
            self.stats['cpu_temp'] = get_temperature()
            self.stats['gpu_temp'] = get_gpu_temperature()
            self.stats['disk'] = get_disk_usage()['percent']
            self.stats['uptime'] = get_uptime()
            self.stats['ip'] = get_ip_address()
            self.stats['hostname'] = get_hostname()
            self.stats['load'] = get_load_average()

            try:
                net = psutil.net_io_counters()
                self.stats['network'] = (net.bytes_sent + net.bytes_recv) / 1000000
            except:
                self.stats['network'] = 0

            # Network connections
            self.stats['connections'] = get_network_connections()

            # NAS storage
            self.stats['nas'] = get_nas_storage()

            # Store history
            self.history['cpu'].append(self.stats['cpu'])
            self.history['memory'].append(self.stats['memory'])
            self.history['cpu_temp'].append(self.stats['cpu_temp'])
            self.history['gpu_temp'].append(self.stats['gpu_temp'])
            self.history['disk'].append(self.stats['disk'])
            self.history['load'].append(self.stats['load'])
            self.history['network'].append(self.stats['network'])

        except Exception as e:
            print(f"Error updating stats: {e}")

    def draw_smooth_area_graph(self, x, y, width, height, data, max_val, color):
        """Draw smooth area graph with gradient fill and enhanced visuals"""
        if len(data) < 2:
            return

        values = list(data)

        # Enhanced gradient background
        self.display.draw_rectangle(x, y, x + width, y + height, fill=self.display.BLACK)

        # Darker top section for gradient effect
        for i in range(min(height // 4, height)):
            shade = 15 - (i * 10 // max(1, height // 4))
            self.display.draw_line(x, y + i, x + width, y + i, color=(shade, shade, shade), width=1)

        # Enhanced grid lines with varying opacity
        for i in range(0, height, 10):
            opacity = 20 if i % 20 == 0 else 10
            self.display.draw_line(x, y + i, x + width, y + i, color=(opacity, opacity, opacity), width=1)

        # Axes with glow effect
        self.display.draw_line(x, y + height, x + width, y + height, color=color, width=3)
        self.display.draw_line(x, y, x, y + height, color=color, width=3)

        # Axis glow (subtle)
        self.display.draw_line(x + 1, y + height + 1, x + width, y + height + 1, color=(30, 30, 30), width=1)
        self.display.draw_line(x + 1, y + 1, x + 1, y + height, color=(30, 30, 30), width=1)

        # Draw smooth curve with points and fill
        point_width = width / len(values)
        prev_x1, prev_y1 = x, y + height

        for i in range(len(values)):
            x1 = x + int(i * point_width)
            y1 = y + height - int((values[i] / max_val) * height)

            if i > 0:
                # Main line with thickness
                self.display.draw_line(prev_x1, prev_y1, x1, y1, color=color, width=3)

                # Fill area with gradient simulation
                for fill_y in range(int(prev_y1), int(y + height)):
                    alpha = (fill_y - prev_y1) / max(1, y + height - prev_y1)
                    shade = int(alpha * 40)
                    self.display.draw_line(int(prev_x1), fill_y, int(x1), fill_y,
                                         color=(shade, shade, shade), width=1)

            prev_x1, prev_y1 = x1, y1

        # Draw pulsing glow effect on latest point
        if len(values) > 0:
            new_x = x + width - (point_width / 2)
            new_y = y + height - int((values[-1] / max_val) * height)
            glow = 4 + (self.animation_counter % 5)

            # Animated glow rings
            for i in range(glow, 0, -1):
                ring_color = tuple(int(c * (i / glow)) for c in color)
                self.display.draw_rectangle(
                    new_x - i - 1, new_y - i - 1, new_x + i + 1, new_y + i + 1,
                    outline=ring_color, fill=None
                )

            # Bright center point
            self.display.draw_rectangle(new_x - 4, new_y - 4, new_x + 4, new_y + 4, fill=color)
            self.display.draw_rectangle(new_x - 3, new_y - 3, new_x + 3, new_y + 3,
                                       outline=self.display.WHITE, fill=None)

    def draw_filled_area_graph(self, x, y, width, height, data, max_val, color):
        """Draw filled area graph with enhanced gradient effect"""
        if len(data) < 2:
            return

        values = list(data)

        # Enhanced background with gradient
        self.display.draw_rectangle(x, y, x + width, y + height, fill=self.display.BLACK)

        # Darker top section for gradient effect
        for i in range(min(height // 4, height)):
            shade = 15 - (i * 10 // max(1, height // 4))
            self.display.draw_line(x, y + i, x + width, y + i, color=(shade, shade, shade), width=1)

        # Enhanced grid lines
        for i in range(0, height, 10):
            opacity = 25 if i % 20 == 0 else 12
            self.display.draw_line(x, y + i, x + width, y + i, color=(opacity, opacity, opacity), width=1)

        # Axes with enhanced appearance
        self.display.draw_line(x, y + height, x + width, y + height, color=color, width=3)
        self.display.draw_line(x, y, x, y + height, color=color, width=3)

        # Axis glow
        self.display.draw_line(x + 1, y + height + 1, x + width, y + height + 1, color=(30, 30, 30), width=1)
        self.display.draw_line(x + 1, y + 1, x + 1, y + height, color=(30, 30, 30), width=1)

        # Draw line and filled area with smooth gradients
        point_width = width / len(values)

        for i in range(len(values) - 1):
            x1 = x + int(i * point_width)
            y1 = y + height - int((values[i] / max_val) * height)

            x2 = x + int((i + 1) * point_width)
            y2 = y + height - int((values[i + 1] / max_val) * height)

            # Thick main line
            self.display.draw_line(x1, y1, x2, y2, color=color, width=3)

            # Fill area with smooth gradient
            for fill_i in range(int(y1), int(y + height)):
                alpha = (fill_i - y1) / max(1, (y + height - y1))
                shade = int(alpha * 70)
                self.display.draw_line(x1, fill_i, x2, fill_i,
                                     color=(shade, shade, shade), width=1)

        # Enhanced point markers
        if len(values) > 0:
            point_width = width / len(values)
            for i, val in enumerate(values[-3:]):  # Last 3 points
                x1 = x + width - (point_width / 2) - ((2 - (len(values) - 1 - (len(values) - 3 + i))) * point_width)
                y1 = y + height - int((val / max_val) * height)
                if x1 > x:
                    self.display.draw_rectangle(x1 - 2, y1 - 2, x1 + 2, y1 + 2, fill=color)

    def draw_circular_gauge(self, x, y, radius, value, max_val, color):
        """Draw enhanced circular gauge/dial with better visuals"""
        # Background circle with gradient effect
        for r in range(radius, max(0, radius - 3), -1):
            shade = 40 if r == radius else 25
            self.display.draw_rectangle(x - r, y - r, x + r, y + r,
                                       outline=(shade, shade, shade), fill=None)

        self.display.draw_rectangle(x - radius, y - radius, x + radius, y + radius,
                                   outline=self.display.WHITE, fill=self.display.BLACK)

        # Calculate angle (0-270 degrees from bottom left)
        angle = (value / max_val) * 270 * (math.pi / 180)

        # Draw enhanced gauge arc with gradient colors
        steps = 30
        for i in range(steps):
            start_angle = (i / steps) * 270 * (math.pi / 180)
            end_angle = ((i + 1) / steps) * 270 * (math.pi / 180)

            progress = (value / max_val)
            if i <= progress * steps:
                # Gradient color based on position
                if progress < 0.5:
                    arc_color = tuple(int(c * (i / (steps * 0.5))) for c in color)
                else:
                    arc_color = color
            else:
                arc_color = (40, 40, 40)

            # Draw arc segments with varying thickness
            thick = 3 if i <= progress * steps else 2
            for r in range(radius, radius - thick, -1):
                x1 = x + int(r * math.cos(start_angle - math.pi / 2))
                y1 = y + int(r * math.sin(start_angle - math.pi / 2))
                x2 = x + int(r * math.cos(end_angle - math.pi / 2))
                y2 = y + int(r * math.sin(end_angle - math.pi / 2))

                self.display.draw_line(x1, y1, x2, y2, color=arc_color, width=1)

        # Draw needle pointer
        needle_angle = angle - math.pi / 2
        needle_x = x + int((radius - 8) * math.cos(needle_angle))
        needle_y = y + int((radius - 8) * math.sin(needle_angle))
        self.display.draw_line(x, y, needle_x, needle_y, color=color, width=3)

        # Center circle with glow
        glow = 2 + (self.animation_counter % 3)
        for g in range(glow, 0, -1):
            self.display.draw_rectangle(x - g - 1, y - g - 1, x + g + 1, y + g + 1,
                                       outline=color, fill=None)
        self.display.draw_rectangle(x - 4, y - 4, x + 4, y + 4, fill=color)

        # Center text with shadow
        self.display.draw_text(x + 1, y + 15, f"{value:.0f}°C",
                             font=self.display.font_large,
                             color=(30, 30, 30), anchor="mm")
        self.display.draw_text(x, y + 14, f"{value:.0f}°C",
                             font=self.display.font_large,
                             color=color, anchor="mm")

    def draw_bar_chart(self, x, y, width, height, data, max_val, color):
        """Draw enhanced animated bar chart"""
        if len(data) < 1:
            return

        values = list(data)

        # Enhanced background with gradient
        self.display.draw_rectangle(x, y, x + width, y + height, fill=self.display.BLACK)

        # Darker top section
        for i in range(min(height // 4, height)):
            shade = 15 - (i * 10 // max(1, height // 4))
            self.display.draw_line(x, y + i, x + width, y + i, color=(shade, shade, shade), width=1)

        # Enhanced grid lines
        for i in range(0, height, 10):
            opacity = 25 if i % 20 == 0 else 12
            self.display.draw_line(x, y + i, x + width, y + i, color=(opacity, opacity, opacity), width=1)

        # Axes with glow
        self.display.draw_line(x, y + height, x + width, y + height, color=color, width=3)
        self.display.draw_line(x, y, x, y + height, color=color, width=3)

        # Axis glow
        self.display.draw_line(x + 1, y + height + 1, x + width, y + height + 1, color=(30, 30, 30), width=1)
        self.display.draw_line(x + 1, y + 1, x + 1, y + height, color=(30, 30, 30), width=1)

        # Draw bars with enhanced styling
        bar_width = width / len(values)
        for i, val in enumerate(values):
            bar_x = x + int(i * bar_width)
            bar_height = int((val / max_val) * height)
            bar_y = y + height - bar_height

            # Bar background shadow
            self.display.draw_rectangle(bar_x + 2, bar_y + 1, bar_x + int(bar_width) - 2, y + height + 1,
                                       fill=(20, 20, 20), outline=None)

            # Main bar with color
            self.display.draw_rectangle(bar_x + 2, bar_y, bar_x + int(bar_width) - 2, y + height,
                                       fill=color, outline=self.display.WHITE)

            # Gradient highlight on bars
            for h in range(0, int(bar_height // 3)):
                alpha = (h / max(1, bar_height // 3))
                shade = int(150 * alpha)
                highlight_color = (min(255, shade), min(255, shade), min(255, shade))
                self.display.draw_line(bar_x + 3, bar_y + h, bar_x + int(bar_width) - 3, bar_y + h,
                                      color=highlight_color, width=1)

            # Top highlight
            self.display.draw_line(bar_x + 2, bar_y - 1, bar_x + int(bar_width) - 2, bar_y - 1,
                                 color=self.display.WHITE, width=1)

    def draw_info_page(self, title, stat_key, color, icon):
        """Draw enhanced info page for connections/NAS"""
        self.display.clear(self.display.BLACK)

        # Enhanced title bar with gradient effect
        for i in range(75):
            shade = int(20 * (1 - i / 75.0))
            self.display.draw_line(0, i, self.display.width, i, color=(shade, shade, shade), width=1)

        # Main title bar
        self.display.draw_rectangle(0, 0, self.display.width, 75, fill=color)
        self.display.draw_rectangle(0, 0, self.display.width, 75, outline=self.display.WHITE, fill=None)
        self.display.draw_rectangle(2, 2, self.display.width - 2, 73, outline=self.display.WHITE, fill=None)
        self.display.draw_rectangle(1, 1, self.display.width - 1, 74, outline=(100, 100, 100), fill=None)

        # Title text with shadow
        self.display.draw_text(self.display.width // 2 + 1, 38, title,
                             font=self.display.font_xlarge, color=(30, 30, 30), anchor="mm")
        self.display.draw_text(self.display.width // 2, 37, title,
                             font=self.display.font_xlarge, color=self.display.BLACK, anchor="mm")

        # Info content
        if stat_key == 'connections':
            conn = self.stats['connections']
            y = 100

            # Established connections - enhanced
            self.display.draw_rectangle(6, y - 2, self.display.width - 6, y + 37, fill=(15, 40, 15), outline=None)
            self.display.draw_rectangle(8, y, self.display.width - 8, y + 35, outline=self.display.GREEN, fill=None)
            self.display.draw_rectangle(7, y - 1, self.display.width - 7, y + 36, outline=(50, 100, 50), fill=None)
            self.display.draw_text(10, y + 5, "Established", font=self.display.font_small, color=self.display.CYAN)
            self.display.draw_text(self.display.width - 12, y + 18, f"{conn['established']}",
                                 font=self.display.font_large, color=self.display.GREEN, anchor="rt")

            # Listening connections - enhanced
            y += 45
            self.display.draw_rectangle(6, y - 2, self.display.width - 6, y + 37, fill=(40, 40, 15), outline=None)
            self.display.draw_rectangle(8, y, self.display.width - 8, y + 35, outline=self.display.YELLOW, fill=None)
            self.display.draw_rectangle(7, y - 1, self.display.width - 7, y + 36, outline=(100, 100, 50), fill=None)
            self.display.draw_text(10, y + 5, "Listening", font=self.display.font_small, color=self.display.CYAN)
            self.display.draw_text(self.display.width - 12, y + 18, f"{conn['listening']}",
                                 font=self.display.font_large, color=self.display.YELLOW, anchor="rt")

            # Total connections - enhanced
            y += 45
            self.display.draw_rectangle(6, y - 2, self.display.width - 6, y + 37, fill=(20, 20, 40), outline=None)
            self.display.draw_rectangle(8, y, self.display.width - 8, y + 35, outline=color, fill=None)
            self.display.draw_rectangle(7, y - 1, self.display.width - 7, y + 36, outline=(60, 60, 120), fill=None)
            self.display.draw_text(10, y + 5, "Total Connections", font=self.display.font_small, color=self.display.CYAN)
            self.display.draw_text(self.display.width - 12, y + 18, f"{conn['total']}",
                                 font=self.display.font_large, color=color, anchor="rt")

        elif stat_key == 'nas':
            nas = self.stats['nas']
            y = 95

            # Enhanced pulsing border for main display with gradient background
            pulse = 2 + (self.animation_counter % 6)
            self.display.draw_rectangle(6, y - 4, self.display.width - 6, y + 52, fill=(20, 20, 30), outline=None)
            self.display.draw_rectangle(8 - pulse, y - pulse, self.display.width - 8 + pulse, y + 50 + pulse,
                                       outline=color, fill=None)
            self.display.draw_rectangle(10, y - 2, self.display.width - 10, y + 50 + 2,
                                       outline=self.display.WHITE, fill=None)
            self.display.draw_rectangle(9 - pulse, y - 1 - pulse, self.display.width - 9 + pulse, y + 49 + pulse,
                                       outline=(60, 60, 120), fill=None)

            # Usage percentage with shadow
            self.display.draw_text(16, y + 6, "Usage", font=self.display.font_small, color=(30, 30, 30))
            self.display.draw_text(15, y + 5, "Usage", font=self.display.font_small, color=self.display.CYAN)
            self.display.draw_text(self.display.width - 14, y + 6, f"{nas['percent']}%",
                                 font=self.display.font_large, color=(30, 30, 30), anchor="rt")
            self.display.draw_text(self.display.width - 15, y + 5, f"{nas['percent']}%",
                                 font=self.display.font_large, color=color, anchor="rt")

            # Enhanced progress bar
            bar_y = y + 22
            bar_width = self.display.width - 30
            self.display.draw_rectangle(14, bar_y - 1, 14 + bar_width + 1, bar_y + 13,
                                       outline=(50, 50, 50), fill=self.display.BLACK)
            self.display.draw_rectangle(15, bar_y, 15 + bar_width, bar_y + 12,
                                       outline=self.display.WHITE, fill=self.display.BLACK)

            fill_width = int((bar_width - 2) * nas['percent'] / 100)
            if fill_width > 0:
                # Gradient fill in progress bar
                for i in range(fill_width):
                    alpha = i / max(1, fill_width)
                    bar_color = tuple(int(c * alpha) for c in color)
                    self.display.draw_line(16 + i, bar_y + 1, 16 + i, bar_y + 11, color=bar_color, width=1)

            # Used/Free/Total info with enhanced styling
            y = 165
            info_box_height = 30

            # Used - with background color
            self.display.draw_rectangle(6, y - 2, self.display.width // 2 - 3, y + info_box_height + 2, fill=(40, 40, 15), outline=None)
            self.display.draw_rectangle(8, y, self.display.width // 2 - 5, y + info_box_height, outline=self.display.YELLOW, fill=None)
            self.display.draw_rectangle(7, y - 1, self.display.width // 2 - 4, y + info_box_height + 1, outline=(100, 100, 50), fill=None)
            self.display.draw_text(12, y + 4, "Used", font=self.display.font_small, color=self.display.WHITE)
            self.display.draw_text(self.display.width // 2 - 10, y + 18, f"{nas['used']}GB",
                                 font=self.display.font_medium, color=self.display.YELLOW, anchor="rt")

            # Free - with background color
            self.display.draw_rectangle(self.display.width // 2 + 3, y - 2, self.display.width - 6, y + info_box_height + 2, fill=(15, 40, 15), outline=None)
            self.display.draw_rectangle(self.display.width // 2 + 5, y, self.display.width - 8, y + info_box_height, outline=self.display.GREEN, fill=None)
            self.display.draw_rectangle(self.display.width // 2 + 4, y - 1, self.display.width - 7, y + info_box_height + 1, outline=(50, 100, 50), fill=None)
            self.display.draw_text(self.display.width // 2 + 10, y + 4, "Free", font=self.display.font_small, color=self.display.WHITE)
            self.display.draw_text(self.display.width - 12, y + 18, f"{nas['free']}GB",
                                 font=self.display.font_medium, color=self.display.GREEN, anchor="rt")

            # Total - spanning full width
            y += 38
            self.display.draw_rectangle(6, y - 2, self.display.width - 6, y + info_box_height + 2, fill=(20, 20, 40), outline=None)
            self.display.draw_rectangle(8, y, self.display.width - 8, y + info_box_height, outline=self.display.CYAN, fill=None)
            self.display.draw_rectangle(7, y - 1, self.display.width - 7, y + info_box_height + 1, outline=(60, 60, 120), fill=None)
            self.display.draw_text(12, y + 4, "Total Storage", font=self.display.font_small, color=self.display.WHITE)
            self.display.draw_text(self.display.width - 12, y + 18, f"{nas['total']}GB",
                                 font=self.display.font_medium, color=self.display.CYAN, anchor="rt")

        self.display.update()

    def draw_premium_stat_page(self, title, stat_key, color, max_val, icon, graph_type):
        """Draw enhanced premium stat page with better visuals"""
        self.display.clear(self.display.BLACK)

        # Get value
        if stat_key in self.stats:
            value = self.stats[stat_key]
        else:
            value = 0

        # Enhanced title bar with gradient effect
        for i in range(75):
            shade = int(30 * (1 - i / 75.0))
            self.display.draw_line(0, i, self.display.width, i, color=(shade, shade, shade), width=1)

        # Extra large title bar with multiple borders
        self.display.draw_rectangle(0, 0, self.display.width, 75, fill=color)
        self.display.draw_rectangle(0, 0, self.display.width, 75, outline=self.display.WHITE, fill=None)
        self.display.draw_rectangle(2, 2, self.display.width - 2, 73, outline=self.display.WHITE, fill=None)
        self.display.draw_rectangle(1, 1, self.display.width - 1, 74, outline=(100, 100, 100), fill=None)

        # Title text with shadow effect
        self.display.draw_text(self.display.width // 2 + 1, 38, title,
                             font=self.display.font_xlarge, color=(30, 30, 30), anchor="mm")
        self.display.draw_text(self.display.width // 2, 37, title,
                             font=self.display.font_xlarge, color=self.display.BLACK, anchor="mm")

        # Value box with enhanced pulsing glow and background
        value_box_y = 88
        pulse = 2 + (self.animation_counter % 6)

        # Background fill for value box
        self.display.draw_rectangle(10, value_box_y - 2, self.display.width - 10, value_box_y + 45 + 2,
                                   fill=(20, 20, 30), outline=None)

        # Multiple pulsing borders with varying opacity
        self.display.draw_rectangle(8 - pulse - 1, value_box_y - pulse - 1,
                                   self.display.width - 8 + pulse + 1, value_box_y + 45 + pulse + 1,
                                   outline=(40, 40, 60), fill=None)
        self.display.draw_rectangle(8 - pulse, value_box_y - pulse,
                                   self.display.width - 8 + pulse, value_box_y + 45 + pulse,
                                   outline=color, fill=None)
        self.display.draw_rectangle(10, value_box_y - 2, self.display.width - 10, value_box_y + 45 + 2,
                                   outline=self.display.WHITE, fill=None)
        self.display.draw_rectangle(9, value_box_y - 1, self.display.width - 9, value_box_y + 45 + 1,
                                   outline=(60, 60, 100), fill=None)

        # Value display with shadow and highlight
        value_text = f"{value:.1f}"
        self.display.draw_text(self.display.width // 2 + 1, value_box_y + 13,
                             value_text, font=self.display.font_large, color=(30, 30, 30), anchor="mm")
        self.display.draw_text(self.display.width // 2, value_box_y + 12,
                             value_text, font=self.display.font_large, color=color, anchor="mm")

        # Draw graph based on type
        graph_y = 148
        graph_height = 122

        if graph_type == 'gauge' and stat_key in ['cpu_temp', 'gpu_temp']:
            self.draw_circular_gauge(self.display.width // 2, graph_y + graph_height // 2, 45, value, 100, color)
        elif graph_type == 'bars':
            self.draw_bar_chart(10, graph_y, self.display.width - 20, graph_height,
                               self.history[stat_key], max_val, color)
        elif graph_type == 'filled_area':
            self.draw_filled_area_graph(10, graph_y, self.display.width - 20, graph_height,
                                       self.history[stat_key], max_val, color)
        else:  # smooth_area
            self.draw_smooth_area_graph(10, graph_y, self.display.width - 20, graph_height,
                                       self.history[stat_key], max_val, color)

        # Enhanced trend indicator with animation
        if len(self.history[stat_key]) >= 2:
            trend_val = list(self.history[stat_key])
            if trend_val[-1] > trend_val[-2]:
                trend = "↑"
                trend_color = self.display.RED
            elif trend_val[-1] < trend_val[-2]:
                trend = "↓"
                trend_color = self.display.GREEN
            else:
                trend = "→"
                trend_color = self.display.WHITE

            # Pulsing trend box
            trend_size = 2 + (self.animation_counter % 3)
            self.display.draw_rectangle(self.display.width - 20 - trend_size, value_box_y + 7 - trend_size,
                                       self.display.width - 10 + trend_size, value_box_y + 23 + trend_size,
                                       outline=trend_color, fill=None)

            # Trend text with shadow
            self.display.draw_text(self.display.width - 15 + 1, value_box_y + 16,
                                 trend, font=self.display.font_large,
                                 color=(30, 30, 30), anchor="mm")
            self.display.draw_text(self.display.width - 15, value_box_y + 15,
                                 trend, font=self.display.font_large,
                                 color=trend_color, anchor="mm")

        self.display.update()

    def update_page(self):
        """Check if we should move to next page"""
        elapsed = time.time() - self.page_start_time
        if elapsed >= self.page_duration:
            self.current_page = (self.current_page + 1) % len(self.pages)
            self.page_start_time = time.time()

    def run(self):
        """Main loop"""
        print("Starting Premium Dashboard...")
        print(f"Pages: {len(self.pages)} | Duration: {self.page_duration}s | Update: {self.update_interval}s")
        print("Press Ctrl+C to stop")

        try:
            while self.running:
                self.update_stats()

                title, stat_key, color, max_val, icon, graph_type = self.pages[self.current_page]

                # Draw either info page or graph page
                if graph_type == 'info':
                    self.draw_info_page(title, stat_key, color, icon)
                else:
                    self.draw_premium_stat_page(title, stat_key, color, max_val, icon, graph_type)

                self.update_page()
                self.animation_counter += 1

                time.sleep(self.update_interval)

        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("Cleaning up...")
            self.display.cleanup()
            print("Done!")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='ST7789V3 Premium Dashboard')
    parser.add_argument('--update', type=int, default=1, help='Update interval in seconds')
    parser.add_argument('--page', type=int, default=5, help='Page duration in seconds')
    args = parser.parse_args()

    dashboard = PremiumDashboard(update_interval=args.update, page_duration=args.page)
    dashboard.run()


if __name__ == "__main__":
    main()
