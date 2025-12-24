# Kafka Services Monitoring & Alerting Setup Guide

This guide provides complete instructions for setting up monitoring and alerting for your Kafka infrastructure (Zookeeper, Kafka Broker, and Kafka Connect).

## Overview

The monitoring solution includes:
- **Python-based monitoring script** - Lightweight, standalone monitoring with email alerts
- **Prometheus + Alertmanager** - Enterprise-grade metrics collection and alerting
- **Grafana** - Visualization dashboards (optional)
- **Blackbox Exporter** - TCP port health checks
- **JMX Exporters** - JVM metrics for Zookeeper and Kafka

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Monitoring Stack                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐    ┌─────────────┐ │
│  │  Prometheus  │─────▶│ Alertmanager │───▶│   Gmail     │ │
│  │   :9090      │      │    :9093     │    │  Alerts     │ │
│  └──────┬───────┘      └──────────────┘    └─────────────┘ │
│         │                                                    │
│         │ Scrapes Metrics                                    │
│         ├──────────────────┬──────────────┬────────────┐   │
│         ▼                  ▼              ▼            ▼   │
│  ┌──────────────┐  ┌─────────────┐ ┌──────────┐ ┌────────┐│
│  │  Blackbox    │  │ JMX Export  │ │ JMX Exp. │ │ Kafka  ││
│  │  Exporter    │  │ (Zookeeper) │ │ (Broker) │ │Connect ││
│  │   :9115      │  │   :7071     │ │  :7072   │ │ :8083  ││
│  └──────────────┘  └─────────────┘ └──────────┘ └────────┘│
└─────────────────────────────────────────────────────────────┘
         │                  │              │            │
         │                  │              │            │
         ▼                  ▼              ▼            ▼
    Port Checks        Zookeeper:2181  Broker:9092  Connect:8083
```

## Prerequisites

- Python 3.6+
- Docker and Docker Compose (for Prometheus stack)
- Root or sudo access
- Gmail account or SMTP server for email alerts

## Option 1: Python-Based Monitoring (Recommended for Quick Setup)

### Step 1: Install Dependencies

```bash
# Install Python dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip

# Install required Python packages
pip3 install requests
```

### Step 2: Configure the Monitor

Edit `kafka_monitor_config.json`:

```json
{
  "zookeeper": {
    "host": "localhost",
    "port": 2181
  },
  "kafka_broker": {
    "host": "localhost",
    "port": 9092
  },
  "kafka_connect": {
    "host": "localhost",
    "port": 8083
  },
  "smtp": {
    "server": "smtp.gmail.com",
    "port": 587,
    "use_tls": true,
    "username": "your-email@gmail.com",
    "password": "your-gmail-app-password",
    "from_email": "your-email@gmail.com",
    "to_emails": [
      "alerts@yourdomain.com",
      "team@yourdomain.com"
    ]
  }
}
```

### Step 3: Generate Gmail App Password

1. Go to Google Account settings: https://myaccount.google.com/
2. Navigate to Security → 2-Step Verification
3. Scroll to "App passwords" and create a new app password
4. Copy the 16-character password and use it in the config file

### Step 4: Test the Monitor

```bash
# Make the script executable
chmod +x kafka_monitor.py

# Run a test
python3 kafka_monitor.py
```

### Step 5: Schedule with Cron

```bash
# Make the cron script executable
chmod +x kafka_monitor_cron.sh

# Edit crontab
crontab -e

# Add one of these lines:
# Check every 5 minutes
*/5 * * * * /home/claude/kafka_monitor_cron.sh

# Check every minute
* * * * * /home/claude/kafka_monitor_cron.sh

# Check every hour
0 * * * * /home/claude/kafka_monitor_cron.sh
```

### Step 6: View Logs

```bash
# View monitoring logs
tail -f /var/log/kafka_monitor.log

# View cron execution logs
tail -f /var/log/kafka_monitor_cron.log
```

## Option 2: Prometheus + Alertmanager Stack (Enterprise Solution)

### Step 1: Install Docker and Docker Compose

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install -y docker-compose

# Add your user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Step 2: Configure Alertmanager

Edit `alertmanager.yml` and update the SMTP settings:

```yaml
global:
  smtp_from: 'kafka-alerts@yourdomain.com'
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: 'your-gmail-app-password'
  smtp_require_tls: true
```

Update the receivers section with your email addresses:

```yaml
receivers:
  - name: 'email-critical'
    email_configs:
      - to: 'oncall@yourdomain.com,team@yourdomain.com'
```

### Step 3: Enable JMX on Kafka Services

Add these environment variables to your Kafka services:

**For Zookeeper:**
```bash
export KAFKA_JMX_OPTS="-Dcom.sun.management.jmxremote \
  -Dcom.sun.management.jmxremote.port=9999 \
  -Dcom.sun.management.jmxremote.authenticate=false \
  -Dcom.sun.management.jmxremote.ssl=false"
```

**For Kafka Broker:**
```bash
export KAFKA_JMX_OPTS="-Dcom.sun.management.jmxremote \
  -Dcom.sun.management.jmxremote.port=9998 \
  -Dcom.sun.management.jmxremote.authenticate=false \
  -Dcom.sun.management.jmxremote.ssl=false"
