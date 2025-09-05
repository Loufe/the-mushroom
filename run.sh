#!/bin/bash
# run.sh - Simple LED controller launcher
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PATH="${SCRIPT_DIR}/mushroom-env"
PYTHON="${VENV_PATH}/bin/python"

if [[ ! -x "$PYTHON" ]]; then
    echo "Error: Virtual environment not found"
    echo ""
    echo "To fix this, run:"
    echo "  ./setup.sh"
    echo ""
    echo "This will create the Python environment and install dependencies."
    echo "Setup takes about 2-3 minutes on first run."
    exit 1
fi

if [[ ! -f "${SCRIPT_DIR}/main.py" ]]; then
    echo "Error: main.py not found in project directory"
    echo "Expected location: ${SCRIPT_DIR}/main.py"
    exit 1
fi

if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    "$PYTHON" main.py --help
    exit 0
fi

if [[ $EUID -ne 0 ]]; then
    echo "LED control requires root access. Elevating to sudo..."
    exec sudo "$0" "$@"
fi

exec "$PYTHON" main.py "$@"