# Manual Setup Instructions

## Step 1: System Preparation
After first boot and SSH connection to DietPi:

```bash
# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install build dependencies for pi5neo
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    build-essential \
    swig \
    libasound2-dev \
    libportaudio2 \
    portaudio19-dev

# Create project directory
mkdir -p /home/dietpi/the-mushroom
cd /home/dietpi/the-mushroom
```

## Step 2: Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv mushroom-env

# Activate it
source mushroom-env/bin/activate

# Upgrade pip
pip install --upgrade pip wheel setuptools
```

## Step 3: Install Python Libraries

```bash
# Install LED control library
pip install pi5neo

# This library is specifically designed for Raspberry Pi 5
# It uses SPI instead of PWM/DMA for better compatibility

# Install audio and utility libraries
pip install sounddevice==0.4.6
pip install numpy==1.24.3
pip install scipy==1.10.1
pip install pyyaml==6.0.1
pip install psutil==5.9.5

# Test imports
python3 -c "import pi5neo; print('✓ LED library OK')"
python3 -c "import sounddevice; print('✓ Audio library OK')"
python3 -c "import numpy; print('✓ NumPy OK')"
```

## Step 4: Configure Audio Device

```bash
# List audio devices
python3 -c "import sounddevice; sounddevice.query_devices()"

# Note the device number for AU-MMSA adapter
# It should show up as a USB audio device

# Test audio capture (adjust device number as needed)
python3 -c "
import sounddevice as sd
import numpy as np
duration = 1  # seconds
fs = 44100
print('Recording for 1 second...')
recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, device=2)
sd.wait()
print(f'Recorded {len(recording)} samples')
print(f'Max amplitude: {np.max(np.abs(recording)):.4f}')
"
```

## Step 5: Test LED Control (Requires sudo)

```bash
# Create simple test script
cat > test_leds.py << 'EOF'
#!/usr/bin/env python3
from pi5neo import Pi5Neo
import time

# LED strip configuration
LED_COUNT = 10        # Test with just 10 LEDs first
SPI_DEVICE = '/dev/spidev0.0'  # SPI0 for GPIO 10
FREQUENCY = 800      # 800kHz for WS2811

# Create Pi5Neo strip
strip = Pi5Neo(SPI_DEVICE, LED_COUNT, FREQUENCY)

print("Testing LEDs - Red, Green, Blue cycle")
colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]

for r, g, b in colors:
    for i in range(LED_COUNT):
        strip.set_pixel_rgb(i, r, g, b)
    strip.update()
    time.sleep(1)

# Clear
strip.fill_rgb(0, 0, 0)
strip.update()
print("Test complete!")
EOF

# Run test (requires sudo for GPIO access)
sudo /home/dietpi/the-mushroom/mushroom-env/bin/python test_leds.py
```

## Step 6: Permissions Setup (Optional - Avoid sudo)

```bash
# Add user to gpio group
sudo usermod -a -G gpio dietpi

# Create udev rule for LED access
sudo bash -c 'cat > /etc/udev/rules.d/99-led.rules << EOF
SUBSYSTEM=="spidev", GROUP="gpio", MODE="0660"
SUBSYSTEM=="gpio", GROUP="gpio", MODE="0660"
EOF'

# Reload rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Logout and login for group changes to take effect
exit
# Then SSH back in
```

## Troubleshooting

### GPIO Access Denied
- Must run as sudo initially
- Check gpio group membership: `groups`

### Audio Device Not Found
- Verify USB adapter connected: `lsusb`
- Check ALSA devices: `arecord -l`

### LED Test Fails
- Verify wiring (GPIO 10 = Pin 19 for SPI0, GPIO 20 = Pin 38 for SPI1)
- Check ground connection between Pi and LED power
- Verify SPI device exists: ls /dev/spidev*
- If signal issues persist, consider adding a level shifter

### Import Errors
- Ensure virtual environment activated
- Check library versions match requirements

## Next Steps
Once all tests pass:
1. Wire up all 700 LEDs
2. Create LED mapping configuration
3. Build pattern engine
4. Integrate audio processing