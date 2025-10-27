#!/usr/bin/env python3
"""
ST7789V3 Carousel Stats Dashboard
Shows each stat on its own page with graph visualization
Rotates every 5 seconds with smooth transitions
"""

import time
import signal
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


class CarouselDashboard:
    """Carousel dashboard with full-screen stat pages"""

    def __init__(self, update_interval=1, page_duration=5):
        """Initialize carousel dashboard"""
        self.display = ST7789Display()
        self.update_interval = update_interval
        self.page_duration = page_duration
        self.running = True

        # History buffers for graphs (store last 20 readings)
        self.history = {
            'cpu': deque(maxlen=20),
            'memory': deque(maxlen=20),
            'cpu_temp': deque(maxlen=20),
            'gpu_temp': deque(maxlen=20),
            'disk': deque(maxlen=20),
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
            'hostname': 'RPi5'
        }

        # Pages to rotate through
        self.pages = [
            ('CPU', 'cpu', self.display.RED, 100),
            ('RAM', 'memory', self.display.CYAN, 100),
            ('CPU Temp', 'cpu_temp', self.display.YELLOW, 100),
            ('GPU Temp', 'gpu_temp', self.display.MAGENTA, 100),
            ('Disk', 'disk', self.display.GREEN, 100),
        ]

        self.current_page = 0
        self.page_start_time = time.time()

        # Setup signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, sig, frame):
        """Handle shutdown signals"""
        print("\nShutting down...")
        self.running = False

    def update_stats(self):
        """Update statistics"""
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

            # Store in history
            self.history['cpu'].append(self.stats['cpu'])
            self.history['memory'].append(self.stats['memory'])
            self.history['cpu_temp'].append(self.stats['cpu_temp'])
            self.history['gpu_temp'].append(self.stats['gpu_temp'])
            self.history['disk'].append(self.stats['disk'])

        except Exception as e:
            print(f"Error updating stats: {e}")

    def draw_graph(self, x, y, width, height, data, max_val, color, animation_frame=0):
        """Draw an animated line graph"""
        if len(data) < 2:
            return

        # Convert to list for easier access
        values = list(data)

        # Draw background
        self.display.draw_rectangle(x, y, x + width, y + height, fill=self.display.BLACK)

        # Draw grid lines
        for i in range(0, height, 20):
            self.display.draw_line(x, y + i, x + width, y + i, color=(30, 30, 30), width=1)

        # Draw axes
        self.display.draw_line(x, y + height, x + width, y + height, color=color, width=2)
        self.display.draw_line(x, y, x, y + height, color=color, width=2)

        # Animation shift (moves graph left as new data comes in from right)
        animation_shift = animation_frame  # 0-10 pixels shift

        # Draw data points and lines with animation
        point_width = width / len(values)
        for i in range(len(values) - 1):
            x1 = x + int(i * point_width) - animation_shift
            y1 = y + height - int((values[i] / max_val) * height)

            x2 = x + int((i + 1) * point_width) - animation_shift
            y2 = y + height - int((values[i + 1] / max_val) * height)

            # Only draw if within bounds
            if x2 >= x and x1 <= x + width:
                # Draw line
                self.display.draw_line(x1, y1, x2, y2, color=color, width=2)

                # Draw point
                if i % 4 == 0:  # Draw every 4th point to avoid clutter
                    self.display.draw_rectangle(x1 - 2, y1 - 2, x1 + 2, y1 + 2, fill=color)

        # Draw incoming new point (animated from right edge)
        if len(values) > 0:
            new_x = x + width - animation_shift
            new_y = y + height - int((values[-1] / max_val) * height)
            if new_x >= x and new_x <= x + width:
                self.display.draw_rectangle(new_x - 2, new_y - 2, new_x + 2, new_y + 2, fill=color)

    def draw_stat_page(self, title, stat_key, color, max_val):
        """Draw full-screen stat page"""
        self.display.clear(self.display.BLACK)

        # Get current value
        if stat_key == 'disk':
            value = self.stats['disk']
        else:
            value = self.stats[stat_key]

        # Large title bar (top 60 pixels)
        self.display.draw_rectangle(0, 0, self.display.width, 60, fill=color)

        # Border around title bar
        self.display.draw_rectangle(0, 0, self.display.width, 60, outline=self.display.WHITE, fill=None)
        self.display.draw_rectangle(2, 2, self.display.width - 2, 58, outline=self.display.WHITE, fill=None)

        # Title text - large and bold
        self.display.draw_text(
            self.display.width // 2, 30,
            title.upper(),
            font=self.display.font_large,
            color=self.display.BLACK,
            anchor="mm"
        )

        # Large current value in the center
        y_center = 110
        value_text = f"{value:.1f}"
        unit_text = "%" if stat_key in ['cpu', 'memory', 'disk'] else "°C"

        # Draw value with larger font
        self.display.draw_text(
            self.display.width // 2, y_center - 15,
            value_text,
            font=self.display.font_large,
            color=color,
            anchor="mm"
        )

        # Draw unit
        self.display.draw_text(
            self.display.width // 2, y_center + 15,
            unit_text,
            font=self.display.font_large,
            color=color,
            anchor="mm"
        )

        # Draw graph (full height)
        graph_y = 160
        graph_height = 110
        self.draw_graph(15, graph_y, self.display.width - 30, graph_height,
                       self.history[stat_key], max_val, color, animation_frame=0)

        self.display.update()

    def update_page(self):
        """Check if we should move to next page"""
        elapsed = time.time() - self.page_start_time
        if elapsed >= self.page_duration:
            self.current_page = (self.current_page + 1) % len(self.pages)
            self.page_start_time = time.time()

    def render_animated_page(self, title, stat_key, color, max_val):
        """Render page with animated graph"""
        # Get current value
        if stat_key == 'disk':
            value = self.stats['disk']
        else:
            value = self.stats[stat_key]

        # Large title bar (top 60 pixels)
        self.display.clear(self.display.BLACK)
        self.display.draw_rectangle(0, 0, self.display.width, 60, fill=color)

        # Border around title bar
        self.display.draw_rectangle(0, 0, self.display.width, 60, outline=self.display.WHITE, fill=None)
        self.display.draw_rectangle(2, 2, self.display.width - 2, 58, outline=self.display.WHITE, fill=None)

        # Title text
        self.display.draw_text(
            self.display.width // 2, 30,
            title.upper(),
            font=self.display.font_large,
            color=self.display.BLACK,
            anchor="mm"
        )

        # Large current value in the center
        y_center = 110
        value_text = f"{value:.1f}"
        unit_text = "%" if stat_key in ['cpu', 'memory', 'disk'] else "°C"

        self.display.draw_text(
            self.display.width // 2, y_center - 15,
            value_text,
            font=self.display.font_large,
            color=color,
            anchor="mm"
        )

        self.display.draw_text(
            self.display.width // 2, y_center + 15,
            unit_text,
            font=self.display.font_large,
            color=color,
            anchor="mm"
        )

        # Draw animated graph
        graph_y = 160
        graph_height = 110
        self.draw_graph(15, graph_y, self.display.width - 30, graph_height,
                       self.history[stat_key], max_val, color, animation_frame=0)

        self.display.update()

    def run(self):
        """Main loop"""
        print("Starting carousel dashboard...")
        print(f"Page duration: {self.page_duration}s")
        print(f"Update interval: {self.update_interval}s")
        print("Press Ctrl+C to stop")

        try:
            while self.running:
                # Update stats
                self.update_stats()

                # Render current page
                title, stat_key, color, max_val = self.pages[self.current_page]
                self.render_animated_page(title, stat_key, color, max_val)

                # Check if we should change pages
                self.update_page()

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

    parser = argparse.ArgumentParser(description='ST7789V3 Carousel Stats Dashboard')
    parser.add_argument('--update', type=int, default=1, help='Update interval in seconds')
    parser.add_argument('--page', type=int, default=5, help='Page duration in seconds')
    args = parser.parse_args()

    dashboard = CarouselDashboard(update_interval=args.update, page_duration=args.page)
    dashboard.run()


if __name__ == "__main__":
    main()
