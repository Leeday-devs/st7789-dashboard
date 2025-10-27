#!/usr/bin/env python3
"""
ST7789V3 Stats Dashboard
Displays system statistics on the display in real-time
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


class StatsDisplay:
    """Stats dashboard controller"""

    def __init__(self, update_interval=2):
        """Initialize stats display"""
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
            'hostname': 'RPi5'
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
        """Draw header section"""
        # Blue header bar
        self.display.draw_rectangle(
            0, 0, self.display.width, 18,
            fill=self.display.BLUE
        )

        # Hostname and uptime
        self.display.draw_text(
            5, 2,
            f"{self.stats['hostname']} | Up: {self.stats['uptime']}",
            font=self.display.font_small,
            color=self.display.WHITE
        )

        # Divider line
        self.display.draw_line(0, 20, self.display.width, 20, color=self.display.GREEN, width=1)

    def draw_stats_row(self, y, label, value, unit, threshold=(50, 80)):
        """Draw a stat row with label and value"""
        color = self.get_color_for_value(value, threshold)

        # Label
        self.display.draw_text(
            5, y,
            f"{label}:",
            font=self.display.font_small,
            color=self.display.CYAN
        )

        # Value
        text = f"{value}{unit}"
        self.display.draw_text(
            70, y,
            text,
            font=self.display.font_small,
            color=color
        )

        # Simple progress bar (visual indicator)
        bar_x = 120
        bar_width = 115
        bar_height = 6

        # Background
        self.display.draw_rectangle(
            bar_x, y - 1, bar_x + bar_width, y + bar_height - 1,
            outline=self.display.WHITE
        )

        # Fill based on percentage (0-100)
        fill_width = int((bar_width - 2) * min(value, 100) / 100)
        if fill_width > 0:
            self.display.draw_rectangle(
                bar_x + 1, y, bar_x + fill_width, y + bar_height - 2,
                fill=color
            )

    def draw_temps(self, y):
        """Draw temperature section"""
        cpu_color = self.get_color_for_value(self.stats['cpu_temp'], (60, 80))
        gpu_color = self.get_color_for_value(self.stats['gpu_temp'], (60, 80))

        self.display.draw_text(
            5, y,
            f"CPU: {self.stats['cpu_temp']}°C",
            font=self.display.font_small,
            color=cpu_color
        )

        self.display.draw_text(
            130, y,
            f"GPU: {self.stats['gpu_temp']}°C",
            font=self.display.font_small,
            color=gpu_color
        )

    def draw_disk(self, y):
        """Draw disk usage"""
        disk = self.stats['disk']
        color = self.get_color_for_value(disk['percent'], (70, 85))

        self.display.draw_text(
            5, y,
            f"Disk: {disk['percent']}%",
            font=self.display.font_small,
            color=color
        )

    def draw_footer(self):
        """Draw footer with IP and timestamp"""
        y = self.display.height - 18

        # Divider
        self.display.draw_line(0, y - 2, self.display.width, y - 2, color=self.display.GREEN, width=1)

        # IP address
        self.display.draw_text(
            5, y + 1,
            f"IP: {self.stats['ip']}",
            font=self.display.font_small,
            color=self.display.CYAN
        )

    def render_frame(self):
        """Render complete display"""
        self.display.clear()

        # Header
        self.draw_header()

        # Main stats
        y = 28
        self.draw_stats_row(y, "CPU", self.stats['cpu'], "%")

        y += 16
        self.draw_stats_row(y, "RAM", self.stats['memory'], "%")

        y += 16
        self.draw_temps(y)

        y += 14
        self.draw_disk(y)

        # Footer
        self.draw_footer()

        # Send to display
        self.display.update()

    def run(self):
        """Main loop"""
        print("Starting stats dashboard...")
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

    parser = argparse.ArgumentParser(description='ST7789V3 Stats Dashboard')
    parser.add_argument('--interval', type=int, default=2, help='Update interval in seconds')
    args = parser.parse_args()

    dashboard = StatsDisplay(update_interval=args.interval)
    dashboard.run()


if __name__ == "__main__":
    main()
