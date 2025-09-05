# The Mushroom 🍄
Interactive LED sculpture controller for 700 WS2811 LEDs on Raspberry Pi 5

## Overview
- **Platform**: Raspberry Pi 5 with DietPi OS
- **LEDs**: 700 WS2811 bullet pixels (250 stem interior, 450 cap exterior)
- **Control**: Dual SPI channels using Pi5Neo library
- **Features**: Real-time patterns, audio-reactive modes, 30+ FPS performance

## Quick Start

### 1. Hardware Setup
- **Stem Interior**: 250 LEDs → SPI1 (GPIO 20/21)
- **Cap Exterior**: 450 LEDs → SPI0 (GPIO 10/11)
- Connect 12V power supply (15A minimum for 12V WS2811)
- Power injection every 200-300 LEDs (12V has less voltage drop)
- No level shifter needed - 12V strips still use 3.3V/5V data signals

### 2. Raspberry Pi 5 Setup
```bash
# Enable both SPI channels
sudo dietpi-config
# Navigate to: Advanced Options > SPI > Enable

# Add SPI1 to boot config
sudo nano /boot/config.txt
# Add: dtoverlay=spi1-1cs

# Reboot
sudo reboot

# Verify SPI devices
ls /dev/spidev*
# Should show: /dev/spidev0.0 and /dev/spidev1.0
```

### 3. Software Installation
```bash
# SSH into your Pi
ssh dietpi@192.168.1.152

# Clone and setup
git clone https://github.com/Loufe/the-mushroom.git
cd the-mushroom
./setup.sh  # Automated setup (no sudo)
```

### 4. Test Hardware
```bash
# Quick test with 10 LEDs per strip
sudo mushroom-env/bin/python tests/test_spi.py --count 10

# Test full configuration
sudo mushroom-env/bin/python tests/test_spi.py --mode both

# Test dual simultaneous control
sudo mushroom-env/bin/python tests/test_spi.py --mode dual
```

### 5. Run Main Application
```bash
# Use the run.sh script to start the LED controller:
./run.sh

# With options:
./run.sh --pattern rainbow_wave --brightness 128
```

## Architecture

```
the-mushroom/
├── src/
│   ├── hardware/
│   │   └── led_controller.py  # Pi5Neo-based hardware control
│   ├── patterns/
│   │   ├── base.py            # Abstract pattern class
│   │   ├── test.py            # Test pattern
│   │   └── rainbow.py         # Rainbow effects
│   └── effects/
│       └── colors.py          # Color utilities and palettes
├── tests/                     # Test files
│   ├── test_spi.py            # SPI hardware test
│   ├── test_gpio_verify.py    # GPIO verification
│   └── led_controller_single.py # Mock controller
├── scripts/                   # Operational scripts
│   ├── setup_autostart.sh    # Systemd service setup
│   └── change_pattern.sh     # Pattern switcher
├── config/
│   ├── led_config.yaml       # Strip configuration
│   └── startup.yaml          # Startup settings
├── main.py                    # Main application
└── requirements.txt          # Python dependencies
```

## LED Configuration

The sculpture uses two independent SPI channels:

- **Stem Interior** (250 LEDs): Creates atmospheric lighting for seated viewers
- **Cap Exterior** (450 LEDs): Visible from outside, main visual display

This dual-channel approach enables:
- Independent control of interior/exterior zones
- Parallel updates for better performance
- Different effects for different viewing angles

## Available Patterns
- `test` - RGB color cycle
- `rainbow_wave` - Traveling rainbow wave
- `rainbow_cycle` - Synchronized rainbow colors

## Troubleshooting

### SPI Not Working
```bash
# Check SPI is enabled
lsmod | grep spi
# Should show: spi_bcm2835

# Check devices exist
ls -la /dev/spidev*

# Test with minimal LEDs
sudo python3 tests/test_spi.py --count 1
```

### Permission Errors
- Always run LED scripts with `sudo`
- Ensure user is in `gpio` and `spi` groups

### Performance Issues
- Check CPU temperature: `vcgencmd measure_temp`
- Ensure active cooling is connected
- Reduce brightness if needed

## Next Steps
- [ ] Audio-reactive patterns using USB microphone
- [ ] Mushroom-themed effects (spots, gills, spores)
- [ ] 3D coordinate mapping for spatial effects
- [ ] Web interface for remote control
- [ ] Sensor integration (motion, sound level)

## Documentation
- [Hardware Setup Guide](docs/hardware-config.md)
- [Development Guide](docs/development-setup.md)
- [Pattern Creation](docs/manual-setup.md)

## License
See LICENSE file