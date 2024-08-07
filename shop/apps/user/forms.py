from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model
from phonenumber_field.widgets import PhoneNumberPrefixWidget

class Zite69UserCreationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        widgets = {
            'phone': PhoneNumberPrefixWidget(),
        }
        fields = '__all__'

class Zite69UserChangeForm(UserChangeForm):
    class Meta:
        model = get_user_model()
        widgets = {
            'phone': PhoneNumberPrefixWidget(),
        }
        fields = '__all__'