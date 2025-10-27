#!/usr/bin/env python3
"""
ST7789V3 Enhanced Stats Dashboard
Premium visual design with better colors, icons, and layout
"""

import time
import signal
import sys
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
import os


def get_load_average():
    """Get system load average"""
    try:
        load = os.getloadavg()
        return {'one': round(load[0], 2), 'five': round(load[1], 2)}
    except:
        return {'one': 0, 'five': 0}


class EnhancedStatsDisplay:
    """Enhanced stats dashboard with premium design"""

    def __init__(self, update_interval=2):
        """Initialize enhanced display"""
        self.display = ST7789Display()
        self.update_interval = update_interval
        self.running = True

        # Stats cache
        self.stats = {
            'cpu': 0,
            'memory': 0,
            'cpu_temp': 0,
            'gpu_temp': 0,
            'disk': {'percent': 0},
            'uptime': '0m',
            'ip': 'N/A',
            'hostname': 'RPi5',
            'load': {'one': 0, 'five': 0}
        }

        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, sig, frame):
        """Handle shutdown signals"""
        print("\nShutting down...")
        self.running = False

    def update_stats(self):
        """Update system statistics"""
        try:
            self.stats['cpu'] = get_cpu_usage()
            self.stats['memory'] = get_memory_usage()
            self.stats['cpu_temp'] = get_temperature()
            self.stats['gpu_temp'] = get_gpu_temperature()
            self.stats['disk'] = get_disk_usage()
            self.stats['uptime'] = get_uptime()
            self.stats['ip'] = get_ip_address()
            self.stats['hostname'] = get_hostname()
            self.stats['load'] = get_load_average()
        except Exception as e:
            print(f"Error updating stats: {e}")

    def get_color_for_value(self, value, thresholds=(50, 80)):
        """Get color based on value threshold"""
        if value >= thresholds[1]:
            return self.display.RED
        elif value >= thresholds[0]:
            return self.display.YELLOW
        else:
            return self.display.GREEN

    def draw_header(self):
        """Draw premium header with gradient effect"""
        # Header background (dark blue-ish)
        self.display.draw_rectangle(
            0, 0, self.display.width, 22,
            fill=self.display.BLUE
        )

        # Hostname
        self.display.draw_text(
            5, 4,
            self.stats['hostname'].upper(),
            font=self.display.font_small,
            color=self.display.WHITE
        )

        # Uptime (right side)
        self.display.draw_text(
            self.display.width - 5, 4,
            f"Up: {self.stats['uptime']}",
            font=self.display.font_small,
            color=self.display.CYAN,
            anchor="rt"
        )

        # Divider line
        self.display.draw_line(0, 22, self.display.width, 22, color=self.display.MAGENTA, width=2)

    def draw_stat_box(self, x, y, width, label, value, unit, icon, color):
        """Draw a stat box with icon and value"""
        # Box border
        self.display.draw_rectangle(
            x, y, x + width, y + 35,
            outline=color,
            fill=None
        )

        # Icon (text-based)
        self.display.draw_text(
            x + 5, y + 4,
            icon,
            font=self.display.font_medium,
            color=color
        )

        # Label
        self.display.draw_text(
            x + 5, y + 15,
            label,
            font=self.display.font_small,
            color=self.display.CYAN
        )

        # Value with unit
        value_text = f"{value}{unit}"
        self.display.draw_text(
            x + width - 8, y + 22,
            value_text,
            font=self.display.font_medium,
            color=color,
            anchor="rt"
        )

    def draw_full_stat_bar(self, x, y, width, label, value, unit, color_normal, color_warn, color_crit):
        """Draw a full-width stat with large progress bar"""
        # Label and value on same line
        label_text = f"{label}:"
        self.display.draw_text(
            x, y,
            label_text,
            font=self.display.font_small,
            color=self.display.CYAN
        )

        value_text = f"{value}{unit}"
        self.display.draw_text(
            x + 70, y,
            value_text,
            font=self.display.font_small,
            color=self.get_color_for_value(value)
        )

        # Large progress bar
        bar_x = x
        bar_y = y + 10
        bar_width = width
        bar_height = 8

        # Background
        self.display.draw_rectangle(
            bar_x, bar_y, bar_x + bar_width, bar_y + bar_height,
            fill=self.display.BLACK,
            outline=self.display.WHITE
        )

        # Determine color
        if value >= 80:
            bar_color = color_crit
        elif value >= 50:
            bar_color = color_warn
        else:
            bar_color = color_normal

        # Fill
        fill_width = int((bar_width - 2) * min(value, 100) / 100)
        if fill_width > 0:
            self.display.draw_rectangle(
                bar_x + 1, bar_y + 1,
                bar_x + fill_width, bar_y + bar_height - 1,
                fill=bar_color
            )

    def draw_temps_section(self, x, y):
        """Draw temperature section with both CPU and GPU"""
        # CPU Temp
        cpu_color = self.get_color_for_value(self.stats['cpu_temp'], (60, 80))
        self.display.draw_rectangle(x, y, x + 115, y + 35, outline=cpu_color)
        self.display.draw_text(x + 5, y + 4, "🌡", font=self.display.font_medium, color=cpu_color)
        self.display.draw_text(x + 5, y + 15, "CPU", font=self.display.font_small, color=self.display.CYAN)
        self.display.draw_text(x + 110, y + 22, f"{self.stats['cpu_temp']}°C",
                             font=self.display.font_medium, color=cpu_color, anchor="rt")

        # GPU Temp
        gpu_color = self.get_color_for_value(self.stats['gpu_temp'], (60, 80))
        self.display.draw_rectangle(x + 125, y, x + 240, y + 35, outline=gpu_color)
        self.display.draw_text(x + 130, y + 4, "🌡", font=self.display.font_medium, color=gpu_color)
        self.display.draw_text(x + 130, y + 15, "GPU", font=self.display.font_small, color=self.display.CYAN)
        self.display.draw_text(x + 235, y + 22, f"{self.stats['gpu_temp']}°C",
                             font=self.display.font_medium, color=gpu_color, anchor="rt")

    def draw_disk_section(self, x, y):
        """Draw disk usage section"""
        disk = self.stats['disk']
        disk_color = self.get_color_for_value(disk['percent'], (70, 85))

        self.display.draw_rectangle(x, y, x + 240, y + 35, outline=disk_color)
        self.display.draw_text(x + 5, y + 4, "💾", font=self.display.font_medium, color=disk_color)
        self.display.draw_text(x + 5, y + 15, "DISK", font=self.display.font_small, color=self.display.CYAN)
        self.display.draw_text(x + 235, y + 22, f"{disk['percent']}%",
                             font=self.display.font_medium, color=disk_color, anchor="rt")

    def draw_network_section(self, x, y):
        """Draw network info section"""
        # Load average
        self.display.draw_rectangle(x, y, x + 115, y + 35, outline=self.display.CYAN)
        self.display.draw_text(x + 5, y + 4, "📊", font=self.display.font_medium, color=self.display.CYAN)
        self.display.draw_text(x + 5, y + 15, "LOAD", font=self.display.font_small, color=self.display.WHITE)
        self.display.draw_text(x + 110, y + 22, f"{self.stats['load']['one']}",
                             font=self.display.font_medium, color=self.display.CYAN, anchor="rt")

        # IP address
        self.display.draw_rectangle(x + 125, y, x + 240, y + 35, outline=self.display.MAGENTA)
        self.display.draw_text(x + 130, y + 4, "🌐", font=self.display.font_medium, color=self.display.MAGENTA)
        self.display.draw_text(x + 130, y + 15, "IP", font=self.display.font_small, color=self.display.WHITE)

        # Show last octet of IP
        ip_short = self.stats['ip'].split('.')[-1] if '.' in self.stats['ip'] else self.stats['ip']
        self.display.draw_text(x + 235, y + 22, f"{ip_short}",
                             font=self.display.font_medium, color=self.display.MAGENTA, anchor="rt")

    def render_frame(self):
        """Render complete enhanced dashboard"""
        self.display.clear()

        # Header
        self.draw_header()

        y = 28

        # Main stats with large progress bars
        self.draw_full_stat_bar(5, y, 230, "CPU", self.stats['cpu'], "%",
                               self.display.GREEN, self.display.YELLOW, self.display.RED)

        y += 22

        self.draw_full_stat_bar(5, y, 230, "RAM", self.stats['memory'], "%",
                               self.display.GREEN, self.display.YELLOW, self.display.RED)

        y += 26

        # Temperature boxes (side by side)
        self.draw_temps_section(5, y)

        y += 40

        # Disk usage (full width)
        self.draw_disk_section(5, y)

        y += 40

        # Network and Load (side by side)
        self.draw_network_section(5, y)

        # Send to display
        self.display.update()

    def run(self):
        """Main loop"""
        print("Starting enhanced stats dashboard...")
        print(f"Update interval: {self.update_interval}s")
        print("Press Ctrl+C to stop")

        try:
            while self.running:
                # Update stats
                self.update_stats()

                # Render
                self.render_frame()

                # Wait
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

    parser = argparse.ArgumentParser(description='Enhanced ST7789V3 Stats Dashboard')
    parser.add_argument('--interval', type=int, default=2, help='Update interval in seconds')
    args = parser.parse_args()

    dashboard = EnhancedStatsDisplay(update_interval=args.interval)
    dashboard.run()


if __name__ == "__main__":
    main()
