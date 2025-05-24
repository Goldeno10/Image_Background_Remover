# app/services/email_notifier.py

import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text    import MIMEText
from app.config import settings
import logging

logger = logging.getLogger(__name__)

def send_notification(processing_id: str, recipient: str) -> bool:
    """
    Send the “your image is ready” email.
    Returns True on success, False on any failure.
    """

    msg = MIMEMultipart()
    msg["From"]    = settings.SMTP_USER
    msg["To"]      = recipient
    msg["Subject"] = "Your background‐removed image is ready"

    download_url = f"{settings.BASE_URL}/download/{processing_id}"
    body = (
        f"Hello,\n\n"
        f"Your image has been processed!\n"
        f"Download link (expires in 24h): {download_url}\n\n"
        f"Thanks for using our service."
    )
    msg.attach(MIMEText(body, "plain"))

    ctx = ssl.create_default_context()

    try:
        # STARTTLS on port 587
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as smtp:
            smtp.ehlo()
            print("say hello 1")
            smtp.starttls(context=ctx)
            smtp.ehlo()
            print("say hello 2")
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            print("login success")
            smtp.send_message(msg)
            print("message sent")
        logger.info(f"Notification sent to {recipient}")
        return True

    except Exception as e:
        logger.error(f"[EmailNotifier] failed to send to {recipient}: {e}")
        return False



# import smtplib, ssl
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# from app.config import settings
# import logging

# logger = logging.getLogger(__name__)

# def send_notification(processing_id: str, recipient: str):
#     msg = MIMEMultipart()
#     msg["From"]    = settings.SMTP_USER
#     msg["To"]      = recipient
#     msg["Subject"] = "Your background-removed image is ready"

#     download_url = f"{settings.BASE_URL}/download/{processing_id}"
#     body = (
#         f"Hello,\n\n"
#         f"Your image has been processed.\n"
#         f"Download link (expires in 24h): {download_url}\n\n"
#         f"Enjoy!"
#     )
#     msg.attach(MIMEText(body, "plain"))

#     context = ssl.create_default_context()

#     try:
#         # Gmail on port 587 requires STARTTLS
#         with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
#             server.ehlo()
#             server.starttls(context=context)
#             server.ehlo()
#             server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
#             server.send_message(msg)
#         # with smtplib.SMTP_SSL(settings.SMTP_SERVER, 465, context=context) as server:
#         #     server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
#         #     server.send_message(msg)
#     except Exception as e:
#         logger.error(f"Failed to send email to {recipient}: {e}")
#         # handle or re-raise


# import smtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# from fastapi import HTTPException
# from app.config import settings
# import logging

# logger = logging.getLogger(__name__)


# def send_notification(processing_id: str, recipient: str):
#     msg = MIMEMultipart()
#     msg["From"] = settings.SMTP_USER
#     msg["To"] = recipient
#     msg["Subject"] = "Background Removal Complete"

#     download_url = f"{settings.BASE_URL}/download/{processing_id}"
#     body = (
#         f"Your image is ready!\n\n"
#         f"Download link: {download_url}\n"
#         f"Link expires in {settings.REDIS_TTL_SECONDS // 3600}h."
#     )
#     msg.attach(MIMEText(body, "plain"))

#     try:
#         with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as smtp:
#             smtp.starttls()
#             smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
#             smtp.send_message(msg)
#     except Exception as e:
#         logger.error(f"Email send failed for {recipient}: {e}")
#         raise HTTPException(500, "Failed to send notification email")