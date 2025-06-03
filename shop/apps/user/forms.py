from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model
from phonenumber_field.widgets import PhoneNumberPrefixWidget
from phonenumber_field.formfields import PhoneNumberField
from allauth.account.forms import SignupForm, PasswordField
import logging
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__package__)

class Zite69UserCreationForm(UserCreationForm):
    phone = PhoneNumberField(required=False)
    class Meta:
        model = get_user_model()
        fields = '__all__'

class Zite69UserChangeForm(UserChangeForm):
    phone = PhoneNumberField(required=False)

    class Meta:
        model = get_user_model()
        fields = '__all__'

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.fields['phone'].widget = PhoneNumberPrefixWidget()
    #     if self.instance:
    #         phone_number = self.instance.phone
    #         country_code = str(phone_number.country_code)
    #         national_number = str(phone_number.national_number)
    #         self.fields['phone'].widget.widgets[0].value = country_code  # Set country code
    #         self.fields['phone'].widget.widgets[1].text = national_number
    #         self.fields['phone'].initial = phone_number
    #         print(country_code)
    #         print(national_number)

class Zite69SignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'] = PasswordField(
                label=_("Password"),
                help_text="<a href='#' data-bs-toggle='tooltip' data-bs-animation='false' data-bs-html='true' data-bs-title='<ul><li>Your password can&apos;t be too similar to your other personal information.</li><li>Your password must contain at least 8 characters.</li><li>Your password can&apos;t be a commonly used password.</li><li>Your password can&apos;t be entirely numeric.</li></ul>'>*</a>",
                required=True
                )
    
    def save(self, request):
        user = super().save(request)
        return user
