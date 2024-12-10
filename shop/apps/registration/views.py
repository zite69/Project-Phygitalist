from collections import OrderedDict
from django.shortcuts import render
from django.conf import settings
from django import forms
from django.views.generic import TemplateView, View
from django.http import HttpResponseRedirect, JsonResponse
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core import serializers
from django.core.exceptions import SuspiciousOperation
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from datetime import datetime
from shop.apps.main.utils.sms import send_phone_otp
from shop.apps.main.utils.email import send_email_verification
from shop.apps.main.utils.urls import get_site_base_uri
from shop.apps.otp.utils import generate_otp
from phonenumber_field.phonenumber import PhoneNumber
from phonenumber_field.validators import validate_international_phonenumber
from formtools.wizard.views import SessionWizardView
from formtools.wizard.forms import ManagementForm
from shop.apps.main.models import State, Postoffice
from .forms import REGISTRATION_FORM_TEMPLATES
from .models import seller_registration_filestorage

import json
import logging
import os
import traceback

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

    def process_step(self, form):
        logger.debug(f"in process_step. form: {form}")
        logger.debug(form)
        logger.debug(f"current step: {self.steps.current}")
        return super().process_step(form)

    def render_goto_step(self, goto_step, **kwargs):
        logger.debug("inside render_goto_step")
        logger.debug(f"goto_step: {goto_step}")
        logger.debug(f"kwargs: {kwargs}")
        return super().render_goto_step(goto_step, **kwargs)

    def render_revalidation_failure(self, step, form, **kwargs):
        logger.debug("inside render_revalidation_failure")
        logger.debug(f"step: {step}")
        logger.debug(f"form: {form.__class__}")
        return super().render_revalidation_failure(step, form, **kwargs)

    def _get_debug_form_list(self):
        form_list = OrderedDict()
        condition_list = OrderedDict()
        condition_result_list = OrderedDict()
        for form_key, form_class in self.form_list.items():
            # try to fetch the value from condition list, by default, the form
            # gets passed to the new list.
            condition = self.condition_dict.get(form_key, True)
            # logger.debug(f"got condition: {condition} for form_key: {form_key}")
            if callable(condition):
                # call the value if needed, passes the current instance.
                condition_list[form_key] = condition
                result = condition(self)
                condition_result_list[form_key] = result
                condition = result
            if condition:
                form_list[form_key] = form_class
        return form_list, condition_list, condition_result_list


    def post(self, *args, **kwargs):
        """
        This method handles POST requests.

        The wizard will render either the current step (if form validation
        wasn't successful), the next step (if the current step was stored
        successful) or the done view (if no more steps are available)
        """
        # Look for a wizard_goto_step element in the posted data which
        # contains a valid step name. If one was found, render the requested
        # form. (This makes stepping back a lot easier).
        wizard_goto_step = self.request.POST.get('wizard_goto_step', None)
        if wizard_goto_step and wizard_goto_step in self.get_form_list():
            return self.render_goto_step(wizard_goto_step)

        # Check if form was refreshed
        management_form = ManagementForm(self.request.POST, prefix=self.prefix)
        if not management_form.is_valid():
            raise SuspiciousOperation(_('ManagementForm data is missing or has been tampered.'))

        form_current_step = management_form.cleaned_data['current_step']
        if (form_current_step != self.steps.current and
                self.storage.current_step is not None):
            logger.debug(f"Changing current step from: {self.steps.current} to: {form_current_step}")
            # form refreshed, change current step
            self.storage.current_step = form_current_step
        logger.debug(f"form_current_step: {form_current_step}")
        # if settings.DEBUG and settings.DEBUG_WIZARD_FORM_STEP == form_current_step:
        #     self.errors = {"error": f"Failed to get step: {self.steps.current}"}
        #     ts = datetime.now().strftime("%Y-%m-%d:%H:%M:%S")
        #     trace_filename = f"{ts}.log"
        #     pickle_forms_filename = f"{ts}-forms.pkl"
        #     pickle_condition_filename = f"{ts}-condition.pkl"
        #     pickle_result_filename = f"{ts}-result.pkl"
        #     logger.debug(f"Got a 500 error in the wizard and self.request.user: {self.request.user}")
        #     user_id = self.request.session.get('user_id', -1)
        #     if user_id != -1:
        #         user = User.objects.get(id=user_id)
        #     else:
        #         user = None
        #     if self.request.user and self.request.user.username:
        #        trace_filename = f"{self.request.user.username}-{trace_filename}"
        #        pickle_forms_filename = f"{self.request.user.username}-{pickle_forms_filename}"
        #        pickle_condition_filename = f"{self.request.user.username}-{pickle_condition_filename}"
        #        pickle_result_filename = f"{self.request.user.username}-{pickle_result_filename}"
        #     elif user:
        #         user_id = self.request.session.get('user_id', -1)
        #         trace_filename = f"{user.username}-{trace_filename}"
        #         pickle_forms_filename = f"{user.username}-{pickle_forms_filename}"
        #         pickle_condition_filename = f"{user.username}-{pickle_condition_filename}"
        #         pickle_result_filename = f"{user.username}-{pickle_result_filename}"

        #     forms_list, condition_list, result_list = self._get_debug_form_list()
        #     import dill as pickle
        #     with open(os.path.join(settings.LOG_DIR, pickle_forms_filename), "wb") as fp:
        #         pickle.dump(forms_list, fp)
        #     with open(os.path.join(settings.LOG_DIR, pickle_condition_filename), "wb") as fp:
        #         pickle.dump(condition_list, fp)
        #     with open(os.path.join(settings.LOG_DIR, pickle_result_filename), "wb") as fp:
        #         pickle.dump(result_list, fp)
        #     with open(os.path.join(settings.LOG_DIR, trace_filename), "w") as f:
        #         f.write("".join(traceback.format_stack()))

        #     return self.render_goto_step('error', user=user)

        # get the form for the current step
        try:
            form = self.get_form(data=self.request.POST, files=self.request.FILES)
        except KeyError as e:
            self.errors = {"error": f"Failed to get step: {self.steps.current}"}
            ts = datetime.now().strftime("%Y-%m-%d:%H:%M:%S")
            trace_filename = f"{ts}.log"
            pickle_forms_filename = f"{ts}-forms.pkl"
            pickle_condition_filename = f"{ts}-condition.pkl"
            pickle_result_filename = f"{ts}-result.pkl"
            logger.debug(f"Got a 500 error in the wizard and self.request.user: {self.request.user}")
            if self.request.user and self.request.user.username:
               trace_filename = f"{self.request.user.username}-{trace_filename}"
               pickle_forms_filename = f"{self.request.user.username}-{pickle_forms_filename}"
               pickle_condition_filename = f"{self.request.user.username}-{pickle_condition_filename}"
               pickle_result_filename = f"{self.request.user.username}-{pickle_result_filename}"
            elif self.request.session.get('user_id', -1) != -1:
                user_id = self.request.session.get('user_id', -1)
                user = User.objects.get(id=user_id)
                trace_filename = f"{user.username}-{trace_filename}"
                pickle_forms_filename = f"{user.username}-{pickle_forms_filename}"
                pickle_condition_filename = f"{user.username}-{pickle_condition_filename}"
                pickle_result_filename = f"{user.username}-{pickle_result_filename}"

            forms_list, condition_list, result_list = self._get_debug_form_list()
            import dill as pickle
            with open(os.path.join(settings.LOG_DIR, pickle_forms_filename), "wb") as fp:
                pickle.dump(forms_list, fp)
            with open(os.path.join(settings.LOG_DIR, pickle_condition_filename), "wb") as fp:
                pickle.dump(condition_list, fp)
            with open(os.path.join(settings.LOG_DIR, pickle_result_filename), "wb") as fp:
                pickle.dump(result_list, fp)
            with open(os.path.join(settings.LOG_DIR, trace_filename), "w") as f:
                f.write("".join(traceback.format_stack()))

            return self.render_goto_step('error')


        # and try to validate
        if form.is_valid():
            # if the form is valid, store the cleaned data and files.
            self.storage.set_step_data(self.steps.current, self.process_step(form))
            self.storage.set_step_files(self.steps.current, self.process_step_files(form))

            # check if the current step is the last step
            if self.steps.current == self.steps.last:
                # no more steps, render done view
                return self.render_done(form, **kwargs)
            else:
                # proceed to the next step
                return self.render_next_step(form)
        return self.render(form)


    def get_form(self, step=None, data=None, files=None):
        logger.debug("inside wizard get_form")
        if step is None:
            step = self.steps.current
            logger.debug(f"step argument passed in is None so it is now set to current: {step}")
        # form_list = self.get_form_list()
        form_class = self.get_form_list()[step]
        # prepare the kwargs for the form instance.
        kwargs = self.get_form_kwargs(step)
        kwargs.update({
            'data': data,
            'files': files,
            'prefix': self.get_form_prefix(step, form_class),
            'initial': self.get_form_initial(step),
        })
        if issubclass(form_class, (forms.ModelForm, forms.models.BaseInlineFormSet)):
            # If the form is based on ModelForm or InlineFormSet,
            # add instance if available and not previously set.
            kwargs.setdefault('instance', self.get_form_instance(step))
        elif issubclass(form_class, forms.models.BaseModelFormSet):
            # If the form is based on ModelFormSet, add queryset if available
            # and not previous set.
            kwargs.setdefault('queryset', self.get_form_instance(step))
        return form_class(**kwargs)

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


        if User.objects.filter(email=email).exclude(pk=user.pk).exists():
            return JsonResponse({"error": "Email address already in use, please login with your email or user to proceed"})

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
            results = list(Postoffice.objects.filter(pincode__startswith=pincode_prefix).order_by('pincode').values_list('pincode', flat=True).distinct()[:20])
        elif action == 'place':
            pincodes = Postoffice.objects.filter(pincode=pincode_prefix).order_by('office')
            results = [ {'id': p.id, 'place': p.office} for p in pincodes ]

        #data = [p.pincode for p in results]
        #data = serializers.serialize('json', results)
        return JsonResponse(results, safe=False)

class ValidatePhoneOtp(View, JsonRequestResponseMixin):

    def post(self, request, *args, **kwargs):
        data = self.get_data(request, *args, **kwargs)
        if type(data) == JsonResponse:
            return data
