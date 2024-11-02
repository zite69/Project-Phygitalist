from django import forms
from django.utils.translation import gettext_lazy as _
from phonenumber_field.formfields import PhoneNumberField
from django.contrib.auth.forms import UserCreationForm
from shop.apps.user.models import User

class SellerRegistrationForm(UserCreationForm):
    phone = PhoneNumberField(required=False, region='IN')

    gstin = forms.CharField(label=_("GSTIN"), max_length=15)
    pan = forms.CharField(label=_("PAN Number"), max_length=10)
    upi = forms.CharField(label=_("UPI ID"))
    tin = forms.CharField(label=_("TIN"), max_length=11)

    #class Meta:
    #    model = User
    #    fields = ['username', 'password1', 'password2', 'email', 'phone', 'gstin', 'pan', 'upi', 'tin']
