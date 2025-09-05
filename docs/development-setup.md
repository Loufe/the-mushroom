# Development Setup Guide

## Development Environment Decision
**Recommendation: SSH development from WSL**
- Use VS Code with Remote-SSH extension
- Keep code on Pi, edit remotely
- No need to sync files or manage versions

## DietPi Initial Setup
Before clicking "Go" in Raspberry Pi Imager:

1. **Enable SSH in Imager:**
   - Click gear icon (Advanced Options)
   - Enable SSH with password authentication
   - Set hostname: `mushroom-pi`
   - Set username: `dietpi` (default)
   - Set password: (your choice)
   - Configure WiFi if available

2. **First Boot Configuration:**
   ```bash
   # After first SSH connection
   sudo dietpi-config
   # Enable: SSH, disable unnecessary services
   # Set static IP if desired
   ```

## Library Decision
**Use pi5neo** for Raspberry Pi 5 compatibility:
- Designed specifically for Pi 5's SPI interface
- Dual SPI channel support for parallel LED control
- No DMA conflicts with audio
- Lower CPU overhead than PWM-based solutions
- Direct SPI communication for reliable timing

**Why not CircuitPython NeoPixel:**
- Limited to 300 LEDs with brightness control (Python overhead)
- Extra abstraction layer adds latency
- We need maximum performance for 700 LEDs + audio processing

**Audio: python-sounddevice confirmed**
- Better than PyAudio on Pi
- Low latency callback mode
- NumPy integration

## Project Dependencies
```txt
# requirements.txt
pi5neo
sounddevice
numpy
scipy
pyyaml
psutil
```

## 3D Coordinate Mapping Validation
**Simple visual validation approach:**
1. Create test patterns that light specific regions
2. Use phone video to verify physical locations
3. Implement coordinate test mode:
   - Light cap center → verify
   - Light cap edge → verify
   - Light stem levels → verify
4. Adjust mapping based on observations

## Next Development Steps
1. Flash DietPi with SSH enabled
2. Initial Pi setup and library installation
3. Hardware test script for LED strips
4. Audio capture test
5. Basic pattern engine