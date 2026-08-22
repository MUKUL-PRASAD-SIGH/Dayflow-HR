"""
app/otp_utils.py – OTP generation, email delivery, and verification.
"""

import os
import random
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()

# In-process OTP store: {email: {"otp": str, "timestamp": float, "verified": bool}}
# In production, replace with Redis or a DB table with TTL.
otp_storage: dict = {}

_OTP_VALIDITY_SECONDS = int(os.getenv("OTP_EXPIRY_MINUTES", "10")) * 60


def generate_otp(email: str) -> str:
    """Generate and store a 6-digit OTP for the given email."""
    otp = str(random.randint(100_000, 999_999))
    otp_storage[email] = {
        "otp": otp,
        "timestamp": time.time(),
        "verified": False,
    }
    print(f"[OTP] Generated for {email}")
    return otp


def send_otp_email(receiver_email: str, otp: str) -> bool:
    """
    Send OTP via SMTP.

    Reads SMTP config from environment variables:
        SMTP_SERVER   (default: smtp.gmail.com)
        SMTP_PORT     (default: 587)
        EMAIL_SENDER
        EMAIL_PASSWORD
    """
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    sender_email = os.getenv("EMAIL_SENDER")
    sender_password = os.getenv("EMAIL_PASSWORD")

    if not sender_email or not sender_password:
        raise EnvironmentError(
            "EMAIL_SENDER and EMAIL_PASSWORD must be set in your .env file."
        )

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = "Your OTP – Dayflow HR"

    body = f"""
    <h2 style="color: #3363b0;">Dayflow HR – One-Time Password</h2>
    <p>Your OTP is: <strong style="font-size: 1.4em;">{otp}</strong></p>
    <p>This code is valid for <b>{os.getenv('OTP_EXPIRY_MINUTES', '10')} minutes</b>.</p>
    <p style="color: #888;">If you did not request this, please ignore this email.</p>
    """
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"[OTP] Email sent to {receiver_email}")
        return True
    except Exception as exc:
        print(f"[OTP] Failed to send email: {exc}")
        return False


def verify_otp(email: str, user_otp: str) -> bool:
    """
    Verify the OTP entered by the user.

    Returns True if the OTP is correct and has not expired.
    The OTP is NOT cleared automatically — call clear_otp() after successful verification.
    """
    if email not in otp_storage:
        print(f"[OTP] No OTP record found for {email}")
        return False

    record = otp_storage[email]
    elapsed = time.time() - record["timestamp"]

    if elapsed > _OTP_VALIDITY_SECONDS:
        print(f"[OTP] Expired for {email} ({elapsed:.0f}s elapsed)")
        del otp_storage[email]
        return False

    if record["otp"] == str(user_otp).strip():
        print(f"[OTP] Verified for {email}")
        record["verified"] = True
        return True

    print(f"[OTP] Mismatch for {email}")
    return False


def is_email_verified(email: str) -> bool:
    """Return True if the email has been successfully verified via OTP."""
    return otp_storage.get(email, {}).get("verified", False)


def clear_otp(email: str) -> None:
    """Remove OTP record for the given email."""
    otp_storage.pop(email, None)
