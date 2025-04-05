from django import forms
from allauth.account.adapter import get_adapter
from allauth.account import app_settings
from allauth.core import ratelimit, context
from allauth.account.forms import (RequestLoginCodeForm as OGRequestLoginCodeForm, 
        LoginForm as OGLoginForm, SignupForm as OGSignupForm)

class RequestLoginCodeForm(OGRequestLoginCodeForm):
    def clean_phone(self):
        adapter = get_adapter()
        phone = self.cleaned_data["phone"]
        if type(phone) != str:
            phone = phone.as_international
        if phone:
            self._user = adapter.get_user_by_phone(phone)
            if not self._user and not app_settings.PREVENT_ENUMERATION:
                raise adapter.validation_error("unknown_phone")
            if not ratelimit.consume(
                context.request, action="request_login_code", key=phone
            ):
                raise adapter.validation_error("too_many_login_attempts")
        return phone
