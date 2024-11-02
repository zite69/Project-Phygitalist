from phonenumber_field.phonenumber import PhoneNumber
from .models import Otp
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.models import Q
import pyotp
import logging

logger = logging.getLogger("shop.apps.otp")

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


def authenticate_otp(otp='', phone='', email='', active=True):
    otp_code = otp
    extra_args = {"is_verified": False}
    user = None
    logger.debug(f"Attempting to authenticate user with email: {email} phone: {phone} otp: {otp_code} typeof phone: {type(phone)}")
    if phone:
        extra_args['to_phone'] = True
        try:
            if type(phone) == str:
                phonenum = PhoneNumber.from_string(phone_number=phone)
                if active:
                    user = User.objects.get(phone=phonenum)
                else:
                    #Complete hack. For some reason User.objects.get() doesn't work with is_active=False and password = blank or empty
                    #So we get a list of all users with is_active = False and blank or null or empty passwords and check their phone
                    #objects
                    for u in User.objects.filter(Q(is_active=False) & (Q(password='') | Q(password__startswith='!') | Q(password__isnull=True))):
                        if u.phone == phonenum:
                            user = u
            elif type(phone) == PhoneNumber:
                if active:
                    user = User.objects.get(phone=phone)
                else:
                    for u in User.objects.filter(Q(is_active=False) & (Q(password='') | Q(password__startswith='!') | Q(password__isnull=True))):
                        if u.phone == phone:
                            user = u
            logger.debug(f"Found user with phone: {user}")
        except User.DoesNotExist:
            logger.debug(f"Failed to find user with phonenumber")
            return None
    elif email:
        extra_args['to_email'] = True
        try:
            user = User.objects.get(email=email)
            logger.debug(f"Found user with email: {user}")
        except User.DoesNotExist:
            logger.debug(f"Failed to find user with email")
            return None

    if user is None or otp_code is None:
        return None

    try:
        otp_obj = Otp.objects.filter(user=user, **extra_args).latest('creation_date')
        totp = pyotp.TOTP(otp_obj.otp_secret)
        logger.debug(f"Found otp_obj: {otp_obj} and TOTP object: {totp}")
        otp_window = getattr(settings, 'OTP_WINDOW', 10)
        if totp.verify(otp_code, valid_window=otp_window):
            otp_obj.is_verified = True
            otp_obj.save()
            logger.debug(f"OTP verified")
            return user
    except Otp.DoesNotExist:
        logger.debug("Otp does not exist")
        return None

    return None
