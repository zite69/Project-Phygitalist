from typing import Any
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.views.generic.edit import FormView
from django.views.generic import View
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.contrib.auth import login
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from shop.apps.main.utils.common import dump
from shop.apps.main.utils.sms import send_phone_otp
from shop.apps.main.utils.email import send_email_otp
from shop.apps.otp.utils import generate_otp

from .forms import EmailOtpRequestForm, PhoneOtpRequestForm, OtpVerificationForm, EmailPhoneOtpRequestForm
import logging
import json
from django.core.validators import validate_email
from phonenumber_field.validators import validate_international_phonenumber
from shop.apps.main.utils.urls import get_absolute_url

logger = logging.getLogger('shop.apps.otp.views')

class RequestOtpJsonView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
           return JsonResponse({"error": "Invalid json input"})

        email_phone = data.get('email_phone', '')
        valid_email = False
        valid_phone = False
        user_kw_args = {}
        generate_kw_args = {}
        try:
            validate_email(email_phone)
            valid_email = True
            user_kw_args["email"] = email_phone
            generate_kw_args["email"] = True
        except ValidationError:
            pass

        if not valid_email:
            try:
                validate_international_phonenumber(email_phone)
                valid_phone = True
                user_kw_args["phone"] = email_phone
                generate_kw_args["phone"] = True
            except ValidationError:
                pass

        if not valid_email and not valid_phone:
            return JsonResponse({"error": "Invalid phone or email address"})

        User = get_user_model()
        try:
            user = User.objects.get(**user_kw_args)
            otp = generate_otp(user, **generate_kw_args)
            if otp:
                if valid_email:
                    resp = send_email_otp(user.email, otp)
                    logger.debug(f"Sent email otp to user: {user}, got response: {resp}")
                else:
                    resp = send_phone_otp(user.phone, otp)
                    logger.debug(f"Sent phone otp to user: {user} got response: {resp}")
            else:
                return JsonResponse({"error": "Failed to generate OTP"})
        except User.DoesNotExist:
            return JsonResponse({"error": "User does not exist"})
        self.request.session['email_phone'] = email_phone
        self.request.session['email_phone_field_type'] = 'email' if valid_email else 'phone'
        return JsonResponse({"code": 200, "message": "OTP successfully sent"})

class RequestOtpView(FormView):
    template_name = "otp/request.html"
    form_class = EmailPhoneOtpRequestForm
    success_url = reverse_lazy("otp:login")

    def form_valid(self, form: Any) -> HttpResponseRedirect:
        form.request_otp()
        valid_email = getattr(form, 'valid_email', False)
        valid_phone = getattr(form, 'valid_phone', False)
        if not valid_email and not valid_phone:
            raise ValueError(_("Form must have either valid phone or email"))
        self.request.session["email_phone"] = form.cleaned_data.get("email_phone")
        self.request.session['email_phone_field_type'] = 'email' if valid_email else 'phone'
        next_url = self.request.GET.get('next', '')
        if next_url != '':
            self.request.session['next'] = next_url
        logger.debug(f"Setting session in RequestOtpView form_valid: {self.request.session['email_phone_field_type']}")
        return super().form_valid(form)

class OtpLoginView(FormView):
    template_name = "otp/login.html"
    form_class = OtpVerificationForm
    # success_url = "/"

    def get_form_kwargs(self) -> dict[str, Any]:
        kw = super().get_form_kwargs()
        logger.debug("Inside FormView get_form_kwargs")
        kw['initial'] = {}
        kw['initial']['email_phone'] = self.request.session.get('email_phone')
        kw['initial']['type'] = self.request.session.get("email_phone_field_type")
        next_url = self.request.GET.get('next', '')
        if next_url == '':
            next_url = self.request.session.get('next', '')
        else:
            self.request.session['next'] = next_url
        if next_url != '':
            kw['initial']['field_next'] = next_url
        logger.debug(f"Setting type to {self.request.session.get('email_phone_field_type')}")
        # if self.request.session.get('email', "") != "":
        #     kw['initial']['email'] = self.request.session.get('email')
        # if self.request.session.get("phone", "") != "":
        #     kw['initial']['phone'] = str(self.request.session.get('phone'))
        #     logger.debug(f"FormView form_kwargs: type: {type(kw['initial']['phone'])}")

        return kw

    def form_valid(self, form: Any) -> HttpResponseRedirect:
        login(self.request, form.get_user())
        next_url = form.cleaned_data.get('field_next', '')
        logger.debug(f"Form valid logged in, next_url: {next_url}")
        if next_url == '' or next_url == '/':
            next_url = self.get_success_url()
            logger.debug(f"next_url from get_success_url: {next_url}")
        # return HttpResponseRedirect(self.get_success_url())
        return HttpResponseRedirect(next_url)

    def get_success_url(self):
        #url = super().get_success_url()
        url = ''
        next_url = self.request.GET.get('next', '')
        if next_url == '':
            next_url = self.request.session.get('next', '')
        if next_url != '':
            url = next_url
        logger.debug(f"success_url: {url}")
        if self.request.user.is_staff:
            return get_absolute_url(site_id=settings.SELLER_SITE_ID, view_name='dashboard:index')
        else:
            if hasattr(self.request.user, 'seller_registration'):
                if self.request.user.seller_registration.approved:
                    return get_absolute_url(site_id=settings.SELLER_SITE_ID, view_name='onboarding-wizard')
                else:
                    return get_absolute_url(site_id=settings.SELLER_SITE_ID, view_name='notapproved')

        return url
