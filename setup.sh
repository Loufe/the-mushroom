#!/bin/bash
#
# Mushroom LED Project - Complete Setup Script
# For Raspberry Pi 5 with DietPi OS
#
# This script handles:
# - System verification and requirements
# - SPI configuration (both channels)
# - Python environment setup
# - Dependency installation
# - Hardware verification
# - Optional autostart service setup

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_NAME="mushroom-env"
VENV_PATH="${PROJECT_DIR}/${VENV_NAME}"
MIN_PYTHON_VERSION="3.9"
REQUIRED_SPI_DEVICES=("/dev/spidev0.0" "/dev/spidev1.0")

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}     🍄 Mushroom LED Project Setup Script      ${NC}"
echo -e "${GREEN}================================================${NC}\n"

# Check if running with appropriate permissions
if [ "$EUID" -eq 0 ]; then 
   echo -e "${GREEN}Running as root${NC}"
else
   echo -e "${YELLOW}Not running as root. Some operations will require sudo password.${NC}"
fi

# Verify we're in the correct directory
if [ ! -f "${PROJECT_DIR}/main.py" ] || [ ! -d "${PROJECT_DIR}/src" ]; then
    echo -e "${RED}Error: This script must be run from the mushroom project directory${NC}"
    echo -e "${RED}Missing critical files. Please ensure you've cloned the repository correctly.${NC}"
    exit 1
fi

# Function to show current status
show_status() {
    echo -e "\n${BLUE}=== Current Setup Status ===${NC}"
    
    # Check virtual environment
    if [ -d "$VENV_PATH" ]; then
        echo -e "${GREEN}✓${NC} Virtual environment exists"
    else
        echo -e "${YELLOW}○${NC} Virtual environment not created"
    fi
    
    # Check SPI devices
    if [ -e "/dev/spidev0.0" ] && [ -e "/dev/spidev1.0" ]; then
        echo -e "${GREEN}✓${NC} Both SPI channels available"
    elif [ -e "/dev/spidev0.0" ] || [ -e "/dev/spidev1.0" ]; then
        echo -e "${YELLOW}○${NC} Partial SPI configuration"
    else
        echo -e "${RED}✗${NC} SPI not configured"
    fi
    
    # Check GPIO drive strength for both SPI channels
    CONFIG_FILE=""
    if [ -f /boot/config.txt ]; then
        CONFIG_FILE="/boot/config.txt"
    elif [ -f /boot/firmware/config.txt ]; then
        CONFIG_FILE="/boot/firmware/config.txt"
    fi
    
    if [ -n "$CONFIG_FILE" ]; then
        GPIO10_OK=false
        GPIO20_OK=false
        
        if grep -q "^gpio=10=.*dh" "$CONFIG_FILE" 2>/dev/null; then
            GPIO10_OK=true
        fi
        if grep -q "^gpio=20=.*dh" "$CONFIG_FILE" 2>/dev/null; then
            GPIO20_OK=true
        fi
        
        if [ "$GPIO10_OK" = true ] && [ "$GPIO20_OK" = true ]; then
            echo -e "${GREEN}✓${NC} GPIO 10 & 20 high drive strength configured"
        elif [ "$GPIO10_OK" = true ] || [ "$GPIO20_OK" = true ]; then
            echo -e "${YELLOW}○${NC} Partial GPIO drive strength configured"
        else
            echo -e "${YELLOW}○${NC} GPIO drive strength not configured"
        fi
    fi
    
    # Check service
    if systemctl is-active --quiet mushroom-lights 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Service is running"
    elif systemctl is-enabled --quiet mushroom-lights 2>/dev/null; then
        echo -e "${YELLOW}○${NC} Service enabled but not running"
    else
        echo -e "${YELLOW}○${NC} Autostart not configured"
    fi
    
    # Check if we can import pi5neo (if venv exists)
    if [ -d "$VENV_PATH" ]; then
        if "$VENV_PATH/bin/python" -c "import pi5neo" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} LED control library installed"
        else
            echo -e "${RED}✗${NC} LED control library not installed"
        fi
    fi
    
    echo -e "${BLUE}=============================${NC}\n"
}

# Show initial status
show_status

