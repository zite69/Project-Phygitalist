#from django.apps import AppConfig
from django.urls import include, path, re_path
from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarConfig
import logging

logger = logging.getLogger("shop.apps.registration.apps")

def check_gst(wizard):
    user = wizard.request.user
    if user.seller_registration and (user.seller_registration.gstin != '' or user.seller_registration.pan != ''):
       return False
    return True

WIZARD_CONDITION_DICT = {
    "username": lambda w: not w.request.user.is_authenticated,
    "mobile": lambda w: w.request.user.is_anonymous or (w.request.user.is_authenticated and not w.request.user.phone_verified),
    "email": lambda w: w.request.user.is_anonymous or (w.request.user.is_authenticated and not w.request.user.email_verified),
    "password": lambda w: w.request.user.is_anonymous or not w.request.user.has_usable_password(),
    "business": lambda w: not hasattr(w.request.user, 'seller_registration'),
    "gst": lambda w: not hasattr(w.request.user,'seller_registration') or (w.request.user.seller_registration.gstin == '' and w.request.user.seller_registration.pan == ''),
    "pincode": lambda w: not hasattr(w.request.user,'seller_registration') or w.request.user.seller_registration.pincode == None,
    "language": lambda w: not hasattr(w.request.user, 'preferences') or w.request.user.preferences['second_language'] == '',
    "shop": lambda w: w.request.user.is_anonymous or not hasattr(w.request.user, 'seller_registration') or w.request.user.seller_registration.shop_name == '',
    "product1": True,
    "product2": True,
    "product3": True,
    "congrats": True,
    "thanks": True
}
# WIZARD_CONDITION_DICT = {
#     "username": lambda w: False, # not w.request.user.is_authenticated,
#     "mobile": lambda w: True, #w.request.user.is_anonymous or (w.request.user.is_authenticated and not w.request.user.phone_verified),
#     "email": lambda w: False, #w.request.user.is_anonymous or (w.request.user.is_authenticated and not w.request.user.email_verified),
#     "password": lambda w: False, #,w.request.user.is_anonymous or not w.request.user.has_usable_password(),
#     "business": lambda w: False, #not hasattr(w.request.user, 'seller_registration'),
#     "gst": lambda w: False, #not hasattr(w.request.user,'seller_registration') or (w.request.user.seller_registration.gstin == '' and w.request.user.seller_registration.pan == ''),
#     "pincode": lambda w: True, #not hasattr(w.request.user,'seller_registration') or w.request.user.seller_registration.pincode == None,
#     "language": lambda w: False, #not hasattr(w.request.user, 'preferences') or w.request.user.preferences['second_language'] == '',
#     "shop": lambda w: False, #w.request.user.is_anonymous or not hasattr(w.request.user, 'seller_registration') or w.request.user.seller_registration.shop_name == '',
#     "product1": False,
#     "product2": False,
#     "product3": False,
#     "congrats": True,
#     "thanks": True
# }

class RegistrationConfig(OscarConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop.apps.registration'
    label = 'registration'
    verbose_name = _("Registration")
    namespace = 'registration'

    def ready(self):
        super().ready()

        from .views import SellerRegistrationWizard, UsernameAvailableJson, SendPhoneOtpJson, SendEmailOtpJson, PincodeListJson

        self.home_view = SellerRegistrationWizard
        self.username_available = UsernameAvailableJson
        self.send_phone_otp = SendPhoneOtpJson
        self.send_email_otp = SendEmailOtpJson
        self.pincode_search = PincodeListJson

    def get_urls(self):
        from shop.apps.registration.forms import  (
            AddBusiness, EmailAndOtp, GstPan, MobileAndOtp, UserName, PincodeForm, LanguagePreference, ShopDetails, AddProduct,
            SELLER_REGISTRATION_FORMS
        )
        urls = super().get_urls()
        urls += [
            path('', self.home_view.as_view(SELLER_REGISTRATION_FORMS, condition_dict=WIZARD_CONDITION_DICT), name='home'),
            path('api/username/', self.username_available.as_view(), name='username_available'),
            path('api/phoneotp/', self.send_phone_otp.as_view(), name='phone_otp'),
            path('api/emailotp/', self.send_email_otp.as_view(), name='email_otp'),
            path('api/pincode/', self.pincode_search.as_view(), name='pincode_search'),
        ]
        logger.debug(f"home_view: {self.home_view}")
        return urls
