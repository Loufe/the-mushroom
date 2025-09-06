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

# Get available patterns dynamically
echo -e "${BLUE}Discovering available patterns...${NC}"
AVAILABLE_PATTERNS=$(cd "$PROJECT_DIR" && "${VENV_PATH}/bin/python" main.py --list-patterns 2>/dev/null)
if [ -z "$AVAILABLE_PATTERNS" ]; then
    echo -e "${YELLOW}Warning: Could not discover patterns, using defaults${NC}"
    AVAILABLE_PATTERNS="rainbow\ntest"
fi

# Convert to array
readarray -t PATTERN_ARRAY <<< "$AVAILABLE_PATTERNS"
DEFAULT_PATTERN="${PATTERN_ARRAY[0]}"  # Use first available pattern as default

echo -e "${GREEN}Found patterns: ${PATTERN_ARRAY[*]}${NC}\n"

# Check if startup config exists
STARTUP_CONFIG="${PROJECT_DIR}/config/startup.yaml"
if [ -f "$STARTUP_CONFIG" ]; then
    echo -e "${GREEN}Using settings from config/startup.yaml${NC}"
    echo -e "${YELLOW}To change patterns/brightness, edit: ${STARTUP_CONFIG}${NC}\n"
else
    echo -e "${YELLOW}No startup.yaml found. Creating configuration...${NC}\n"
    
    # Let user choose patterns
    echo "Select default patterns for your mushroom:"
    echo "Available patterns: ${PATTERN_ARRAY[*]}"
    echo ""
    
    # Cap pattern selection
    read -p "Pattern for cap (450 LEDs) [${DEFAULT_PATTERN}]: " CAP_PATTERN
    CAP_PATTERN=${CAP_PATTERN:-$DEFAULT_PATTERN}
    
    # Stem pattern selection  
    read -p "Pattern for stem (250 LEDs) [${DEFAULT_PATTERN}]: " STEM_PATTERN
    STEM_PATTERN=${STEM_PATTERN:-$DEFAULT_PATTERN}
    
    # Brightness selection
    read -p "Global brightness (0-255) [${DEFAULT_BRIGHTNESS}]: " BRIGHTNESS
    BRIGHTNESS=${BRIGHTNESS:-$DEFAULT_BRIGHTNESS}
    
    # Create startup config
    mkdir -p "${PROJECT_DIR}/config"
    cat > "$STARTUP_CONFIG" << EOCONFIG
# Startup Configuration
# This file controls what patterns and settings are used when the light show starts on boot

# Patterns for cap and stem (can be different or same)
# Available patterns: ${PATTERN_ARRAY[*]}
cap_pattern: ${CAP_PATTERN}     # 450 LEDs on cap exterior
stem_pattern: ${STEM_PATTERN}    # 250 LEDs on stem interior

# Global brightness (0-255)
brightness: ${BRIGHTNESS}

# Optional: Set different brightness for each zone
# If not specified, uses the global brightness value above
# cap_brightness: 128
# stem_brightness: 96
EOCONFIG
    echo -e "\n${GREEN}Created startup config at: ${STARTUP_CONFIG}${NC}"
fi

echo -e "\n${GREEN}Creating systemd service...${NC}"

# Check if service file already exists
if [ -f "$SERVICE_FILE" ]; then
    echo -e "${YELLOW}Service file already exists at: $SERVICE_FILE${NC}"
    
    # Show current service status
    if systemctl is-active --quiet ${SERVICE_NAME}; then
        echo -e "${GREEN}✓ Service is currently running${NC}"
    elif systemctl is-enabled --quiet ${SERVICE_NAME}; then
        echo -e "${YELLOW}○ Service is enabled but not running${NC}"
    else
        echo -e "${YELLOW}○ Service exists but is disabled${NC}"
    fi
    
    read -p "Overwrite existing service file? (y/n): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Keeping existing service file${NC}"
        echo -e "${YELLOW}Skipping service creation - proceeding with reload/restart options${NC}"
        
        # Still offer to reload and restart if they didn't overwrite
        echo -e "\n${GREEN}Reloading systemd...${NC}"
        systemctl daemon-reload
        
        # Ask if they want to restart the service
        echo ""
        read -p "Do you want to restart the service with new config? (y/n): " RESTART_NOW
        
        if [[ $RESTART_NOW =~ ^[Yy]$ ]]; then
            echo -e "\n${GREEN}Restarting ${SERVICE_NAME} service...${NC}"
            systemctl restart ${SERVICE_NAME}.service
            sleep 2
            
            if systemctl is-active --quiet ${SERVICE_NAME}.service; then
                echo -e "${GREEN}✓ Service restarted successfully!${NC}"
            else
                echo -e "${RED}✗ Service failed to restart. Check logs with:${NC}"
                echo -e "  sudo journalctl -u ${SERVICE_NAME} -n 50"
            fi
        fi
        
        # Jump to the end without creating new service
        echo -e "\n${GREEN}================================${NC}"
        echo -e "${GREEN}Update Complete!${NC}"
        echo -e "${GREEN}================================${NC}\n"
        
        echo "Useful commands:"
        echo -e "  ${YELLOW}Check status:${NC}  sudo systemctl status ${SERVICE_NAME}"
        echo -e "  ${YELLOW}View logs:${NC}     sudo journalctl -u ${SERVICE_NAME} -f"
        echo -e "  ${YELLOW}Restart:${NC}       sudo systemctl restart ${SERVICE_NAME}"
        echo ""
        echo "Configuration file: ${STARTUP_CONFIG}"
        echo ""
        echo "To change pattern or brightness:"
        echo "  1. Edit: nano ${STARTUP_CONFIG}"
        echo "  2. Restart: sudo systemctl restart ${SERVICE_NAME}"
        exit 0
    fi
fi

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