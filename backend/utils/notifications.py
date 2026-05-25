import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class NotificationService:
    """Сервис отправки уведомлений"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def send_notification(self, channel, recipient, subject, message, task_name=None, status=None):
        """Отправить уведомление через указанный канал"""
        try:
            if channel == 'email':
                return self.send_email(recipient, subject, message, task_name, status)
            elif channel == 'telegram':
                return self.send_telegram(message, task_name, status)
            elif channel == 'slack':
                return self.send_slack(message, task_name, status)
        except Exception as e:
            self.logger.error(f"Failed to send {channel} notification: {str(e)}")
            return False
    
    def send_email(self, recipient, subject, message, task_name=None, status=None):
        """Отправить email уведомление"""
        try:
            if not self.config.SMTP_USER or not self.config.SMTP_PASSWORD:
                self.logger.warning("Email credentials not configured")
                return False
            
            # Форматирование сообщения
            html_body = self._format_email_body(message, task_name, status)
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config.SMTP_USER
            msg['To'] = recipient
            msg['Date'] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
            
            # Attach both plain text and HTML versions
            part1 = MIMEText(message, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            with smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT) as server:
                server.starttls()
                server.login(self.config.SMTP_USER, self.config.SMTP_PASSWORD)
                server.send_message(msg)
            
            self.logger.info(f"Email sent to {recipient}")
            return True
        except Exception as e:
            self.logger.error(f"Email send failed: {str(e)}")
            return False
    
    def send_telegram(self, message, task_name=None, status=None):
        """Отправить Telegram уведомление"""
        try:
            if not self.config.TELEGRAM_BOT_TOKEN or not self.config.TELEGRAM_CHAT_ID:
                self.logger.warning("Telegram credentials not configured")
                return False
            
            # Форматирование сообщения
            formatted_message = self._format_telegram_message(message, task_name, status)
            
            url = f"https://api.telegram.org/bot{self.config.TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': self.config.TELEGRAM_CHAT_ID,
                'text': formatted_message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                self.logger.info("Telegram message sent successfully")
                return True
            else:
                self.logger.error(f"Telegram API error: {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Telegram send failed: {str(e)}")
            return False
    
    def send_slack(self, message, task_name=None, status=None):
        """Отправить Slack уведомление"""
        try:
            if not self.config.SLACK_WEBHOOK_URL:
                self.logger.warning("Slack webhook URL not configured")
                return False
            
            # Форматирование сообщения
            color = self._get_status_color(status)
            
            payload = {
                'attachments': [{
                    'color': color,
                    'title': task_name or 'System Task',
                    'text': message,
                    'footer': 'SysAdmin Tasks Manager',
                    'ts': int(datetime.utcnow().timestamp())
                }]
            }
            
            response = requests.post(self.config.SLACK_WEBHOOK_URL, json=payload, timeout=10)
            
            if response.status_code == 200:
                self.logger.info("Slack message sent successfully")
                return True
            else:
                self.logger.error(f"Slack API error: {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Slack send failed: {str(e)}")
            return False
    
    @staticmethod
    def _format_email_body(message, task_name, status):
        """Форматировать HTML тело письма"""
        status_color = 'green' if status == 'success' else 'red' if status == 'failed' else 'orange'
        
        html = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .container {{ max-width: 600px; margin: 0 auto; }}
                    .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
                    .content {{ background-color: #ecf0f1; padding: 20px; }}
                    .status {{ color: {status_color}; font-weight: bold; }}
                    .footer {{ background-color: #34495e; color: white; padding: 10px; text-align: center; border-radius: 0 0 5px 5px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>SysAdmin Tasks Manager</h2>
                    </div>
                    <div class="content">
                        <p><strong>Task:</strong> {task_name or 'System Task'}</p>
                        <p><strong>Status:</strong> <span class="status">{status or 'Unknown'}</span></p>
                        <p><strong>Message:</strong></p>
                        <p>{message}</p>
                        <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                    <div class="footer">
                        <p>© 2024 SysAdmin Tasks Manager. All rights reserved.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        return html
    
    @staticmethod
    def _format_telegram_message(message, task_name, status):
        """Форматировать Telegram сообщение"""
        status_emoji = '✅' if status == 'success' else '❌' if status == 'failed' else '⚠️'
        
        return f"""
{status_emoji} <b>Task Notification</b>

<b>Task:</b> {task_name or 'System Task'}
<b>Status:</b> {status or 'Unknown'}

<b>Message:</b>
{message}

<b>Time:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
        """
    
    @staticmethod
    def _get_status_color(status):
        """Получить цвет статуса для Slack"""
        colors = {
            'success': '#36a64f',
            'failed': '#e74c3c',
            'warning': '#f39c12',
            'running': '#3498db'
        }
        return colors.get(status, '#95a5a6')
