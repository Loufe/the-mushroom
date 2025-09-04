#!/bin/bash
#
# Remove Mushroom LED Autostart
# Stops and removes the systemd service
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}================================${NC}"
echo -e "${YELLOW}Remove Mushroom LED Autostart${NC}"
echo -e "${YELLOW}================================${NC}\n"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
   echo -e "${RED}Please run with sudo: sudo bash remove_autostart.sh${NC}"
   exit 1
fi

SERVICE_NAME="mushroom-lights"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

# Check if service exists
if [ ! -f "$SERVICE_FILE" ]; then
    echo -e "${YELLOW}Service not found. Nothing to remove.${NC}"
    exit 0
fi

echo -e "${GREEN}Stopping service...${NC}"
systemctl stop ${SERVICE_NAME}.service 2>/dev/null || true

echo -e "${GREEN}Disabling autostart...${NC}"
systemctl disable ${SERVICE_NAME}.service 2>/dev/null || true

echo -e "${GREEN}Removing service file...${NC}"
rm -f "$SERVICE_FILE"

echo -e "${GREEN}Reloading systemd...${NC}"
systemctl daemon-reload

echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}Autostart Removed Successfully!${NC}"
echo -e "${GREEN}================================${NC}\n"

echo "The light show will no longer start on boot."
echo "You can still run it manually with:"
echo "  cd ~/the-mushroom"
echo "  sudo mushroom-env/bin/python main.py"