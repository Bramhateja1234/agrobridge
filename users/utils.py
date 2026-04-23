import requests
from django.conf import settings
from decouple import config

from django.core.mail import send_mail

def send_email_otp(email, otp):
    """
    Sends an OTP to the given email using Django's core mail component.
    Also prints the OTP to the terminal as a fallback for development.
    """
    # Fallback to display OTP in terminal during dev/testing
    print("=" * 50)
    print(f"*** FALLBACK: LOCAL OTP DELIVERY ***")
    print(f"To Email: {email}")
    print(f"Your OTP is: {otp}")
    print("=" * 50)
        
    subject = "AgroBridge Password Reset OTP"
    message = f"Your OTP for AgroBridge is {otp}. It is valid for 5 minutes."
    
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
        print("[SUCCESS] Email sent successfully")
        return {"success": True, "message": "Email sent"}
    except Exception as e:
        print("[ERROR] Email failed:", str(e))
        return {"success": False, "message": str(e)}
