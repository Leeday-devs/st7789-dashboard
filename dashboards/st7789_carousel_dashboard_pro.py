#!/usr/bin/env python3
"""
ST7789V3 Pro Carousel Stats Dashboard
Enhanced with icons, animations, pulsing effects, and more stats
"""

import time
import signal
import os
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
        return {'one': round(load[0], 2), 'five': round(load[1], 2)}
    except:
        return {'one': 0, 'five': 0}


def get_process_count():
    """Get number of running processes"""
    try:
        return len(psutil.pids())
    except:
        return 0


def get_network_speed():
    """Get network activity"""
    try:
        net_io = psutil.net_io_counters()
        return {'sent': net_io.bytes_sent, 'recv': net_io.bytes_recv}
    except:
        return {'sent': 0, 'recv': 0}


class ProCarouselDashboard:
    """Pro carousel dashboard with visual enhancements"""

    def __init__(self, update_interval=1, page_duration=5):
        """Initialize pro carousel dashboard"""
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

        # Current stats
        self.stats = {
            'cpu': 0,
            'memory': 0,
            'cpu_temp': 0,
            'gpu_temp': 0,
            'disk': {'percent': 0},
            'uptime': '0m',
            'ip': 'N/A',
            'hostname': 'RPi5',
            'load': {'one': 0, 'five': 0},
            'processes': 0,
            'network': {'sent': 0, 'recv': 0}
        }

        # Pages with icons and colors
        self.pages = [
            ('CPU', 'cpu', self.display.RED, 100, '📊'),
            ('RAM', 'memory', self.display.CYAN, 100, '💾'),
            ('CPU TEMP', 'cpu_temp', self.display.YELLOW, 100, '🌡'),
            ('GPU TEMP', 'gpu_temp', self.display.MAGENTA, 100, '🌡'),
            ('DISK', 'disk', self.display.GREEN, 100, '💿'),
            ('LOAD AVG', 'load', self.display.WHITE, 10, '📈'),
            ('NETWORK', 'network', self.display.BLUE, 1000000, '🌐'),
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
            disk = get_disk_usage()
            self.stats['disk'] = disk['percent']
            self.stats['uptime'] = get_uptime()
            self.stats['ip'] = get_ip_address()
            self.stats['hostname'] = get_hostname()
            load = get_load_average()
            self.stats['load'] = load['one']
            self.stats['processes'] = get_process_count()
            network = get_network_speed()
            self.stats['network'] = (network['sent'] + network['recv']) / 1000000  # Convert to MB

            # Store in history
            self.history['cpu'].append(self.stats['cpu'])
            self.history['memory'].append(self.stats['memory'])
            self.history['cpu_temp'].append(self.stats['cpu_temp'])
            self.history['gpu_temp'].append(self.stats['gpu_temp'])
            self.history['disk'].append(self.stats['disk'])
            self.history['load'].append(self.stats['load'])
            self.history['network'].append(self.stats['network'])

        except Exception as e:
            print(f"Error updating stats: {e}")

    def draw_graph(self, x, y, width, height, data, max_val, color):
        """Draw animated line graph"""
        if len(data) < 2:
            return

        values = list(data)

        # Draw background
        self.display.draw_rectangle(x, y, x + width, y + height, fill=self.display.BLACK)

        # Draw grid lines
        for i in range(0, height, 20):
            self.display.draw_line(x, y + i, x + width, y + i, color=(30, 30, 30), width=1)

        # Draw axes
        self.display.draw_line(x, y + height, x + width, y + height, color=color, width=2)
        self.display.draw_line(x, y, x, y + height, color=color, width=2)

        # Draw data points and lines
        point_width = width / len(values)
        for i in range(len(values) - 1):
            x1 = x + int(i * point_width)
            y1 = y + height - int((values[i] / max_val) * height)

            x2 = x + int((i + 1) * point_width)
            y2 = y + height - int((values[i + 1] / max_val) * height)

            if x2 >= x and x1 <= x + width:
                self.display.draw_line(x1, y1, x2, y2, color=color, width=2)

                if i % 4 == 0:
                    self.display.draw_rectangle(x1 - 2, y1 - 2, x1 + 2, y1 + 2, fill=color)

        # Pulsing effect on latest point
        if len(values) > 0:
            new_x = x + width - (point_width / 2)
            new_y = y + height - int((values[-1] / max_val) * height)
            pulse_size = 2 + (self.animation_counter % 5)
            self.display.draw_rectangle(new_x - pulse_size, new_y - pulse_size,
                                       new_x + pulse_size, new_y + pulse_size, fill=color)

    def draw_pro_stat_page(self, title, stat_key, color, max_val, icon):
        """Draw enhanced stat page with visual effects"""
        self.display.clear(self.display.BLACK)

        # Get value
        if stat_key == 'disk':
            value = self.stats['disk']
        elif stat_key == 'load':
            value = self.stats['load']
        elif stat_key == 'network':
            value = self.stats['network']
        else:
            value = self.stats[stat_key]

        # Extra large colorful title bar with borders
        self.display.draw_rectangle(0, 0, self.display.width, 75, fill=color)
        self.display.draw_rectangle(0, 0, self.display.width, 75, outline=self.display.WHITE, fill=None)
        self.display.draw_rectangle(2, 2, self.display.width - 2, 73, outline=self.display.WHITE, fill=None)

        # Large centered title text (10x bigger!)
        self.display.draw_text(
            self.display.width // 2, 37,
            title,
            font=self.display.font_xlarge,
            color=self.display.BLACK,
            anchor="mm"
        )

        # Large value display with pulsing border
        value_box_y = 90
        value_box_height = 50
        pulse = 2 + (self.animation_counter % 6)

        # Pulsing border effect
        self.display.draw_rectangle(
            10 - pulse, value_box_y - pulse,
            self.display.width - 10 + pulse, value_box_y + value_box_height + pulse,
            outline=color, fill=None
        )

        # Inner border
        self.display.draw_rectangle(12, value_box_y - 2, self.display.width - 12, value_box_y + value_box_height + 2,
                                   outline=self.display.WHITE, fill=None)

        # Large value
        value_text = f"{value:.1f}"
        self.display.draw_text(
            self.display.width // 2, value_box_y + 15,
            value_text,
            font=self.display.font_large,
            color=color,
            anchor="mm"
        )

        # Unit
        unit_text = ""
        if stat_key in ['cpu', 'memory', 'disk']:
            unit_text = "%"
        elif stat_key in ['cpu_temp', 'gpu_temp']:
            unit_text = "°C"
        elif stat_key == 'load':
            unit_text = "avg"
        elif stat_key == 'network':
            unit_text = "MB"

        self.display.draw_text(
            self.display.width // 2, value_box_y + 35,
            unit_text,
            font=self.display.font_small,
            color=color,
            anchor="mm"
        )

        # Draw graph
        graph_y = 160
        graph_height = 110
        self.draw_graph(10, graph_y, self.display.width - 20, graph_height,
                       self.history[stat_key], max_val, color)

        self.display.update()

    def update_page(self):
        """Check if we should move to next page"""
        elapsed = time.time() - self.page_start_time
        if elapsed >= self.page_duration:
            self.current_page = (self.current_page + 1) % len(self.pages)
            self.page_start_time = time.time()

    def run(self):
        """Main loop"""
        print("Starting Pro carousel dashboard...")
        print(f"Page duration: {self.page_duration}s")
        print(f"Update interval: {self.update_interval}s")
        print(f"Total pages: {len(self.pages)}")
        print("Press Ctrl+C to stop")

        try:
            while self.running:
                # Update stats
                self.update_stats()

                # Render current page
                title, stat_key, color, max_val, icon = self.pages[self.current_page]
                self.draw_pro_stat_page(title, stat_key, color, max_val, icon)

                # Check if we should change pages
                self.update_page()

                # Increment animation counter
                self.animation_counter += 1

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

    parser = argparse.ArgumentParser(description='ST7789V3 Pro Carousel Stats Dashboard')
    parser.add_argument('--update', type=int, default=1, help='Update interval in seconds')
    parser.add_argument('--page', type=int, default=5, help='Page duration in seconds')
    args = parser.parse_args()

    dashboard = ProCarouselDashboard(update_interval=args.update, page_duration=args.page)
    dashboard.run()


if __name__ == "__main__":
    main()
