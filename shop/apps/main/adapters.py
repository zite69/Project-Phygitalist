from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.dispatch import receiver
from allauth.socialaccount.signals import social_account_added
from phonenumber_field.formfields import PhoneNumberField
from allauth.socialaccount.models import SocialAccount, SocialToken, SocialLogin
from django.contrib.auth import get_user, get_user_model
from shop.apps.main.utils.sms import send_phone_otp
import requests
import logging

User = get_user_model()

logger = logging.getLogger(__package__)

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
        return PhoneNumberField(**kwargs)

    def get_phone_field(self, request):
        return PhoneNumberField(region='IN')

    def get_phone(self, user):
        return user.phone.as_international, user.phone_verified

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
