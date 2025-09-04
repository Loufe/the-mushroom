#!/bin/bash
#
# Quick Pattern Changer for Mushroom LEDs
# Changes the startup pattern and optionally restarts the service
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CONFIG_FILE="/home/dietpi/the-mushroom/config/startup.yaml"
SERVICE_NAME="mushroom-lights"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Mushroom LED Pattern Changer${NC}"
echo -e "${BLUE}================================${NC}\n"

# Check if config exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}Config file not found at: $CONFIG_FILE${NC}"
    echo "Run setup_autostart.sh first to create the configuration."
    exit 1
fi

# Get current settings
CURRENT_PATTERN=$(grep "^pattern:" "$CONFIG_FILE" | awk '{print $2}')
CURRENT_BRIGHTNESS=$(grep "^brightness:" "$CONFIG_FILE" | awk '{print $2}')

echo -e "Current settings:"
echo -e "  Pattern: ${GREEN}${CURRENT_PATTERN}${NC}"
echo -e "  Brightness: ${GREEN}${CURRENT_BRIGHTNESS}${NC}\n"

# Pattern selection
echo "Available patterns:"
echo "  1) test         - RGB color cycle"
echo "  2) rainbow_wave - Traveling rainbow"
echo "  3) rainbow_cycle - Synchronized rainbow"
echo ""
read -p "Select pattern (1-3) or press Enter to keep current: " PATTERN_CHOICE

case $PATTERN_CHOICE in
    1) NEW_PATTERN="test" ;;
    2) NEW_PATTERN="rainbow_wave" ;;
    3) NEW_PATTERN="rainbow_cycle" ;;
    "") NEW_PATTERN=$CURRENT_PATTERN ;;
    *) echo "Invalid choice. Keeping current pattern."; NEW_PATTERN=$CURRENT_PATTERN ;;
esac

# Brightness selection
read -p "Enter brightness (0-255) or press Enter to keep current [$CURRENT_BRIGHTNESS]: " NEW_BRIGHTNESS
if [ -z "$NEW_BRIGHTNESS" ]; then
    NEW_BRIGHTNESS=$CURRENT_BRIGHTNESS
elif ! [[ "$NEW_BRIGHTNESS" =~ ^[0-9]+$ ]] || [ "$NEW_BRIGHTNESS" -lt 0 ] || [ "$NEW_BRIGHTNESS" -gt 255 ]; then
    echo -e "${YELLOW}Invalid brightness. Keeping current value.${NC}"
    NEW_BRIGHTNESS=$CURRENT_BRIGHTNESS
fi

# Update config file
echo -e "\n${GREEN}Updating configuration...${NC}"
sed -i "s/^pattern:.*/pattern: $NEW_PATTERN/" "$CONFIG_FILE"
sed -i "s/^brightness:.*/brightness: $NEW_BRIGHTNESS/" "$CONFIG_FILE"

echo -e "${GREEN}✓ Configuration updated${NC}"
echo -e "  Pattern: ${NEW_PATTERN}"
echo -e "  Brightness: ${NEW_BRIGHTNESS}"

# Check if service is running
if systemctl is-active --quiet ${SERVICE_NAME}; then
    echo ""
    read -p "Service is running. Restart now to apply changes? (y/n): " RESTART
    if [[ $RESTART =~ ^[Yy]$ ]]; then
        echo -e "\n${GREEN}Restarting service...${NC}"
        sudo systemctl restart ${SERVICE_NAME}
        sleep 2
        if systemctl is-active --quiet ${SERVICE_NAME}; then
            echo -e "${GREEN}✓ Service restarted successfully!${NC}"
        else
            echo -e "${YELLOW}⚠ Service failed to restart. Check logs:${NC}"
            echo "  sudo journalctl -u ${SERVICE_NAME} -n 20"
        fi
    else
        echo -e "\n${YELLOW}Changes saved. Restart the service to apply:${NC}"
        echo "  sudo systemctl restart ${SERVICE_NAME}"
    fi
else
    echo -e "\n${YELLOW}Service not running. Start it with:${NC}"
    echo "  sudo systemctl start ${SERVICE_NAME}"
fi

echo ""