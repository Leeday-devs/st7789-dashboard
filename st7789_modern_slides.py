#!/usr/bin/env python3
# ST7789V3 240x280 1.69" Modern Sliding Dashboard
# Pi5 Stats | Synology NAS | Portainer Stats

import os
import sys
sys.path.append("/home/pi/LCD_Module_RPI_code/RaspberryPi/python")

import time
import itertools
import psutil
import docker
import math
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from lib import LCD_1inch69

# ========== CONFIG ==========
PAGE_TIME = 8           # Seconds per page
SLIDE_FRAMES = 25       # Number of frames in slide animation
SLIDE_DELAY = 0.015     # Delay between slide frames (smoother)
NET_IFACE = "eth0"
NAS_PATH = "/mnt/nas_docker"

# ========== DISPLAY SETUP ==========
disp = LCD_1inch69.LCD_1inch69()
disp.Init()
disp.clear()

W = disp.width   # 240
H = disp.height  # 280

# ========== MODERN COLORS ==========
BG = (12, 14, 20)
BG_CARD = (22, 25, 32)
BG_CARD_LIGHT = (30, 34, 42)
FG = (248, 250, 252)
FG_DIM = (170, 178, 192)
FG_MUTED = (110, 120, 140)

ACCENT = (88, 166, 255)
CYAN = (34, 211, 238)
GREEN = (52, 211, 153)
ORANGE = (251, 146, 60)
RED = (248, 113, 113)

OK = (52, 211, 153)
WARN = (251, 191, 36)
BAD = (248, 113, 113)

SHADOW = (6, 8, 12, 180)

# ========== FONTS ==========
def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

F32B = load_font("/usr/share/fonts/truetype/roboto/Roboto-Bold.ttf", 32)
F28B = load_font("/usr/share/fonts/truetype/roboto/Roboto-Bold.ttf", 28)
F24B = load_font("/usr/share/fonts/truetype/roboto/Roboto-Bold.ttf", 24)
F20B = load_font("/usr/share/fonts/truetype/roboto/Roboto-Bold.ttf", 20)
F18 = load_font("/usr/share/fonts/truetype/roboto/Roboto-Regular.ttf", 18)
F16 = load_font("/usr/share/fonts/truetype/roboto/Roboto-Regular.ttf", 16)
F14 = load_font("/usr/share/fonts/truetype/roboto/Roboto-Regular.ttf", 14)
F12 = load_font("/usr/share/fonts/truetype/roboto/Roboto-Regular.ttf", 12)

# ========== UI COMPONENTS ==========
def draw_pill_card(draw, x, y, w, h, color=ACCENT):
    """Draw flat pill-shaped card"""
    radius = h // 2  # Full pill shape
    draw.rounded_rectangle((x, y, x+w, y+h), radius=radius, fill=color)

def draw_heartbeat_graph(draw, x, y, w, h, percent, color=(255, 255, 255)):
    """Draw heartbeat/waveform style graph"""
    # Base line position
    mid_y = y + h // 2

    # Calculate number of points based on width
    num_points = w // 3
    points = []

    for i in range(num_points):
        px = x + (i * w) // num_points

        # Create heartbeat pattern
        t = (i / num_points) * 4 * math.pi

        # Different waveform patterns based on percentage
        if i < int(num_points * percent / 100):
            # Active heartbeat wave
            wave = math.sin(t * 3) * 0.3 + math.sin(t * 0.5) * 0.5
            py = mid_y + int(wave * (h * 0.35))
        else:
            # Flat line after percentage
            py = mid_y

        points.append((px, py))

    # Draw the waveform
    if len(points) > 1:
        for i in range(len(points) - 1):
            draw.line([points[i], points[i+1]], fill=color, width=2)

def draw_stat_pill(draw, x, y, w, h, label, value, percent, icon="", color=ACCENT):
    """Flat stat pill card with heartbeat graph"""
    draw_pill_card(draw, x, y, w, h, color=color)
    # Centered text
    label_text = f"{icon} {label}"
    label_w = draw.textlength(label_text, font=F12)
    draw.text((x + (w - label_w) / 2, y + 8), label_text, font=F12, fill=(255, 255, 255, 200))

    value_w = draw.textlength(value, font=F24B)
    draw.text((x + (w - value_w) / 2, y + 24), value, font=F24B, fill=(255, 255, 255))

    # Centered heartbeat graph
    draw_heartbeat_graph(draw, x + 14, y + h - 16, w - 28, 10, percent, (255, 255, 255))