# Function to check if running on Raspberry Pi 5
check_raspberry_pi() {
    echo -e "${BLUE}Checking system...${NC}"
    
    if [ ! -f /proc/cpuinfo ]; then
        echo -e "${RED}Error: Cannot detect system type${NC}"
        exit 1
    fi
    
    # Check for Raspberry Pi - try multiple methods
    IS_PI=false
    IS_PI5=false
    
    # Method 1: Check /proc/device-tree/model (most reliable)
    if [ -f /proc/device-tree/model ]; then
        MODEL=$(cat /proc/device-tree/model | tr -d '\0')
        if [[ "$MODEL" == *"Raspberry Pi"* ]]; then
            IS_PI=true
            echo -e "${GREEN}✓ Detected: $MODEL${NC}"
            if [[ "$MODEL" == *"Raspberry Pi 5"* ]]; then
                IS_PI5=true
            fi
        fi
    fi
    
    # Method 2: Fallback to /proc/cpuinfo
    if [ "$IS_PI" = false ] && grep -q "Raspberry Pi" /proc/cpuinfo; then
        IS_PI=true
        # Check for BCM2712 (Pi 5 processor)
        if grep -q "BCM2712" /proc/cpuinfo; then
            IS_PI5=true
        fi
    fi
    
    # Report findings
    if [ "$IS_PI" = false ]; then
        echo -e "${YELLOW}Warning: This doesn't appear to be a Raspberry Pi${NC}"
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    elif [ "$IS_PI5" = false ]; then
        echo -e "${YELLOW}⚠ Not a Raspberry Pi 5 - performance may vary${NC}"
    fi
    
    # Check for DietPi
    if [ -f /boot/dietpi/.version ]; then
        DIETPI_VERSION=$(sed -n 1p /boot/dietpi/.version)
        echo -e "${GREEN}✓ DietPi ${DIETPI_VERSION} detected${NC}"
    else
        echo -e "${YELLOW}⚠ DietPi not detected - using generic Linux${NC}"
    fi
}

# Function to check Python version
check_python() {
    echo -e "\n${BLUE}Checking Python...${NC}"
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python3 not found${NC}"
        echo "Install with: sudo apt-get install python3 python3-pip python3-venv"
        exit 1
    fi
    
    # Get Python version
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 9 ]; then
        echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"
    else
        echo -e "${RED}Error: Python ${MIN_PYTHON_VERSION}+ required (found ${PYTHON_VERSION})${NC}"
        exit 1
    fi
}

# Function to check and enable SPI
check_spi() {
    echo -e "\n${BLUE}Checking SPI configuration...${NC}"
    
    local spi_issues=0
    
    # Check if SPI kernel module is loaded
    if ! lsmod | grep -q spi_bcm2835; then
        echo -e "${YELLOW}⚠ SPI kernel module not loaded${NC}"
        spi_issues=1
    fi
    
    # Check for SPI devices
    for device in "${REQUIRED_SPI_DEVICES[@]}"; do
        if [ ! -e "$device" ]; then
            echo -e "${YELLOW}⚠ Missing: $device${NC}"
            spi_issues=1
        else
            echo -e "${GREEN}✓ Found: $device${NC}"
        fi
    done
    
    # Only check config if devices are missing
    if [ $spi_issues -eq 1 ]; then
        # Check boot config for SPI1 overlay
        CONFIG_CHECKED=false
        if [ -f /boot/config.txt ]; then
            CONFIG_CHECKED=true
            if ! grep -q "dtoverlay=spi1" /boot/config.txt; then
                echo -e "${YELLOW}⚠ SPI1 overlay not found in /boot/config.txt${NC}"
            fi
        elif [ -f /boot/firmware/config.txt ]; then
            CONFIG_CHECKED=true
            if ! grep -q "dtoverlay=spi1" /boot/firmware/config.txt; then
                echo -e "${YELLOW}⚠ SPI1 overlay not found in /boot/firmware/config.txt${NC}"
            fi
        fi
        
        if [ "$CONFIG_CHECKED" = false ]; then
            echo -e "${YELLOW}⚠ Could not locate boot config file${NC}"
        fi
    fi
    
    if [ $spi_issues -eq 1 ]; then
        echo -e "\n${YELLOW}SPI configuration needs attention!${NC}"
        echo "To fix:"
        echo "1. Enable SPI in dietpi-config:"
        echo "   sudo dietpi-config"
        echo "   Navigate to: Advanced Options > SPI > Enable"
        echo ""
        echo "2. Add SPI1 overlay to boot config:"
        echo "   sudo nano /boot/config.txt"
        echo "   Add line: dtoverlay=spi1-1cs"
        echo ""
        echo "3. Reboot: sudo reboot"
        echo ""
        read -p "Continue without proper SPI setup? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo -e "${GREEN}✓ SPI properly configured${NC}"
    fi
}

