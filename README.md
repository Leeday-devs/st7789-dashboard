# ST7789 Dashboard

Modern dashboard for Raspberry Pi 5 with 1.69" ST7789 display (240x280).

## Features

- 🖥️ **Pi5 Stats**: CPU, Memory, Temperature, Network speed
- 💾 **NAS Storage**: Synology NAS storage monitoring
- 🐋 **Docker**: Container status and running containers
- 🎨 **Colorful pill-shaped UI** with heartbeat graphs
- 🔄 **Auto-sliding pages** with smooth animations

## Installation

### Requirements

```bash
sudo apt install python3-pip python3-pil
pip3 install psutil docker
```

### Display Setup

1. Connect ST7789 1.69" display to Raspberry Pi 5
2. Install LCD library (Waveshare 1.69" ST7789)

### Configuration

Edit `st7789_modern_slides.py`:
- `PAGE_TIME`: Seconds per page (default: 8)
- `NET_IFACE`: Network interface (default: "eth0")
- `NAS_PATH`: NAS mount path (default: "/mnt/nas_docker")

### Run Manually

```bash
python3 st7789_modern_slides.py
```

### Auto-start on Boot

```bash
sudo cp st7789-display.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable st7789-display
sudo systemctl start st7789-display
```

## Service Management

```bash
# Check status
sudo systemctl status st7789-display

# Stop
sudo systemctl stop st7789-display

# Restart
sudo systemctl restart st7789-display

# View logs
journalctl -u st7789-display -f
```

## Display Pages

1. **Raspberry Pi 5** - CPU/Memory usage with heartbeat graphs, temperature, network speed
2. **Synology NAS** - Storage usage, used/free space
3. **Docker** - Total/Active/Stopped containers, running container list

## Color Scheme

- **Blue** - CPU, Docker total
- **Purple** - Memory
- **Orange** - Temperature, NAS used
- **Green** - Network, NAS free, Docker active
- **Cyan/Pink/Sky Blue** - Container pills (rotating)

## License

MIT
