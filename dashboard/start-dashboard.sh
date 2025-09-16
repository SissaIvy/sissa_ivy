#!/bin/bash
#
# SISSA Ivy Security Dashboard Startup Script
# Launches the real-time security monitoring dashboard
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== SISSA Ivy Security Dashboard ==="
echo "Project Root: $PROJECT_ROOT"
echo

# Configuration
DASHBOARD_HOST="${DASHBOARD_HOST:-0.0.0.0}"
DASHBOARD_PORT="${DASHBOARD_PORT:-5000}"
COLLECTION_INTERVAL="${COLLECTION_INTERVAL:-60}"
LINUX_PROBE="$PROJECT_ROOT/cogsec/collectors/cogsec_probe_linux.py"
WINDOWS_PROBE="$PROJECT_ROOT/cogsec/collectors/Get-CogSecEndpointState.ps1"

# Check dependencies
echo "Checking dependencies..."
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required"
    exit 1
fi

# Check for required Python packages
echo "Checking Python packages..."
python3 -c "import flask, plotly" 2>/dev/null || {
    echo "Installing required packages..."
    pip3 install -r "$SCRIPT_DIR/requirements.txt"
}

# Verify probe scripts exist
echo "Checking probe scripts..."
if [[ -f "$LINUX_PROBE" ]]; then
    echo "✓ Linux probe found: $LINUX_PROBE"
else
    echo "⚠ Linux probe not found: $LINUX_PROBE"
fi

if [[ -f "$WINDOWS_PROBE" ]]; then
    echo "✓ Windows probe found: $WINDOWS_PROBE"
else
    echo "⚠ Windows probe not found: $WINDOWS_PROBE"
fi

# Test probe execution
echo "Testing probe execution..."
if [[ -f "$LINUX_PROBE" ]]; then
    if python3 "$LINUX_PROBE" > /dev/null 2>&1; then
        echo "✓ Linux probe test successful"
    else
        echo "⚠ Linux probe test failed"
    fi
fi

echo
echo "Starting Security Dashboard..."
echo "Host: $DASHBOARD_HOST"
echo "Port: $DASHBOARD_PORT"
echo "Collection Interval: ${COLLECTION_INTERVAL}s"
echo "Dashboard URL: http://$DASHBOARD_HOST:$DASHBOARD_PORT"
echo
echo "Press Ctrl+C to stop the dashboard"
echo

# Set Flask app location
export FLASK_APP="$SCRIPT_DIR/security_dashboard.py"

# Start the dashboard
cd "$SCRIPT_DIR"
python3 security_dashboard.py \
    --linux-probe "$LINUX_PROBE" \
    --windows-probe "$WINDOWS_PROBE" \
    --host "$DASHBOARD_HOST" \
    --port "$DASHBOARD_PORT" \
    --interval "$COLLECTION_INTERVAL" \
    "$@"