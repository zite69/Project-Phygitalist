from phonenumber_field.phonenumber import PhoneNumber
from .models import Otp
from django.contrib.auth import get_user_model
import pyotp

User = get_user_model()

def generate_otp(user, email=False, phone=False):
    if not email and not phone:
        return False
    
    otp_secret = pyotp.random_base32()
    otp = pyotp.TOTP(otp_secret)
    otp_code = otp.now()

    if email:
        otp_obj = Otp.objects.create(user=user, to_email=email)
    else:
        otp_obj = Otp.objects.create(user=user, to_phone=phone)

    otp_obj.otp_secret = otp_secret
    otp_obj.save()

    return otp_code
    
def validate_otp(user, otp):
    pass

def send_otp_to_phone(phonenumber):
    try:
        phone = PhoneNumber.from_string(phonenumber)
        user = User.objects.get(phone=phone)
        otp_secret = pyotp.random_base32()
        otp = pyotp.TOTP(otp_secret)
        otp_code = otp.now()

        otp_obj = Otp.objects.create(user=user, phone=phone)
        otp_obj.otp_secret = otp_secret
        otp_obj.save()
        
        response = send_otp(phone.as_national, otp_code)


    except User.DoesNotExist:
        return False
