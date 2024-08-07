from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from oscar.apps.customer.abstract_models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField

class User(AbstractUser, PermissionsMixin):
    username = models.CharField(_("Username"), max_length=64, unique=True, blank=False)
    phone = PhoneNumberField(_("Phone Number"), unique=True, region='IN')

