# Setup Guide

## Prerequisites
- Raspberry Pi 5 with active cooling
- DietPi OS (or Raspberry Pi OS)
- 700 WS2811 LED pixels
- 12V 20A+ power supply
- Internet connection for initial setup

## Hardware Connections

### Data Connections
- **Cap LEDs (450)**: GPIO 10 (Pin 19) → LED data wire
- **Stem LEDs (250)**: GPIO 20 (Pin 38) → LED data wire
- **Ground**: Pi GND → LED ground → Power supply ground (shared)

### Power Setup
- 12V power supply → LED strips (NOT from Pi)
- Power injection every 200-300 LEDs (check for 10.5V minimum at injection points)
- Use 14-16 AWG wire for power distribution to prevent voltage drop
- Each LED draws ~20mA at full white (typical: 5-10mA mixed colors)
- Common ground between Pi and LED power supply is essential

## Quick Install (Automated)

```bash
# SSH into your Pi
ssh dietpi@[your-pi-ip]

# Clone and setup
git clone https://github.com/Loufe/the-mushroom.git
cd the-mushroom
./setup.sh  # Handles everything automatically

# Test installation
sudo mushroom-env/bin/python tests/test_spi.py --count 10

# Run the light show
./run.sh --pattern rainbow --brightness 64
```

The setup script will:
- Check system requirements
- Enable both SPI channels
- Install Python dependencies
- Test hardware connections
- Optionally configure autostart service

## Manual Installation

### 1. Enable SPI Channels

```bash
# Enable SPI0 via dietpi-config
sudo dietpi-config
# Navigate to: Advanced Options > SPI > Enable

# Enable SPI1 by editing boot config
sudo nano /boot/config.txt
# Add line: dtoverlay=spi1-1cs

# Reboot
sudo reboot

# Verify both SPI devices exist
ls /dev/spidev*
# Should show: /dev/spidev0.0 /dev/spidev1.0
```

### 2. Install Dependencies

```bash
# System packages
sudo apt update
sudo apt install -y python3-pip python3-venv git python3-dev build-essential

# Create virtual environment
cd ~/the-mushroom
python3 -m venv mushroom-env
source mushroom-env/bin/activate

# Install Python packages
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Test Hardware

```bash
cd ~/the-mushroom
source mushroom-env/bin/activate

# Test with minimal LEDs first
sudo mushroom-env/bin/python tests/test_spi.py --count 1 --mode stem
sudo mushroom-env/bin/python tests/test_spi.py --count 1 --mode cap

# If successful, test full configuration
sudo mushroom-env/bin/python tests/test_spi.py --mode both
```

## Troubleshooting

### No SPI Devices Found
```bash
lsmod | grep spi  # Check SPI module loaded
cat /boot/config.txt | grep spi  # Verify configuration
```

### Permission Errors
- Must use `sudo` for GPIO/SPI access
- Or add user to gpio group: `sudo usermod -a -G gpio $USER`

### LEDs Not Responding
1. Verify 12V power is on
2. Check common ground between Pi and LEDs
3. Test with single LED: `--count 1`
4. Ensure data wires are under 3ft

### Performance Issues
```bash
vcgencmd measure_temp  # Check temperature (<80°C)
htop  # Monitor CPU usage
```

## Autostart Configuration

### Enable Service
```bash
sudo bash scripts/setup_autostart.sh
```

This creates a systemd service that:
- Starts the LED show on boot
- Automatically restarts on failure
- Uses settings from `config/startup.yaml`

### Service Management
```bash
sudo systemctl status mushroom-lights   # Check status
sudo systemctl restart mushroom-lights  # Restart service
sudo systemctl stop mushroom-lights     # Stop service
sudo systemctl disable mushroom-lights  # Disable autostart
sudo journalctl -u mushroom-lights -f   # View logs
```

### Change Patterns
```bash
# Interactive pattern changer
bash scripts/change_pattern.sh

# Or edit config directly
nano config/startup.yaml
sudo systemctl restart mushroom-lights
```

## Updating

```bash
cd ~/the-mushroom
git pull
source mushroom-env/bin/activate
pip install --upgrade -r requirements.txt
sudo systemctl restart mushroom-lights  # If using service
```