```

### Step 4: Start the Monitoring Stack

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 5: Access the Interfaces

- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

### Step 6: Verify Monitoring

1. Open Prometheus: http://localhost:9090
2. Go to Status → Targets
3. Verify all targets are "UP"
4. Go to Alerts to see configured alert rules

### Step 7: Test Alerting

```bash
# Stop Kafka broker to trigger alert
sudo systemctl stop kafka

# Wait 1-2 minutes, then check:
# 1. Prometheus Alerts page - should show "KafkaBrokerDown" as FIRING
# 2. Alertmanager - should show active alert
# 3. Email inbox - should receive alert email

# Restart broker
sudo systemctl start kafka
```

## Monitoring Connector Status

Both solutions automatically monitor Kafka Connect connector status:

1. **Checks connector state** - Alerts if not in RUNNING state
2. **Checks task status** - Alerts if any task fails
3. **Monitors Connect API** - Alerts if API is unreachable

The connector monitoring uses the Kafka Connect REST API:
- GET `/connectors` - List all connectors
- GET `/connectors/{name}/status` - Get connector status

## Alert Types

### Critical Alerts (Immediate Action Required)
- Zookeeper is down
- Kafka Broker is down
- Kafka Connect is down
- Connector in FAILED state
- Connector task in FAILED state

### Warning Alerts (Investigation Needed)
- Connector not in RUNNING state
- High memory usage (>90%)
- High CPU usage (>80%)
- Low disk space (<10%)

## Troubleshooting

### Python Monitor Issues

**Problem**: Email not sending
```bash
# Check SMTP configuration
# Test with this command:
python3 -c "import smtplib; server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls(); server.login('your-email@gmail.com', 'app-password'); print('Success')"
```

**Problem**: Cannot connect to Kafka services
```bash
# Check if ports are open
netstat -tuln | grep -E '2181|9092|8083'

# Check if services are running
ps aux | grep -E 'zookeeper|kafka|connect'
```

### Prometheus Stack Issues

**Problem**: Targets showing as DOWN
```bash
# Check if exporters are running
docker-compose ps

# Check exporter logs
docker-compose logs blackbox-exporter
docker-compose logs jmx-zookeeper
docker-compose logs jmx-kafka
```

**Problem**: No alerts firing
```bash
# Check Prometheus alert rules
docker-compose exec prometheus promtool check rules /etc/prometheus/kafka_alert_rules.yml

# Check Alertmanager config
docker-compose exec alertmanager amtool check-config /etc/alertmanager/alertmanager.yml
```

**Problem**: Alerts not sending emails
```bash
# Test Alertmanager email
docker-compose exec alertmanager amtool alert add --alertmanager=http://localhost:9093 test_alert service=test

# Check Alertmanager logs
docker-compose logs alertmanager | grep -i email
```

## Best Practices

1. **Use Gmail App Passwords** - Never use your actual Gmail password
2. **Test alerts regularly** - Stop services periodically to ensure alerts work
3. **Monitor the monitors** - Set up a secondary check to ensure monitoring is running
4. **Adjust thresholds** - Tune alert thresholds based on your environment
5. **Document on-call procedures** - Create runbooks for each alert type
6. **Rotate logs** - Set up log rotation to prevent disk space issues

## Adding Custom Connectors Monitoring

To monitor specific connectors, you can modify the Python script or add Prometheus rules:

**Python approach:**
The script automatically discovers and monitors all connectors.

**Prometheus approach:**
Add specific alerts in `kafka_alert_rules.yml`:

```yaml
- alert: SpecificConnectorDown
  expr: kafka_connect_connector_status{connector="my-important-connector",state!="RUNNING"} > 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Critical connector is down"
    description: "The my-important-connector is not running!"
```

## Maintenance

### Update configurations
```bash
# For Python monitor
vim kafka_monitor_config.json
# No restart needed - takes effect on next run

# For Prometheus stack
vim alertmanager.yml
docker-compose restart alertmanager

vim prometheus.yml
docker-compose restart prometheus
```

### View current alerts
```bash
# Python monitor
tail -f /var/log/kafka_monitor.log

# Prometheus
curl http://localhost:9090/api/v1/alerts | jq .

# Alertmanager
curl http://localhost:9093/api/v2/alerts | jq .
```

## Scaling Considerations

For multiple Kafka clusters:
1. Deploy separate monitoring instances per cluster
2. Use different alert email groups per cluster
3. Add cluster labels to Prometheus configs
4. Use federation if you need centralized monitoring

## Security Recommendations

1. **Encrypt SMTP passwords** - Use secrets management (Vault, AWS Secrets Manager)
2. **Restrict API access** - Add authentication to Prometheus/Alertmanager
3. **Use TLS** - Enable TLS for all monitoring endpoints
4. **Network isolation** - Run monitoring in a separate network segment
5. **Regular updates** - Keep Docker images and Python packages updated

## Support

For issues or questions:
1. Check logs: `/var/log/kafka_monitor.log`
2. Review Prometheus targets: http://localhost:9090/targets
3. Check Alertmanager: http://localhost:9093
4. Test email configuration with sample alerts

## Summary

You now have two options for monitoring your Kafka infrastructure:

1. **Python Monitor** - Quick to set up, runs via cron, sends direct email alerts
2. **Prometheus Stack** - Enterprise-grade, with metrics history, advanced alerting, and dashboards

Choose the Python monitor for simplicity, or the Prometheus stack for comprehensive monitoring and historical metrics.
