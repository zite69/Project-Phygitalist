from crispy_forms.layout import Div, Layout
from django import forms
from .models import Registration
from crispy_forms.helper import FormHelper

class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ['name', 'pincode', 'email_phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
                Div(
                    Div(
                        'name', 'pincode', css_class='form-group'
                    ),
                    Div(
                        'email_phone', css_class='form-group full-width'
                    ),
                    css_class='form-grid'
                )
                )
