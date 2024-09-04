from typing import Any
from django.contrib.auth import get_user_model
from .models import Otp
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.base_user import AbstractBaseUser
from django.http import HttpRequest
from phonenumber_field.phonenumber import PhoneNumber
import pyotp
import logging

logger = logging.getLogger('shop.apps.otp.auth')

class OtpBackend(ModelBackend):
    def authenticate(self, request: HttpRequest, **credentials) -> AbstractBaseUser | None:
        User = get_user_model()
        otp_code = credentials.get('otp')
        phone = credentials.get('phone')
        email = credentials.get('email')
        extra_args = {"is_verified": False}

        logger.debug(f"Attempting to authenticate user with email: {email} phone: {phone} otp: {otp_code}")
        if phone:
            extra_args['to_phone'] = True
            try:
                user = User.objects.get(phone=PhoneNumber.from_string(phone_number=phone))
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
            otp = pyotp.TOTP(otp_obj.otp_secret)
            logger.debug(f"Found otp_obj: {otp_obj} and TOTP object: {otp}")
            if otp.verify(otp_code, valid_window=10):
                otp_obj.is_verified = True
                otp_obj.save()
                logger.debug(f"OTP verified")
                return user
        except Otp.DoesNotExist:
            logger.debug("Otp does not exist")
            return None


    def get_user(self, user_id: int) -> AbstractBaseUser | None:
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
