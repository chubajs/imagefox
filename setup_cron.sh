#!/bin/bash

# Setup cron job for ImageFox Agent
# This script sets up a cron job to run the ImageFox agent every 5 minutes

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXECUTOR_SCRIPT="$SCRIPT_DIR/executor.sh"
CRON_ENTRY="*/5 * * * * $EXECUTOR_SCRIPT run"

echo "Setting up ImageFox Agent cron job..."
echo "Script directory: $SCRIPT_DIR"
echo "Executor script: $EXECUTOR_SCRIPT"
echo "Cron entry: $CRON_ENTRY"

# Check if executor script exists and is executable
if [ ! -x "$EXECUTOR_SCRIPT" ]; then
    echo "Error: Executor script not found or not executable: $EXECUTOR_SCRIPT"
    echo "Make sure to run: chmod +x $EXECUTOR_SCRIPT"
    exit 1
fi

# Get current crontab
TEMP_CRON=$(mktemp)
crontab -l 2>/dev/null > "$TEMP_CRON"

# Check if ImageFox cron entry already exists
if grep -q "imagefox.*executor.sh" "$TEMP_CRON" 2>/dev/null; then
    echo "ImageFox cron job already exists. Current entries:"
    grep "imagefox.*executor.sh" "$TEMP_CRON"
    echo ""
    echo "Remove existing entries? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        # Remove existing entries
        grep -v "imagefox.*executor.sh" "$TEMP_CRON" > "${TEMP_CRON}.new"
        mv "${TEMP_CRON}.new" "$TEMP_CRON"
        echo "Existing entries removed."
    else
        echo "Keeping existing entries. Exiting."
        rm -f "$TEMP_CRON"
        exit 0
    fi
fi

# Add new cron entry
echo "$CRON_ENTRY" >> "$TEMP_CRON"

# Install new crontab
if crontab "$TEMP_CRON"; then
    echo "✓ ImageFox Agent cron job installed successfully!"
    echo "  - Runs every 5 minutes"
    echo "  - Logs to: $SCRIPT_DIR/logs/cron_imagefox_agent.log"
    echo ""
    echo "Current crontab entries:"
    crontab -l | grep -E "(imagefox|#)"
    echo ""
    echo "To check logs:"
    echo "  tail -f $SCRIPT_DIR/logs/cron_imagefox_agent.log"
    echo ""
    echo "To disable the cron job:"
    echo "  crontab -e  # and remove the ImageFox line"
else
    echo "✗ Failed to install cron job"
    rm -f "$TEMP_CRON"
    exit 1
fi

# Cleanup
rm -f "$TEMP_CRON"

# Optional: Add cleanup and health check cron jobs
echo ""
echo "Would you like to add additional maintenance cron jobs? (y/N)"
echo "  - Daily log cleanup (runs at 2 AM)"
echo "  - Hourly health check"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    TEMP_CRON=$(mktemp)
    crontab -l > "$TEMP_CRON"
    
    # Add cleanup job (daily at 2 AM)
    echo "0 2 * * * $EXECUTOR_SCRIPT cleanup" >> "$TEMP_CRON"
    
    # Add health check (every hour)
    echo "0 * * * * $EXECUTOR_SCRIPT health" >> "$TEMP_CRON"
    
    if crontab "$TEMP_CRON"; then
        echo "✓ Additional maintenance jobs installed!"
        echo "  - Daily cleanup: 2:00 AM"
        echo "  - Hourly health check"
    else
        echo "✗ Failed to install additional jobs"
    fi
    
    rm -f "$TEMP_CRON"
fi

echo ""
echo "Setup complete! The ImageFox Agent will now run automatically every 5 minutes."
echo "Monitor the logs to ensure it's working properly."