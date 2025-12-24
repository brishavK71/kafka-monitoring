#!/bin/bash
# Cron-based Kafka Monitoring Script
# This script runs the Python monitor and can be scheduled via cron

# Set paths
SCRIPT_DIR="/home/claude"
PYTHON_SCRIPT="$SCRIPT_DIR/kafka_monitor.py"
LOG_FILE="/var/log/kafka_monitor_cron.log"

# Ensure log file exists
touch "$LOG_FILE"

# Log execution start
echo "========================================" >> "$LOG_FILE"
echo "Kafka Monitor executed at $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Run the Python monitoring script
/usr/bin/python3 "$PYTHON_SCRIPT" >> "$LOG_FILE" 2>&1

# Log completion
echo "Completed at $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

exit 0
