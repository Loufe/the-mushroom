# Claude Code Context

## Critical Constraints
- **Hardware**: Raspberry Pi 5 only (Pi5Neo library, not CircuitPython)
- **LEDs**: Exactly 700 WS2811 pixels
  - Cap exterior: 450 LEDs on SPI0 (GPIO 10, Pin 19)
  - Stem interior: 250 LEDs on SPI1 (GPIO 20, Pin 38)
- **Power**: 12V system, requires sudo for GPIO access
- **OS**: DietPi preferred (lighter than Raspberry Pi OS)

## Quick Commands
```bash
# Test hardware
sudo mushroom-env/bin/python tests/test_spi.py

# Run main application
./run.sh --pattern rainbow_wave --brightness 128

# View service logs
sudo journalctl -u mushroom-lights -f

# Restart service after config changes
sudo systemctl restart mushroom-lights
```

## Performance Targets
- 30+ FPS with all 700 LEDs
- <30% CPU usage on Pi 5
- <60°C with active cooling
- <21ms update time for full strip

## Code Guidelines
- DO NOT create new files unless essential
- DO NOT add comments unless requested
- PREFER editing existing patterns over creating new files

## Project Structure
- `main.py` - Entry point and pattern management
- `src/hardware/` - LED controller abstraction
- `src/patterns/` - Pattern implementations (auto-registered)
- `config/` - YAML configurations
- `tests/` - Hardware validation scripts