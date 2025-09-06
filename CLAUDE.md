# Claude Code Context

## Critical Constraints
- **Hardware**: Raspberry Pi 5 only (Pi5Neo library using spidev)
- **LEDs**: Exactly 700 WS2811 pixels (GRB color order)
  - Cap exterior: 450 LEDs on SPI0 (GPIO 10, Pin 19, /dev/spidev0.0)
  - Stem interior: 250 LEDs on SPI1 (GPIO 20, Pin 38, /dev/spidev1.0)
- **Power**: 12V system, requires sudo for GPIO/SPI access
- **OS**: DietPi preferred (lighter than Raspberry Pi OS)
- **Protocol**: 800kHz SPI with bitstream encoding (0xC0=LOW, 0xF8=HIGH)

## Quick Commands
```bash
# Test hardware
sudo mushroom-env/bin/python tests/test_spi.py

# Run main application
./run.sh --pattern rainbow --brightness 128

# View service logs
sudo journalctl -u mushroom-lights -f

# Restart service after config changes
sudo systemctl restart mushroom-lights
```

## Performance Targets
- 30 FPS minimum, 60 FPS target with all 700 LEDs
- <30% CPU usage on Pi 5
- <60°C with active cooling
- <21ms update time for full strip

## Code Guidelines
- DO NOT create new files unless essential
- DO NOT add comments unless requested
- PREFER editing existing patterns over creating new files

## Performance Reality (Measured)
**Actual bottleneck**: SPI transmission (~20ms for 450 LEDs), not buffer prep (<1ms)
- Cap: ~48 FPS limited by hardware protocol timing
- Stem: ~98 FPS (half the LEDs = half the time)
- WS2811 protocol requires bitstream encoding and precise timing

## Project Structure
- `main.py` - Entry point and pattern management
- `src/hardware/led_controller.py` - Pi5Neo wrapper with dual SPI support
- `src/patterns/` - Pattern implementations (auto-registered)
- `config/led_config.yaml` - Strip definitions and hardware settings
- `tests/test_spi.py` - Hardware validation scripts