from django import forms
from django.utils.translation import gettext as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from moneyed.classes import CLE
from shop.apps.registration.models import SellerRegistration
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.validators import ValidationError as PhoneValidationError
from .models import InvitationCode, Invitation

User = get_user_model()

class InviteForm(forms.Form):
    email_address = forms.EmailField()

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def clean_email_address(self):
        email = self.cleaned_data["email_address"]
        if EmailAddress.objects.filter(email=email, verified=True).exists():
            raise forms.ValidationError(_("Email address already in use"))
        elif JoinInvitation.objects.filter(from_user=self.user, signup_code__email=email).exists():
            raise forms.ValidationError(_("You have already invited this user"))
        return email

class InvitationForm(forms.ModelForm):

    class Meta:
        model = Invitation
        fields = [
            'email', 'phone', 'invite_type'
        ]
        # widgets = {
        #     "phone": PhoneNumberField(region='IN')
        # }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit(name="submit", value="Send Invite"))

    def clean_email(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        if email == "":
            return cleaned_data

        if User.objects.filter(email=email).exists():
            raise ValidationError(_("A user with that email address already exists"))

        if SellerRegistration.objects.filter(email=email).exists():
            raise ValidationError(_("A user with that email address already exists"))

        return cleaned_data

    def clean_phone(self):
        cleaned_data = super().clean()
        phone = cleaned_data.get('phone')

        if phone == "":
            return cleaned_data

        return cleaned_data

    def clean(self):
        return super().clean()
