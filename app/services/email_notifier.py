import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.config import settings
import logging

logger = logging.getLogger(__name__)

def send_notification(processing_id: str, recipient: str) -> bool:
    """
    Send the “your image is ready” email with HTML formatting.
    Returns True on success, False on any failure.
    """
    msg = MIMEMultipart("alternative")
    msg["From"] = "smtp@mailtrap.io"  # or settings.SMTP_USER
    msg["To"] = recipient
    msg["Subject"] = "Your background‐removed image is ready"

    download_url = f"{settings.BASE_URL}/download/{processing_id}"

    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f0f8ff; padding: 20px; color: #333;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 8px; padding: 20px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
          <h2 style="color: #2e8b57;">🎉 Your Image is Ready!</h2>
          <p>Hi there,</p>
          <p>Your image has been successfully processed using <strong>MIB Tech Background Remover</strong>.</p>
          <p>
            <a href="{download_url}" style="display: inline-block; background-color: #add8e6; color: #ffffff; padding: 12px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">
              👉 Download Your Image
            </a>
          </p>
          <p style="font-size: 0.9em; color: #777;">Note: This link will expire in 24 hours.</p>
          <hr style="border: none; border-top: 1px solid #eee;">
          <p style="font-size: 0.9em;">Thanks for using our service,<br>MIB Tech</p>
        </div>
      </body>
    </html>
    """

    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
            smtp_server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp_server.sendmail(msg["From"], msg["To"], msg.as_string())

        logger.info(f"Notification sent to {recipient}")
        return True

    except Exception as e:
        logger.error(f"[EmailNotifier] failed to send to {recipient}: {e}")
        return False
