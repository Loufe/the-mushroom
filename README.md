# The Mushroom 🍄
Interactive LED sculpture controller for 700 WS2811 LEDs on Raspberry Pi 5

## Quick Start

### 1. Hardware Setup
- Connect 74HCT125 level shifter to Pi GPIO pins 10, 12, 18, 21
- Wire LED strips (2×200 + 2×150 configuration)
- Connect 5V power supply with appropriate current capacity

### 2. Software Installation
```bash
# SSH into your Pi
ssh dietpi@mushroom-pi

# Clone repository
git clone https://github.com/yourusername/the-mushroom.git
cd the-mushroom

# Create virtual environment
python3 -m venv mushroom-env
source mushroom-env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Test Hardware
```bash
# Test single strip (10 LEDs on GPIO 10)
sudo mushroom-env/bin/python test_hardware.py --gpio 10 --count 10

# Test all configured GPIO pins
sudo mushroom-env/bin/python test_hardware.py --all --count 10
```

### 4. Run Rainbow Wave Pattern
```bash
# Run with default settings
sudo mushroom-env/bin/python main.py

# Run with options
sudo mushroom-env/bin/python main.py --pattern rainbow_wave --brightness 128
```

## Architecture

```
the-mushroom/
├── src/
│   ├── led_controller.py    # Hardware abstraction layer
│   └── patterns/
│       ├── base.py          # Abstract pattern class
│       └── rainbow.py       # Rainbow effects
├── config/
│   ├── led_config.yaml     # Hardware configuration
│   └── coordinates.yaml    # 3D mapping (TBD)
├── main.py                  # Main application
└── test_hardware.py         # Hardware test utility
```

## Available Patterns
- `test` - RGB color cycle
- `rainbow_wave` - Traveling rainbow wave
- `rainbow_cycle` - All LEDs cycle through rainbow together

## Documentation
- [Development Setup](docs/development-setup.md)
- [Hardware Configuration](docs/hardware-config.md)
- [Manual Setup Guide](docs/manual-setup.md)

## License
See LICENSE file
