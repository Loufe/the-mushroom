# The Mushroom 🍄

Interactive LED sculpture controller for a 14ft mushroom with 700 WS2811 LEDs.

## Features
- 700 WS2811 bullet pixels (450 cap, 250 stem)
- Dual SPI channels for parallel control
- 30+ FPS real-time patterns
- Auto-start service on boot
- Extensible pattern system
- Future: Audio-reactive modes

## Quick Start

```bash
# Clone and setup (automated)
git clone https://github.com/Loufe/the-mushroom.git
cd the-mushroom
./setup.sh

# Run the light show
./run.sh --pattern rainbow_wave --brightness 128
```

## Documentation
- [Setup Guide](docs/SETUP.md) - Installation, hardware connections, troubleshooting
- [Development](docs/DEVELOPMENT.md) - Creating patterns and architecture

## Available Patterns
- `test` - RGB color cycle
- `rainbow_wave` - Traveling rainbow wave
- `rainbow_cycle` - Synchronized rainbow colors
- `solid` - Single color
- `breathing` - Smooth fade in/out

## Requirements
- Raspberry Pi 5 with active cooling
- DietPi OS (recommended) or Raspberry Pi OS
- Python 3.9+
- 12V 20A+ power supply for LEDs
- Common ground between Pi and LED power

## License
See LICENSE file