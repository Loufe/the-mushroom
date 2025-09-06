#!/bin/bash
# run.sh - LED controller management script
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PATH="${SCRIPT_DIR}/mushroom-env"
PYTHON="${VENV_PATH}/bin/python"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Find mushroom processes (specifically our venv python)
find_mushroom_processes() {
    pgrep -f "mushroom-env/bin/python.*main.py" 2>/dev/null || true
}

# Check if virtual environment exists
check_venv() {
    if [[ ! -x "$PYTHON" ]]; then
        echo -e "${RED}Error: Virtual environment not found${NC}"
        echo ""
        echo "To fix this, run:"
        echo "  ./setup.sh"
        echo ""
        echo "This will create the Python environment and install dependencies."
        exit 1
    fi
}

# Start LED controller
cmd_start() {
    check_venv
    
    # Check if already running
    PIDS=$(find_mushroom_processes)
    if [ -n "$PIDS" ]; then
        echo -e "${YELLOW}LED controller already running (PID: $PIDS)${NC}"
        echo "Use './run.sh stop' to stop it first"
        exit 1
    fi
    
    # Parse arguments using array for safety
    PATTERN=""
    BRIGHTNESS=""
    ARGS=()
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --brightness|-b)
                BRIGHTNESS="$2"
                ARGS+=("--brightness" "$2")
                shift 2
                ;;
            --pattern|-p)
                PATTERN="$2"
                ARGS+=("--pattern" "$2")
                shift 2
                ;;
            *)
                # First non-flag argument is pattern
                if [ -z "$PATTERN" ]; then
                    PATTERN="$1"
                    ARGS+=("--pattern" "$1")
                fi
                shift
                ;;
        esac
    done
    
    echo "Starting LED controller..."
    if [ -n "$PATTERN" ]; then
        echo "  Pattern: $PATTERN"
    fi
    if [ -n "$BRIGHTNESS" ]; then
        echo "  Brightness: $BRIGHTNESS"
    fi
    
    # Start in background with nohup
    if [[ $EUID -ne 0 ]]; then
        echo "LED control requires root access. Elevating to sudo..."
        exec sudo "$0" start "${ARGS[@]}"
    fi
    
    # Rotate log if it's too large (>10MB)
    if [ -f /tmp/mushroom-lights.log ] && [ $(stat -c%s /tmp/mushroom-lights.log 2>/dev/null || echo 0) -gt 10485760 ]; then
        mv /tmp/mushroom-lights.log /tmp/mushroom-lights.log.old
    fi
    
    nohup "$PYTHON" "$SCRIPT_DIR/main.py" "${ARGS[@]}" > /tmp/mushroom-lights.log 2>&1 &
    PID=$!
    
    # Wait a moment to check if it started successfully
    sleep 1
    if kill -0 $PID 2>/dev/null; then
        echo -e "${GREEN}✓ LED controller started (PID: $PID)${NC}"
        echo "Logs: tail -f /tmp/mushroom-lights.log"
    else
        echo -e "${RED}✗ Failed to start LED controller${NC}"
        echo "Check logs: cat /tmp/mushroom-lights.log"
        exit 1
    fi
}

# Stop all LED processes
cmd_stop() {
    echo "Stopping LED controller..."
    
    # Check systemd service
    if systemctl is-active --quiet mushroom-lights 2>/dev/null; then
        echo "Stopping systemd service..."
        sudo systemctl stop mushroom-lights
        echo -e "${GREEN}✓ Stopped systemd service${NC}"
    fi
    
    # Find our processes
    PIDS=$(find_mushroom_processes)
    if [ -z "$PIDS" ]; then
        echo "No LED processes running"
        return 0
    fi
    
    # Graceful shutdown with SIGTERM
    echo "Stopping process(es): $PIDS"
    kill -TERM $PIDS 2>/dev/null || true
    
    # Wait up to 3 seconds for graceful shutdown
    for i in 1 2 3; do
        sleep 1
        PIDS=$(find_mushroom_processes)
        if [ -z "$PIDS" ]; then
            echo -e "${GREEN}✓ All LED processes stopped${NC}"
            return 0
        fi
    done
    
    # Force kill if still running
    echo "Force stopping stubborn process(es)..."
    kill -KILL $PIDS 2>/dev/null || true
    sleep 1
    
    PIDS=$(find_mushroom_processes)
    if [ -z "$PIDS" ]; then
        echo -e "${GREEN}✓ All LED processes stopped${NC}"
    else
        echo -e "${RED}✗ Failed to stop processes: $PIDS${NC}"
        exit 1
    fi
}

# Restart LED controller
cmd_restart() {
    cmd_stop
    echo ""
    cmd_start "$@"
}

