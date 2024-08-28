from typing import Any
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from oscar.apps.customer.abstract_models import AbstractUser
from oscar.core.loading import get_class, get_model
from phonenumber_field.modelfields import PhoneNumberField
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

import re

#Address = get_model("address", "Address")

REX_UPI = re.compile(r"^.+@.+$")

@deconstructible
class validate_length:
    def __init__(self, length=15) -> None:
        self.length = length

    def __call__(self, value, **kwds: Any) -> Any:
        if len(str(value)) != self.length:
            raise ValidationError(_("Value %(value)s is not of %(length)s"), params={"value": value, "length": self.length})
        
    def __eq__(self, other):
        return self.length == other.length
    
def validate_upi(value):
    if not REX_UPI.match(value):
        raise ValidationError(_("UPI ID %(value)s does not appear to be valid"))
    
class User(AbstractUser, PermissionsMixin):
    username = models.CharField(_("Username"), max_length=64, unique=True, blank=False)
    phone = PhoneNumberField(_("Phone Number"), unique=True, region='IN')
    email_verified = models.BooleanField(_("Verified Email"), default=False)
    phone_verified = models.BooleanField(_("Verified Phonenumber"), default=False)


class ProfileAddesses(models.Model):
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE)
    address = models.ForeignKey('address.UserAddress', on_delete=models.CASCADE)
    primary = models.BooleanField(_("Primary Address?"), default=False)
    shipping = models.BooleanField(_("Shipping Address?"), default=False)
    pickup = models.BooleanField(_("Pickup Address for Sellers"), default=False)

class Profile(models.Model):
    TYPE_BUYER = 'B'
    TYPE_SELLER = 'S'
    TYPE_BOTH = 'O'
    TYPE_CEO = 'C'
    TYPE_CHOICES = (
        (TYPE_BUYER, _("Buyer")),
        (TYPE_SELLER, _("Seller")),
        (TYPE_BOTH, _("Both")),
        (TYPE_CEO, _("CEO")),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True, blank=False, null=False)
    type = models.CharField(_("User Profile Type"), name="type", max_length=4, db_index=True, choices=TYPE_CHOICES)

    gstin = models.CharField(_("GSTIN Number"), name="gstin", max_length=15, db_index=True, blank=True, null=True, unique=True, validators=[validate_length(15)])
    pan = models.CharField(_("PAN Number"), name="pan", max_length=10, db_index=True, blank=True, null=True, unique=True, validators=[validate_length(10)])
    upi = models.CharField(_("UPI ID"), name="upi", max_length=45, db_index=True, blank=True, null=True, unique=True, validators=[validate_upi])
    tin = models.CharField(_("TIN Number"), name="tin", max_length=11, db_index=True, blank=True, null=True, unique=True, validators=[validate_length(11)])

    def get_type(self):
        for k, v in self.TYPE_CHOICES:
            if k == self.type:
                return v
        
        return ""
    