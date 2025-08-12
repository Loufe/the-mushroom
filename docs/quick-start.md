# Quick Start Guide

## Step 1: Flash DietPi
In Raspberry Pi Imager:
1. Choose "DietPi" as OS (under "Other specific-purpose OS")
2. Click gear icon for settings:
   - **Enable SSH:** Yes, use password
   - **Username:** dietpi
   - **Password:** [choose secure password]
   - **Hostname:** mushroom-pi
   - **WiFi:** Configure if using (note: production won't have network)
3. Flash the SD card

## Step 2: First Boot
1. Insert SD card and power on Pi 5 with active cooling
2. Find IP address (check router or use `arp -a` from WSL)
3. SSH from WSL: `ssh dietpi@[IP-ADDRESS]`
4. Run automated setup (we'll create this next)

## Step 3: VS Code Setup (from WSL)
1. Install "Remote - SSH" extension
2. Add SSH host: `dietpi@[IP-ADDRESS]`
3. Connect and open `/home/dietpi/the-mushroom`
4. Terminal will run directly on Pi

## GPIO → LED Strip Wiring
Connect 74HCT125 level shifter:
- Pi GPIO 10 (Pin 19) → 74HCT125 Input 1A → Output 1Y → Strip 1 Data
- Pi GPIO 20 (Pin 38) → 74HCT125 Input 2A → Output 2Y → Strip 2 Data  
- Pi GPIO 21 (Pin 40) → 74HCT125 Input 3A → Output 3Y → Strip 3 Data
- Pi GPIO 12 (Pin 32) → 74HCT125 Input 4A → Output 4Y → Strip 4 Data
- Pi GND → 74HCT125 GND & OE pins (1,7,10)
- Pi 3.3V → 74HCT125 VCC (Pin 14)
- 5V PSU → 74HCT125 VCC & LED strips

## Ready to Code!
Once connected via SSH, we'll run the setup script to install everything.