import os
import pathlib
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from jinja2 import Template

env_path = pathlib.Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", f"Kaimur Explorer <{MAIL_USERNAME}>")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", MAIL_USERNAME)

BOOKING_EMAIL_TEMPLATE = Template("""
<h2>New Booking Confirmed</h2>
<p><strong>Booking ID:</strong> {{ booking_id }}</p>
<p><strong>Tour:</strong> {{ tour_name }}</p>
<p><strong>Name:</strong> {{ name }}</p>
<p><strong>Location:</strong> {{ location }}</p>
<p><strong>Age:</strong> {{ age }}</p>
<p><strong>Email:</strong> {{ email }}</p>
<p><strong>Phone:</strong> {{ phone }}</p>
<p><strong>Date of Booking:</strong> {{ date_of_booking }}</p>
<p><strong>Status:</strong> {{ status }}</p>
<p>The booking has been confirmed. Please contact the customer soon to finalize details.</p>
""")

STATUS_EMAIL_TEMPLATE = Template("""
<h2>Your Kaimur Explorer Booking Status Update</h2>
<p>Dear {{ name }},</p>
<p>Your booking for <strong>{{ tour_name }}</strong> has been <strong>{{ status }}</strong>.</p>
<p><strong>Booking details:</strong></p>
<ul>
    <li><strong>Tour:</strong> {{ tour_name }}</li>
    <li><strong>Status:</strong> {{ status }}</li>
    <li>{{ details }}</li>
</ul>
<p>{% if status == 'Confirmed' %}Your booking is confirmed successfully. We will contact you soon with further details.{% else %}Your booking request has been rejected. Please try another tour or contact support for assistance.{% endif %}</p>
<p>Regards,<br/>Kaimur Explorer Team</p>
""")

OTP_EMAIL_TEMPLATE = Template("""
<h2>Your Kaimur Explorer OTP Code</h2>
<p>Hello,</p>
<p>Your one-time password for login is:</p>
<p style="font-size: 1.4rem; font-weight: bold;">{{ otp_code }}</p>
<p>This OTP expires in 5 minutes. Do not share it with anyone.</p>
""")


def _send_email(subject, recipients, html_body):
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        raise RuntimeError("Mail credentials are not configured. Set MAIL_USERNAME and MAIL_PASSWORD in backend/.env.")

    if isinstance(recipients, str):
        recipients = [recipients]

    message = MIMEMultipart("alternative")
    message["From"] = MAIL_DEFAULT_SENDER
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.attach(MIMEText(html_body, "html"))

    if len(MAIL_PASSWORD) != 16 or " " in MAIL_PASSWORD:
        print("[SMTP] WARNING: Gmail App Password must be 16 characters and contain no spaces.")
        print("[SMTP] Current MAIL_PASSWORD looks invalid. Update backend/.env with a valid App Password.")
      
    try:
        with smtplib.SMTP(MAIL_SERVER, MAIL_PORT, timeout=20) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(MAIL_USERNAME, MAIL_PASSWORD)
            smtp.sendmail(MAIL_DEFAULT_SENDER, recipients, message.as_string())
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"[SMTP] Authentication failed for {MAIL_USERNAME}: {e}")
        print("[SMTP] Make sure you are using a Gmail App Password, not your normal Gmail password.")
        return False
    except Exception as e:
        print(f"[SMTP] Failed to send email to {recipients}: {e}")
        return False


def send_otp_email(user_email, otp_code):
    subject = "Kaimur Explorer OTP Login Code"
    html = OTP_EMAIL_TEMPLATE.render(otp_code=otp_code)
    return _send_email(subject, user_email, html)


def send_booking_notification(admin_email, booking_data):
    print("\n" + "=" * 60)
    print("NEW BOOKING NOTIFICATION")
    print("=" * 60)
    for key, value in booking_data.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    print("=" * 60 + "\n")

    subject = f"New Booking Request: {booking_data['tour_name']}"
    html = BOOKING_EMAIL_TEMPLATE.render(**booking_data)
    sent = _send_email(subject, admin_email, html)
    if not sent:
        print("[Booking Notification] Email failed, but booking is saved.")
    return sent


def send_status_email(user_email, booking_data):
    subject = f"Booking {booking_data['status']}: {booking_data['tour_name']}"
    html = STATUS_EMAIL_TEMPLATE.render(**booking_data)
    return _send_email(subject, user_email, html)
