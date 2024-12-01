from django.shortcuts import render
from django.conf import settings
from django.views.generic import TemplateView, View
from django.http import HttpResponseRedirect, JsonResponse
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core import serializers
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from shop.apps.main.utils.sms import send_phone_otp
from shop.apps.main.utils.email import send_email_verification
from shop.apps.main.utils.urls import get_site_base_uri
from shop.apps.otp.utils import generate_otp
from phonenumber_field.phonenumber import PhoneNumber
from phonenumber_field.validators import validate_international_phonenumber
from formtools.wizard.views import SessionWizardView
from shop.apps.main.models import State, Pincode
from .forms import REGISTRATION_FORM_TEMPLATES
from .models import seller_registration_filestorage

import json
import logging
import os

logger = logging.getLogger("shop.apps.registration.views")

User = get_user_model()


class HomeView(TemplateView):
    template_name = 'registration/home.html'


class SellerRegistrationWizard(SessionWizardView):
    template_name = 'registration/seller.html'
    file_storage = seller_registration_filestorage

    def get_template_names(self):
        logger.debug(f"Returning template: {REGISTRATION_FORM_TEMPLATES[self.steps.current]} for step {self.steps.current}")
        return [REGISTRATION_FORM_TEMPLATES[self.steps.current]]

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)
        kwargs['request'] = self.request
        return kwargs

    def done(self, form_list, **kwargs):
        # from shop.apps.main.utils.email import send_email_seller_welcome
        # from shop.apps.registration.models import SellerRegistration
        # logger.debug(f"Completed the wizard: form_list {form_list}")
        # if self.request.user.seller_registration.approval_status == SellerRegistration.STATUS_IN_PROGRESS:
        #     send_email_seller_welcome(self.request.user)
        #     self.request.user.seller_registration.approval_status = SellerRegistration.STATUS_PENDING
        #     self.request.user.seller_registration.save()
        # return super().done(form_list, **kwargs)
        url = get_site_base_uri(site_id=settings.DEFAULT_SITE_ID)
        return HttpResponseRedirect(url)

    def get_auth_next_step(self, step):
        if not self.request.user.phone_verified:
            return 'mobile'
        if not self.request.user.email_verified:
            return 'email'
        return 'business'

    # def get_form(self, step=None, data=None, files=None):
    #     logger.debug("Inside get_form")
    #     if self.request.user.is_authenticated and (step is None or int(step) < 4):
    #         logger.debug("User is authenticated")
    #         step = self.get_auth_next_step(step)

    #     if step is None:
    #         step = self.steps.current
    #         logger.debug(f"Step was none, now it is set to {step}")
    #         #logger.debug(f"{type(step)}")

    #     step = 'business'
    #     #logger.debug(dir(self))
    #     logger.debug(f"We are sending some step: {step} ")

    #     return super().get_form(step, data, files)

class UsernameAvailableJson(View):
   def post(self, request, *args, **kwargs):
       try:
           data = json.loads(request.body)
       except json.JSONDecodeError:
           return JsonResponse({"error": "Invalid json input"})

       username = data.get('username', '')
       logger.debug(f"got username: {username}")

       if username == "":
            return JsonResponse({"error": "Username is required"})

       try:
           User.objects.get(username=username)
           return JsonResponse({"status": "unavailable"})
       except User.DoesNotExist:
           return JsonResponse({"status": "available"})

class JsonRequestResponseMixin(object):
    def get_data(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid json input"})

        return data

    def get_user(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return request.user

        user_id = request.session.get('user_id', -1)
        if user_id == -1:
            return JsonResponse({"error": "System error: User not found in session"})


        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({"error": "Username is not available"})
        logger.debug(f"Found user in session: {user}")

        return user


class SendPhoneOtpJson(View, JsonRequestResponseMixin):

    def post(self, request, *args, **kwargs):
        data = self.get_data(request, *args, **kwargs)
        if type(data) == JsonResponse:
            return data

        user = self.get_user(request, *args, **kwargs)
        if type(user) == JsonResponse:
            return user

        phone = data.get('phone', '')
        if phone == '':
            return JsonResponse({"error": "Phone number is required"})

        try:
           validate_international_phonenumber(phone)
        except ValidationError:
            return JsonResponse({"error": "Invalid phone number"})

        phone_object = PhoneNumber.from_string(phone_number=phone)
        logger.debug(phone_object)

        try:
            pu = User.objects.get(phone=phone_object)
            if pu.id != user.id:
                return JsonResponse({"error": "Phone number already in use, please login with your number to proceed"})
        except User.DoesNotExist:
            user.phone=phone_object
            user.save()

        otp = generate_otp(user, phone=True)
        logger.debug(f"created user: {user} sending phone: {user.phone} an otp: {otp}")

        resp = send_phone_otp(user.phone, otp, sms_template=settings.SMS_VALIDATE_PHONE_OTP)
        logger.debug(f"Got response after sending phone otp: {resp}")

        return JsonResponse({"status": "success", "id": user.id})

class SendEmailOtpJson(View, JsonRequestResponseMixin):
    def post(self, request, *args, **kwargs):
        data = self.get_data(request, *args, **kwargs)
        if type(data) == JsonResponse:
            return data

        user = self.get_user(request, *args, **kwargs)
        if type(user) == JsonResponse:
            return user

        email = data.get('email', '')
        if email == '':
            return JsonResponse({"error": "Email address cannot be blank"})

        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({"error": "Invalid email address, please check and re-enter"})


        try:
            User.objects.get(email=email)
            return JsonResponse({"error": "Email address already in use, please login with your email or user to proceed"})
        except User.DoesNotExist:
            pass

        user.email = email
        user.save()

        otp = generate_otp(user, email=True)
        logger.debug(f"created user: {user}, sending email: {user.email} an otp: {otp}")

        resp = send_email_verification(email, otp)
        #logger.debug(f"Response after sending email otp: {resp}")

        logger.debug(f"Sent {user.email} an otp: {otp}")

        return JsonResponse({"status": "success", "id": user.id})

@method_decorator(cache_page(60*30), name='dispatch')
class PincodeListJson(View, JsonRequestResponseMixin):
    def get(self, request, *args, **kwargs):
        pincode_prefix = request.GET.get('term', '')
        action = request.GET.get('action', 'pincode')
        if len(pincode_prefix) < 3:
            return JsonResponse([])

        results = []
        if action == 'pincode':
            results = list(Pincode.objects.filter(pincode__startswith=pincode_prefix).order_by('pincode').values_list('pincode', flat=True).distinct()[:20])
        elif action == 'place':
            pincodes = Pincode.objects.filter(pincode=pincode_prefix).order_by('office')
            results = [ {'id': p.id, 'place': p.office} for p in pincodes ]

        #data = [p.pincode for p in results]
        #data = serializers.serialize('json', results)
        return JsonResponse(results, safe=False)

class ValidatePhoneOtp(View, JsonRequestResponseMixin):

    def post(self, request, *args, **kwargs):
        data = self.get_data(request, *args, **kwargs)
        if type(data) == JsonResponse:
            return data
