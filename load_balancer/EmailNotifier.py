import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

class EmailNotifier:
    def __init__(self, smtp_server, smtp_port, email_user, email_password, receiver_email):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_user = email_user
        self.email_password = email_password
        self.receiver_email = receiver_email

    def send_alert_email(self, subject, error):
        """Send an email alert."""
        msg = EmailMessage()
        msg.set_content(error)
        msg['Subject'] = subject
        msg['From'] = self.email_user
        msg['To'] = self.receiver_email

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
        except Exception as e:
            print(f"Failed to send email. Error: {e}")

load_dotenv()
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
RECEIVER_EMAIL = os.getenv('RECEIVER_EMAIL', "server-status.7yhf8@aleeas.com")
email_notifier = EmailNotifier(SMTP_SERVER, SMTP_PORT, EMAIL_USER, EMAIL_PASSWORD, RECEIVER_EMAIL)
