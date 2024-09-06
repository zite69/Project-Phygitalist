from typing import Any
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.generic.edit import FormView
from django.views.generic import View
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.contrib.auth import login
from django.utils.translation import gettext_lazy as _
from shop.apps.main.utils.common import dump
from .forms import EmailOtpRequestForm, PhoneOtpRequestForm, OtpVerificationForm, EmailPhoneOtpRequestForm
import logging

logger = logging.getLogger('shop.apps.otp.views')

class RequestOtpView(FormView):
    template_name = "otp/request.html"
    form_class = EmailPhoneOtpRequestForm
    success_url = reverse_lazy("otp:login")

    def form_valid(self, form: Any) -> HttpResponse:
        form.request_otp()
        valid_email = getattr(form, 'valid_email', False)
        valid_phone = getattr(form, 'valid_phone', False)
        if not valid_email and not valid_phone:
            raise ValueError(_("Form must have either valid phone or email"))
        self.request.session["email_phone"] = form.cleaned_data.get("email_phone")
        self.request.session['email_phone_field_type'] = 'email' if valid_email else 'phone'
        logger.debug(f"Setting session in RequestOtpView form_valid: {self.request.session['email_phone_field_type']}")
        return super().form_valid(form)

    # def post(self, request, *args, **kwargs):
    #     ctxt = {}
    #     logger.debug(f"Inside request Otp post view")
    #     #logger.debug(request.POST)

    #     if 'email-form' in request.POST:
    #         email_form = EmailOtpRequestForm(request.POST)
    #         logger.debug(f"Inside email got form: {email_form}")

    #         if email_form.is_valid():
    #             logger.debug(f"Got cleaned email: {email_form.cleaned_data.get('email')}")
    #             request.session['email'] = email_form.cleaned_data.get('email')
    #             return redirect(reverse("otp:login"))
    #         else:
    #             ctxt['email_form'] = email_form
    #     elif 'phone-form' in request.POST:
    #         phone_form = PhoneOtpRequestForm(request.POST)
    #         logger.debug(f"Inside phone got form")

    #         if phone_form.is_valid():
    #             #logger.debug(f"Phone form is valid")
    #             logger.debug(f"Phone: {phone_form.cleaned_data.get('phone')}")
    #             #logger.debug(f"Type of Phone: {type(phone_form.cleaned_data.get('phone'))}")
    #             phone_form.request_otp()
    #             request.session['phone'] = phone_form.cleaned_data.get('phone').national_number
    #             return redirect(reverse("otp:login"))
    #         else:
    #             logger.debug("Errors in the phone_form")
    #             ctxt['phone_form'] = phone_form

    #     return render(request, self.template_name, self.get_context_data(**ctxt))

class OtpLoginView(FormView):
    template_name = "otp/login.html"
    form_class = OtpVerificationForm
    success_url = "/"

    def get_form_kwargs(self) -> dict[str, Any]:
        kw = super().get_form_kwargs()
        logger.debug("Inside FormView get_form_kwargs")
        kw['initial'] = {}
        kw['initial']['email_phone'] = self.request.session.get('email_phone')
        kw['initial']['type'] = self.request.session.get("email_phone_field_type")
        logger.debug(f"Setting type to {self.request.session.get('email_phone_field_type')}")
        # if self.request.session.get('email', "") != "":
        #     kw['initial']['email'] = self.request.session.get('email')
        # if self.request.session.get("phone", "") != "":
        #     kw['initial']['phone'] = str(self.request.session.get('phone'))
        #     logger.debug(f"FormView form_kwargs: type: {type(kw['initial']['phone'])}")

        return kw

    def form_valid(self, form: Any) -> HttpResponse:
        login(self.request, form.get_user())
        return HttpResponseRedirect(self.get_success_url())


