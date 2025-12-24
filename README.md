# Kafka Services Monitoring & Alerting System

Complete monitoring solution for Kafka infrastructure with email alerts to Google Workspace.

## 🚀 Quick Start

```bash
# Make the quick start script executable
chmod +x quick_start.sh

# Run the setup
./quick_start.sh
```

## 📋 What Gets Monitored

✅ **Zookeeper** (Port 2181)
- Service availability
- Port connectivity
- JVM metrics (optional)

✅ **Kafka Broker** (Port 9092)
- Service availability
- Port connectivity
- JVM metrics (optional)

✅ **Kafka Connect** (Port 8083)
- Service availability
- REST API health
- Connector status (RUNNING/FAILED/PAUSED)
- Task status for each connector

## 📧 Alert Notifications

Alerts are sent via email to Google Workspace when:
- Any service stops responding
- Port connectivity fails
- Kafka Connect connector is not in RUNNING state
- Kafka Connect connector task fails
- Kafka Connect API becomes unreachable

## 🎯 Two Implementation Options

### Option 1: Python Monitor (Recommended for Quick Setup)
- Lightweight standalone script
- Minimal dependencies (just Python + requests)
- Runs via cron for periodic checks
- Direct SMTP email alerts
- Easy to customize and debug

**Files:**
- `kafka_monitor.py` - Main monitoring script
- `kafka_monitor_config.json` - Configuration file
- `kafka_monitor_cron.sh` - Cron wrapper script
- `quick_start.sh` - Automated setup script

### Option 2: Prometheus + Alertmanager (Enterprise Solution)
- Full metrics collection and storage
- Historical data and trend analysis
- Advanced alerting with templates
- Grafana dashboards included
- Scales to multiple clusters

**Files:**
- `docker-compose.yml` - Complete monitoring stack
- `prometheus.yml` - Prometheus configuration
- `alertmanager.yml` - Alert routing and notifications
- `kafka_alert_rules.yml` - Alert definitions
- `blackbox.yml` - TCP/HTTP probe configuration

## 📖 Documentation

- **SETUP_GUIDE.md** - Complete installation and configuration guide
- Covers both Python and Prometheus approaches
- Troubleshooting tips
- Best practices

## 🔧 Configuration

### For Python Monitor

Edit `kafka_monitor_config.json`:

```json
{
  "zookeeper": {"host": "localhost", "port": 2181},
  "kafka_broker": {"host": "localhost", "port": 9092},
  "kafka_connect": {"host": "localhost", "port": 8083},
  "smtp": {
    "server": "smtp.gmail.com",
    "port": 587,
    "username": "your-email@gmail.com",
    "password": "your-gmail-app-password",
    "from_email": "your-email@gmail.com",
    "to_emails": ["alerts@yourdomain.com"]
  }
}
```

### Gmail App Password Setup

1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification
3. Generate an App Password
4. Use the 16-character password in configuration

## 🧪 Testing

### Test Python Monitor
```bash
python3 kafka_monitor.py
```

### Trigger Test Alert
```bash
# Stop a service to trigger alert
sudo systemctl stop kafka

# Wait 1-2 minutes for alert
# Check email inbox

# Restart service
sudo systemctl start kafka
```

## 📊 Monitoring Logs

```bash
# Python monitor logs
tail -f /var/log/kafka_monitor.log

# Cron execution logs
tail -f /var/log/kafka_monitor_cron.log

# Prometheus logs (if using docker-compose)
docker-compose logs -f prometheus
```

## 🔄 Scheduling

The Python monitor can be scheduled via cron. Example schedules:

```bash
# Every minute (testing)
* * * * * /path/to/kafka_monitor_cron.sh

# Every 5 minutes (recommended)
*/5 * * * * /path/to/kafka_monitor_cron.sh

# Every hour
0 * * * * /path/to/kafka_monitor_cron.sh
```

## 📦 Files Included

### Core Monitoring
- `kafka_monitor.py` - Python monitoring script
- `kafka_monitor_config.json` - Configuration template
- `kafka_monitor_cron.sh` - Cron wrapper script
- `quick_start.sh` - Automated setup

### Prometheus Stack
- `docker-compose.yml` - Full monitoring stack
- `prometheus.yml` - Metrics collection config
- `alertmanager.yml` - Alert routing config
- `kafka_alert_rules.yml` - Alert definitions
- `blackbox.yml` - Probe configuration

### Documentation
- `SETUP_GUIDE.md` - Complete setup instructions
- `README.md` - This file

### Optional Files
- `kafka-monitor.service` - Systemd service file

## 🛠️ Requirements

### Python Monitor
- Python 3.6+
- `requests` library
- Cron (for scheduling)
- SMTP access (Gmail or other)

### Prometheus Stack
- Docker
- Docker Compose
- 4GB RAM minimum
- 10GB disk space

## 🎯 Use Cases

**Development/Testing:**
Use Python monitor for quick setup and testing.

**Production:**
Use Prometheus stack for comprehensive monitoring with historical data.

**Small Deployments:**
Python monitor is sufficient for 1-5 clusters.

**Large Scale:**
Prometheus stack with federation for multiple clusters.

## 🐛 Troubleshooting

### Email not working?
1. Check SMTP credentials in config
2. Verify Gmail App Password is correct
3. Test SMTP connection manually
4. Check firewall rules for port 587

### Services showing as down?
1. Verify service ports: `netstat -tuln | grep -E '2181|9092|8083'`
2. Check service status: `ps aux | grep kafka`
3. Review service logs
4. Test connectivity: `telnet localhost 2181`

### Connector status not detected?
1. Verify Kafka Connect is running
2. Check Connect REST API: `curl http://localhost:8083/connectors`
3. Verify connector exists: `curl http://localhost:8083/connectors/{name}/status`
4. Review Connect logs

## 📚 Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Alertmanager Guide](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Kafka Connect REST API](https://docs.confluent.io/platform/current/connect/references/restapi.html)
- [Gmail SMTP Settings](https://support.google.com/mail/answer/7126229)

## 🤝 Support

For issues or questions:
1. Check logs for error messages
2. Review SETUP_GUIDE.md for detailed instructions
3. Test each component individually
4. Verify network connectivity

## 📄 License

This monitoring solution is provided as-is for use with your Kafka infrastructure.

---

**Ready to start monitoring?** Run `./quick_start.sh` and follow the prompts!