# Function to configure GPIO drive strength for better signal integrity
config_gpio_drive() {
    echo -e "\n${BLUE}Configuring GPIO drive strength for SPI signals...${NC}"
    
    # Determine config file location
    CONFIG_FILE=""
    if [ -f /boot/config.txt ]; then
        CONFIG_FILE="/boot/config.txt"
    elif [ -f /boot/firmware/config.txt ]; then
        CONFIG_FILE="/boot/firmware/config.txt"
    else
        echo -e "${YELLOW}⚠ Could not locate boot config file${NC}"
        echo "GPIO drive strength configuration skipped"
        return
    fi
    
    # Check both GPIO pins used for SPI
    # GPIO 10 (Pin 19) - SPI0 MOSI for cap (450 LEDs)
    # GPIO 20 (Pin 38) - SPI1 MOSI for stem (250 LEDs)
    
    local NEEDS_UPDATE=false
    local GPIO10_OK=false
    local GPIO20_OK=false
    
    # Check GPIO 10
    if grep -q "^gpio=10=.*dh" "$CONFIG_FILE"; then
        echo -e "${GREEN}✓ GPIO 10 (SPI0/Cap) high drive strength already enabled${NC}"
        GPIO10_OK=true
    elif grep -q "^gpio=10=" "$CONFIG_FILE"; then
        echo -e "${YELLOW}⚠ GPIO 10 configured but not set to high drive${NC}"
        NEEDS_UPDATE=true
    else
        echo -e "${YELLOW}⚠ GPIO 10 (SPI0/Cap) drive strength not configured${NC}"
        NEEDS_UPDATE=true
    fi
    
    # Check GPIO 20
    if grep -q "^gpio=20=.*dh" "$CONFIG_FILE"; then
        echo -e "${GREEN}✓ GPIO 20 (SPI1/Stem) high drive strength already enabled${NC}"
        GPIO20_OK=true
    elif grep -q "^gpio=20=" "$CONFIG_FILE"; then
        echo -e "${YELLOW}⚠ GPIO 20 configured but not set to high drive${NC}"
        NEEDS_UPDATE=true
    else
        echo -e "${YELLOW}⚠ GPIO 20 (SPI1/Stem) drive strength not configured${NC}"
        NEEDS_UPDATE=true
    fi
    
    # If both are OK, we're done
    if [ "$GPIO10_OK" = true ] && [ "$GPIO20_OK" = true ]; then
        echo -e "${GREEN}✓ Both SPI GPIO pins configured correctly${NC}"
        return
    fi
    
    # Otherwise offer to configure
    if [ "$NEEDS_UPDATE" = true ]; then
        echo -e "\n${YELLOW}High drive strength improves signal integrity through the 74AHCT125 level shifter${NC}"
        echo "This helps prevent flickering and data corruption at high speeds"
        read -p "Configure GPIO pins for high drive strength (16mA)? (y/n): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Backup config file
            sudo cp "$CONFIG_FILE" "${CONFIG_FILE}.bak"
            
            # Remove any existing GPIO 10/20 configs
            sudo sed -i '/^gpio=10=/d' "$CONFIG_FILE"
            sudo sed -i '/^gpio=20=/d' "$CONFIG_FILE"
            
            # Add GPIO configuration
            echo "" | sudo tee -a "$CONFIG_FILE" > /dev/null
            echo "# Mushroom LED - High drive strength for SPI signals through 74AHCT125" | sudo tee -a "$CONFIG_FILE" > /dev/null
            echo "gpio=10=op,dh  # SPI0 MOSI (Pin 19) for cap exterior" | sudo tee -a "$CONFIG_FILE" > /dev/null
            echo "gpio=20=op,dh  # SPI1 MOSI (Pin 38) for stem interior" | sudo tee -a "$CONFIG_FILE" > /dev/null
            
            echo -e "${GREEN}✓ GPIO 10 and 20 configured for high drive strength${NC}"
            echo -e "${YELLOW}⚠ Reboot required for changes to take effect${NC}"
        else
            echo -e "${YELLOW}Skipping GPIO configuration${NC}"
            echo "Note: You may experience flickering without increased drive strength"
        fi
    fi
}

