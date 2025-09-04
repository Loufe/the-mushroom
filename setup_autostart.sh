#!/bin/bash
#
# Mushroom LED Autostart Setup Script
# Sets up systemd service to run light show on boot
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Mushroom LED Autostart Setup${NC}"
echo -e "${GREEN}================================${NC}\n"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
   echo -e "${RED}Please run with sudo: sudo bash setup_autostart.sh${NC}"
   exit 1
fi

# Variables
SERVICE_NAME="mushroom-lights"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
PROJECT_DIR="/home/dietpi/the-mushroom"
VENV_PATH="${PROJECT_DIR}/mushroom-env"
DEFAULT_PATTERN="rainbow_wave"
DEFAULT_BRIGHTNESS="64"

# Check if project exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}Error: Project directory not found at $PROJECT_DIR${NC}"
    echo "Please ensure the mushroom project is installed first."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}Error: Virtual environment not found at $VENV_PATH${NC}"
    echo "Please run the installation script first."
    exit 1
fi

# Check if startup config exists
STARTUP_CONFIG="${PROJECT_DIR}/config/startup.yaml"
if [ -f "$STARTUP_CONFIG" ]; then
    echo -e "${GREEN}Using settings from config/startup.yaml${NC}"
    echo -e "${YELLOW}To change pattern/brightness, edit: ${STARTUP_CONFIG}${NC}\n"
else
    echo -e "${YELLOW}No startup.yaml found. Creating with defaults...${NC}"
    # Create default startup config
    mkdir -p "${PROJECT_DIR}/config"
    cat > "$STARTUP_CONFIG" << EOCONFIG
# Startup Configuration
# This file controls what pattern and settings are used when the light show starts on boot

# Pattern to load at startup
# Available: test, rainbow_wave, rainbow_cycle
pattern: ${DEFAULT_PATTERN}

# Global brightness (0-255)
brightness: ${DEFAULT_BRIGHTNESS}

# Pattern-specific parameters (optional)
pattern_params:
  rainbow_wave:
    wave_length: 100
    speed: 50.0
  rainbow_cycle:
    cycle_time: 5.0
  test:
    cycle_time: 3.0
EOCONFIG
    echo -e "${GREEN}Created default startup config at: ${STARTUP_CONFIG}${NC}"
fi

echo -e "\n${GREEN}Creating systemd service...${NC}"

# Create systemd service file
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Mushroom LED Light Show
After=multi-user.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=root
WorkingDirectory=${PROJECT_DIR}
Environment="PATH=${VENV_PATH}/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PYTHONPATH=${PROJECT_DIR}"
ExecStart=${VENV_PATH}/bin/python ${PROJECT_DIR}/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}Service file created at: $SERVICE_FILE${NC}"

# Reload systemd
echo -e "\n${GREEN}Reloading systemd...${NC}"
systemctl daemon-reload

# Enable service
echo -e "${GREEN}Enabling service to start on boot...${NC}"
systemctl enable ${SERVICE_NAME}.service

# Ask if user wants to start now
echo ""
read -p "Do you want to start the light show now? (y/n): " START_NOW

if [[ $START_NOW =~ ^[Yy]$ ]]; then
    echo -e "\n${GREEN}Starting ${SERVICE_NAME} service...${NC}"
    systemctl start ${SERVICE_NAME}.service
    sleep 2
    
    # Check status
    if systemctl is-active --quiet ${SERVICE_NAME}.service; then
        echo -e "${GREEN}✓ Service started successfully!${NC}"
    else
        echo -e "${RED}✗ Service failed to start. Check logs with:${NC}"
        echo -e "  sudo journalctl -u ${SERVICE_NAME} -n 50"
    fi
fi

echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}================================${NC}\n"

echo "Useful commands:"
echo -e "  ${YELLOW}Check status:${NC}  sudo systemctl status ${SERVICE_NAME}"
echo -e "  ${YELLOW}View logs:${NC}     sudo journalctl -u ${SERVICE_NAME} -f"
echo -e "  ${YELLOW}Stop service:${NC}  sudo systemctl stop ${SERVICE_NAME}"
echo -e "  ${YELLOW}Start service:${NC} sudo systemctl start ${SERVICE_NAME}"
echo -e "  ${YELLOW}Restart:${NC}       sudo systemctl restart ${SERVICE_NAME}"
echo -e "  ${YELLOW}Disable boot:${NC}  sudo systemctl disable ${SERVICE_NAME}"
echo ""
echo -e "${GREEN}The light show will now start automatically on boot!${NC}"
echo ""

# Show current configuration
echo "Configuration file: ${STARTUP_CONFIG}"
echo ""
echo "To change pattern or brightness:"
echo "  1. Edit: nano ${STARTUP_CONFIG}"
echo "  2. Restart: sudo systemctl restart ${SERVICE_NAME}"
echo ""
echo "No need to reload systemd - changes take effect on restart!"