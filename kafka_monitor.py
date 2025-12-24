#!/usr/bin/env python3
"""
Kafka Services Monitoring Script
Monitors: Zookeeper, Kafka Broker, Kafka Connect, and Connector Status
Sends email alerts via SMTP when services are down
"""

import socket
import requests
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
import sys
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/kafka_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class KafkaMonitor:
    def __init__(self, config):
        self.config = config
        self.alerts = []
        
    def check_port(self, host, port, service_name):
        """Check if a port is open and accepting connections"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                logging.info(f"✓ {service_name} is running on {host}:{port}")
                return True
            else:
                error_msg = f"✗ {service_name} is DOWN - Cannot connect to {host}:{port}"
                logging.error(error_msg)
                self.alerts.append({
                    'service': service_name,
                    'status': 'DOWN',
                    'message': error_msg,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                return False
        except Exception as e:
            error_msg = f"✗ {service_name} check failed: {str(e)}"
            logging.error(error_msg)
            self.alerts.append({
                'service': service_name,
                'status': 'ERROR',
                'message': error_msg,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            return False
    
    def check_kafka_connect_api(self):
        """Check Kafka Connect REST API and connector status"""
        connect_host = self.config['kafka_connect']['host']
        connect_port = self.config['kafka_connect']['port']
        base_url = f"http://{connect_host}:{connect_port}"
        
        try:
            # Check Connect API health
            response = requests.get(f"{base_url}/", timeout=5)
            if response.status_code == 200:
                logging.info(f"✓ Kafka Connect REST API is responding")
            else:
                error_msg = f"✗ Kafka Connect REST API returned status {response.status_code}"
                logging.error(error_msg)
                self.alerts.append({
                    'service': 'Kafka Connect API',
                    'status': 'UNHEALTHY',
                    'message': error_msg,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                return False
            
            # Check connector status
            connectors_response = requests.get(f"{base_url}/connectors", timeout=5)
            if connectors_response.status_code == 200:
                connectors = connectors_response.json()
                logging.info(f"Found {len(connectors)} connectors: {connectors}")
                
                for connector in connectors:
                    status_response = requests.get(
                        f"{base_url}/connectors/{connector}/status",
                        timeout=5
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        connector_state = status_data.get('connector', {}).get('state', 'UNKNOWN')
                        
                        if connector_state != 'RUNNING':
                            error_msg = f"✗ Connector '{connector}' is in {connector_state} state"
                            logging.error(error_msg)
                            self.alerts.append({
                                'service': f'Connector: {connector}',
                                'status': connector_state,
                                'message': error_msg,
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'details': status_data
                            })
                        else:
                            logging.info(f"✓ Connector '{connector}' is RUNNING")
                        
                        # Check task status
                        tasks = status_data.get('tasks', [])
                        for task in tasks:
                            task_state = task.get('state', 'UNKNOWN')
                            task_id = task.get('id', 'unknown')
                            if task_state != 'RUNNING':
                                error_msg = f"✗ Connector '{connector}' task {task_id} is in {task_state} state"
                                logging.error(error_msg)
                                self.alerts.append({
                                    'service': f'Connector Task: {connector}-{task_id}',
                                    'status': task_state,
                                    'message': error_msg,
                                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                })
                
                return True
            else:
                error_msg = f"✗ Failed to retrieve connectors list: {connectors_response.status_code}"
                logging.error(error_msg)
                self.alerts.append({
                    'service': 'Kafka Connect Connectors',
                    'status': 'ERROR',
                    'message': error_msg,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                return False
                
        except requests.exceptions.RequestException as e:
            error_msg = f"✗ Kafka Connect API check failed: {str(e)}"
            logging.error(error_msg)
            self.alerts.append({
                'service': 'Kafka Connect API',
                'status': 'UNREACHABLE',
                'message': error_msg,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            return False
    
    def send_email_alert(self):
        """Send email alert via SMTP"""
        if not self.alerts:
            logging.info("No alerts to send")
            return
        
        smtp_config = self.config['smtp']
        
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🚨 Kafka Services Alert - {len(self.alerts)} Issue(s) Detected"
        msg['From'] = smtp_config['from_email']
        msg['To'] = ', '.join(smtp_config['to_emails'])
        
        # Create HTML email body
        html_body = self._generate_html_alert()
        
        # Create plain text version
        text_body = self._generate_text_alert()
        
        # Attach both versions
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        try:
            # Connect to SMTP server
            if smtp_config.get('use_tls', True):
                server = smtplib.SMTP(smtp_config['server'], smtp_config['port'])
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(smtp_config['server'], smtp_config['port'])
            
            # Login if credentials provided
            if smtp_config.get('username') and smtp_config.get('password'):
                server.login(smtp_config['username'], smtp_config['password'])
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            logging.info(f"✓ Alert email sent successfully to {smtp_config['to_emails']}")
        except Exception as e:
            logging.error(f"✗ Failed to send email alert: {str(e)}")
    
    def _generate_html_alert(self):
        """Generate HTML formatted alert email"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #d9534f; color: white; padding: 20px; text-align: center; }}
                .alert {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
                .alert.critical {{ background-color: #f2dede; border-color: #d9534f; }}
                .alert-title {{ font-weight: bold; color: #d9534f; margin-bottom: 5px; }}
                .timestamp {{ color: #666; font-size: 0.9em; }}
                .footer {{ margin-top: 20px; padding: 10px; background-color: #f5f5f5; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚨 Kafka Services Alert</h1>
                <p>Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            <div style="padding: 20px;">
                <h2>Alert Summary</h2>
                <p><strong>{len(self.alerts)} issue(s)</strong> detected in your Kafka infrastructure:</p>
        """
        
        for alert in self.alerts:
            html += f"""
                <div class="alert critical">
                    <div class="alert-title">🔴 {alert['service']} - {alert['status']}</div>
                    <div>{alert['message']}</div>
                    <div class="timestamp">Time: {alert['timestamp']}</div>
                </div>
            """
        
        html += """
            </div>
            <div class="footer">
                <p>This is an automated alert from your Kafka Monitoring System.</p>
                <p>Please investigate and resolve these issues as soon as possible.</p>
            </div>
        </body>
        </html>
        """
        return html
    
    def _generate_text_alert(self):
        """Generate plain text alert email"""
        text = f"KAFKA SERVICES ALERT\n"
        text += f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        text += "=" * 60 + "\n\n"
        text += f"{len(self.alerts)} issue(s) detected:\n\n"
        
        for i, alert in enumerate(self.alerts, 1):
            text += f"{i}. {alert['service']} - {alert['status']}\n"
            text += f"   {alert['message']}\n"
            text += f"   Time: {alert['timestamp']}\n\n"
        
        text += "=" * 60 + "\n"
        text += "Please investigate and resolve these issues as soon as possible.\n"
        return text
    
    def run_checks(self):
        """Run all monitoring checks"""
        logging.info("=" * 60)
        logging.info("Starting Kafka Services Health Check")
        logging.info("=" * 60)
        
        # Check Zookeeper
        self.check_port(
            self.config['zookeeper']['host'],
            self.config['zookeeper']['port'],
            'Zookeeper'
        )
        
        # Check Kafka Broker
        self.check_port(
            self.config['kafka_broker']['host'],
            self.config['kafka_broker']['port'],
            'Kafka Broker'
        )
        
        # Check Kafka Connect port
        connect_port_ok = self.check_port(
            self.config['kafka_connect']['host'],
            self.config['kafka_connect']['port'],
            'Kafka Connect'
        )
        
        # Check Kafka Connect API and connectors if port is open
        if connect_port_ok:
            self.check_kafka_connect_api()
        
        # Send alerts if any issues found
        if self.alerts:
            logging.warning(f"Found {len(self.alerts)} issue(s), sending alert email...")
            self.send_email_alert()
        else:
            logging.info("✓ All services are healthy!")
        
        logging.info("=" * 60)
        return len(self.alerts) == 0


def load_config(config_file='/home/claude/kafka_monitor_config.json'):
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in configuration file: {e}")
        sys.exit(1)


def main():
    # Load configuration
    config = load_config()
    
    # Create monitor instance
    monitor = KafkaMonitor(config)
    
    # Run checks
    all_healthy = monitor.run_checks()
    
    # Exit with appropriate code
    sys.exit(0 if all_healthy else 1)


if __name__ == "__main__":
    main()
