from django.db import models
from django.conf import settings
from django.db.models.fields import validators
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from phonenumber_field.modelfields import PhoneNumberField
import re

SWIFT_REX = re.compile(r"[A-Z]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?")

def validate_swift(code):
    if not SWIFT_REX.match(code):
        raise ValidationError(_("SWIFT Code is invalid"))

class BankAccount(models.Model):
    TYPE_SAVINGS, TYPE_CURRENT, TYPE_OTHER = ('S', 'C', 'O')
    ACCOUNT_TYPES = (
        (TYPE_SAVINGS, _("Savings Account")),
        (TYPE_CURRENT, _("Current Account")),
        (TYPE_OTHER, _("Other"))
        )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=False)
    name = models.CharField(_("Account Holder Name"), max_length=255, db_index=True, blank=False, null=True)
    primary = models.BooleanField(_("Primary Account"), default=False)
    bank = models.CharField(_("Bank Name"), max_length=128, db_index=True, blank=False, null=False)
    branch = models.CharField(_("Branch Name"), max_length=128, blank=False, null=False)
    account_type = models.CharField(_("Account Type"), max_length=2, choices=ACCOUNT_TYPES) 
    branch_address = models.ForeignKey('address.OrganizationAddress', on_delete=models.CASCADE, null=True)
    imps = models.BooleanField(_("IMPS Available"), default=False)
    rtgs = models.BooleanField(_("RTGS Available"), default=False)
    neft = models.BooleanField(_("NEFT Available"), default=False)
    contact = PhoneNumberField(_("Bank Contact"), region='IN', blank=False, null=True)
    ifsc = models.CharField(_("IFSC Code"), max_length=11, db_index=True, blank=False, null=False)
    micr = models.CharField(_("MICR"), max_length=9, db_index=True, blank=True, null=True)
    swift = models.CharField(_("SWIFT"), max_length=11, db_index=True, blank=True, null=True, validators=[validate_swift])
    account_number = models.CharField(_("Account Number"), max_length=18, db_index=True, blank=False, null=False)
    registered_phone = PhoneNumberField(_("Registered Mobile Number"), region='IN', blank=True, null=True)

    class Meta:
        unique_together = ['bank', 'account_number']

