from typing import Any
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.generic.edit import FormView
from django.views.generic import View
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import login
from .forms import EmailOtpRequestForm, PhoneOtpRequestForm, OtpVerificationForm
import logging
from shop.apps.main.utils.common import dump

logger = logging.getLogger('shop.apps.otp.views')

class RequestOtpView(View):
    template_name = "otp/request.html"

    def get_context_data(self, **kwargs):
        if 'email_form' not in kwargs:
            kwargs['email_form'] =  EmailOtpRequestForm()
        if 'phone_form' not in kwargs:
            kwargs['phone_form'] = PhoneOtpRequestForm()

        return kwargs
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())
    
    def post(self, request, *args, **kwargs):
        ctxt = {}
        logger.debug(f"Inside request Otp post view")
        #logger.debug(request.POST)

        if 'email-form' in request.POST:
            email_form = EmailOtpRequestForm(request.POST)
            logger.debug(f"Inside email got form: {email_form}")

            if email_form.is_valid():
                logger.debug(f"Got cleaned email: {email_form.cleaned_data.get('email')}")
                request.session['email'] = email_form.cleaned_data.get('email')
                return redirect(reverse("otp:login"))
            else:
                ctxt['email_form'] = email_form
        elif 'phone-form' in request.POST:
            phone_form = PhoneOtpRequestForm(request.POST)
            logger.debug(f"Inside phone got form")

            if phone_form.is_valid():
                #logger.debug(f"Phone form is valid")
                logger.debug(f"Phone: {phone_form.cleaned_data.get('phone')}")
                #logger.debug(f"Type of Phone: {type(phone_form.cleaned_data.get('phone'))}")
                phone_form.request_otp()
                request.session['phone'] = phone_form.cleaned_data.get('phone').national_number
                return redirect(reverse("otp:login"))
            else:
                logger.debug("Errors in the phone_form")
                ctxt['phone_form'] = phone_form

        return render(request, self.template_name, self.get_context_data(**ctxt))

class OtpLoginView(FormView):
    template_name = "otp/login.html"
    form_class = OtpVerificationForm
    success_url = "/"

    def get_form_kwargs(self) -> dict[str, Any]:
        kw = super().get_form_kwargs()
        logger.debug("Inside FormView get_form_kwargs")
        kw['initial'] = {}
        if self.request.session.get('email', "") != "":
            kw['initial']['email'] = self.request.session.get('email')
        if self.request.session.get("phone", "") != "":
            kw['initial']['phone'] = str(self.request.session.get('phone'))
            logger.debug(f"FormView form_kwargs: type: {type(kw['initial']['phone'])}")
            
        return kw
    
    def form_valid(self, form: Any) -> HttpResponse:
        login(self.request, form.get_user())
        return HttpResponseRedirect(self.get_success_url())


