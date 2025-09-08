# Claude Code Context

## Critical Constraints
- **Hardware**: Raspberry Pi 5 only (Pi5Neo library using spidev)
- **LEDs**: Total of cap + stem LEDs from config (GRB color order)
  - Single SPI chain on SPI0 (GPIO 10, Pin 19, /dev/spidev0.0)
  - Cap wired first, stem wired second in series
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
- DO NOT add comments unless requested - this includes obvious comments like "# Get buffers" or "# Wait for patterns"
- PREFER editing existing patterns over creating new files
- ALWAYS fail fast - no soft failures, raise errors immediately
  - Use RuntimeError for logic errors, ValueError for bad inputs
  - Never use .get() with defaults - check existence and fail if missing
  - No "shouldn't happen" code paths - always raise if unexpected state

## Performance Reality (Measured)
**Actual bottleneck**: SPI transmission (~32ms for all LEDs), not buffer prep (<1ms)
- Single SPI channel for all LEDs eliminates dual-channel interference
- ~30 FPS with single continuous transmission
- WS2811 protocol requires bitstream encoding and precise timing

## Project Structure
- `main.py` - Entry point and pattern management
- `src/hardware/led_controller.py` - Single SPI controller with parallel pattern generation
- `src/patterns/` - Pattern implementations (auto-registered)
- `config/led_config.yaml` - Strip definitions and hardware settings
- `tests/test_spi.py` - Hardware validation scripts