# Function to check system dependencies
check_system_deps() {
    echo -e "\n${BLUE}Checking system dependencies...${NC}"
    
    local missing_deps=()
    
    # Essential packages for building Python modules and GPIO access
    local required_packages=("python3-venv" "build-essential" "python3-dev" "git" "libportaudio2")
    
    for pkg in "${required_packages[@]}"; do
        if ! dpkg -l | grep -q "^ii  $pkg"; then
            missing_deps+=("$pkg")
        fi
    done
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        echo -e "${YELLOW}Missing packages: ${missing_deps[*]}${NC}"
        read -p "Install missing packages? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${GREEN}Installing packages...${NC}"
            sudo apt-get update
            sudo apt-get install -y "${missing_deps[@]}"
        else
            echo -e "${YELLOW}Warning: Some features may not work without these packages${NC}"
        fi
    else
        echo -e "${GREEN}✓ All system dependencies installed${NC}"
    fi
}

# Function to setup virtual environment
setup_venv() {
    echo -e "\n${BLUE}Setting up Python virtual environment...${NC}"
    
    if [ -d "$VENV_PATH" ]; then
        echo -e "${YELLOW}Virtual environment already exists at $VENV_PATH${NC}"
        read -p "Delete and recreate? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$VENV_PATH"
        else
            echo -e "${GREEN}Using existing virtual environment${NC}"
            return 0
        fi
    fi
    
    echo -e "${GREEN}Creating virtual environment...${NC}"
    python3 -m venv "$VENV_PATH"
    
    if [ ! -f "$VENV_PATH/bin/activate" ]; then
        echo -e "${RED}Error: Failed to create virtual environment${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Virtual environment created${NC}"
}

# Function to install Python dependencies
install_dependencies() {
    echo -e "\n${BLUE}Installing Python dependencies...${NC}"
    
    # Activate virtual environment
    source "$VENV_PATH/bin/activate"
    
    # Upgrade pip first
    echo -e "${GREEN}Upgrading pip...${NC}"
    pip install --upgrade pip
    
    # Install requirements
    if [ -f "${PROJECT_DIR}/requirements.txt" ]; then
        echo -e "${GREEN}Installing from requirements.txt...${NC}"
        pip install -r "${PROJECT_DIR}/requirements.txt"
        
        # Verify critical packages
        echo -e "\n${BLUE}Verifying installations...${NC}"
        
        # Check pi5neo (critical for LED control)
        if python -c "import pi5neo" 2>/dev/null; then
            echo -e "${GREEN}✓ pi5neo installed${NC}"
        else
            echo -e "${RED}✗ pi5neo installation failed${NC}"
            echo -e "${YELLOW}This is critical for LED control. Possible fixes:${NC}"
            echo "  1. Check build-essential is installed"
            echo "  2. Verify you're on a Raspberry Pi"
            echo "  3. Try reinstalling: pip install -r requirements.txt"
        fi
        
        # Check numpy
        if python -c "import numpy" 2>/dev/null; then
            echo -e "${GREEN}✓ numpy installed${NC}"
        else
            echo -e "${RED}✗ numpy installation failed${NC}"
        fi
        
        # Check pyyaml
        if python -c "import yaml" 2>/dev/null; then
            echo -e "${GREEN}✓ pyyaml installed${NC}"
        else
            echo -e "${RED}✗ pyyaml installation failed${NC}"
        fi
    else
        echo -e "${RED}Error: requirements.txt not found${NC}"
        exit 1
    fi
    
    # Deactivate for now
    deactivate
}

