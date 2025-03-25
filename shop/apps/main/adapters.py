from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.dispatch import receiver
from allauth.socialaccount.signals import social_account_added
from phonenumber_field.formfields import PhoneNumberField
from allauth.socialaccount.models import SocialAccount, SocialToken, SocialLogin
import requests
import logging

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
    def get_phone_field(self, request):
        return PhoneNumberField(region='IN')

    def set_phone_number(self, user, phone_number):
        user.phone = phone_number
        user.save()

    def verify_phone_number(self, user):
        user.phone_verified = True
        user.save()

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
