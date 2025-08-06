import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os



# Fallback values to avoid crashing if .env is not loaded
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))  # Default to 587 if not provided
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# Safety check before starting the email process
if not EMAIL_USER or not EMAIL_PASS:
    raise Exception("EMAIL_USER is missing in .env file")


def send_email(subject: str, to_email: str, body: str):
    message = MIMEMultipart()
    message["From"] = EMAIL_USER
    message["To"] = to_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, to_email, message.as_string())
            print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Email send failed: {e}")
