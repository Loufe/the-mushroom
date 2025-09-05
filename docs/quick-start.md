# Quick Start Guide - Fresh Installation

## System Requirements
- Raspberry Pi 5 with active cooling
- DietPi OS 
- 700 WS2811 LED pixels
- 12V 20A+ power supply
- Ethernet or WiFi for initial setup

## Installation Steps

### 1. Enable SPI Communication

```bash
# Enable SPI0 
sudo dietpi-config
# Navigate to: Advanced Options > SPI > Enable

# Enable SPI1 by editing boot config
sudo nano /boot/config.txt
# Add at the end:
dtoverlay=spi1-1cs

# Save and reboot
sudo reboot

# Verify both SPI devices exist
ls /dev/spidev*
# Expected output: /dev/spidev0.0 /dev/spidev1.0
```

### 2. Install Software

```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3-pip python3-venv git python3-dev

# Clone project
cd ~
git clone https://github.com/Loufe/the-mushroom.git
cd the-mushroom

# Create Python virtual environment
python3 -m venv mushroom-env
source mushroom-env/bin/activate

# Install Python packages
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Hardware Connections

**Data connections:**
- GPIO 10 (Pin 19) → Cap LEDs data (450 pixels)
- GPIO 20 (Pin 38) → Stem LEDs data (250 pixels)
- Pi GND → LED ground and power supply ground (shared)

**Power:**
- 12V supply → LED power (NOT from Pi)
- Power injection every 100-150 LEDs
- Common ground essential

**Note on level shifting:** SPI signals are 3.3V but typically work directly with WS2811 LEDs. If you experience signal issues, consider adding a level shifter.

### 4. Test Installation

```bash
cd ~/the-mushroom
source mushroom-env/bin/activate

# Test with minimal LEDs first
sudo mushroom-env/bin/python tests/test_spi.py --count 1 --mode stem
sudo mushroom-env/bin/python tests/test_spi.py --count 1 --mode cap

# Test full configuration
sudo mushroom-env/bin/python tests/test_spi.py --mode both
```

### 5. Run Light Show

```bash
# Start with reduced brightness
sudo mushroom-env/bin/python main.py --brightness 64

# Available patterns: test, rainbow_wave, rainbow_cycle
sudo mushroom-env/bin/python main.py --pattern rainbow_wave
```

## Troubleshooting

**No SPI devices:**
```bash
lsmod | grep spi  # Check module loaded
cat /boot/config.txt | grep spi  # Verify configuration
```

**Permission errors:**
Must use `sudo` for SPI/GPIO access

**LEDs not responding:**
- Verify 12V at LED strips
- Check common ground
- Test with single LED
- If signal issues persist, consider adding a level shifter

**Performance monitoring:**
```bash
htop  # CPU usage
vcgencmd measure_temp  # Temperature
```

## Updating an Existing Installation

To update your mushroom installation:

```bash
cd ~/the-mushroom
source mushroom-env/bin/activate

# Get latest code
git pull

# Update dependencies
pip install --upgrade -r requirements.txt
```

## Technical Notes

This project uses Pi5Neo library which communicates via SPI instead of PWM/PCM. Benefits:
- Raspberry Pi 5 compatible
- Simpler than PWM/DMA configuration
- Two independent LED channels
- Direct GPIO connection typically works well

The SPI approach trades some GPIO flexibility for Pi 5 compatibility and simpler setup.