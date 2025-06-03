from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.dispatch import receiver
from allauth.socialaccount.signals import social_account_added
from phonenumber_field.formfields import PhoneNumberField as PhoneNumberFormField
from allauth.socialaccount.models import SocialAccount, SocialToken, SocialLogin
from django.contrib.auth import get_user, get_user_model
from django.urls import reverse
from shop.apps.main.utils.sms import send_phone_otp
import requests
import logging
import base64
import json

from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings
from django.db.models import FileField
from django.db.models.fields import (
    BinaryField,
    DateField,
    DateTimeField,
    TimeField,
)
from django.utils import dateparse
from django.utils.encoding import force_bytes, force_str
from phonenumber_field.modelfields import PhoneNumberField
from shop.apps.main.utils.urls import get_absolute_url

User = get_user_model()

logger = logging.getLogger(__package__)

SERIALIZED_DB_FIELD_PREFIX = "_db_"


def serialize_instance(instance):
    """
    Since Django 1.6 items added to the session are no longer pickled,
    but JSON encoded by default. We are storing partially complete models
    in the session (user, account, token, ...). We cannot use standard
    Django serialization, as these are models are not "complete" yet.
    Serialization will start complaining about missing relations et al.
    """
    data = {}
    for k, v in instance.__dict__.items():
        if k.startswith("_") or callable(v):
            continue
        try:
            field = instance._meta.get_field(k)
            if isinstance(field, BinaryField):
                if v is not None:
                    v = force_str(base64.b64encode(v))
            elif isinstance(field, FileField):
                if v and not isinstance(v, str):
                    v = {
                        "name": v.name,
                        "content": base64.b64encode(v.read()).decode("ascii"),
                    }
            elif isinstance(field, PhoneNumberField):
                if v is not None:
                    v = v.as_international
            # Check if the field is serializable. If not, we'll fall back
            # to serializing the DB values which should cover most use cases.
            try:
                json.dumps(v, cls=DjangoJSONEncoder)
            except TypeError:
                v = field.get_prep_value(v)
                k = SERIALIZED_DB_FIELD_PREFIX + k
        except FieldDoesNotExist:
            pass
        data[k] = v
    return json.loads(json.dumps(data, cls=DjangoJSONEncoder))


def deserialize_instance(model, data):
    ret = model()
    for k, v in data.items():
        is_db_value = False
        if k.startswith(SERIALIZED_DB_FIELD_PREFIX):
            k = k[len(SERIALIZED_DB_FIELD_PREFIX) :]
            is_db_value = True
        if v is not None:
            try:
                f = model._meta.get_field(k)
                if isinstance(f, DateTimeField):
                    v = dateparse.parse_datetime(v)
                elif isinstance(f, TimeField):
                    v = dateparse.parse_time(v)
                elif isinstance(f, DateField):
                    v = dateparse.parse_date(v)
                elif isinstance(f, BinaryField):
                    v = force_bytes(base64.b64decode(force_bytes(v)))
                elif isinstance(f, FileField):
                    if isinstance(v, dict):
                        v = ContentFile(base64.b64decode(v["content"]), name=v["name"])
                elif isinstance(f, PhoneNumberField):
                    v = PhoneNumberField(v).to_python(v)
                elif is_db_value:
                    try:
                        # This is quite an ugly hack, but will cover most
                        # use cases...
                        # The signature of `from_db_value` changed in Django 3
                        # https://docs.djangoproject.com/en/3.0/releases/3.0/#features-removed-in-3-0
                        v = f.from_db_value(v, None, None)
                    except Exception:
                        raise ImproperlyConfigured(
                            "Unable to auto serialize field '{}', custom"
                            " serialization override required".format(k)
                        )
            except FieldDoesNotExist:
                pass
        setattr(ret, k, v)
    return ret

@receiver(social_account_added, sender=SocialLogin)
def after_social_account_added(request, sociallogin, *args, **kwargs):
    logger.debug("inside after_social_account_added. using token:")
    logger.debug(sociallogin.token.token)
    headers = {
        "Authorization": f"Bearer {sociallogin.token.token}"
    }
    params = {
        "personFields": "phoneNumbers"
    }
    response = requests.get("https://people.googleapis.com/v1/people/me", headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        logger.debug(data)
        if 'phoneNumbers' in data:
            for phone in data['phoneNumbers']:
                if phone['metadata']['primary'] == True and phone['type'] == 'mobile':
                    # This is the mobile number
                    sociallogin.user.phone = phone['canonicalForm']
                    sociallogin.user.phone_verified = phone['metadata']['verified']
                    sociallogin.user.save()
    else:
        logger.critical("Failed to access googleapis.com - Status code and response below:")
        logger.debug(response.status_code)
        logger.debug(response.text)

class AccountAdapter(DefaultAccountAdapter):
    def phone_form_field(self, **kwargs):
        kwargs['region'] = 'IN'
        return PhoneNumberFormField(**kwargs)

    def get_login_redirect_url(self, request):
        logger.debug(request.user.is_staff)
        if request.user.is_staff:
            return get_absolute_url(site_id=settings.SELLER_SITE_ID, view_name='dashboard:index')
        else:
            return get_absolute_url(site_id=settings.DEFAULT_SITE_ID)

    def get_phone_field(self, request):
        return PhoneNumberFormField(region='IN')

    def get_phone(self, user):
        if user.phone is not None:
            return user.phone.as_international, user.phone_verified
        else:
            return "", False

    def set_phone(self, user, phone_number, verified):
        user.phone = phone_number
        user.phone_verified = verified
        user.save()

    def set_phone_verified(self, user, phone):
        user.phone_verified = True
        user.save()

    def get_user_by_phone(self, phone):
        try:
            return User.objects.get(phone=phone)
        except User.DoesNotExist:
            return None

    def send_verification_code_sms(self, user, phone, code, **kwargs):
        logger.debug(f"Sending code: {code} to phone: {phone} for user: {user}")
        resp = send_phone_otp(user.phone, code)
        logger.debug("Got reponse after sending an SMS")
        logger.debug(resp)

    def send_unknown_account_sms(self, phone, **kwargs):
        # Phonenumber sent to unknown account
        pass

class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def on_authentication_error(self, request, provider, error=None, exception=None, extra_context=None):
        logger.debug('Social Auth Failure')
        logger.debug('Error:')
        logger.debug(error)
        logger.debug("Exception:")
        logger.debug(exception)
        logger.debug("extra_context:")
        logger.debug(extra_context)
        return super().on_authentication_error(request, provider, error, exception, extra_context)

    def deserialize_instance(self, model, data):
        return deserialize_instance(model, data)

    def serialize_instance(self, instance):
        return serialize_instance(instance)


    # def populate_user(self, request, sociallogin, data):
    #     user = super().populate_user(request, sociallogin, data)
    #     logger.debug("Inside populate_user")
    #     logger.debug(dir(sociallogin))
    #     extra_data = sociallogin.account.extra_data
    #     logger.debug(extra_data)
    #     logger.debug(data)
    #     logger.debug("token:")
    #     logger.debug(sociallogin.token)
    #     headers = {
    #         "Authorization": f"Bearer {sociallogin.token}"
    #     }
    #     params = {
    #         "personFields": "phoneNumbers"
    #     }
    #     response = requests.get("https://people.googleapis.com/v1/people/me", headers=headers, params=params)
    #     if response.status_code == 200:
    #         logger.debug(response.json())
    #     else:
    #         logger.debug(response.status_code)
    #         logger.debug(response.text)
    #     return user
