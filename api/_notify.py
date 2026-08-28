"""Owner email notification, sent via the owner's own Gmail account (SMTP + app
password) so a real booking notice reaches him regardless of what app the
customer has installed - unlike the WhatsApp button, which only fires if the
customer has WhatsApp and chooses to tap it.

Needs two environment variables on Vercel:
  GMAIL_ADDRESS       - the Gmail address to send from (and default recipient)
  GMAIL_APP_PASSWORD  - a 16-character Gmail "app password" (not the normal
                        Google password - generated under Google Account ->
                        Security -> 2-Step Verification -> App passwords)
Optional:
  OWNER_NOTIFY_EMAIL  - where notifications go, if different from GMAIL_ADDRESS
"""
import os
import smtplib
from email.mime.text import MIMEText


def send_owner_email(subject, body):
    sender = os.environ.get('GMAIL_ADDRESS')
    app_password = os.environ.get('GMAIL_APP_PASSWORD')
    recipient = os.environ.get('OWNER_NOTIFY_EMAIL') or sender
    if not sender or not app_password or not recipient:
        return False

    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=8) as server:
            server.login(sender, app_password)
            server.sendmail(sender, [recipient], msg.as_string())
        return True
    except Exception:
        return False
