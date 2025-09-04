# Hardware Configuration

## Physical Dimensions
- **Cap:** 14ft diameter, angled top (higher at center/entrance)
- **Stem:** 6ft wide, 7ft tall
- **Total Height:** ~14ft from ground to cap top
- **Interior:** Hollow with round door, seating for 2

## LED Strip Setup (Raspberry Pi 5)
- **Total LEDs:** 700 WS2811 bullet pixels
- **Configuration:** 2 strips via dual SPI channels
- **Stem Interior:** 250 LEDs on SPI1
- **Cap Exterior:** 450 LEDs on SPI0
- **Control:** Pi5Neo library (Pi 5 compatible)
- **Power:** 5V 20A minimum, injection every 100-150 LEDs

### SPI Configuration
Raspberry Pi 5 uses SPI for reliable WS2811 control:

#### SPI0 (Cap Exterior - 450 LEDs)
- **MOSI:** GPIO 10 (Pin 19)
- **SCLK:** GPIO 11 (Pin 23)
- **Device:** /dev/spidev0.0
- **Purpose:** Main visual display visible from outside

#### SPI1 (Stem Interior - 250 LEDs)
- **MOSI:** GPIO 20 (Pin 38)
- **SCLK:** GPIO 21 (Pin 40)
- **Device:** /dev/spidev1.0
- **Purpose:** Atmospheric lighting for seated viewers

### Wiring Notes
- **No level shifter required** - SPI signals are sufficient for WS2811
- Connect LED data lines directly to GPIO pins
- Share ground between Pi and LED power supply
- Keep data lines under 3ft for signal integrity

## System Configuration

### Enable SPI Channels
```bash
# Enable SPI0 (enabled by default)
sudo dietpi-config
# Navigate to: Advanced Options > SPI > Enable

# Enable SPI1
sudo nano /boot/config.txt
# Add line: dtoverlay=spi1-1cs

# Verify after reboot
ls /dev/spidev*
# Should show: /dev/spidev0.0 and /dev/spidev1.0
```

### Power Distribution
- **Supply:** 5V 20A (minimum)
- **Per LED:** 60mA max (white, full brightness)
- **Typical:** 10-15mA per LED (mixed colors)
- **Injection Points:**
  - Cap: Every 150 LEDs (3 injection points)
  - Stem: Every 125 LEDs (2 injection points)

## Audio Configuration
- **Hardware:** AU-MMSA USB adapter
- **Placement:** Inside mushroom stem
- **Target:** Human voice reactivity
- **Sampling:** 44.1kHz, 16-bit, mono
- **Buffer:** 64 samples (~1.5ms latency)
- **Library:** python-sounddevice

## Performance Specifications
- **Platform:** Raspberry Pi 5 (2.4GHz quad-core)
- **OS:** DietPi (optimized, ~32MB RAM idle)
- **Frame Rate:** 30-60 FPS achievable
- **Update Time:** ~21ms for 700 LEDs
- **Audio Latency:** < 10ms total
- **CPU Target:** < 30% utilization
- **Temperature:** < 60°C with active cooling

## Development Setup
- **SSH Access:** dietpi@192.168.1.152
- **Virtual Environment:** /home/dietpi/the-mushroom/mushroom-env
- **Test Script:** tests/test_spi.py for hardware validation
- **Main Application:** main.py for patterns

## Troubleshooting

### LED Issues
- Verify SPI enabled: `lsmod | grep spi`
- Check permissions: Run with `sudo`
- Test minimal: `sudo python3 tests/test_spi.py --count 1`

### Performance
- Monitor temp: `vcgencmd measure_temp`
- Check CPU: `htop` or `top`
- Reduce brightness if needed

### Power Problems
- Check voltage at injection points (4.5V minimum)
- Verify ground connections
- Use thicker wire for power distribution (14-16 AWG)