# Show status
cmd_status() {
    echo "Mushroom LED Controller Status"
    echo "=============================="
    
    # Check systemd service
    if systemctl is-enabled --quiet mushroom-lights 2>/dev/null; then
        if systemctl is-active --quiet mushroom-lights 2>/dev/null; then
            SYSD_PID=$(systemctl show mushroom-lights -p MainPID --value)
            echo -e "Systemd service: ${GREEN}active${NC} (PID: $SYSD_PID)"
        else
            echo -e "Systemd service: ${RED}inactive${NC}"
        fi
    else
        echo "Systemd service: not installed"
    fi
    
    echo ""
    
    # Find running processes
    PIDS=$(find_mushroom_processes)
    if [ -z "$PIDS" ]; then
        echo -e "Process status: ${RED}stopped${NC}"
    else
        echo -e "Process status: ${GREEN}running${NC}"
        for pid in $PIDS; do
            echo ""
            echo "  PID $pid:"
            
            # Get uptime
            UPTIME=$(ps -p $pid -o etime= 2>/dev/null | xargs)
            [ -n "$UPTIME" ] && echo "    Uptime: $UPTIME"
            
            # Parse command line for pattern and brightness
            if [ -r "/proc/$pid/cmdline" ]; then
                CMDLINE=$(tr '\0' ' ' < /proc/$pid/cmdline)
                
                # Extract pattern
                if echo "$CMDLINE" | grep -q -- '--pattern'; then
                    PATTERN=$(echo "$CMDLINE" | sed -n 's/.*--pattern \([^ ]*\).*/\1/p')
                    [ -n "$PATTERN" ] && echo "    Pattern: $PATTERN"
                fi
                
                # Extract brightness
                if echo "$CMDLINE" | grep -q -- '--brightness'; then
                    BRIGHTNESS=$(echo "$CMDLINE" | sed -n 's/.*--brightness \([0-9]*\).*/\1/p')
                    [ -n "$BRIGHTNESS" ] && echo "    Brightness: $BRIGHTNESS"
                fi
            fi
            
            # Check if started by systemd
            if systemctl status mushroom-lights 2>/dev/null | grep -q "Main PID: $pid"; then
                echo "    Started by: systemd"
            else
                echo "    Started by: manual"
            fi
        done
    fi
}

# Run hardware test
cmd_test() {
    check_venv
    
    # Stop any running processes first
    PIDS=$(find_mushroom_processes)
    if [ -n "$PIDS" ]; then
        echo "Stopping running LED processes for test..."
        cmd_stop
        echo ""
    fi
    
    echo "Running hardware test..."
    echo "========================"
    
    if [[ $EUID -ne 0 ]]; then
        echo "Test requires root access. Elevating to sudo..."
        exec sudo "$0" test
    fi
    
    "$PYTHON" tests/test_spi.py
}

# List available patterns
cmd_list() {
    check_venv
    echo "Available LED patterns:"
    echo "======================"
    "$PYTHON" "$SCRIPT_DIR/main.py" --list-patterns | while read pattern; do
        echo "  • $pattern"
    done
}

# View logs
cmd_log() {
    # Prefer systemd logs if service exists (even if stopped)
    if systemctl list-units --all mushroom-lights.service 2>/dev/null | grep -q mushroom-lights; then
        # journalctl uses less by default as pager, -e jumps to end
        sudo journalctl -u mushroom-lights -e
    elif [[ -f /tmp/mushroom-lights.log ]]; then
        # Use less with +G to jump to end of file
        less +G /tmp/mushroom-lights.log
    else
        echo "No logs available. Start the controller with:"
        echo "  ./run.sh start"
        exit 1
    fi
}

# Show command list for no arguments
if [ $# -eq 0 ]; then
    echo "Mushroom LED Controller"
    echo ""
    echo "Usage: ./run.sh COMMAND [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start [pattern] [--brightness N]  Start LED controller"
    echo "  stop                              Stop all LED processes"
    echo "  restart [pattern]                 Restart LED controller"
    echo "  status                           Show running status"
    echo "  test                             Run hardware test"
    echo "  list                             List available patterns"
    echo "  log                              View logs in pager"
    echo ""
    echo "Examples:"
    echo "  ./run.sh start rainbow_wave --brightness 128"
    echo "  ./run.sh status"
    echo "  ./run.sh log"
    echo ""
    echo "Note: Commands require sudo for GPIO/SPI access"
    exit 0
fi

# Main command dispatcher
case "$1" in
    start)
        shift
        cmd_start "$@"
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        shift
        cmd_restart "$@"
        ;;
    status)
        cmd_status
        ;;
    test)
        cmd_test
        ;;
    list)
        cmd_list
        ;;
    log)
        cmd_log
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo "Run './run.sh' without arguments for usage"
        exit 1
        ;;
esac