# Function to test hardware
test_hardware() {
    echo -e "\n${BLUE}Hardware test${NC}"
    echo -e "${YELLOW}This will briefly flash the LEDs to verify connections${NC}"
    echo -e "${YELLOW}Make sure LEDs are powered on!${NC}"
    read -p "Run hardware test? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f "${PROJECT_DIR}/tests/test_spi.py" ]; then
            echo -e "${GREEN}Running LED test...${NC}"
            sudo "$VENV_PATH/bin/python" "${PROJECT_DIR}/tests/test_spi.py"
            
            echo ""
            read -p "Did the LEDs flash correctly? (y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo -e "${GREEN}✓ Hardware test successful${NC}"
            else
                echo -e "${YELLOW}Hardware troubleshooting tips:${NC}"
                echo "1. Check power supply is on (12V, 20A minimum)"
                echo "2. Verify SPI connections:"
                echo "   - Stem (250 LEDs): SPI1 on GPIO 20 (Pin 38)"
                echo "   - Cap (450 LEDs): SPI0 on GPIO 10 (Pin 19)"
                echo "3. Check ground connection between Pi and LED power"
                echo "4. Try with fewer LEDs: --count 1"
            fi
        else
            echo -e "${YELLOW}Test script not found, skipping hardware test${NC}"
        fi
    fi
}

# Function to setup autostart
setup_autostart() {
    echo -e "\n${BLUE}Autostart Configuration${NC}"
    
    # Check if service already exists
    if systemctl list-unit-files | grep -q "^mushroom-lights.service"; then
        echo -e "${GREEN}✓ Autostart service already configured${NC}"
        
        if systemctl is-active --quiet mushroom-lights; then
            echo -e "${GREEN}✓ Service is currently running${NC}"
        elif systemctl is-enabled --quiet mushroom-lights; then
            echo -e "${YELLOW}○ Service is enabled but not running${NC}"
        else
            echo -e "${YELLOW}○ Service exists but is disabled${NC}"
        fi
        
        read -p "Reconfigure autostart service? (y/n): " -n 1 -r
        echo
        
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Keeping existing autostart configuration${NC}"
            return 0
        fi
    else
        read -p "Setup automatic startup on boot? (y/n): " -n 1 -r
        echo
        
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Skipping autostart setup${NC}"
            echo "You can set it up later with: sudo bash scripts/setup_autostart.sh"
            return 0
        fi
    fi
    
    if [ -f "${PROJECT_DIR}/scripts/setup_autostart.sh" ]; then
        echo -e "${GREEN}Running autostart setup script...${NC}"
        sudo bash "${PROJECT_DIR}/scripts/setup_autostart.sh"
    else
        echo -e "${YELLOW}Autostart script not found${NC}"
    fi
}

# Main setup flow
main() {
    echo "Starting setup from: $PROJECT_DIR"
    echo ""
    
    # Run all checks
    check_raspberry_pi
    check_python
    check_spi
    config_gpio_drive
    check_system_deps
    
    # Setup environment
    setup_venv
    install_dependencies
    
    # Test and configure
    test_hardware
    setup_autostart
    
    # Final summary
    echo -e "\n${GREEN}================================================${NC}"
    echo -e "${GREEN}           Setup Complete! 🍄                  ${NC}"
    echo -e "${GREEN}================================================${NC}\n"
    
    echo "Quick start commands:"
    echo -e "  ${YELLOW}Test LEDs:${NC}  sudo ${VENV_PATH}/bin/python tests/test_spi.py"
    echo -e "  ${YELLOW}Run now:${NC}    ./run.sh"
    echo -e "  ${YELLOW}Run with pattern:${NC} ./run.sh --pattern rainbow"
    echo -e "  ${YELLOW}Change settings:${NC} nano config/startup.yaml"
    echo ""
    
    if systemctl is-active --quiet mushroom-lights; then
        echo -e "${GREEN}✓ Service is running!${NC}"
        echo -e "  ${YELLOW}View logs:${NC} sudo journalctl -u mushroom-lights -f"
        echo -e "  ${YELLOW}Restart:${NC}   sudo systemctl restart mushroom-lights"
    else
        echo "To start the light show:"
        echo "  ./run.sh"
    fi
    
    echo ""
    echo -e "${GREEN}Enjoy your mushroom! 🍄✨${NC}"
}

# Run main function
main