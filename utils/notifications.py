"""
Notification system for QuantWave.
Supports Telegram and Email.
"""
import logging
import os
import smtplib
from email.mime.text import MIMEText
from typing import Dict, Optional
import requests

logger = logging.getLogger(__name__)

class NotificationManager:
    """Manages multi-channel notifications using trading_profile.yml structure."""
    
    def __init__(self, config: Dict):
        trader_config = config.get("trader", {})
        self.notif_config = trader_config.get("notifications", {})
        
        # Email settings (if available in config, else fallback to trader email)
        self.email_enabled = self.notif_config.get("email_enabled", False)
        self.trader_email = trader_config.get("email", "")
        
    def send_telegram(self, message: str):
        """Send message via Telegram bot."""
        if not self.notif_config.get("telegram_enabled"):
            return
            
        token = self.notif_config.get("telegram_bot_token")
        chat_id = self.notif_config.get("telegram_chat_id")
        
        if not token or not chat_id:
            logger.warning("Telegram token or chat_id missing in trading_profile.yml")
            return
            
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            response = requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"})
            if response.status_code != 200:
                logger.error(f"Telegram error: {response.text}")
        except Exception as e:
            logger.error(f"Telegram exception: {e}")

    def send_email(self, subject: str, body: str):
        """Send message via Email."""
        if not self.email_enabled:
            return
            
        # Email settings from config
        smtp_server = self.notif_config.get("smtp_server", "smtp.gmail.com")
        smtp_port = self.notif_config.get("smtp_port", 587)
        username = self.notif_config.get("email_username")
        password = self.notif_config.get("email_password")
        receiver = self.trader_email
        
        if not all([smtp_server, username, password, receiver]):
            logger.warning("Email configuration incomplete in trading_profile.yml")
            return
            
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = username
        msg['To'] = receiver
        
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)
        except Exception as e:
            logger.error(f"Email exception: {e}")

    def notify(self, message: str, subject: str = "QuantWave Alert"):
        """Send notification to all enabled channels."""
        self.send_telegram(message)
        self.send_email(subject, message)
