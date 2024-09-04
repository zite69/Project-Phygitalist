from typing import Any, Mapping
from django import forms
from django.forms.renderers import BaseRenderer
from django.forms.utils import ErrorList
from phonenumber_field.formfields import PhoneNumberField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from shop.apps.main.utils.sms import send_phone_otp
from shop.apps.main.utils.email import send_email_otp
from .utils import generate_otp
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from shop.apps.main.utils.common import dump
import logging
from shop.apps.main.utils.common import dump

logger = logging.getLogger('shop.apps.otp')

class RequestOtpFormMixin(object):
    def request_otp(self):
        User = get_user_model()
        #dump(self.fields, logger)
        try:
            logger.debug("Inside request_otp")
            if 'email' in self.cleaned_data:
                #logger.debug(f"we have email: {self.email}")
                email = self.cleaned_data['email']
                user = User.objects.get(email=email)
                otp = generate_otp(user, email=True)
                logger.debug(f"Generated OTP: {otp}")
                if otp:
                    resp = send_email_otp(user.email, otp)
                    logger.debug(f"Got response from sending email otp: {resp}")
            elif 'phone' in self.fields:
                phone = self.cleaned_data['phone']
                user = User.objects.get(phone=phone)
                otp = generate_otp(user, phone=True)
                logger.debug(f"Generated phone OTP: {otp}")
                if otp:
                    resp = send_phone_otp(user.phone, otp)
                    #logger.debug(f"Got response from sending phone otp: {resp}")
            else:
                raise ValueError(_("Badly configured either email or phone field must be defined"))
            return True
        except User.DoesNotExist:
            return False
            
class EmailOtpRequestForm(forms.Form, RequestOtpFormMixin):
    email = forms.EmailField(required=True)      
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = "id-request-email-otp"
        
        self.helper.add_input(Submit(name="email-form", value="Request OTP by Email"))
        
class PhoneOtpRequestForm(forms.Form, RequestOtpFormMixin):
    phone = PhoneNumberField(required=True, region="IN")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = "id-requesst-phone-otp"

        self.helper.add_input(Submit(name="phone-form", value="Request OTP to Phone"))

class OtpLoginMixin(object):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields['otp'] = forms.CharField(max_length=10)
        
    def do_login(self):
        User = get_user_model()
        if hasattr(self, 'email'):
            try:
                user = User.objects.get(email=self.email)

            except User.DoesNotExist:
                raise ValidationError(_("Invalid Credentials Provided"))                

class OtpVerificationForm(forms.Form):
    email = forms.EmailField()
    phone = PhoneNumberField()
    otp = forms.CharField(max_length=10)

    def __init__(self, request=None, *args, **kwargs) -> None:
        self.request = request
        self.user_cache = None
       
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_id = "login-form"
        self.helper.add_input(Submit(name="login", value="Login"))
        email = phone = ""
        #logger.debug(f"type: {type(self.fields['email'].initial)}")
        #logger.debug(f"getattr e: {getattr(self.fields['email'], 'initial', None)}")
        #logger.debug(f"getattr p: {getattr(self.fields['phone'], 'initial', None)}")
        #dump(self.initial['phone'], logger)
        #logger.debug(type(self.initial['phone']))
        if  'email' in self.initial:
            email = self.initial['email']
            logger.debug(f"OtpVerificationForm received email: {email}")
        
        if 'phone' in self.initial:
            #logger.debug("Setting phone value")
            phone = self.initial['phone']
            logger.debug(f"OtpVerificationForm received phone: {phone}")

        #logger.debug(f"Got empty values: {email}, {phone}")
        if email == "" and phone == "":
            raise ValidationError(_("Form must have recieved either email address or phone number"))
        
        if email == "":
            self.fields['email'].widget = forms.HiddenInput()
            self.fields['email'].required = False
        else:
            self.fields['phone'].widget = forms.HiddenInput()
            self.fields['phone'].required = False

    def clean(self):
        email = self.cleaned_data.get('email')
        phone = self.cleaned_data.get('phone')
        otp = self.cleaned_data.get('otp')
        logger.debug(f"Attempting to authenticate: email: {email}, phone: {phone}, otp: {otp}")
        if (email is not None or phone is not None) and otp is not None:
            self.user_cache = authenticate(self.request, email=email, phone=str(phone.national_number), otp=otp)
            logger.debug(f"authenticate returned: {self.user_cache}")
            if self.user_cache is None:
                raise ValidationError(_("Invalid Credentials"))
            else:
                self.confirm_login_allowed(self.user_cache)
        
        return self.cleaned_data
    
    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise ValidationError(_("Account is not active. Please contact the administrator"))
        
    def get_user(self):
        return self.user_cache
    

