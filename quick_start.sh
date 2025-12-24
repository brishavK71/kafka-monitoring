#!/bin/bash
# Quick Start Script for Kafka Monitoring Setup

set -e

echo "=========================================="
echo "Kafka Monitoring Quick Start Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${YELLOW}Warning: Running as root. Consider running as a regular user with sudo.${NC}"
fi

# Install Python dependencies
echo -e "${GREEN}[1/6] Installing Python dependencies...${NC}"
if command -v pip3 &> /dev/null; then
    pip3 install requests --break-system-packages 2>/dev/null || pip3 install requests
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
else
    echo -e "${RED}✗ pip3 not found. Please install Python 3 and pip3 first.${NC}"
    exit 1
fi

# Create log directory
echo -e "${GREEN}[2/6] Setting up log directory...${NC}"
sudo mkdir -p /var/log
sudo touch /var/log/kafka_monitor.log
sudo chmod 666 /var/log/kafka_monitor.log
echo -e "${GREEN}✓ Log directory configured${NC}"

# Make scripts executable
echo -e "${GREEN}[3/6] Making scripts executable...${NC}"
chmod +x kafka_monitor.py
chmod +x kafka_monitor_cron.sh
echo -e "${GREEN}✓ Scripts are now executable${NC}"

# Configuration prompt
echo ""
echo -e "${YELLOW}[4/6] Configuration Setup${NC}"
echo "Please edit kafka_monitor_config.json with your settings:"
echo "  - SMTP server details (Gmail or your email provider)"
echo "  - Alert recipient email addresses"
echo "  - Service hostnames (if not localhost)"
echo ""
read -p "Press Enter after you've configured the file, or Ctrl+C to exit..."

# Test configuration
echo -e "${GREEN}[5/6] Testing configuration...${NC}"
if [ -f "kafka_monitor_config.json" ]; then
    echo -e "${GREEN}✓ Configuration file found${NC}"
    
    # Run a quick test
    echo "Running connectivity test..."
    python3 kafka_monitor.py
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ All services are healthy!${NC}"
    else
        echo -e "${YELLOW}⚠ Some services are down. Check the output above.${NC}"
        echo "This is normal if you want to test alerting."
    fi
else
    echo -e "${RED}✗ Configuration file not found!${NC}"
    exit 1
fi

# Setup cron job
echo ""
echo -e "${GREEN}[6/6] Setting up cron job...${NC}"
echo "Select monitoring frequency:"
echo "  1) Every minute (testing/high-frequency)"
echo "  2) Every 5 minutes (recommended)"
echo "  3) Every 15 minutes"
echo "  4) Every hour"
echo "  5) Skip cron setup (manual scheduling)"
read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        CRON_SCHEDULE="* * * * *"
        ;;
    2)
        CRON_SCHEDULE="*/5 * * * *"
        ;;
    3)
        CRON_SCHEDULE="*/15 * * * *"
        ;;
    4)
        CRON_SCHEDULE="0 * * * *"
        ;;
    5)
        echo -e "${YELLOW}Skipping cron setup${NC}"
        CRON_SCHEDULE=""
        ;;
    *)
        echo -e "${YELLOW}Invalid choice. Using default (every 5 minutes)${NC}"
        CRON_SCHEDULE="*/5 * * * *"
        ;;
esac

if [ -n "$CRON_SCHEDULE" ]; then
    CRON_COMMAND="$CRON_SCHEDULE $(pwd)/kafka_monitor_cron.sh"
    
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "kafka_monitor_cron.sh"; then
        echo -e "${YELLOW}Cron job already exists. Skipping...${NC}"
    else
        # Add to crontab
        (crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -
        echo -e "${GREEN}✓ Cron job added: $CRON_SCHEDULE${NC}"
    fi
fi

# Final summary
echo ""
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Summary:"
echo "--------"
echo "• Python monitor: kafka_monitor.py"
echo "• Configuration: kafka_monitor_config.json"
echo "• Main log: /var/log/kafka_monitor.log"
echo "• Cron log: /var/log/kafka_monitor_cron.log"
echo ""
echo "Useful Commands:"
echo "----------------"
echo "• Manual test:    python3 kafka_monitor.py"
echo "• View main log:  tail -f /var/log/kafka_monitor.log"
echo "• View cron log:  tail -f /var/log/kafka_monitor_cron.log"
echo "• Edit config:    vim kafka_monitor_config.json"
echo "• Edit crontab:   crontab -e"
echo "• View crontab:   crontab -l"
echo ""
echo "Next Steps:"
echo "-----------"
echo "1. Wait for the next scheduled run, or run manually for immediate test"
echo "2. Monitor the logs to see if alerts are working"
echo "3. Test by stopping a Kafka service to trigger an alert"
echo "4. Check your email for alert notifications"
echo ""
echo -e "${GREEN}Happy monitoring! 📊${NC}"
