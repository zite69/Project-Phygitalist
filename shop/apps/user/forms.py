from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model
from phonenumber_field.widgets import PhoneNumberPrefixWidget
from phonenumber_field.formfields import PhoneNumberField


class Zite69UserCreationForm(UserCreationForm):
    phone = PhoneNumberField()
    class Meta:
        model = get_user_model()
        fields = '__all__'

class Zite69UserChangeForm(UserChangeForm):
    phone = PhoneNumberField()

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
        
