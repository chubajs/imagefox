#!/bin/bash

# ImageFox Agent Executor Script
# Runs the ImageFox agent for automatic image processing

# Set up environment
export PATH=$PATH:/home/sbulaev/.local/bin
cd "$(dirname "$0")"

# Set environment variables from storyteller (fallback location for API keys)
if [ -f "/home/sbulaev/storyteller/.env" ]; then
    set -a
    source /home/sbulaev/storyteller/.env
    set +a
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to run the ImageFox agent
run_imagefox_agent() {
    local log_file="logs/cron_imagefox_agent.log"
    local agent_script="imagefox_agent.py"
    
    echo "$(date): Starting ImageFox Agent" >> "$log_file"
    
    if ps aux | grep -v grep | grep "$agent_script" >/dev/null 2>&1; then
        echo "$(date): ImageFox Agent is already running" >> "$log_file"
    else
        echo "$(date): Starting ImageFox Agent" >> "$log_file"
        # Activate virtual environment and run the agent
        source venv/bin/activate
        python "$agent_script" >> "$log_file" 2>&1
        exit_code=$?
        echo "$(date): ImageFox Agent finished with exit code $exit_code" >> "$log_file"
    fi
}

# Function to check agent health
check_agent_health() {
    local health_log="logs/agent_health.log"
    echo "$(date): Health check - ImageFox Agent" >> "$health_log"
    
    # Check if log file exists and has recent entries
    local main_log="logs/imagefox_agent.log"
    if [ -f "$main_log" ]; then
        local last_entry=$(tail -n 1 "$main_log" 2>/dev/null)
        echo "$(date): Last log entry: $last_entry" >> "$health_log"
    else
        echo "$(date): Warning: No main log file found" >> "$health_log"
    fi
}

# Function to clean old log files
cleanup_logs() {
    local cleanup_log="logs/cleanup.log"
    echo "$(date): Starting log cleanup" >> "$cleanup_log"
    
    # Remove log files older than 7 days
    find logs/ -name "*.log" -mtime +7 -exec rm {} \; 2>/dev/null
    
    # Rotate main log if it's too large (>10MB)
    local main_log="logs/imagefox_agent.log"
    if [ -f "$main_log" ] && [ $(stat --format=%s "$main_log") -gt 10485760 ]; then
        mv "$main_log" "${main_log}.$(date +%Y%m%d_%H%M%S)"
        echo "$(date): Rotated main log file" >> "$cleanup_log"
    fi
    
    echo "$(date): Log cleanup completed" >> "$cleanup_log"
}

# Main execution based on argument
case "${1:-run}" in
    "run")
        run_imagefox_agent
        ;;
    "health")
        check_agent_health
        ;;
    "cleanup")
        cleanup_logs
        ;;
    "test")
        echo "$(date): Running ImageFox Agent test"
        python3 test_agent.py
        ;;
    *)
        echo "Usage: $0 [run|health|cleanup|test]"
        echo "  run     - Execute the ImageFox agent (default)"
        echo "  health  - Check agent health status" 
        echo "  cleanup - Clean up old log files"
        echo "  test    - Run test suite"
        exit 1
        ;;
esac