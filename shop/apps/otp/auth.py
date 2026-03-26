from typing import Any
from django.contrib.auth import get_user_model

from shop.apps.otp.utils import authenticate_otp
from .models import Otp
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.base_user import AbstractBaseUser
from django.http import HttpRequest
from phonenumber_field.phonenumber import PhoneNumber
from django.conf import settings
import pyotp
import logging

logger = logging.getLogger('shop.apps.otp.auth')

class OtpBackend(ModelBackend):
    def authenticate(self, request: HttpRequest, **credentials) -> AbstractBaseUser | None:
        if 'otp' not in credentials:
            return None
        return authenticate_otp(**credentials)


    def get_user(self, user_id: int) -> AbstractBaseUser | None:
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
