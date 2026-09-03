import random
import string
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from .models import OTP
import logging

logger = logging.getLogger(__name__)

def generate_otp(user, purpose, length=None):
    if length is None:
        length = settings.OTP_LENGTH
    code = ''.join(random.choices(string.digits, k=length))
    # Invalidate old unused OTPs for the same user and purpose
    OTP.objects.filter(user=user, purpose=purpose, is_used=False).update(is_used=True)
    otp = OTP.objects.create(
        user=user,
        code=code,
        purpose=purpose,
        expires_at=timezone.now() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
    )
    return otp

def send_otp_email(user, otp_code, purpose):
    subject_map = {
        'login': 'Your login OTP',
        'verify': 'Verify your email',
        'reset': 'Reset your password',
    }
    subject = subject_map.get(purpose, 'Your OTP code')
    message = f'Your OTP is: {otp_code}\nIt expires in {settings.OTP_EXPIRY_MINUTES} minutes.'
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP email to {user.email}: {e}")
        return False

def send_otp_sms(user, otp_code):
    # Placeholder – integrate with Africa's Talking or Twilio
    try:
        # Example with africastalking
        # import africastalking
        # africastalking.initialize(settings.AFRICASTALKING_USERNAME, settings.AFRICASTALKING_API_KEY)
        # sms = africastalking.SMS
        # sms.send(f'Your OTP is: {otp_code}', [user.phone_number])
        logger.info(f"SMS OTP to {user.phone_number}: {otp_code}")
        return True
    except Exception as e:
        logger.error(f"Failed to send SMS OTP to {user.phone_number}: {e}")
        return False

def send_otp(user, purpose, contact=None):
    """Send OTP via the appropriate channel based on contact (email or phone)."""
    if contact is None:
        contact = user.email or user.phone_number
    otp = generate_otp(user, purpose)
    sent = False
    if '@' in contact:
        sent = send_otp_email(user, otp.code, purpose)
    else:
        sent = send_otp_sms(user, otp.code)
    return otp if sent else None