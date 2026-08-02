import json
import os
import pathlib
from urllib import error as urllib_error
from urllib import request as urllib_request

from dotenv import load_dotenv
from jinja2 import Template

env_path = pathlib.Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "").strip() or os.getenv("MAIL_DEFAULT_SENDER", "").strip() or "Kaimur Explorer <onboarding@resend.dev>"
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@kaimurexplorer.com")

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
    if not RESEND_API_KEY:
        print("[Resend] RESEND_API_KEY is not configured. Set it in backend/.env.")
        return False

    if isinstance(recipients, str):
        recipients = [recipients]

    payload = {
        "from": RESEND_FROM_EMAIL,
        "to": recipients,
        "subject": subject,
        "html": html_body,
    }

    try:
        req = urllib_request.Request(
            "https://api.resend.com/emails",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib_request.urlopen(req, timeout=20) as response:
            response.read()
        return True
    except urllib_error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="ignore")
        print(f"[Resend] Failed to send email to {recipients}: {exc.code} {error_body}")
        return False
    except Exception as exc:
        print(f"[Resend] Failed to send email to {recipients}: {exc}")
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