def draw_header(draw, title, icon=""):
    """Minimal clean header"""
    now = datetime.now().strftime("%H:%M:%S")
    draw.text((14, 14), icon, font=F20B, fill=ACCENT)
    draw.text((46, 16), title, font=F18, fill=FG)
    time_w = draw.textlength(now, font=F12)
    draw.text((W-time_w-14, 18), now, font=F12, fill=FG_DIM)
    draw.rectangle((14, 46, W-14, 47), fill=BG_CARD_LIGHT)

def status_color(percent):
    """Return color based on percentage"""
    if percent < 70:
        return OK
    elif percent < 85:
        return WARN
    else:
        return BAD

def human_bytes(n):
    """Convert bytes to human readable format"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"

_prev_net = None
def get_network_speed(iface):
    """Get network upload/download speed"""
    global _prev_net
    io = psutil.net_io_counters(pernic=True).get(iface)
    t = time.time()

    if not io:
        return 0.0, 0.0

    cur = (t, io.bytes_recv, io.bytes_sent)

    if not _prev_net:
        _prev_net = cur
        return 0.0, 0.0

    dt = max(cur[0] - _prev_net[0], 1e-6)
    down = (cur[1] - _prev_net[1]) / dt
    up = (cur[2] - _prev_net[2]) / dt
    _prev_net = cur

    return down, up

# ========== PAGE 1: PI5 STATS ==========
def page_pi5():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    draw_header(d, "Raspberry Pi 5", "🖥️")

    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent

    try:
        temp_sensors = psutil.sensors_temperatures()
        if 'cpu_thermal' in temp_sensors and temp_sensors['cpu_thermal']:
            temp = temp_sensors['cpu_thermal'][0].current
        else:
            temp = 0
    except:
        temp = 0

    # CPU & Memory pills - thinner with more space
    draw_stat_pill(d, 12, 60, 216, 68, "CPU", f"{int(cpu)}%", cpu, "⚡", (88, 166, 255))
    draw_stat_pill(d, 12, 140, 216, 68, "Memory", f"{int(mem)}%", mem, "💾", (168, 85, 247))

    # Temperature pill
    draw_pill_card(d, 12, 228, 105, 42, color=(251, 146, 60))
    temp_text = f"🌡️ {int(temp)}°C"
    temp_w = d.textlength(temp_text, font=F16)
    d.text((12 + (105 - temp_w) / 2, 232), temp_text, font=F16, fill=(255, 255, 255))
    temp_label_w = d.textlength("Temp", font=F12)
    d.text((12 + (105 - temp_label_w) / 2, 252), "Temp", font=F12, fill=(255, 255, 255, 180))

    # Network speed pill
    draw_pill_card(d, 123, 228, 105, 42, color=(16, 185, 129))
    down, up = get_network_speed(NET_IFACE)
    net_icon_w = d.textlength("🌐", font=F12)
    d.text((123 + (105 - net_icon_w) / 2, 230), "🌐", font=F12, fill=(255, 255, 255, 200))
    down_text = f"↓{human_bytes(down)}/s"
    down_w = d.textlength(down_text, font=F12)
    d.text((123 + (105 - down_w) / 2, 242), down_text, font=F12, fill=(255, 255, 255))
    up_text = f"↑{human_bytes(up)}/s"
    up_w = d.textlength(up_text, font=F12)
    d.text((123 + (105 - up_w) / 2, 254), up_text, font=F12, fill=(255, 255, 255, 180))

    return img

# ========== PAGE 2: SYNOLOGY NAS ==========
def page_nas():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    draw_header(d, "Synology NAS", "💾")

    try:
        st = os.statvfs(NAS_PATH)
        total = st.f_blocks * st.f_frsize
        free = st.f_bavail * st.f_frsize
        used = total - free
        pct = (used / total * 100) if total else 0

        # Main usage pill - pink/magenta (thinner)
        draw_pill_card(d, 12, 60, 216, 95, color=(236, 72, 153))

        pct_text = f"{int(pct)}%"
        tw = d.textlength(pct_text, font=F28B)
        d.text((12 + (216 - tw) / 2, 67), pct_text, font=F28B, fill=(255, 255, 255))

        storage_text = "Storage Used"
        storage_w = d.textlength(storage_text, font=F12)
        d.text((12 + (216 - storage_w) / 2, 100), storage_text, font=F12, fill=(255, 255, 255, 180))

        draw_heartbeat_graph(d, 28, 120, W-56, 12, pct, (255, 255, 255))

        usage_text = f"{used/1e9:.1f}GB / {total/1e9:.1f}GB"
        usage_w = d.textlength(usage_text, font=F12)
        d.text((12 + (216 - usage_w) / 2, 137), usage_text, font=F12, fill=(255, 255, 255, 200))

        # Used/Free pills - centered text
        draw_pill_card(d, 12, 170, 105, 58, color=(239, 68, 68))
        used_label_w = d.textlength("Used", font=F12)
        d.text((12 + (105 - used_label_w) / 2, 176), "Used", font=F12, fill=(255, 255, 255, 180))
        used_val = f"{used/1e9:.1f}"
        used_val_w = d.textlength(used_val, font=F20B)
        d.text((12 + (105 - used_val_w) / 2, 192), used_val, font=F20B, fill=(255, 255, 255))
        gb_w = d.textlength("GB", font=F12)
        d.text((12 + (105 - gb_w) / 2, 216), "GB", font=F12, fill=(255, 255, 255, 180))

        draw_pill_card(d, 123, 170, 105, 58, color=(34, 197, 94))
        free_label_w = d.textlength("Free", font=F12)
        d.text((123 + (105 - free_label_w) / 2, 176), "Free", font=F12, fill=(255, 255, 255, 180))
        free_val = f"{free/1e9:.1f}"
        free_val_w = d.textlength(free_val, font=F20B)
        d.text((123 + (105 - free_val_w) / 2, 192), free_val, font=F20B, fill=(255, 255, 255))
        gb_w2 = d.textlength("GB", font=F12)
        d.text((123 + (105 - gb_w2) / 2, 216), "GB", font=F12, fill=(255, 255, 255, 180))

    except FileNotFoundError:
        draw_pill_card(d, 20, 110, W-40, 60, color=(248, 113, 113))
        err_text = "⚠️ NAS Not Mounted"
        err_w = d.textlength(err_text, font=F14)
        d.text((20 + (W-40 - err_w) / 2, 130), err_text, font=F14, fill=(255, 255, 255))

    return img

# ========== PAGE 3: PORTAINER/DOCKER ==========
def page_portainer():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    draw_header(d, "Docker", "🐋")

    try:
        cli = docker.from_env()
        containers = cli.containers.list()
        total_containers = len(cli.containers.list(all=True))
        running = len(containers)
        stopped = total_containers - running

        # Stats pills - centered text
        draw_pill_card(d, 12, 60, 68, 56, color=(59, 130, 246))
        total_label_w = d.textlength("Total", font=F12)
        d.text((12 + (68 - total_label_w) / 2, 66), "Total", font=F12, fill=(255, 255, 255, 180))
        total_val_w = d.textlength(str(total_containers), font=F24B)
        d.text((12 + (68 - total_val_w) / 2, 80), str(total_containers), font=F24B, fill=(255, 255, 255))

        draw_pill_card(d, 86, 60, 68, 56, color=(34, 197, 94))
        active_label_w = d.textlength("Active", font=F12)
        d.text((86 + (68 - active_label_w) / 2, 66), "Active", font=F12, fill=(255, 255, 255, 180))
        active_val_w = d.textlength(str(running), font=F24B)
        d.text((86 + (68 - active_val_w) / 2, 80), str(running), font=F24B, fill=(255, 255, 255))

        draw_pill_card(d, 160, 60, 68, 56, color=(107, 114, 128))
        off_label_w = d.textlength("Off", font=F12)
        d.text((160 + (68 - off_label_w) / 2, 66), "Off", font=F12, fill=(255, 255, 255, 180))
        off_val_w = d.textlength(str(stopped), font=F24B)
        d.text((160 + (68 - off_val_w) / 2, 80), str(stopped), font=F24B, fill=(255, 255, 255))

        # Running containers list
        d.text((14, 130), "Running Containers", font=F14, fill=FG_DIM)

        if running == 0:
            draw_pill_card(d, 12, 154, W-24, 44, color=(71, 85, 105))
            none_text = "None running"
            none_w = d.textlength(none_text, font=F14)
            d.text((12 + (W-24 - none_w) / 2, 166), none_text, font=F14, fill=(255, 255, 255))
        else:
            # Colorful pills for each container - centered text
            y = 154
            colors = [
                (14, 165, 233),   # Sky blue
                (168, 85, 247),   # Purple
                (236, 72, 153),   # Pink
                (251, 146, 60),   # Orange
            ]
            for idx, container in enumerate(sorted(containers, key=lambda c: c.name)[:4]):
                if y > H - 45:
                    break

                color = colors[idx % len(colors)]
                draw_pill_card(d, 12, y, W-24, 34, color=color)

                name = container.name[:22] if len(container.name) > 22 else container.name
                name_w = d.textlength(name, font=F14)

                # Center the text with dot indicator
                dot_size = 6
                total_w = dot_size + 6 + name_w  # dot + spacing + text
                start_x = 12 + (W-24 - total_w) / 2

                d.ellipse((start_x, y+13, start_x+dot_size, y+19), fill=(255, 255, 255))
                d.text((start_x + dot_size + 6, y+8), name, font=F14, fill=(255, 255, 255))

                y += 42

            if running > 4:
                more_text = f"+{running - 4} more"
                more_w = d.textlength(more_text, font=F12)
                d.text((W/2 - more_w/2, y+4), more_text, font=F12, fill=FG_MUTED)

    except Exception as e:
        draw_pill_card(d, 20, 110, W-40, 60, color=(248, 113, 113))
        err_text = "⚠️ Docker Error"
        err_w = d.textlength(err_text, font=F14)
        d.text((20 + (W-40 - err_w) / 2, 130), err_text, font=F14, fill=(255, 255, 255))

    return img

# ========== SLIDING ANIMATION ==========
def slide_left(img_current, img_next):
    """Smooth slide from right to left"""
    for i in range(SLIDE_FRAMES + 1):
        offset = int((W * i) / SLIDE_FRAMES)
        composite = Image.new("RGB", (W, H), BG)

        if offset < W:
            current_crop = img_current.crop((offset, 0, W, H))
            composite.paste(current_crop, (0, 0))

        if offset > 0:
            next_crop = img_next.crop((0, 0, offset, H))
            composite.paste(next_crop, (W - offset, 0))

        disp.ShowImage(composite)
        time.sleep(SLIDE_DELAY)

# ========== MAIN LOOP ==========
PAGES = [page_pi5, page_nas, page_portainer]

def main():
    print("✨ ST7789 Modern Dashboard")
    print(f"📺 Display: {W}x{H}")
    print(f"⏱️  Page interval: {PAGE_TIME}s")
    print(f"📊 Pages: Pi5 → NAS → Docker\n")

    cycle = itertools.cycle(PAGES)
    current_page_func = next(cycle)
    current_img = current_page_func()
    disp.ShowImage(current_img)
    last_switch = time.time()

    while True:
        time.sleep(1)

        current_img = current_page_func()
        disp.ShowImage(current_img)

        if time.time() - last_switch >= PAGE_TIME:
            print(f"Switching to next page... ({datetime.now().strftime('%H:%M:%S')})")
            next_page_func = next(cycle)
            next_img = next_page_func()
            slide_left(current_img, next_img)
            current_page_func = next_page_func
            current_img = next_img
            last_switch = time.time()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nStopping dashboard...")
    finally:
        disp.module_exit()
        print("Cleanup complete. Goodbye!")
